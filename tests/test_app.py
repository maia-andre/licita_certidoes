import pathlib

import pytest

import certidoes.app as app
from certidoes.empresa import Empresa, ErroIdentificacao
from certidoes.portais.comum import Pedido, PortalErro
from certidoes.sequencia import Item

CNPJ = "11222333000181"
FILIAL = "11222333000262"


def matriz_sp(cnpj):
    return Empresa(cnpj, "EMPRESA FICTICIA LTDA", "SP", "ATIVA", True)


def item(chave, obter):
    return Item(chave, chave.upper(), f"Portal {chave}", obter, "Instrução {cnpj}")


def obtem(caminho):
    return lambda cnpj, ao_aguardar, **kw: pathlib.Path(caminho)


class PreferenciasMemoria:
    """Preferências sem disco, para os testes não gravarem no perfil do usuário."""
    def __init__(self, email=""):
        self.gravado = email

    def email(self):
        return self.gravado

    def salvar_email(self, email):
        self.gravado = email
        return True


def criar_api(itens=None, abrir=None, executar=lambda funcao: funcao(), consultar=matriz_sp, preferencias=None):
    itens = itens or [item("a", obtem("/tmp/a.pdf")), item("b", obtem("/tmp/b.pdf"))]
    return app.Api(itens=itens, abrir=abrir or (lambda caminho: None), executar=executar, consultar=consultar,
                   preferencias=preferencias or PreferenciasMemoria())


def iniciar(api, cnpj=CNPJ):
    """Identifica e emite, como a tela faz."""
    assert api.identificar(cnpj)["ok"] is True
    return api.emitir(cnpj)


def test_cnpj_invalido_mostra_erro_sem_consulta_externa():
    chamadas = []
    api = criar_api(itens=[item("a", lambda cnpj, ao_aguardar, **kw: chamadas.append(cnpj))])
    resposta = api.identificar("11.222.333/0001-82")
    assert resposta["ok"] is False
    assert "CNPJ inválido" in resposta["mensagem"]
    assert chamadas == []
    assert api.estado() == {"rodando": False, "itens": []}


def test_emitir_inicia_a_sequencia_com_o_cnpj_normalizado():
    chamadas = []

    def obter(cnpj, ao_aguardar, **kw):
        chamadas.append(cnpj)
        return pathlib.Path("/tmp/a.pdf")

    api = criar_api(itens=[item("a", obter)])
    assert api.identificar("11.222.333/0001-81")["empresa"]["cnpj"] == CNPJ
    resposta = api.emitir(CNPJ)
    assert resposta == {"ok": True, "cnpj": "11.222.333/0001-81", "aviso": None}
    assert chamadas == [CNPJ]


def test_emitir_roda_em_segundo_plano():
    agendadas = []
    api = criar_api(executar=agendadas.append)
    assert iniciar(api)["ok"] is True
    estado = api.estado()
    assert estado["rodando"] is True
    assert [i["estado"] for i in estado["itens"]] == ["Aguardando", "Aguardando"]
    agendadas[0]()
    assert api.estado()["rodando"] is False


def test_estado_mostra_cada_item_com_o_arquivo_como_texto():
    api = criar_api()
    iniciar(api)
    estado = api.estado()
    assert estado["rodando"] is False
    assert [(i["chave"], i["estado"], i["arquivo"]) for i in estado["itens"]] == [
        ("a", "Obtida", str(pathlib.Path("/tmp/a.pdf"))),
        ("b", "Obtida", str(pathlib.Path("/tmp/b.pdf"))),
    ]


def test_falha_em_um_item_nao_interrompe_o_outro():
    def falha(cnpj, ao_aguardar, **kw):
        raise PortalErro("Tempo esgotado")

    api = criar_api(itens=[item("a", falha), item("b", obtem("/tmp/b.pdf"))])
    iniciar(api)
    a, b = api.estado()["itens"]
    assert (a["estado"], a["mensagem"], a["arquivo"]) == ("Falha técnica", "Tempo esgotado", None)
    assert b["estado"] == "Obtida"


