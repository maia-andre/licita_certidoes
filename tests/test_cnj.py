import datetime as dt

import pytest

from certidoes import leitura
from certidoes.pdf import texto_do_pdf
from certidoes.portais import cnj
from certidoes.portais.comum import PortalErro, Pulada, SinalServidor

CNPJ = "11222333000181"
AGORA = dt.datetime(2026, 11, 12, 17, 24, 0)


@pytest.fixture(autouse=True)
def sem_proxy(monkeypatch):
    # Na rede da prefeitura, o proxy do Windows intercepta até 127.0.0.1.
    monkeypatch.setenv("NO_PROXY", "127.0.0.1")


def obter(portal, base, tmp_path, **kw):
    return cnj.obter_certidao(CNPJ, pasta_base=tmp_path, url_base=portal.url + base, tempo_limite_s=10, agora=AGORA,
                              **kw)


def test_sem_condenacoes_baixa_a_certidao_negativa(portal, tmp_path):
    arquivo = obter(portal, "/cnj", tmp_path)
    assert arquivo == tmp_path / CNPJ / "improbidade-cnj-20261112-172400.pdf"
    lido = leitura.ler(leitura.ler_improbidade_cnj, texto_do_pdf(arquivo.read_bytes()), CNPJ)
    assert lido.situacao == leitura.NADA_CONSTA
    assert portal.cnj[-1]["certidao"] == {"tipoCertidao": "N", "cpfCnpj": CNPJ, "tipoPessoa": "J"}


def test_verifica_as_condenacoes_como_a_pagina_do_cnj_e_sem_dados_do_usuario(portal, tmp_path):
    obter(portal, "/cnj", tmp_path)
    verificacao = portal.cnj[0]
    assert verificacao["verificacao"]["rs"] == ["verificaRequeridoPossuiCertidao"]
    assert verificacao["verificacao"]["rsargs[]"][:3] == [CNPJ, "J", "I"]  # o nome vazio some no parse_qs
    assert {p["agente"] for p in portal.cnj} == {"licita_certidoes"}


def test_com_condenacoes_baixa_a_certidao_com_registros_e_nao_presume_nada_consta(portal, tmp_path):
    arquivo = obter(portal, "/cnj-registros", tmp_path)
    assert portal.cnj[-1]["certidao"]["tipoCertidao"] == "P"
    lido = leitura.ler(leitura.ler_improbidade_cnj, texto_do_pdf(arquivo.read_bytes()), CNPJ)
    assert lido.situacao == leitura.CONFERIR


def test_resposta_inesperada_da_verificacao_gera_erro_sem_baixar_certidao(portal, tmp_path):
    with pytest.raises(PortalErro, match="inesperado"):
        obter(portal, "/cnj-estranho", tmp_path)
    assert not any("certidao" in p for p in portal.cnj)
    assert not list(tmp_path.rglob("*.pdf"))


def test_portal_fora_do_ar_gera_erro_claro(tmp_path):
    with pytest.raises(PortalErro, match="não respondeu"):
        cnj.obter_certidao(CNPJ, pasta_base=tmp_path, url_base="http://127.0.0.1:9", tempo_limite_s=2)


def test_pular_antes_da_consulta_nao_faz_nenhum_pedido(portal, tmp_path):
    sinal = SinalServidor()
    sinal.pular()
    with pytest.raises(Pulada):
        obter(portal, "/cnj", tmp_path, sinal=sinal)
    assert portal.cnj == []


def test_nunca_chama_ao_aguardar(portal, tmp_path):
    avisos = []
    obter(portal, "/cnj", tmp_path, ao_aguardar=lambda: avisos.append("x"))
    assert avisos == []
