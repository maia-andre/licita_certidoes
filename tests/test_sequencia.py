import datetime as dt
import pathlib

from certidoes import leitura
from certidoes import sequencia as seq
from certidoes.portais import cnj, esaj, receita, tcesp, tcu
from certidoes.portais.comum import NaoEmitida, Pedido, PortalErro
from tests.conftest import pdf_com_texto

CNPJ = "11222333000181"


def item(chave, obter, instrucao="Faça a sua parte para {cnpj}.", modo=seq.AUTOMATIZADO):
    return seq.Item(chave, chave.upper(), f"Portal {chave}", obter, instrucao, modo)


def obtem(caminho):
    def obter(cnpj, ao_aguardar, **kw):
        ao_aguardar()
        return pathlib.Path(caminho)
    return obter


def test_itens_seguem_a_ordem_da_rn01_com_o_modo_de_cada_portal():
    assert [(i.chave, i.modo) for i in seq.ITENS] == [
        ("cnd", seq.NAVEGADOR), ("crf", seq.NAVEGADOR), ("cndt", seq.AUTOMATIZADO), ("falencia", seq.AUTOMATIZADO),
        ("sancoes", seq.DIRETO), ("improbidade", seq.DIRETO), ("apenados", seq.NAVEGADOR)]


def test_sancoes_vem_do_tcu_sem_dados_extras():
    sancoes = {i.chave: i for i in seq.ITENS}["sancoes"]
    assert (sancoes.obter, sancoes.precisa) == (tcu.obter_consulta, ())


def test_improbidade_vem_do_cnj_por_consulta_direta():
    improbidade = {i.chave: i for i in seq.ITENS}["improbidade"]
    assert (improbidade.obter, improbidade.precisa, improbidade.modo) == (cnj.obter_certidao, (), seq.DIRETO)


def test_cnd_federal_pede_a_matriz_quando_o_cnpj_e_de_filial():
    cnd = {i.chave: i for i in seq.ITENS}["cnd"]
    assert (cnd.obter, cnd.precisa, cnd.aviso_matriz) == (receita.obter_cnd, ("matriz",), receita.AVISO_MATRIZ)
    assert [i.chave for i in seq.ITENS if "matriz" in i.precisa] == ["cnd"]  # o CRF segue a filial


def test_apenados_vem_do_tcesp_no_navegador_do_servidor():
    apenados = {i.chave: i for i in seq.ITENS}["apenados"]
    assert (apenados.obter, apenados.precisa) == (tcesp.obter_certidao, ())
    assert "{cnpj}" in apenados.instrucao


def test_falencia_pede_razao_social_e_email_ao_esaj():
    falencia = {i.chave: i for i in seq.ITENS}["falencia"]
    assert falencia.obter is esaj.obter_pedido_falencia
    assert falencia.precisa == ("razao_social", "email", "avisar")


def test_estado_inicial_e_aguardando():
    execucao = seq.Execucao([item("a", obtem("/a.pdf"))], CNPJ)
    assert execucao.itens() == [{"chave": "a", "nome": "A", "portal": "Portal a", "modo": "automatizado",
                                 "estado": "Aguardando", "mensagem": "", "arquivo": None,
                                 "situacao": None, "validade": None, "vencida": False, "hora": None}]


def nao_emite_ate_o_servidor_avisar(execucao_ref):
    """Portal no navegador do servidor que só termina quando o servidor informa pela tela."""
    def obter(cnpj, ao_aguardar, sinal):
        ao_aguardar()
        execucao_ref["acao"]()
        sinal.verificar()
        return pathlib.Path("/a.pdf")
    return obter


def test_servidor_informa_nao_emitida_com_a_mensagem_do_portal():
    ref = {}
    execucao = seq.Execucao([item("a", nao_emite_ate_o_servidor_avisar(ref), modo=seq.NAVEGADOR),
                             item("b", obtem("/b.pdf"))], CNPJ)
    respostas = []
    ref["acao"] = lambda: respostas.append(execucao.informar_nao_emitida("a", "  As informações\n são insuficientes. "))
    execucao.rodar()
    a, b = execucao.itens()
    assert respostas == [True]
    assert a["estado"] == "Não emitida"
    assert a["mensagem"] == "Mensagem do portal, informada pelo servidor: As informações são insuficientes."
    assert a["arquivo"] is None
    assert b["estado"] == "Obtida"