def test_informar_nao_emitida_repassa_para_o_item_que_aguarda_o_servidor():
    from certidoes.portais.comum import NaoEmitida
    from certidoes.sequencia import NAVEGADOR

    respostas = []

    def obter(cnpj, ao_aguardar, sinal):
        ao_aguardar()
        respostas.append(api.informar_nao_emitida("a", 123))  # mensagem que não é texto é recusada
        respostas.append(api.informar_nao_emitida("a", "Empregador não cadastrado."))
        sinal.verificar()
        raise AssertionError("o sinal deveria ter encerrado")

    api = criar_api(itens=[Item("a", "A", "Portal a", obter, "Instrução", NAVEGADOR)])
    assert api.informar_nao_emitida("a", "") is False  # sem consulta
    iniciar(api)
    item_a = api.estado()["itens"][0]
    assert respostas == [False, True]
    assert (item_a["estado"], item_a["modo"]) == ("Não emitida", "navegador")
    assert "Empregador não cadastrado." in item_a["mensagem"]


def test_abrir_pdf_abre_o_arquivo_do_item_escolhido():
    abertos = []
    api = criar_api(abrir=abertos.append)
    iniciar(api)
    assert api.abrir_pdf("b") is True
    assert abertos == [pathlib.Path("/tmp/b.pdf")]


def test_abrir_pdf_sem_certidao_nao_abre_nada():
    abertos = []
    api = criar_api(abrir=abertos.append)
    assert api.abrir_pdf("a") is False
    iniciar(api)
    assert api.abrir_pdf("inexistente") is False
    assert abertos == []


def test_abrir_pdf_apagado_devolve_false():
    def abrir(caminho):
        raise FileNotFoundError(caminho)

    api = criar_api(abrir=abrir)
    iniciar(api)
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
    assert iniciar(api)["ok"] is True
    segunda = api.emitir(CNPJ)
    assert segunda["ok"] is False
    assert "andamento" in segunda["mensagem"]
    assert api.identificar(CNPJ) == {"ok": False, "mensagem": app.EM_ANDAMENTO}
    agendadas[0]()
    assert api.emitir(CNPJ)["ok"] is True


def test_nova_consulta_depois_de_erro_inesperado_e_aceita():
    def quebra(cnpj, ao_aguardar, **kw):
        raise RuntimeError("boom")

    api = criar_api(itens=[item("a", quebra)])
    iniciar(api)
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
    for elemento in ('id="cnpj"', 'id="identificar"', 'id="empresa"', 'id="aviso-filial"', 'id="status"', 'id="itens"', 'id="aviso"', "O portal não emitiu",
                     "Mensagem do portal (opcional)", "informar_nao_emitida"):
        assert elemento in html
    assert "innerHTML" not in html


def test_aviso_permanente_de_que_a_decisao_cabe_ao_servidor():
    html = app.TELA.read_text(encoding="utf-8")
    assert "A análise dos documentos e a decisão cabem ao servidor" in html
    aviso = html.split('id="aviso"', 1)[1].split(">", 1)[0]
    assert "hidden" not in aviso


def empresas(**por_cnpj):
    """Fake da BrasilAPI: devolve a Empresa cadastrada ou levanta ErroIdentificacao."""
    def consultar(cnpj):
        valor = por_cnpj.get(f"c{cnpj}")
        if isinstance(valor, Exception):
            raise valor
        if valor is None:
            raise ErroIdentificacao("CNPJ não encontrado na BrasilAPI.")
        return valor
    return consultar


def test_identificar_mostra_os_dados_da_matriz():
    api = criar_api()
    r = api.identificar("11.222.333/0001-81")
    assert r["ok"] is True
    assert r["empresa"]["razao_social"] == "EMPRESA FICTICIA LTDA"
    assert (r["empresa"]["matriz"], r["empresa"]["uf"], r["matriz"], r["erro_matriz"]) == (True, "SP", None, None)


def test_cnpj_invalido_nao_consulta_a_brasilapi():
    consultas = []
    api = criar_api(consultar=lambda cnpj: consultas.append(cnpj))
    assert api.identificar("11.222.333/0001-82")["ok"] is False
    assert consultas == []


