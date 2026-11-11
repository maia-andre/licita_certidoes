"""CNDT no portal do TST (modo automatizado): preenche o CNPJ, o servidor resolve o captcha e o PDF é guardado."""
import datetime as dt
import pathlib
import tempfile
import time

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeout
from playwright.sync_api import sync_playwright

from certidoes.portais.comum import PASTA_PADRAO, PortalErro, guardar_pdf

__all__ = ["obter_cndt", "PortalErro", "INSTRUCAO"]

URL = "https://cndt-certidao.tst.jus.br/gerarCertidao"
TEMPO_LIMITE_MS = 5 * 60 * 1000
TEMPO_FORMULARIO_MS = 30 * 1000
INTERVALO_MS = 500
INSTRUCAO = 'Na janela do Chromium, digite os caracteres da imagem e clique em "Emitir Certidão".'
FECHADA = "A janela do portal foi fechada antes da emissão."


def _verificar(sinal):
    if sinal is not None:
        sinal.verificar()


def _esperar_download(pagina, baixados, sinal, tempo_limite_ms):
    """Espera o download em passos curtos, para atender o servidor (pular/fechar) sem demora."""
    fim = time.monotonic() + tempo_limite_ms / 1000
    while not baixados:
        _verificar(sinal)
        if pagina.is_closed():
            raise PortalErro(FECHADA)
        if time.monotonic() >= fim:
            raise PortalErro("Tempo esgotado aguardando a emissão da certidão.")
        try:
            pagina.wait_for_timeout(INTERVALO_MS)
        except PlaywrightError as erro:
            raise PortalErro(FECHADA) from erro
    return baixados[0]


def obter_cndt(
    cnpj,
    ao_aguardar=None,
    sinal=None,
    pasta_base=PASTA_PADRAO,
    url=URL,
    headless=False,
    tempo_limite_ms=TEMPO_LIMITE_MS,
    agora=None,
) -> pathlib.Path:
    """Abre o portal e espera o servidor resolver o captcha e emitir a certidão.

    `ao_aguardar` é chamado quando o CNPJ já está preenchido e falta o servidor agir.
    `sinal` (SinalServidor) permite ao servidor pular o item pela tela.
    """
    with sync_playwright() as p:
        try:
            navegador = p.chromium.launch(headless=headless)
        except PlaywrightError as erro:
            raise PortalErro("Não foi possível abrir o navegador Chromium.") from erro
        try:
            pagina = navegador.new_context(accept_downloads=True).new_page()
            baixados = []
            pagina.on("download", lambda download: baixados.append(download))
            try:
                pagina.goto(url, wait_until="domcontentloaded", timeout=TEMPO_FORMULARIO_MS)
            except PlaywrightError as erro:
                raise PortalErro("Não foi possível abrir o portal do TST.") from erro
            _verificar(sinal)
            try:
                campo = pagina.locator("#cpfCnpj")
                campo.wait_for(timeout=min(tempo_limite_ms, TEMPO_FORMULARIO_MS))
                campo.fill(cnpj)
                pagina.locator("#captcha-resposta").focus()
            except PlaywrightTimeout as erro:
                raise PortalErro("O formulário do portal do TST mudou ou não carregou.") from erro
            except PlaywrightError as erro:
                raise PortalErro(FECHADA) from erro
            if ao_aguardar:
                ao_aguardar()
            baixado = _esperar_download(pagina, baixados, sinal, tempo_limite_ms)
            with tempfile.TemporaryDirectory() as temporaria:
                origem = pathlib.Path(temporaria) / "certidao"
                try:
                    baixado.save_as(origem)
                except PlaywrightError as erro:
                    raise PortalErro(FECHADA) from erro
                return guardar_pdf(origem.read_bytes(), cnpj, pasta_base, "cndt", agora or dt.datetime.now())
        finally:
            try:
                navegador.close()
            except PlaywrightError:
                pass  # já fechado pelo servidor