def test_nao_emitida_sem_mensagem_pede_para_conferir_no_portal():
    ref = {}
    execucao = seq.Execucao([item("a", nao_emite_ate_o_servidor_avisar(ref), modo=seq.NAVEGADOR)], CNPJ)
    ref["acao"] = lambda: execucao.informar_nao_emitida("a", "   ")
    execucao.rodar()
    assert execucao.itens()[0]["mensagem"] == "Informado pelo servidor. Confira a mensagem no portal."


def test_nao_emitida_so_vale_para_item_do_navegador_que_aguarda_o_servidor():
    recebidos = []

    def automatizado(cnpj, ao_aguardar, **kw):
        recebidos.append(kw)
        ao_aguardar()
        recusas.append(execucao.informar_nao_emitida("auto"))
        return pathlib.Path("/auto.pdf")

    recusas = []
    execucao = seq.Execucao([item("auto", automatizado), item("nav", obtem("/nav.pdf"), modo=seq.NAVEGADOR)], CNPJ)
    assert execucao.informar_nao_emitida("nav") is False  # ainda "Aguardando"
    execucao.rodar()
    assert list(recebidos[0]) == ["sinal"]  # todo item recebe o sinal (para "Pular")
    assert recusas == [False]  # mas "não emitiu" só vale no navegador do servidor
    assert execucao.informar_nao_emitida("nav") is False  # já "Obtida"
    assert execucao.informar_nao_emitida("inexistente") is False
    assert [i["estado"] for i in execucao.itens()] == ["Obtida", "Obtida"]


def test_mensagem_muito_longa_e_cortada():
    ref = {}
    execucao = seq.Execucao([item("a", nao_emite_ate_o_servidor_avisar(ref), modo=seq.NAVEGADOR)], CNPJ)
    ref["acao"] = lambda: execucao.informar_nao_emitida("a", "x" * 5000)
    execucao.rodar()
    assert execucao.itens()[0]["mensagem"].endswith("x" * seq.LIMITE_MENSAGEM)
    assert "x" * (seq.LIMITE_MENSAGEM + 1) not in execucao.itens()[0]["mensagem"]


def test_percorre_os_itens_em_sequencia_e_marca_obtida():
    ordem = []

    def registrando(chave):
        def obter(cnpj, ao_aguardar, **kw):
            ordem.append((chave, cnpj))
            return pathlib.Path(f"/{chave}.pdf")
        return obter

    execucao = seq.Execucao([item("a", registrando("a")), item("b", registrando("b"))], CNPJ)
    execucao.rodar()
    assert ordem == [("a", CNPJ), ("b", CNPJ)]
    assert [(i["estado"], i["arquivo"]) for i in execucao.itens()] == [
        ("Obtida", pathlib.Path("/a.pdf")), ("Obtida", pathlib.Path("/b.pdf"))]


def test_estados_durante_a_execucao():
    vistos = []
    execucao = None

    def obter(cnpj, ao_aguardar, **kw):
        vistos.append(execucao.itens()[0]["estado"])
        ao_aguardar()
        vistos.append((execucao.itens()[0]["estado"], execucao.itens()[0]["mensagem"]))
        return pathlib.Path("/a.pdf")

    execucao = seq.Execucao([item("a", obter)], CNPJ)
    execucao.rodar()
    assert vistos == ["Em andamento", ("Aguardando servidor", "Faça a sua parte para 11.222.333/0001-81.")]
    assert execucao.itens()[0]["estado"] == "Obtida"
    assert execucao.itens()[0]["mensagem"] == ""


def test_item_seguinte_fica_aguardando_enquanto_o_anterior_roda():
    vistos = []
    execucao = None

    def primeiro(cnpj, ao_aguardar, **kw):
        vistos.append(execucao.itens()[1]["estado"])
        return pathlib.Path("/a.pdf")

    execucao = seq.Execucao([item("a", primeiro), item("b", obtem("/b.pdf"))], CNPJ)
    execucao.rodar()
    assert vistos == ["Aguardando"]