def test_brasilapi_fora_do_ar_informa_e_nao_libera_portais():
    api = criar_api(consultar=empresas(**{f"c{CNPJ}": ErroIdentificacao("a BrasilAPI não respondeu")}))
    assert api.identificar(CNPJ) == {"ok": False, "mensagem": "a BrasilAPI não respondeu"}
    assert api.emitir(CNPJ)["ok"] is False
    assert api.estado()["itens"] == []


def test_nova_tentativa_depois_de_falha_da_brasilapi():
    falhas = [ErroIdentificacao("fora do ar")]

    def consultar(cnpj):
        if falhas:
            raise falhas.pop()
        return matriz_sp(cnpj)

    api = criar_api(consultar=consultar)
    assert api.identificar(CNPJ)["ok"] is False
    assert api.identificar(CNPJ)["ok"] is True
    assert api.emitir(CNPJ)["ok"] is True


def test_emitir_sem_identificar_e_recusado():
    chamadas = []
    api = criar_api(itens=[item("a", lambda cnpj, ao_aguardar, **kw: chamadas.append(cnpj))])
    assert api.emitir(CNPJ) == {"ok": False, "mensagem": "Identifique a empresa antes de emitir as certidões."}
    assert api.emitir(None)["ok"] is False
    assert chamadas == []


def test_empresa_de_outra_uf_consulta_os_itens_de_qualquer_uf_e_nao_abre_o_portal_de_sp():
    chamadas = []

    def obter(chave):
        def funcao(cnpj, ao_aguardar, **kw):
            chamadas.append(chave)
            return pathlib.Path(f"/tmp/{chave}.pdf")
        return funcao

    rj = Empresa(CNPJ, "EMPRESA RJ LTDA", "RJ", "ATIVA", True)
    so_sp = Item("sp", "SP", "Portal SP", obter("sp"), "", precisa=("email",), uf="SP", fora_da_uf="CNPJ de {uf}: não.")
    api = criar_api(itens=[item("federal", obter("federal")), so_sp], consultar=empresas(**{f"c{CNPJ}": rj}))
    assert api.identificar(CNPJ)["empresa"]["uf"] == "RJ"
    assert api.emitir(CNPJ)["ok"] is True  # sem e-mail: o único item que o pede não se aplica
    assert chamadas == ["federal"]
    estados = {i["chave"]: (i["estado"], i["mensagem"]) for i in api.estado()["itens"]}
    assert estados["sp"] == ("Não se aplica", "CNPJ de RJ: não.")


def test_situacao_cadastral_nao_ativa_aparece_e_permite_continuar():
    baixada = Empresa(CNPJ, "EMPRESA FICTICIA LTDA", "SP", "BAIXADA", True)
    api = criar_api(consultar=empresas(**{f"c{CNPJ}": baixada}))
    r = api.identificar(CNPJ)
    assert (r["empresa"]["situacao_cadastral"], r["empresa"]["ativa"]) == ("BAIXADA", False)
    assert api.emitir(CNPJ)["ok"] is True


def test_filial_mostra_a_matriz_e_permite_escolher():
    filial = Empresa(FILIAL, "EMPRESA FICTICIA LTDA", "SP", "ATIVA", False)
    api = criar_api(consultar=empresas(**{f"c{FILIAL}": filial, f"c{CNPJ}": matriz_sp(CNPJ)}))
    r = api.identificar(FILIAL)
    assert r["empresa"]["matriz"] is False
    assert r["matriz"]["cnpj"] == CNPJ
    assert r["matriz"]["cnpj_formatado"] == "11.222.333/0001-81"


def test_escolher_a_filial_mostra_o_aviso_da_falencia_pela_sede():
    filial = Empresa(FILIAL, "EMPRESA FICTICIA LTDA", "SP", "ATIVA", False)
    chamadas = []

    def obter(cnpj, ao_aguardar, **kw):
        chamadas.append(cnpj)
        return pathlib.Path("/tmp/a.pdf")

    api = criar_api(itens=[item("a", obter)], consultar=empresas(**{f"c{FILIAL}": filial, f"c{CNPJ}": matriz_sp(CNPJ)}))
    api.identificar(FILIAL)
    resposta = api.emitir(FILIAL)
    assert resposta["aviso"] == app.AVISO_FILIAL
    assert "art. 69, II" in resposta["aviso"]
    assert chamadas == [FILIAL]


