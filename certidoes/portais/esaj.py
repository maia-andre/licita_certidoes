"""Pedido da certidão de falências no e-SAJ/TJSP (REQ-12, modo automatizado).

O programa preenche modelo, pessoa jurídica, razão social, CNPJ e o e-mail informado pelo servidor.
O servidor confere, marca a confirmação, resolve o reCAPTCHA e clica em "Enviar".
Aceito o pedido, o programa consulta logo em "Visualizar Certidão" (sem captcha): quando a empresa não tem
apontamentos, a certidão costuma sair na hora e o resultado é o PDF. Senão, o resultado é o Pedido, e as
instruções chegam por e-mail.
"""
import dataclasses
import datetime as dt
import pathlib
import re
import time

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeout
from playwright.sync_api import sync_playwright

from certidoes.cnpj import formatar
from certidoes.portais.comum import PASTA_PADRAO, NaoEmitida, Pedido, PortalErro, Pulada, guardar_pdf

__all__ = ["obter_pedido_falencia", "INSTRUCAO", "email_valido"]

URL = "https://esaj.tjsp.jus.br/sco/abrirCadastro.do"
URL_DOWNLOAD = "https://esaj.tjsp.jus.br/sco/abrirDownload.do"
CONSULTAS = 3  # tentativas em "Visualizar Certidão" logo depois do pedido
INTERVALO_CONSULTA_S = 10
TEMPO_DOWNLOAD_MS = 15 * 1000
CONSULTANDO = "Pedido nº {numero} aceito. Consultando se a certidão já foi liberada..."
NAO_LIBERADA = ('A certidão ainda não estava liberada na consulta feita logo após o pedido. Acompanhe pelo '
                'e-mail ou em "Visualizar Certidão", no e-SAJ, com o número e a data do pedido.')
MODELO = "CERT DIST - FALÊNCIAS, CONCORDATAS E RECUPERAÇÕES"
TEMPO_LIMITE_MS = 10 * 60 * 1000
TEMPO_FORMULARIO_MS = 30 * 1000
INTERVALO_MS = 500
INSTRUCAO = ('Na janela do Chromium, confira os dados, marque "Confirmo que as informações acima estão '
             'corretamente preenchidas" e clique em "Enviar". Se o reCAPTCHA pedir, resolva o desafio.')
FECHADA = "A janela do portal foi fechada antes do envio do pedido."
SUCESSO = "pedido foi cadastrado com sucesso"

_EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s.]{2,}")
_NUMERO = re.compile(r"N[úu]mero do Pedido\s*:\s*(\d+)", re.IGNORECASE)
_DATA = re.compile(r"Data do Pedido\s*:\s*(\d{2}/\d{2}/\d{4})", re.IGNORECASE)
_PRAZO = re.compile(r"Prazo m[áa]ximo para libera[çc][ãa]o da Certid[ãa]o\s*(\d+)\s*dias", re.IGNORECASE)


def email_valido(email) -> bool:
    """E-mail plausível para o TJSP mandar as instruções (CE-12)."""
    return isinstance(email, str) and len(email) <= 254 and _EMAIL.fullmatch(email.strip()) is not None


def ler_confirmacao(texto: str, email: str) -> Pedido | None:
    """Pedido mostrado na página de resultado do e-SAJ; None se o pedido ainda não foi aceito."""
    if SUCESSO not in texto.lower():
        return None

    def achar(padrao):
        encontrado = padrao.search(texto)
        return encontrado.group(1) if encontrado else None

    return Pedido(numero=achar(_NUMERO), data=achar(_DATA), email=email, prazo_dias=achar(_PRAZO))


def _verificar(sinal):
    if sinal is not None:
        sinal.verificar()


def _preencher(pagina, cnpj, razao_social, email):
    pagina.locator("#cdModelo").select_option(label=MODELO)
    pagina.locator("#tpPessoaJ").check()
    razao = pagina.locator("#nmCadastroJ")
    razao.wait_for(state="visible")
    razao.fill(razao_social)
    campo_cnpj = pagina.locator("[id='identity.nuCnpjFormatado']")
    campo_cnpj.click()
    campo_cnpj.press_sequentially(cnpj, delay=30)  # o campo tem máscara; fill() não dispara a formatação
    pagina.locator("[id='identity.solicitante.deEmail']").fill(email)
    if re.sub(r"\D", "", campo_cnpj.input_value()) != cnpj:
        raise PortalErro(f"O CNPJ não ficou preenchido no e-SAJ. Confira o formulário ({formatar(cnpj)}).")
    pagina.locator("#confirmacaoInformacoes").focus()


def _esperar_pedido(pagina, email, sinal, tempo_limite_ms):
    """Espera a página de resultado em passos curtos, para atender o servidor (pular/fechar) sem demora."""
    fim = time.monotonic() + tempo_limite_ms / 1000
    while True:
        _verificar(sinal)
        if pagina.is_closed():
            raise PortalErro(FECHADA)
        try:
            pedido = ler_confirmacao(pagina.locator("body").inner_text(timeout=2000), email)
        except PlaywrightError:
            pedido = None  # página trocando depois do envio
        if pedido:
            return pedido
        if time.monotonic() >= fim:
            raise PortalErro("Tempo esgotado aguardando o envio do pedido.")
        try:
            pagina.wait_for_timeout(INTERVALO_MS)
        except PlaywrightError as erro:
            raise PortalErro(FECHADA) from erro