def test_falha_de_portal_vira_falha_tecnica_e_a_sequencia_segue():
    def falha(cnpj, ao_aguardar, **kw):
        raise PortalErro("Portal fora do ar.")

    execucao = seq.Execucao([item("a", falha), item("b", obtem("/b.pdf"))], CNPJ)
    execucao.rodar()
    a, b = execucao.itens()
    assert (a["estado"], a["mensagem"], a["arquivo"]) == ("Falha técnica", "Portal fora do ar.", None)
    assert b["estado"] == "Obtida"


def test_erro_inesperado_tambem_vira_falha_tecnica_e_a_sequencia_segue():
    def quebra(cnpj, ao_aguardar, **kw):
        raise RuntimeError("boom")

    execucao = seq.Execucao([item("a", quebra), item("b", obtem("/b.pdf"))], CNPJ)
    execucao.rodar()
    a, b = execucao.itens()
    assert a["estado"] == "Falha técnica"
    assert "boom" in a["mensagem"]
    assert b["estado"] == "Obtida"


def test_arquivo_por_chave():
    execucao = seq.Execucao([item("a", obtem("/a.pdf"))], CNPJ)
    assert execucao.arquivo("a") is None
    execucao.rodar()
    assert execucao.arquivo("a") == pathlib.Path("/a.pdf")
    assert execucao.arquivo("x") is None


def test_itens_devolve_copia():
    execucao = seq.Execucao([item("a", obtem("/a.pdf"))], CNPJ)
    execucao.itens()[0]["estado"] = "alterado"
    assert execucao.itens()[0]["estado"] == "Aguardando"


def pdf_cndt(tmp_path, validade="10/05/2027", cnpj="11.222.333/0001-81"):
    arquivo = tmp_path / "cndt.pdf"
    arquivo.write_bytes(pdf_com_texto("CERTIDAO NEGATIVA DE DEBITOS TRABALHISTAS", f"CNPJ: {cnpj}",
                                      f"Validade: {validade} - 180 dias"))
    return arquivo


def executar_com_leitura(arquivo, hoje=dt.date(2026, 11, 11), ler=leitura.ler_cndt):
    execucao = seq.Execucao([seq.Item("a", "A", "P", lambda cnpj, ao_aguardar, **kw: arquivo, "", seq.AUTOMATIZADO, ler)],
                            CNPJ, hoje=lambda: hoje)
    execucao.rodar()
    return execucao.itens()[0]


def test_certidao_obtida_mostra_situacao_e_validade_lidas_do_pdf(tmp_path):
    item_a = executar_com_leitura(pdf_cndt(tmp_path))
    assert (item_a["estado"], item_a["situacao"], item_a["validade"], item_a["vencida"]) == (
        "Obtida", "Negativa", "10/05/2027", False)


def test_certidao_com_validade_anterior_a_hoje_aparece_vencida(tmp_path):
    item_a = executar_com_leitura(pdf_cndt(tmp_path, validade="10/11/2026"))
    assert (item_a["validade"], item_a["vencida"]) == ("10/11/2026", True)


def test_validade_igual_a_hoje_ainda_nao_esta_vencida(tmp_path):
    assert executar_com_leitura(pdf_cndt(tmp_path, validade="11/11/2026"))["vencida"] is False


def test_pdf_ilegivel_continua_obtida_e_pede_conferencia(tmp_path):
    arquivo = tmp_path / "quebrado.pdf"
    arquivo.write_bytes(b"%PDF-1.4 sem texto")
    item_a = executar_com_leitura(arquivo)
    assert (item_a["estado"], item_a["situacao"], item_a["validade"], item_a["vencida"]) == (
        "Obtida", "Conferir no PDF", "Conferir no PDF", False)


def test_pdf_de_outra_empresa_pede_conferencia(tmp_path):
    item_a = executar_com_leitura(pdf_cndt(tmp_path, cnpj="99.999.999/0001-91"))
    assert (item_a["situacao"], item_a["validade"]) == ("Conferir no PDF", "Conferir no PDF")


