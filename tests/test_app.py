import pathlib

import pytest

import certidoes.app as app
from certidoes.portais.tst import PortalErro

CNPJ = "11222333000181"


def criar_api(obter=None, abrir=None):
    return app.Api(obter=obter or (lambda cnpj: pathlib.Path("/tmp/x.pdf")), abrir=abrir or (lambda caminho: None))


def test_cnpj_invalido_mostra_erro_sem_consulta_externa():
    chamadas = []
    api = criar_api(obter=lambda cnpj: chamadas.append(cnpj))
    resposta = api.emitir("11.222.333/0001-82")
    assert resposta["ok"] is False
    assert "CNPJ inválido" in resposta["mensagem"]
    assert chamadas == []


def test_emitir_passa_cnpj_normalizado_e_informa_o_arquivo():
    chamadas = []

    def obter(cnpj):
        chamadas.append(cnpj)
        return pathlib.Path("/tmp/certidao.pdf")

    resposta = criar_api(obter=obter).emitir("11.222.333/0001-81")
    assert chamadas == [CNPJ]
    assert resposta == {"ok": True, "mensagem": "CNDT obtida.", "arquivo": "/tmp/certidao.pdf"}


def test_erro_do_portal_vira_mensagem_para_a_tela():
    def obter(cnpj):
        raise PortalErro("Tempo esgotado")

    assert criar_api(obter=obter).emitir(CNPJ) == {"ok": False, "mensagem": "Tempo esgotado"}


def test_abrir_pdf_abre_o_ultimo_arquivo_obtido():
    abertos = []
    api = criar_api(obter=lambda cnpj: pathlib.Path("/tmp/certidao.pdf"), abrir=abertos.append)
    api.emitir(CNPJ)
    assert api.abrir_pdf() is True
    assert abertos == [pathlib.Path("/tmp/certidao.pdf")]


def test_abrir_pdf_sem_certidao_nao_abre_nada():
    abertos = []
    assert criar_api(abrir=abertos.append).abrir_pdf() is False
    assert abertos == []


def test_segunda_consulta_simultanea_e_recusada():
    respostas = []

    def obter(cnpj):
        respostas.append(api.emitir(CNPJ))
        return pathlib.Path("/tmp/certidao.pdf")

    api = criar_api(obter=obter)
    assert api.emitir(CNPJ)["ok"] is True
    assert respostas[0]["ok"] is False
    assert "andamento" in respostas[0]["mensagem"]
    assert api.emitir(CNPJ)["ok"] is True


def test_iniciar_cria_janela_com_a_tela_e_a_api(monkeypatch):
    criadas = {}
    monkeypatch.setattr(app.webview, "create_window", lambda titulo, **kw: criadas.update(titulo=titulo, **kw))
    monkeypatch.setattr(app.webview, "start", lambda: criadas.update(iniciado=True))
    app.iniciar()
    assert criadas["iniciado"] is True
    assert isinstance(criadas["js_api"], app.Api)
    assert 'id="cnpj"' in criadas["html"]


def test_tela_tem_campo_botoes_e_nao_usa_innerhtml():
    html = app.TELA.read_text(encoding="utf-8")
    for elemento in ('id="cnpj"', 'id="emitir"', 'id="abrir"', 'id="status"'):
        assert elemento in html
    assert "innerHTML" not in html
