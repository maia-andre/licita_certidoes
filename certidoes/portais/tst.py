"""CNDT no portal do TST (modo automatizado): preenche o CNPJ, o servidor resolve o captcha e o PDF é guardado."""
import datetime as dt
import pathlib
import tempfile

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeout
from playwright.sync_api import sync_playwright

from certidoes.portais.comum import PASTA_PADRAO, PortalErro, guardar_pdf

__all__ = ["obter_cndt", "PortalErro", "INSTRUCAO"]

URL = "https://cndt-certidao.tst.jus.br/gerarCertidao"
TEMPO_LIMITE_MS = 5 * 60 * 1000
TEMPO_FORMULARIO_MS = 30 * 1000
INSTRUCAO = 'Na janela do Chromium, digite os caracteres da imagem e clique em "Emitir Certidão".'


def obter_cndt(
    cnpj,
    ao_aguardar=None,
    pasta_base=PASTA_PADRAO,
    url=URL,
    headless=False,
    tempo_limite_ms=TEMPO_LIMITE_MS,
    agora=None,
) -> pathlib.Path:
    """Abre o portal e espera o servidor resolver o captcha e emitir a certidão.

    `ao_aguardar` é chamado quando o CNPJ já está preenchido e falta o servidor agir.
    """
    with sync_playwright() as p:
        try:
            navegador = p.chromium.launch(headless=headless)
        except PlaywrightError as erro:
            raise PortalErro("Não foi possível abrir o navegador Chromium.") from erro
        try:
            pagina = navegador.new_context(accept_downloads=True).new_page()
            try:
                pagina.goto(url, wait_until="domcontentloaded", timeout=TEMPO_FORMULARIO_MS)
            except PlaywrightError as erro:
                raise PortalErro("Não foi possível abrir o portal do TST.") from erro
            try:
                with pagina.expect_download(timeout=tempo_limite_ms) as baixado:
                    campo = pagina.locator("#cpfCnpj")
                    campo.wait_for(timeout=min(tempo_limite_ms, TEMPO_FORMULARIO_MS))
                    campo.fill(cnpj)
                    pagina.locator("#captcha-resposta").focus()
                    if ao_aguardar:
                        ao_aguardar()
            except PlaywrightTimeout as erro:
                if pagina.locator("#cpfCnpj").count() == 0:
                    raise PortalErro("O formulário do portal do TST mudou ou não carregou.") from erro
                raise PortalErro("Tempo esgotado aguardando a emissão da certidão.") from erro
            except PlaywrightError as erro:
                raise PortalErro("A janela do portal foi fechada antes da emissão.") from erro
            with tempfile.TemporaryDirectory() as temporaria:
                origem = pathlib.Path(temporaria) / "certidao"
                baixado.value.save_as(origem)
                return guardar_pdf(origem.read_bytes(), cnpj, pasta_base, "cndt", agora or dt.datetime.now())
        finally:
            navegador.close()