def test_arquivo_que_sumiu_pede_conferencia(tmp_path):
    item_a = executar_com_leitura(tmp_path / "nao-existe.pdf")
    assert (item_a["estado"], item_a["situacao"]) == ("Obtida", "Conferir no PDF")


def test_item_nao_obtido_fica_sem_situacao_e_validade():
    def falha(cnpj, ao_aguardar, **kw):
        raise PortalErro("fora do ar")

    execucao = seq.Execucao([item("a", falha)], CNPJ)
    execucao.rodar()
    assert (execucao.itens()[0]["situacao"], execucao.itens()[0]["validade"]) == (None, None)


def test_itens_reais_tem_leitor():
    assert [i.ler for i in seq.ITENS] == [leitura.ler_cnd, leitura.ler_crf, leitura.ler_cndt, leitura.ler_falencia,
                                          leitura.ler_sancoes_tcu, leitura.ler_improbidade_cnj,
                                          leitura.ler_apenados_tcesp]


def espera_ate_pular(execucao_ref, chave):
    """Portal que chama a ação de teste enquanto aguarda e respeita o sinal."""
    def obter(cnpj, ao_aguardar, sinal):
        ao_aguardar()
        execucao_ref["acao"]()
        sinal.verificar()
        return pathlib.Path(f"/{chave}.pdf")
    return obter


def test_servidor_pula_o_item_em_andamento_e_a_sequencia_segue():
    ref = {}
    execucao = seq.Execucao([item("a", espera_ate_pular(ref, "a")), item("b", obtem("/b.pdf"))], CNPJ)
    respostas = []
    ref["acao"] = lambda: respostas.append(execucao.pular("a"))
    execucao.rodar()
    a, b = execucao.itens()
    assert respostas == [True]
    assert (a["estado"], a["mensagem"], a["arquivo"]) == ("Pulada", "Pulada pelo servidor.", None)
    assert b["estado"] == "Obtida"


def test_so_pula_o_item_em_andamento():
    vistos = []
    execucao = None

    def primeiro(cnpj, ao_aguardar, **kw):
        vistos.append(execucao.pular("b"))  # "b" ainda está "Aguardando"
        return pathlib.Path("/a.pdf")

    execucao = seq.Execucao([item("a", primeiro), item("b", obtem("/b.pdf"))], CNPJ)
    assert execucao.pular("a") is False  # nada rodando
    execucao.rodar()
    assert vistos == [False]
    assert execucao.pular("a") is False  # já "Obtida"
    assert execucao.pular("x") is False
    assert [i["estado"] for i in execucao.itens()] == ["Obtida", "Obtida"]


def test_repete_so_o_item_que_falhou():
    tentativas = {"a": 0, "b": 0}

    def a_falha_na_primeira(cnpj, ao_aguardar, **kw):
        tentativas["a"] += 1
        if tentativas["a"] == 1:
            raise PortalErro("fora do ar")
        return pathlib.Path("/a.pdf")

    def b(cnpj, ao_aguardar, **kw):
        tentativas["b"] += 1
        return pathlib.Path("/b.pdf")

    execucao = seq.Execucao([item("a", a_falha_na_primeira), item("b", b)], CNPJ)
    execucao.rodar()
    assert execucao.itens()[0]["estado"] == "Falha técnica"
    assert execucao.pode_repetir("a") and not execucao.pode_repetir("b")
    execucao.repetir("a")
    assert tentativas == {"a": 2, "b": 1}
    assert [i["estado"] for i in execucao.itens()] == ["Obtida", "Obtida"]
    assert execucao.itens()[0]["mensagem"] == ""


def test_repete_item_pulado_e_nao_emitido():
    ref = {"acao": lambda: None}
    execucao = seq.Execucao([item("a", espera_ate_pular(ref, "a")),
                             item("n", nao_emite_ate_o_servidor_avisar(ref), modo=seq.NAVEGADOR)], CNPJ)
    ref["acao"] = lambda: (execucao.pular("a"), execucao.informar_nao_emitida("n", "msg"))
    execucao.rodar()
    assert [i["estado"] for i in execucao.itens()] == ["Pulada", "Não emitida"]
    ref["acao"] = lambda: None
    execucao.repetir("a")
    execucao.repetir("n")
    assert [i["estado"] for i in execucao.itens()] == ["Obtida", "Obtida"]


