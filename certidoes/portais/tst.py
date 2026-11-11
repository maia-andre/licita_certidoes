"""CNDT no portal do TST: preenche o CNPJ, o servidor resolve o captcha e o PDF é guardado."""
import datetime as dt
import pathlib
import tempfile

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeout
from playwright.sync_api import sync_playwright

URL = "https://cndt-certidao.tst.jus.br/gerarCertidao"
PASTA_PADRAO = pathlib.Path.home() / "Certidoes"
TEMPO_LIMITE_MS = 5 * 60 * 1000
TEMPO_FORMULARIO_MS = 30 * 1000


class PortalErro(Exception):
    pass


def _guardar(origem: pathlib.Path, cnpj: str, pasta_base: pathlib.Path, agora: dt.datetime) -> pathlib.Path:
    if origem.read_bytes()[:4] != b"%PDF":
        raise PortalErro("O arquivo recebido do portal não é um PDF.")
    pasta = pasta_base / cnpj
    pasta.mkdir(parents=True, exist_ok=True)
    destino = pasta / f"cndt-{agora:%Y%m%d-%H%M%S}.pdf"
    destino.write_bytes(origem.read_bytes())
    return destino


def obter_cndt(
    cnpj,
    pasta_base=PASTA_PADRAO,
    url=URL,
    headless=False,
    tempo_limite_ms=TEMPO_LIMITE_MS,
    agora=None,
) -> pathlib.Path:
    """Abre o portal e espera o servidor resolver o captcha e emitir a certidão."""
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
            except PlaywrightTimeout as erro:
                if pagina.locator("#cpfCnpj").count() == 0:
                    raise PortalErro("O formulário do portal do TST mudou ou não carregou.") from erro
                raise PortalErro("Tempo esgotado aguardando a emissão da certidão.") from erro
            except PlaywrightError as erro:
                raise PortalErro("A janela do portal foi fechada antes da emissão.") from erro
            with tempfile.TemporaryDirectory() as temporaria:
                origem = pathlib.Path(temporaria) / "certidao"
                baixado.value.save_as(origem)
                return _guardar(origem, cnpj, pathlib.Path(pasta_base), agora or dt.datetime.now())
        finally:
            navegador.close()
