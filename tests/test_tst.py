import datetime as dt
import time
from unittest.mock import MagicMock

import pytest
from playwright.sync_api import Error as PlaywrightError

from certidoes.portais import tst
from certidoes.portais.tst import PortalErro, obter_cndt

CNPJ = "11222333000181"
AGORA = dt.datetime(2026, 11, 6, 14, 30, 5)


def obter(portal, caminho, tmp_path, tempo_limite_ms=10_000):
    return obter_cndt(
        CNPJ,
        pasta_base=tmp_path,
        url=portal.url + caminho,
        headless=True,
        tempo_limite_ms=tempo_limite_ms,
        agora=AGORA,
    )


def test_guarda_pdf_na_pasta_do_cnpj(portal, tmp_path):
    arquivo = obter(portal, "/ok", tmp_path)
    assert arquivo == tmp_path / CNPJ / "cndt-20261106-143005.pdf"
    assert arquivo.read_bytes().startswith(b"%PDF")


def test_preenche_cnpj_e_deixa_o_captcha_para_o_servidor(portal, tmp_path):
    obter(portal, "/ok", tmp_path)
    assert portal.registro == {"cnpj": CNPJ, "captcha": "", "foco": "captcha-resposta"}


def test_avisa_que_aguarda_o_servidor_depois_de_preencher_o_cnpj(portal, tmp_path):
    avisos = []
    obter_cndt(CNPJ, ao_aguardar=lambda: avisos.append("aguardando"), pasta_base=tmp_path,
               url=portal.url + "/ok", headless=True, tempo_limite_ms=10_000, agora=AGORA)
    assert avisos == ["aguardando"]


def test_captcha_errado_continua_aguardando_ate_o_servidor_acertar(portal, tmp_path):
    arquivo = obter(portal, "/captcha-errado", tmp_path)
    assert arquivo.read_bytes().startswith(b"%PDF")


def test_arquivo_que_nao_e_pdf_gera_erro_e_nao_fica_guardado(portal, tmp_path):
    with pytest.raises(PortalErro, match="não é um PDF"):
        obter(portal, "/nao-pdf", tmp_path)
    assert not list(tmp_path.rglob("*.pdf"))


def test_tempo_esgotado_gera_erro_claro(portal, tmp_path):
    with pytest.raises(PortalErro, match="Tempo esgotado"):
        obter(portal, "/parado", tmp_path, tempo_limite_ms=500)


def test_janela_fechada_gera_erro_claro(monkeypatch, tmp_path):
    # Página fechada pelo próprio servidor não dá para provocar por script no portal falso.
    playwright = MagicMock()
    navegador = playwright.return_value.__enter__.return_value.chromium.launch.return_value
    pagina = navegador.new_context.return_value.new_page.return_value
    pagina.is_closed.return_value = False
    pagina.wait_for_timeout.side_effect = PlaywrightError("Target page, context or browser has been closed")
    monkeypatch.setattr(tst, "sync_playwright", playwright)
    with pytest.raises(PortalErro, match="fechada"):
        tst.obter_cndt(CNPJ, pasta_base=tmp_path)
    navegador.close.assert_called_once()


def test_navegador_que_nao_abre_gera_erro_claro(monkeypatch, tmp_path):
    # Ex.: Chromium do Playwright não instalado ou bloqueado na máquina.
    playwright = MagicMock()
    chromium = playwright.return_value.__enter__.return_value.chromium
    chromium.launch.side_effect = PlaywrightError("Executable doesn't exist")
    monkeypatch.setattr(tst, "sync_playwright", playwright)
    with pytest.raises(PortalErro, match="navegador"):
        tst.obter_cndt(CNPJ, pasta_base=tmp_path)


def test_portal_fora_do_ar_gera_erro_claro(tmp_path):
    with pytest.raises(PortalErro, match="Não foi possível"):
        obter_cndt(CNPJ, pasta_base=tmp_path, url="http://127.0.0.1:9/", headless=True, tempo_limite_ms=2_000)


def test_formulario_diferente_do_esperado_gera_erro_claro(portal, tmp_path):
    with pytest.raises(PortalErro, match="formulário"):
        obter(portal, "/sem-formulario", tmp_path, tempo_limite_ms=500)


@pytest.mark.parametrize("fechar", [
    lambda pagina: pagina.close(),  # servidor fecha a aba
    lambda pagina: pagina.context.browser.close(),  # servidor fecha o Chromium inteiro
])
def test_janela_fechada_durante_a_espera_vira_erro_claro(portal, tmp_path, monkeypatch, fechar):
    # CE-08 com Playwright real: fecha de verdade logo antes da espera pelo download.
    original = tst._esperar_download

    def fechar_e_esperar(pagina, *args):
        fechar(pagina)
        return original(pagina, *args)

    monkeypatch.setattr(tst, "_esperar_download", fechar_e_esperar)
    with pytest.raises(PortalErro, match="fechada"):
        obter(portal, "/parado", tmp_path)
    assert not list(tmp_path.rglob("*.pdf"))


def test_servidor_pula_o_item_enquanto_o_tst_espera(portal, tmp_path):
    import threading

    from certidoes.portais.comum import Pulada, SinalServidor

    sinal = SinalServidor()
    inicio = time.monotonic()
    with pytest.raises(Pulada):
        obter_cndt(CNPJ, ao_aguardar=lambda: threading.Timer(0.3, sinal.pular).start(), sinal=sinal,
                   pasta_base=tmp_path, url=portal.url + "/parado", headless=True, tempo_limite_ms=20_000, agora=AGORA)
    assert time.monotonic() - inicio < 10  # não esperou o tempo-limite
    assert not list(tmp_path.rglob("*.pdf"))