def test_repetir_item_obtido_ou_inexistente_nao_faz_nada():
    chamadas = []

    def obter(cnpj, ao_aguardar, **kw):
        chamadas.append(cnpj)
        return pathlib.Path("/a.pdf")

    execucao = seq.Execucao([item("a", obter)], CNPJ)
    execucao.rodar()
    execucao.repetir("a")
    execucao.repetir("x")
    assert chamadas == [CNPJ]


def test_repeticao_limpa_situacao_e_validade_anteriores(tmp_path):
    arquivo = pdf_cndt(tmp_path)
    tentativas = []

    def obter(cnpj, ao_aguardar, **kw):
        tentativas.append(1)
        if len(tentativas) == 2:
            raise PortalErro("caiu na repetição")
        return arquivo

    execucao = seq.Execucao([seq.Item("a", "A", "P", obter, "", seq.AUTOMATIZADO, leitura.ler_cndt)], CNPJ,
                            hoje=lambda: dt.date(2026, 11, 11))
    execucao.rodar()
    assert execucao.itens()[0]["situacao"] == "Negativa"
    with execucao._trava:  # força o item a um estado repetível
        execucao._estado["a"]["estado"] = "Falha técnica"
    execucao.repetir("a")
    a = execucao.itens()[0]
    assert (a["estado"], a["situacao"], a["validade"], a["arquivo"]) == ("Falha técnica", None, None, None)


def pede(pedido, recebidos=None):
    def obter(cnpj, ao_aguardar, sinal, **dados):
        if recebidos is not None:
            recebidos.append(dados)
        ao_aguardar()
        return pedido
    return obter


def item_pedido(obter):
    return seq.Item("f", "Falência", "e-SAJ", obter, "Envie.", seq.AUTOMATIZADO, precisa=("razao_social", "email"))


def test_pedido_aceito_vira_pedido_feito_acompanhar_com_numero_e_email():
    pedido = Pedido(numero="101890915", data="12/11/2026", email="compras@exemplo.gov.br", prazo_dias="05")
    execucao = seq.Execucao([item_pedido(pede(pedido)), item("b", obtem("/b.pdf"))], CNPJ,
                            dados={"razao_social": "X", "email": "compras@exemplo.gov.br"})
    execucao.rodar()
    falencia, seguinte = execucao.itens()
    assert falencia["estado"] == "Pedido feito: acompanhar"
    assert falencia["mensagem"] == ("Pedido nº 101890915 de 12/11/2026 aceito pelo portal. As instruções para emitir "
                                    "a certidão vão para compras@exemplo.gov.br. Prazo máximo informado: 05 dias.")
    assert (falencia["arquivo"], falencia["situacao"], falencia["validade"]) == (None, None, None)
    assert seguinte["estado"] == "Obtida"


def test_pedido_sem_numero_ainda_e_pedido_feito():
    execucao = seq.Execucao([item_pedido(pede(Pedido()))], CNPJ, dados={"razao_social": "X", "email": "a@b.com"})
    execucao.rodar()
    assert execucao.itens()[0]["estado"] == "Pedido feito: acompanhar"
    assert execucao.itens()[0]["mensagem"] == "Pedido aceito pelo portal."


def test_item_recebe_so_os_dados_que_precisa():
    recebidos = []
    execucao = seq.Execucao([item_pedido(pede(Pedido(), recebidos))], CNPJ,
                            dados={"razao_social": "EMPRESA", "email": "a@b.com", "outro": "nao"})
    execucao.rodar()
    assert recebidos == [{"razao_social": "EMPRESA", "email": "a@b.com"}]