def test_escolher_a_matriz_consulta_o_cnpj_da_matriz_sem_aviso():
    filial = Empresa(FILIAL, "EMPRESA FICTICIA LTDA", "SP", "ATIVA", False)
    chamadas = []

    def obter(cnpj, ao_aguardar, **kw):
        chamadas.append(cnpj)
        return pathlib.Path("/tmp/a.pdf")

    api = criar_api(itens=[item("a", obter)], consultar=empresas(**{f"c{FILIAL}": filial, f"c{CNPJ}": matriz_sp(CNPJ)}))
    api.identificar(FILIAL)
    assert api.emitir(CNPJ)["aviso"] is None
    assert chamadas == [CNPJ]


def test_filial_em_sp_com_matriz_fora_de_sp():
    filial = Empresa(FILIAL, "EMPRESA FICTICIA LTDA", "SP", "ATIVA", False)
    matriz_mg = Empresa(CNPJ, "EMPRESA FICTICIA LTDA", "MG", "ATIVA", True)
    api = criar_api(consultar=empresas(**{f"c{FILIAL}": filial, f"c{CNPJ}": matriz_mg}))
    r = api.identificar(FILIAL)
    assert r["matriz"]["uf"] == "MG"
    assert api.emitir(CNPJ)["ok"] is True  # matriz escolhida: itens de SP ficam "Não se aplica" (REQ-04)
    resposta = api.emitir(FILIAL)  # filial escolhida: continua com o aviso da RN-07
    assert resposta["ok"] is True
    assert resposta["aviso"] == app.AVISO_FILIAL


def test_matriz_nao_identificada_ainda_permite_a_filial():
    filial = Empresa(FILIAL, "EMPRESA FICTICIA LTDA", "SP", "ATIVA", False)
    api = criar_api(consultar=empresas(**{f"c{FILIAL}": filial, f"c{CNPJ}": ErroIdentificacao("fora do ar")}))
    r = api.identificar(FILIAL)
    assert r["matriz"] is None
    assert "11.222.333/0001-81" in r["erro_matriz"] and "fora do ar" in r["erro_matriz"]
    assert api.emitir(CNPJ)["ok"] is False
    assert api.emitir(FILIAL)["ok"] is True


def test_nova_identificacao_descarta_as_opcoes_anteriores():
    outra = "11444777000161"
    api = criar_api()
    api.identificar(CNPJ)
    api.identificar(outra)
    assert api.emitir(CNPJ)["ok"] is False
    assert api.emitir(outra)["ok"] is True


def test_pular_e_repetir_pela_api():
    agendadas = []
    tentativas = []

    def obter(cnpj, ao_aguardar, sinal):
        tentativas.append(1)
        ao_aguardar()
        respostas.append(api.pular("a"))
        sinal.verificar()
        return pathlib.Path("/tmp/a.pdf")

    respostas = []
    api = criar_api(itens=[item("a", obter), item("b", obtem("/tmp/b.pdf"))], executar=agendadas.append)
    assert api.pular("a") is False  # sem consulta
    assert api.repetir("a") == {"ok": False, "mensagem": "Não há consulta para repetir."}
    iniciar(api)
    assert api.repetir("a")["mensagem"] == app.EM_ANDAMENTO  # consulta ainda rodando
    agendadas.pop()()
    assert respostas == [True]
    assert [i["estado"] for i in api.estado()["itens"]] == ["Pulada", "Obtida"]
    assert api.repetir("b")["ok"] is False  # "Obtida" não se repete
    respostas.clear()
    assert api.repetir("a") == {"ok": True}
    assert api.estado()["rodando"] is True
    assert api.emitir(CNPJ)["ok"] is False  # repetição em andamento
    agendadas.pop()()
    assert api.estado()["rodando"] is False
    assert len(tentativas) == 2


def test_tela_tem_botoes_pular_e_repetir():
    html = app.TELA.read_text(encoding="utf-8")
    for trecho in ("'Pular'", "'Repetir'", "api.pular(", "api.repetir("):
        assert trecho in html