def _digitos(texto):
    return "".join(c for c in texto if c.isdigit())


def _consultar_uma_vez(pagina, pedido, cnpj, url_download, tempo_download_ms):
    """Uma consulta em "Visualizar Certidão". Devolve os bytes do PDF, ou None se não veio certidão."""
    pagina.goto(url_download, wait_until="domcontentloaded", timeout=TEMPO_FORMULARIO_MS)
    pagina.locator("[id='identity.nuPedido']").fill(pedido.numero)
    data = pagina.locator("[id='identity.dtPedido']")
    data.click()
    data.press_sequentially(_digitos(pedido.data), delay=30)  # campo com máscara
    pagina.locator("#tpPessoaJ").check()
    campo_cnpj = pagina.locator("[id='identity.nuCnpjFormatado']")
    campo_cnpj.click()
    campo_cnpj.press_sequentially(cnpj, delay=30)
    try:
        with pagina.expect_download(timeout=tempo_download_ms) as baixado:
            pagina.locator("#pbConsultar").click()
    except PlaywrightTimeout:
        return None  # sem download: certidão ainda não liberada (ou o portal mostrou outra mensagem)
    dados = pathlib.Path(baixado.value.path()).read_bytes()
    return dados if dados[:4] == b"%PDF" else None


def _baixar_certidao(pagina, pedido, cnpj, url_download, sinal, consultas, intervalo_s,
                     tempo_download_ms=TEMPO_DOWNLOAD_MS):
    """Tenta baixar a certidão do pedido recém-aceito. Nunca levanta: o pedido já foi feito.

    Pular durante a consulta só encerra a consulta; o item fica com o pedido.
    """
    if not (pedido.numero and pedido.data):
        return None
    for tentativa in range(consultas):
        try:
            if tentativa:
                fim = time.monotonic() + intervalo_s
                while time.monotonic() < fim:
                    _verificar(sinal)
                    pagina.wait_for_timeout(INTERVALO_MS)
            _verificar(sinal)
            dados = _consultar_uma_vez(pagina, pedido, cnpj, url_download, tempo_download_ms)
        except (Pulada, NaoEmitida, PlaywrightError):
            return None  # servidor pulou, fechou a janela ou a tela de consulta mudou
        if dados:
            return dados
    return None


def obter_pedido_falencia(
    cnpj,
    ao_aguardar=None,
    sinal=None,
    *,
    razao_social,
    email,
    avisar=None,
    url=URL,
    url_download=URL_DOWNLOAD,
    pasta_base=PASTA_PADRAO,
    headless=False,
    tempo_limite_ms=TEMPO_LIMITE_MS,
    consultas=CONSULTAS,
    intervalo_consulta_s=INTERVALO_CONSULTA_S,
    tempo_download_ms=TEMPO_DOWNLOAD_MS,
    agora=None,
) -> Pedido | pathlib.Path:
    """Abre o pedido no e-SAJ, preenche os dados conhecidos, espera o servidor enviar e tenta baixar a certidão.

    Devolve o caminho do PDF, se a certidão já estiver liberada, ou o Pedido.
    `avisar(mensagem)` informa a tela de que o pedido foi aceito e a consulta começou.
    """
    if not email_valido(email):
        raise PortalErro("E-mail inválido para o pedido no e-SAJ.")
    email = email.strip()
    with sync_playwright() as p:
        try:
            navegador = p.chromium.launch(headless=headless)
        except PlaywrightError as erro:
            raise PortalErro("Não foi possível abrir o navegador Chromium.") from erro
        try:
            pagina = navegador.new_context(accept_downloads=True).new_page()
            pagina.set_default_timeout(min(tempo_limite_ms, TEMPO_FORMULARIO_MS))
            try:
                pagina.goto(url, wait_until="domcontentloaded", timeout=TEMPO_FORMULARIO_MS)
            except PlaywrightError as erro:
                raise PortalErro("Não foi possível abrir o e-SAJ.") from erro
            _verificar(sinal)
            try:
                _preencher(pagina, cnpj, razao_social, email)
            except PlaywrightTimeout as erro:
                raise PortalErro("O formulário do e-SAJ mudou ou não carregou.") from erro
            except PlaywrightError as erro:
                if pagina.is_closed():
                    raise PortalErro(FECHADA) from erro
                raise PortalErro("O formulário do e-SAJ mudou ou não carregou.") from erro
            if ao_aguardar:
                ao_aguardar()
            pedido = _esperar_pedido(pagina, email, sinal, tempo_limite_ms)
            if avisar:
                avisar(CONSULTANDO.format(numero=pedido.numero or "?"))
            dados = _baixar_certidao(pagina, pedido, cnpj, url_download, sinal, consultas, intervalo_consulta_s,
                                     tempo_download_ms)
            if dados:
                return guardar_pdf(dados, cnpj, pasta_base, "falencia", agora or dt.datetime.now())
            if pedido.numero and pedido.data:
                return dataclasses.replace(pedido, observacao=NAO_LIBERADA)
            return pedido
        finally:
            try:
                navegador.close()
            except PlaywrightError:
                pass  # já fechado pelo servidor