def test_pedido_feito_nao_pode_ser_repetido():
    # Repetir enviaria um segundo pedido ao TJSP.
    chamadas = []
    execucao = seq.Execucao([item_pedido(pede(Pedido(), chamadas))], CNPJ, dados={"razao_social": "X", "email": "a@b.com"})
    execucao.rodar()
    assert execucao.pode_repetir("f") is False
    execucao.repetir("f")
    assert len(chamadas) == 1


def test_falha_no_pedido_pode_ser_repetida_com_os_mesmos_dados():
    recebidos = []
    tentativas = iter([PortalErro("Tempo esgotado aguardando o envio do pedido."), Pedido(numero="1")])

    def obter(cnpj, ao_aguardar, sinal, **dados):
        recebidos.append(dados)
        resultado = next(tentativas)
        if isinstance(resultado, Exception):
            raise resultado
        return resultado

    execucao = seq.Execucao([item_pedido(obter)], CNPJ, dados={"razao_social": "X", "email": "a@b.com"})
    execucao.rodar()
    assert execucao.itens()[0]["estado"] == "Falha técnica"
    execucao.repetir("f")
    assert execucao.itens()[0]["estado"] == "Pedido feito: acompanhar"
    assert recebidos == [{"razao_social": "X", "email": "a@b.com"}] * 2


def test_avisar_atualiza_a_mensagem_do_item_em_andamento():
    vistos = []

    def obter(cnpj, ao_aguardar, sinal, avisar, **dados):
        avisar("Consultando...")
        vistos.append((execucao.itens()[0]["estado"], execucao.itens()[0]["mensagem"]))
        return Pedido(numero="1")

    execucao = seq.Execucao([seq.Item("f", "F", "e-SAJ", obter, "", precisa=("email", "avisar"))], CNPJ,
                            dados={"email": "a@b.com"})
    execucao.rodar()
    assert vistos == [("Em andamento", "Consultando...")]


def test_observacao_do_pedido_entra_na_mensagem():
    pedido = Pedido(numero="1", observacao="Ainda não liberada.")
    execucao = seq.Execucao([item_pedido(pede(pedido))], CNPJ, dados={"razao_social": "X", "email": "a@b.com"})
    execucao.rodar()
    assert execucao.itens()[0]["mensagem"] == "Pedido nº 1 aceito pelo portal. Ainda não liberada."


def test_falencia_baixada_mostra_nada_consta_e_a_emissao_no_lugar_da_validade(tmp_path):
    from tests.conftest import ESAJ_CERTIDAO

    arquivo = tmp_path / "falencia.pdf"
    arquivo.write_bytes(pdf_com_texto(*ESAJ_CERTIDAO))
    obter = lambda cnpj, ao_aguardar, sinal, **dados: arquivo  # noqa: E731
    execucao = seq.Execucao([seq.Item("f", "F", "e-SAJ", obter, "", ler=leitura.ler_falencia)], CNPJ)
    execucao.rodar()
    estado = execucao.itens()[0]
    assert (estado["estado"], estado["situacao"], estado["validade"], estado["vencida"]) == (
        "Obtida", "Nada consta", "Não impressa (emitida em 12/11/2026)", False)


def _sancoes(tmp_path, linhas):
    arquivo = tmp_path / "sancoes.pdf"
    arquivo.write_bytes(pdf_com_texto(*linhas))
    obter = lambda cnpj, ao_aguardar, sinal, **dados: arquivo  # noqa: E731
    execucao = seq.Execucao([seq.Item("s", "S", "TCU", obter, "", seq.DIRETO, leitura.ler_sancoes_tcu)], CNPJ)
    execucao.rodar()
    return execucao.itens()[0]


def test_sancoes_nada_consta_mostram_cada_cadastro_e_a_data_da_consulta(tmp_path):
    from tests.conftest import TCU_CONSULTA

    estado = _sancoes(tmp_path, TCU_CONSULTA)
    assert (estado["estado"], estado["situacao"], estado["validade"]) == (
        "Obtida", "Nada consta", "Não impressa (emitida em 12/11/2026)")
    assert estado["mensagem"] == ("TCU (Licitantes Inidôneos): Nada consta. "
                                  "CNJ (CNIA, improbidade): Nada consta (confira o item de improbidade do CNJ). "
                                  "CEIS: Nada consta. CNEP: Nada consta.")
    assert estado["arquivo"] == tmp_path / "sancoes.pdf"