def item_falencia(recebidos):
    def obter(cnpj, ao_aguardar, sinal, **dados):
        recebidos.append(dados)
        return Pedido(numero="1")
    return Item("falencia", "Falência", "e-SAJ", obter, "Envie.", precisa=("razao_social", "email"))


@pytest.mark.parametrize("email", [None, "", "   ", "sem-arroba", 42])
def test_email_vazio_ou_invalido_nao_inicia_a_consulta(email):
    # CE-12: nenhum portal é aberto e a tela pede a correção do e-mail.
    recebidos = []
    api = criar_api(itens=[item("a", obtem("/tmp/a.pdf")), item_falencia(recebidos)])
    assert api.identificar(CNPJ)["ok"] is True
    resposta = api.emitir(CNPJ, email)
    assert resposta == {"ok": False, "mensagem": app.EMAIL_INVALIDO, "campo": "email"}
    assert recebidos == []
    assert api.estado() == {"rodando": False, "itens": []}
    assert api.emitir(CNPJ, "compras@exemplo.gov.br")["ok"] is True  # corrigido, segue


def test_pedido_de_falencia_recebe_a_razao_social_identificada_e_o_email():
    recebidos = []
    api = criar_api(itens=[item_falencia(recebidos)])
    assert api.identificar(CNPJ)["ok"] is True
    assert api.emitir(CNPJ, " compras@exemplo.gov.br ")["ok"] is True
    assert recebidos == [{"razao_social": "EMPRESA FICTICIA LTDA", "email": "compras@exemplo.gov.br"}]
    assert api.estado()["itens"][0]["estado"] == "Pedido feito: acompanhar"


def test_sem_item_que_precise_de_email_ele_e_dispensado():
    api = criar_api()
    assert iniciar(api)["ok"] is True


def test_tela_tem_campo_de_email_para_o_esaj():
    html = app.TELA.read_text(encoding="utf-8")
    assert 'id="email"' in html and 'type="email"' in html
    assert "emitir(cnpj, email.value)" in html
    assert "Pedido feito: acompanhar" in html


def test_email_valido_fica_salvo_para_as_proximas_consultas():
    prefs = PreferenciasMemoria()
    api = criar_api(itens=[item_falencia([])], preferencias=prefs)
    assert api.email_salvo() == ""
    assert api.identificar(CNPJ)["ok"] is True
    assert api.emitir(CNPJ, " compras@exemplo.gov.br ")["ok"] is True
    assert prefs.gravado == "compras@exemplo.gov.br"
    assert api.email_salvo() == "compras@exemplo.gov.br"


def test_email_invalido_nao_substitui_o_salvo():
    prefs = PreferenciasMemoria("compras@exemplo.gov.br")
    api = criar_api(itens=[item_falencia([])], preferencias=prefs)
    assert api.identificar(CNPJ)["ok"] is True
    assert api.emitir(CNPJ, "errado")["ok"] is False
    assert prefs.gravado == "compras@exemplo.gov.br"


def test_tela_abre_com_o_email_salvo():
    html = app.TELA.read_text(encoding="utf-8")
    assert "pywebviewready" in html and "email_salvo()" in html


def test_filial_escolhida_passa_o_cnpj_da_matriz_para_a_sequencia():
    filial = Empresa(FILIAL, "EMPRESA FICTICIA LTDA", "SP", "ATIVA", False)
    recebidos = []

    def obter(cnpj, ao_aguardar, sinal, matriz=None):
        recebidos.append((cnpj, matriz))
        return pathlib.Path("/tmp/cnd.pdf")

    cnd = Item("cnd", "CND", "Receita", obter, "Cole {cnpj}.", precisa=("matriz",), aviso_matriz="Matriz {matriz}.")
    api = criar_api(itens=[cnd], consultar=empresas(**{f"c{FILIAL}": filial, f"c{CNPJ}": matriz_sp(CNPJ)}))
    api.identificar(FILIAL)
    api.emitir(FILIAL)
    api.emitir(CNPJ)
    assert recebidos == [(FILIAL, CNPJ), (CNPJ, None)]
