"""Consulta Consolidada do TCU contra um portal falso local (RNF-06)."""
import datetime as dt
import socket

import pytest

from certidoes import leitura
from certidoes.pdf import texto_do_pdf
from certidoes.portais import tcu
from certidoes.portais.comum import PortalErro, Pulada, SinalServidor

CNPJ = "11222333000181"
AGORA = dt.datetime(2026, 11, 12, 11, 28, 12)


@pytest.fixture(autouse=True)
def sem_proxy(monkeypatch):
    """O portal falso é local: não passa pelo proxy que o Windows da rede da prefeitura configura."""
    monkeypatch.setenv("NO_PROXY", "127.0.0.1")


def consultar(portal, tmp_path, caminho="/tcu/{cnpj}", **kw):
    return tcu.obter_consulta(CNPJ, pasta_base=tmp_path, url=portal.url + caminho, agora=AGORA, **kw)


def test_baixa_o_pdf_e_guarda_na_pasta_do_cnpj(portal, tmp_path):
    arquivo = consultar(portal, tmp_path)
    assert arquivo == tmp_path / CNPJ / "sancoes-tcu-20261112-112812.pdf"
    texto = texto_do_pdf(arquivo.read_bytes())
    assert leitura.ler(leitura.ler_sancoes_tcu, texto, CNPJ).situacao == leitura.NADA_CONSTA


def test_pede_o_pdf_pelo_cnpj_sem_dados_do_usuario(portal, tmp_path):
    consultar(portal, tmp_path)
    assert portal.tcu == [{"caminho": f"/tcu/{CNPJ}", "accept": "application/pdf", "agente": "licita_certidoes"}]


def test_sem_captcha_nao_chama_o_servidor(portal, tmp_path):
    chamadas = []
    consultar(portal, tmp_path, ao_aguardar=lambda: chamadas.append(1))
    assert chamadas == []


def test_erro_do_portal_vira_falha_com_o_codigo(portal, tmp_path):
    with pytest.raises(PortalErro, match="erro 503"):
        consultar(portal, tmp_path, caminho="/tcu-erro/{cnpj}")
    assert not (tmp_path / CNPJ).exists()


def test_resposta_que_nao_e_pdf_vira_falha(portal, tmp_path):
    with pytest.raises(PortalErro, match="não é um PDF"):
        consultar(portal, tmp_path, caminho="/tcu-html/{cnpj}")


def test_portal_fora_do_ar_vira_falha(tmp_path):
    with socket.socket() as livre:
        livre.bind(("127.0.0.1", 0))
        porta = livre.getsockname()[1]
    with pytest.raises(PortalErro, match="não respondeu"):
        tcu.obter_consulta(CNPJ, pasta_base=tmp_path, url=f"http://127.0.0.1:{porta}/tcu/{{cnpj}}", tempo_limite_s=5)


def test_pular_antes_da_consulta_nao_acessa_o_portal(portal, tmp_path):
    sinal = SinalServidor()
    sinal.pular()
    with pytest.raises(Pulada):
        consultar(portal, tmp_path, sinal=sinal)
    assert portal.tcu == []