def test_sancoes_com_cnj_indisponivel_seguem_nada_consta_e_apontam_o_item_do_cnj(tmp_path):
    from tests.conftest import TCU_CONSULTA

    linhas = tuple("Resultado da consulta: Sistema do CNJ esta indisponivel" if i == 13 else linha
                   for i, linha in enumerate(TCU_CONSULTA))
    estado = _sancoes(tmp_path, linhas)
    assert (estado["estado"], estado["situacao"]) == ("Obtida", "Nada consta")
    assert "CNJ (CNIA, improbidade): Sistema do CNJ esta indisponivel (confira o item de improbidade do CNJ)." \
           in estado["mensagem"]


def test_sancoes_com_cadastro_que_decide_indisponivel_ficam_obtidas_para_conferir(tmp_path):
    from tests.conftest import TCU_CONSULTA

    linhas = tuple("Resultado da consulta: Sistema indisponivel" if i == 17 else linha  # CEIS
                   for i, linha in enumerate(TCU_CONSULTA))
    estado = _sancoes(tmp_path, linhas)
    assert (estado["estado"], estado["situacao"]) == ("Obtida", "Conferir no PDF")
    assert "CEIS: Sistema indisponivel (consulta manual: https://portaldatransparencia.gov.br/sancoes/ceis)." \
           in estado["mensagem"]


def test_apenados_nada_consta_mostram_a_data_de_emissao_e_nao_vencem_no_dia_seguinte(tmp_path):
    from tests.conftest import TCESP_CERTIDAO

    arquivo = tmp_path / "apenados.pdf"
    arquivo.write_bytes(pdf_com_texto(*TCESP_CERTIDAO))
    obter = lambda cnpj, ao_aguardar, sinal, **dados: arquivo  # noqa: E731
    execucao = seq.Execucao([seq.Item("t", "T", "TCE-SP", obter, "", seq.NAVEGADOR, leitura.ler_apenados_tcesp)],
                            CNPJ, hoje=lambda: dt.date(2026, 11, 13))
    execucao.rodar()
    estado = execucao.itens()[0]
    assert (estado["estado"], estado["situacao"], estado["validade"], estado["vencida"]) == (
        "Obtida", "Nada consta", "Não impressa (emitida em 12/11/2026)", False)


def test_item_de_outra_uf_nao_se_aplica_e_nao_abre_o_portal():
    chamadas = []

    def obter(cnpj, ao_aguardar, **kw):
        chamadas.append(cnpj)
        return pathlib.Path("/tmp/sp.pdf")

    so_sp = seq.Item("sp", "SP", "Portal SP", obter, "", uf="SP", fora_da_uf="CNPJ de {uf}: peça na sede.")
    execucao = seq.Execucao([so_sp, item("b", obtem("/b.pdf"))], CNPJ, uf="RJ")
    assert execucao.itens()[0]["estado"] == "Não se aplica"  # já na tela, antes de rodar
    execucao.rodar()
    estado = execucao.itens()[0]
    assert (estado["estado"], estado["mensagem"]) == ("Não se aplica", "CNPJ de RJ: peça na sede.")
    assert execucao.itens()[1]["estado"] == "Obtida"
    assert chamadas == []
    assert not execucao.pode_repetir("sp")


def test_item_da_mesma_uf_ou_sem_uf_conhecida_e_consultado():
    so_sp = seq.Item("sp", "SP", "Portal SP", obtem("/sp.pdf"), "", uf="SP")
    for uf in ("SP", "sp", None):
        execucao = seq.Execucao([so_sp], CNPJ, uf=uf)
        execucao.rodar()
        assert execucao.itens()[0]["estado"] == "Obtida"


def test_so_a_falencia_depende_da_uf_e_aponta_o_tribunal_da_sede():
    assert {i.chave: i.uf for i in seq.ITENS if i.uf} == {"falencia": "SP"}
    falencia = {i.chave: i for i in seq.ITENS}["falencia"]
    assert "art. 69, II" in falencia.fora_da_uf.format(uf="MG")


