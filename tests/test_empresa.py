import io
import json
import urllib.error

import pytest

from certidoes import empresa as emp

RESPOSTA = {
    "cnpj": "11222333000181", "razao_social": "EMPRESA FICTICIA LTDA ", "uf": "sp",
    "identificador_matriz_filial": 1, "descricao_identificador_matriz_filial": "MATRIZ",
    "situacao_cadastral": 2, "descricao_situacao_cadastral": "ATIVA",
}


def buscar_fixo(dados, urls=None):
    def buscar(url):
        if urls is not None:
            urls.append(url)
        return dados
    return buscar


def test_consulta_a_brasilapi_e_le_os_dados_da_empresa():
    urls = []
    e = emp.consultar("11222333000181", buscar=buscar_fixo(RESPOSTA, urls))
    assert urls == ["https://brasilapi.com.br/api/cnpj/v1/11222333000181"]
    assert e == emp.Empresa("11222333000181", "EMPRESA FICTICIA LTDA", "SP", "ATIVA", True)
    assert e.ativa


def test_filial_de_outra_uf_e_inativa():
    dados = dict(RESPOSTA, uf="RJ", identificador_matriz_filial=2, descricao_situacao_cadastral="BAIXADA")
    e = emp.consultar("11222333000262", buscar=buscar_fixo(dados))
    assert (e.matriz, e.uf, e.ativa) == (False, "RJ", False)


def test_para_tela():
    e = emp.Empresa("11222333000181", "EMPRESA FICTICIA LTDA", "SP", "ATIVA", True)
    assert e.para_tela() == {"cnpj": "11222333000181", "cnpj_formatado": "11.222.333/0001-81",
                             "razao_social": "EMPRESA FICTICIA LTDA", "uf": "SP", "situacao_cadastral": "ATIVA",
                             "ativa": True, "matriz": True}


def test_resposta_incompleta_gera_erro_claro():
    with pytest.raises(emp.ErroIdentificacao, match="incompleta"):
        emp.consultar("11222333000181", buscar=buscar_fixo({"uf": "SP"}))


def test_situacao_ausente_vira_nao_informada():
    dados = dict(RESPOSTA)
    del dados["descricao_situacao_cadastral"]
    e = emp.consultar("11222333000181", buscar=buscar_fixo(dados))
    assert e.situacao_cadastral == "Não informada"
    assert e.ativa is False


class Resposta(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def test_buscar_envia_user_agent_generico_e_le_json(monkeypatch):
    pedidos = []

    def urlopen(pedido, timeout):
        pedidos.append((pedido.full_url, pedido.get_header("User-agent"), timeout))
        return Resposta(json.dumps(RESPOSTA).encode())

    monkeypatch.setattr(emp.urllib.request, "urlopen", urlopen)
    assert emp._buscar("https://exemplo/x") == RESPOSTA
    assert pedidos == [("https://exemplo/x", "licita_certidoes", emp.TEMPO_LIMITE_S)]


@pytest.mark.parametrize("erro, trecho", [
    (urllib.error.HTTPError("u", 404, "Not Found", {}, None), "não encontrado"),
    (urllib.error.HTTPError("u", 500, "Erro", {}, None), "erro 500"),
    (urllib.error.URLError("sem rede"), "não respondeu"),
    (TimeoutError(), "não respondeu"),
])
def test_falhas_da_brasilapi_geram_erro_claro(monkeypatch, erro, trecho):
    def urlopen(pedido, timeout):
        raise erro

    monkeypatch.setattr(emp.urllib.request, "urlopen", urlopen)
    with pytest.raises(emp.ErroIdentificacao, match=trecho):
        emp._buscar("https://exemplo/x")


def test_json_invalido_gera_erro_claro(monkeypatch):
    monkeypatch.setattr(emp.urllib.request, "urlopen", lambda pedido, timeout: Resposta(b"<html>"))
    with pytest.raises(emp.ErroIdentificacao, match="inesperada"):
        emp._buscar("https://exemplo/x")
