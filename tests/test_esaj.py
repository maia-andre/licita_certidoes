import datetime as dt
import threading
import time
from unittest.mock import MagicMock

import pytest
from playwright.sync_api import Error as PlaywrightError

from certidoes import leitura
from certidoes.pdf import texto_do_pdf
from certidoes.portais import esaj
from certidoes.portais.comum import Pedido, PortalErro, Pulada, SinalServidor
from tests.conftest import ESAJ_CONSULTA_ESPERADA

CNPJ = "11222333000181"
RAZAO = "EMPRESA FICTICIA LTDA"
EMAIL = "compras@exemplo.gov.br"


def pedir(portal, caminho, tempo_limite_ms=10_000, consulta="/esaj-consulta-pendente", **kw):
    kw.setdefault("consultas", 1)
    kw.setdefault("intervalo_consulta_s", 0)
    kw.setdefault("tempo_download_ms", 1_000)
    return esaj.obter_pedido_falencia(CNPJ, razao_social=RAZAO, email=kw.pop("email", EMAIL),
                                      url=portal.url + caminho, url_download=portal.url + consulta,
                                      headless=True, tempo_limite_ms=tempo_limite_ms, **kw)


def test_pedido_enviado_pelo_servidor_devolve_numero_data_e_prazo(portal):
    assert pedir(portal, "/esaj") == Pedido(numero="101890915", data="12/11/2026", email=EMAIL, prazo_dias="05",
                                            observacao=esaj.NAO_LIBERADA)


def test_certidao_ja_liberada_e_baixada_logo_apos_o_pedido(portal, tmp_path):
    avisos = []
    arquivo = pedir(portal, "/esaj", consulta="/esaj-consulta", pasta_base=tmp_path, avisar=avisos.append,
                    agora=dt.datetime(2026, 11, 12, 15, 0, 0))
    assert arquivo == tmp_path / CNPJ / "falencia-20261112-150000.pdf"
    assert "VERIFICOU NADA CONSTAR" in leitura.normalizar(texto_do_pdf(arquivo.read_bytes()))
    assert portal.consultas == [ESAJ_CONSULTA_ESPERADA]  # número, data, pessoa jurídica e CNPJ do pedido
    assert avisos == ["Pedido nº 101890915 aceito. Consultando se a certidão já foi liberada..."]


def test_certidao_nao_liberada_tenta_algumas_vezes_e_fica_o_pedido(portal, tmp_path):
    resultado = pedir(portal, "/esaj", pasta_base=tmp_path, consultas=3, intervalo_consulta_s=0.2)
    assert isinstance(resultado, Pedido) and resultado.numero == "101890915"
    assert resultado.observacao == esaj.NAO_LIBERADA
    assert len(portal.consultas) == 3
    assert not list(tmp_path.rglob("*.pdf"))


def test_pular_durante_a_consulta_encerra_a_consulta_e_mantem_o_pedido(portal):
    sinal = SinalServidor()
    resultado = pedir(portal, "/esaj", sinal=sinal, avisar=lambda mensagem: sinal.pular(),
                      consultas=3, intervalo_consulta_s=5)
    assert isinstance(resultado, Pedido) and resultado.numero == "101890915"
    assert portal.consultas == []


def test_pedido_sem_numero_nao_e_consultado():
    pagina = MagicMock()
    assert esaj._baixar_certidao(pagina, Pedido(), CNPJ, "http://x", None, 3, 0) is None
    pagina.goto.assert_not_called()


def test_tela_de_consulta_diferente_nao_derruba_o_pedido():
    pagina = MagicMock()
    pagina.goto.side_effect = PlaywrightError("net::ERR")
    assert esaj._baixar_certidao(pagina, Pedido("1", "12/11/2026"), CNPJ, "http://x", None, 2, 0) is None


def test_preenche_os_dados_conhecidos_e_deixa_confirmacao_e_envio_para_o_servidor(portal):
    pedir(portal, "/esaj")
    assert portal.registro == {
        "modelo": "CERT DIST - FALÊNCIAS, CONCORDATAS E RECUPERAÇÕES", "pessoa": "J", "razao": RAZAO,
        "cnpj": "11.222.333/0001-81", "email": EMAIL, "confirmado": "false",
    }


def test_avisa_que_aguarda_o_servidor_depois_de_preencher(portal):
    avisos = []
    pedir(portal, "/esaj", ao_aguardar=lambda: avisos.append(portal.registro))
    assert avisos == [None]  # avisou antes de o servidor agir


def test_email_com_espacos_vai_limpo(portal):
    pedido = pedir(portal, "/esaj", email=f"  {EMAIL} ")
    assert portal.registro["email"] == EMAIL
    assert pedido.email == EMAIL


