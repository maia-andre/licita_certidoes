import pathlib

import pytest

import certidoes.app as app
from certidoes.portais.comum import PortalErro
from certidoes.sequencia import Item

CNPJ = "11222333000181"


def item(chave, obter):
    return Item(chave, chave.upper(), f"Portal {chave}", obter, "Instrução {cnpj}")


def obtem(caminho):
    return lambda cnpj, ao_aguardar: pathlib.Path(caminho)


def criar_api(itens=None, abrir=None, executar=lambda funcao: funcao()):
    itens = itens or [item("a", obtem("/tmp/a.pdf")), item("b", obtem("/tmp/b.pdf"))]
    return app.Api(itens=itens, abrir=abrir or (lambda caminho: None), executar=executar)


def test_cnpj_invalido_mostra_erro_sem_consulta_externa():
    chamadas = []
    api = criar_api(itens=[item("a", lambda cnpj, ao_aguardar: chamadas.append(cnpj))])
    resposta = api.emitir("11.222.333/0001-82")
    assert resposta["ok"] is False
    assert "CNPJ inválido" in resposta["mensagem"]
    assert chamadas == []
    assert api.estado() == {"rodando": False, "itens": []}


def test_emitir_inicia_a_sequencia_com_o_cnpj_normalizado():
    chamadas = []

    def obter(cnpj, ao_aguardar):
        chamadas.append(cnpj)
        return pathlib.Path("/tmp/a.pdf")

    resposta = criar_api(itens=[item("a", obter)]).emitir("11.222.333/0001-81")
    assert resposta == {"ok": True, "cnpj": "11.222.333/0001-81"}
    assert chamadas == [CNPJ]


def test_emitir_roda_em_segundo_plano():
    agendadas = []
    api = criar_api(executar=agendadas.append)
    assert api.emitir(CNPJ)["ok"] is True
    estado = api.estado()
    assert estado["rodando"] is True
    assert [i["estado"] for i in estado["itens"]] == ["Aguardando", "Aguardando"]
    agendadas[0]()
    assert api.estado()["rodando"] is False


def test_estado_mostra_cada_item_com_o_arquivo_como_texto():
    api = criar_api()
    api.emitir(CNPJ)
    estado = api.estado()
    assert estado["rodando"] is False
    assert [(i["chave"], i["estado"], i["arquivo"]) for i in estado["itens"]] == [
        ("a", "Obtida", str(pathlib.Path("/tmp/a.pdf"))),
        ("b", "Obtida", str(pathlib.Path("/tmp/b.pdf"))),
    ]


def test_falha_em_um_item_nao_interrompe_o_outro():
    def falha(cnpj, ao_aguardar):
        raise PortalErro("Tempo esgotado")

    api = criar_api(itens=[item("a", falha), item("b", obtem("/tmp/b.pdf"))])
    api.emitir(CNPJ)
    a, b = api.estado()["itens"]
    assert (a["estado"], a["mensagem"], a["arquivo"]) == ("Falha técnica", "Tempo esgotado", None)
    assert b["estado"] == "Obtida"


def test_abrir_pdf_abre_o_arquivo_do_item_escolhido():
    abertos = []
    api = criar_api(abrir=abertos.append)
    api.emitir(CNPJ)
    assert api.abrir_pdf("b") is True
    assert abertos == [pathlib.Path("/tmp/b.pdf")]


def test_abrir_pdf_sem_certidao_nao_abre_nada():
    abertos = []
    api = criar_api(abrir=abertos.append)
    assert api.abrir_pdf("a") is False
    api.emitir(CNPJ)
    assert api.abrir_pdf("inexistente") is False
    assert abertos == []


def test_abrir_pdf_apagado_devolve_false():
    def abrir(caminho):
        raise FileNotFoundError(caminho)

    api = criar_api(abrir=abrir)
    api.emitir(CNPJ)
    assert api.abrir_pdf("a") is False


def test_abrir_arquivo_no_windows_usa_o_programa_padrao(monkeypatch):
    abertos = []
    monkeypatch.setattr(app.sys, "platform", "win32")
    monkeypatch.setattr(app.os, "startfile", abertos.append, raising=False)
    monkeypatch.setattr(app.subprocess, "Popen", lambda *a, **kw: pytest.fail("não deveria chamar xdg-open"))
    app._abrir_arquivo(pathlib.Path("C:/Certidoes/x.pdf"))
    assert abertos == [pathlib.Path("C:/Certidoes/x.pdf")]


def test_abrir_arquivo_no_linux_usa_xdg_open(monkeypatch):
    comandos = []
    monkeypatch.setattr(app.sys, "platform", "linux")
    monkeypatch.setattr(app.subprocess, "Popen", comandos.append)
    app._abrir_arquivo(pathlib.Path("/home/u/Certidoes/x.pdf"))
    assert comandos == [["xdg-open", str(pathlib.Path("/home/u/Certidoes/x.pdf"))]]


def test_segunda_consulta_simultanea_e_recusada():
    agendadas = []
    api = criar_api(executar=agendadas.append)
    assert api.emitir(CNPJ)["ok"] is True
    segunda = api.emitir(CNPJ)
    assert segunda["ok"] is False
    assert "andamento" in segunda["mensagem"]
    agendadas[0]()
    assert api.emitir(CNPJ)["ok"] is True


def test_nova_consulta_depois_de_erro_inesperado_e_aceita():
    def quebra(cnpj, ao_aguardar):
        raise RuntimeError("boom")

    api = criar_api(itens=[item("a", quebra)])
    api.emitir(CNPJ)
    assert api.estado()["rodando"] is False
    assert api.emitir(CNPJ)["ok"] is True


def test_iniciar_cria_janela_com_a_tela_e_a_api(monkeypatch):
    criadas = {}
    monkeypatch.setattr(app.webview, "create_window", lambda titulo, **kw: criadas.update(titulo=titulo, **kw))
    monkeypatch.setattr(app.webview, "start", lambda: criadas.update(iniciado=True))
    app.iniciar()
    assert criadas["iniciado"] is True
    assert isinstance(criadas["js_api"], app.Api)
    assert 'id="cnpj"' in criadas["html"]


def test_tela_tem_campo_botao_tabela_e_nao_usa_innerhtml():
    html = app.TELA.read_text(encoding="utf-8")
    for elemento in ('id="cnpj"', 'id="emitir"', 'id="status"', 'id="itens"'):
        assert elemento in html
    assert "innerHTML" not in html