def _execucao_cnd(dados, copiados):
    def obter(cnpj, ao_aguardar, sinal, matriz=None):
        copiados.append((cnpj, matriz))
        ao_aguardar()
        return pathlib.Path("/tmp/cnd.pdf")

    cnd = seq.Item("cnd", "CND", "Receita", obter, "Cole o CNPJ {cnpj}.", seq.NAVEGADOR, precisa=("matriz",),
                   aviso_matriz="Pedida com a matriz {matriz}.")
    return seq.Execucao([cnd], "11222333000262", dados=dados)


def test_filial_pede_a_cnd_com_o_cnpj_da_matriz_e_explica_na_tela():
    copiados, instrucoes = [], []
    execucao = _execucao_cnd({"matriz": "11222333000181"}, copiados)
    original = execucao._marcar

    def marcar(chave, estado, mensagem="", arquivo=None):
        if estado == seq.AGUARDANDO_SERVIDOR:
            instrucoes.append(mensagem)
        original(chave, estado, mensagem, arquivo)

    execucao._marcar = marcar
    execucao.rodar()
    assert copiados == [("11222333000262", "11222333000181")]
    assert instrucoes == ["Cole o CNPJ 11.222.333/0001-81. Pedida com a matriz 11.222.333/0001-81."]
    estado = execucao.itens()[0]
    assert (estado["estado"], estado["mensagem"]) == ("Obtida", "Pedida com a matriz 11.222.333/0001-81.")


def test_matriz_pede_a_cnd_com_o_proprio_cnpj_sem_aviso():
    copiados = []
    execucao = _execucao_cnd({"matriz": None}, copiados)
    execucao.rodar()
    assert copiados == [("11222333000262", None)]
    assert execucao.itens()[0]["mensagem"] == ""


def test_cada_item_final_recebe_a_hora_da_consulta():
    horas = iter([dt.datetime(2026, 11, 12, 16, 35, 0), dt.datetime(2026, 11, 12, 16, 37, 5),
                  dt.datetime(2026, 11, 12, 16, 37, 5)])
    execucao = seq.Execucao([item("a", obtem("/a.pdf"))], CNPJ, relogio=lambda: next(horas, dt.datetime(2026, 11, 12, 16, 38)))
    assert execucao.inicio == dt.datetime(2026, 11, 12, 16, 35, 0)
    execucao.rodar()
    assert execucao.itens()[0]["hora"] == "12/11/2026 16:37:05"


def test_pdf_obtido_vai_para_a_subpasta_da_consulta(tmp_path):
    origem = tmp_path / CNPJ / "cndt-20261112-163705.pdf"
    origem.parent.mkdir()
    origem.write_bytes(b"%PDF-teste")
    pasta = tmp_path / CNPJ / "2026-11-12 16h35"
    execucao = seq.Execucao([item("a", lambda cnpj, ao_aguardar, sinal: origem)], CNPJ, pasta_consulta=pasta)
    execucao.rodar()
    assert execucao.itens()[0]["arquivo"] == pasta / "cndt-20261112-163705.pdf"
    assert (pasta / "cndt-20261112-163705.pdf").read_bytes() == b"%PDF-teste"
    assert not origem.exists()


def test_sem_subpasta_o_pdf_fica_onde_o_portal_guardou():
    execucao = seq.Execucao([item("a", obtem("/tmp/a.pdf"))], CNPJ)
    execucao.rodar()
    assert execucao.itens()[0]["arquivo"] == pathlib.Path("/tmp/a.pdf")


def test_cnpj_do_item_e_o_da_matriz_so_na_cnd_de_filial():
    cnd = seq.Item("cnd", "CND", "Receita", obtem("/a.pdf"), "", precisa=("matriz",))
    outro = item("crf", obtem("/b.pdf"))
    execucao = seq.Execucao([cnd, outro], "11222333000262", dados={"matriz": CNPJ})
    assert (execucao.cnpj_do_item("cnd"), execucao.cnpj_do_item("crf")) == (CNPJ, "11222333000262")