@pytest.mark.parametrize("email", ["", "   ", "sem-arroba", "a@b", "a b@c.com", None])
def test_email_invalido_nao_abre_o_portal(monkeypatch, email):
    # CE-12: o pedido não é enviado.
    playwright = MagicMock()
    monkeypatch.setattr(esaj, "sync_playwright", playwright)
    with pytest.raises(PortalErro, match="E-mail inválido"):
        esaj.obter_pedido_falencia(CNPJ, razao_social=RAZAO, email=email)
    playwright.assert_not_called()


@pytest.mark.parametrize("email,valido", [
    ("compras@sjc.sp.gov.br", True), ("a.b+c@exemplo.com", True), (" x@y.com.br ", True),
    ("", False), ("x@y", False), ("x@y.c", False), ("x@@y.com", False), ("x y@z.com", False), (None, False),
    (123, False), ("a" * 250 + "@x.com", False),
])
def test_email_valido(email, valido):
    assert esaj.email_valido(email) is valido


def test_tempo_esgotado_gera_erro_claro(portal):
    with pytest.raises(PortalErro, match="Tempo esgotado"):
        pedir(portal, "/esaj-parado", tempo_limite_ms=1_000)


def test_formulario_diferente_do_esperado_gera_erro_claro(portal):
    with pytest.raises(PortalErro, match="formulário do e-SAJ"):
        pedir(portal, "/sem-formulario", tempo_limite_ms=1_000)


def test_portal_fora_do_ar_gera_erro_claro():
    with pytest.raises(PortalErro, match="Não foi possível abrir o e-SAJ"):
        esaj.obter_pedido_falencia(CNPJ, razao_social=RAZAO, email=EMAIL, url="http://127.0.0.1:9/",
                                   headless=True, tempo_limite_ms=2_000)


def test_navegador_que_nao_abre_gera_erro_claro(monkeypatch):
    playwright = MagicMock()
    playwright.return_value.__enter__.return_value.chromium.launch.side_effect = PlaywrightError("Executable")
    monkeypatch.setattr(esaj, "sync_playwright", playwright)
    with pytest.raises(PortalErro, match="navegador"):
        esaj.obter_pedido_falencia(CNPJ, razao_social=RAZAO, email=EMAIL)


@pytest.mark.parametrize("fechar", [
    lambda pagina: pagina.close(),  # servidor fecha a aba
    lambda pagina: pagina.context.browser.close(),  # servidor fecha o Chromium inteiro
])
def test_janela_fechada_antes_do_envio_vira_erro_claro(portal, monkeypatch, fechar):
    original = esaj._esperar_pedido

    def fechar_e_esperar(pagina, *args):
        fechar(pagina)
        return original(pagina, *args)

    monkeypatch.setattr(esaj, "_esperar_pedido", fechar_e_esperar)
    with pytest.raises(PortalErro, match="fechada antes do envio"):
        pedir(portal, "/esaj-parado")


def test_servidor_pula_enquanto_o_esaj_espera(portal):
    sinal = SinalServidor()
    inicio = time.monotonic()
    with pytest.raises(Pulada):
        pedir(portal, "/esaj-parado", tempo_limite_ms=20_000, sinal=sinal,
              ao_aguardar=lambda: threading.Timer(0.3, sinal.pular).start())
    assert time.monotonic() - inicio < 10


# Texto da página de resultado real (12/11/2026), com o e-mail trocado.
RESULTADO_REAL = """Cadastro de Pedido de Certidão
Orientações
 O seu pedido foi cadastrado com sucesso. Para emissão da Certidão, serão encaminhadas instruções no e-mail informado, ou anote o Número e a Data do seu Pedido, para posterior emissão da Certidão.
 Prazo máximo para liberação da Certidão 05 dias.
Dados para Emissão da Certidão
Número do Pedido
:
\t101890915
Data do Pedido
:
\t12/11/2026
Resumo do Pedido
Modelo
:
\tCERT DIST - FALÊNCIAS, CONCORDATAS E RECUPERAÇÕES
Razão Social
:
\tVIACAO SAENS PENA LTDA
"""


def test_le_a_pagina_de_resultado_real():
    assert esaj.ler_confirmacao(RESULTADO_REAL, EMAIL) == Pedido("101890915", "12/11/2026", EMAIL, "05")


def test_formulario_ainda_nao_enviado_nao_e_pedido():
    assert esaj.ler_confirmacao("Cadastro de Pedido de Certidão\nModelo*\n:\nE-Mail*", EMAIL) is None


def test_sucesso_sem_numero_ainda_e_pedido_feito():
    pedido = esaj.ler_confirmacao("O seu pedido foi cadastrado com sucesso.", EMAIL)
    assert pedido == Pedido(numero=None, data=None, email=EMAIL, prazo_dias=None)
