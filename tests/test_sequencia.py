import datetime as dt
import pathlib

from certidoes import leitura
from certidoes import sequencia as seq
from certidoes.portais.comum import NaoEmitida, PortalErro
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
        ("cnd", seq.NAVEGADOR), ("crf", seq.NAVEGADOR), ("cndt", seq.AUTOMATIZADO)]


def test_estado_inicial_e_aguardando():
    execucao = seq.Execucao([item("a", obtem("/a.pdf"))], CNPJ)
    assert execucao.itens() == [{"chave": "a", "nome": "A", "portal": "Portal a", "modo": "automatizado",
                                 "estado": "Aguardando", "mensagem": "", "arquivo": None,
                                 "situacao": None, "validade": None, "vencida": False}]


def nao_emite_ate_o_servidor_avisar(execucao_ref):
    """Portal no navegador do servidor que só termina quando o servidor informa pela tela."""
    def obter(cnpj, ao_aguardar, nao_emitida):
        ao_aguardar()
        execucao_ref["acao"]()
        if nao_emitida.informado():
            raise NaoEmitida(nao_emitida.mensagem)
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
    assert recebidos == [{}]  # item automatizado não recebe o sinal
    assert recusas == [False]
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
        def obter(cnpj, ao_aguardar):
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

    def obter(cnpj, ao_aguardar):
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

    def primeiro(cnpj, ao_aguardar):
        vistos.append(execucao.itens()[1]["estado"])
        return pathlib.Path("/a.pdf")

    execucao = seq.Execucao([item("a", primeiro), item("b", obtem("/b.pdf"))], CNPJ)
    execucao.rodar()
    assert vistos == ["Aguardando"]


def test_falha_de_portal_vira_falha_tecnica_e_a_sequencia_segue():
    def falha(cnpj, ao_aguardar):
        raise PortalErro("Portal fora do ar.")

    execucao = seq.Execucao([item("a", falha), item("b", obtem("/b.pdf"))], CNPJ)
    execucao.rodar()
    a, b = execucao.itens()
    assert (a["estado"], a["mensagem"], a["arquivo"]) == ("Falha técnica", "Portal fora do ar.", None)
    assert b["estado"] == "Obtida"


def test_erro_inesperado_tambem_vira_falha_tecnica_e_a_sequencia_segue():
    def quebra(cnpj, ao_aguardar):
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
    execucao = seq.Execucao([seq.Item("a", "A", "P", lambda cnpj, ao_aguardar: arquivo, "", seq.AUTOMATIZADO, ler)],
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
    def falha(cnpj, ao_aguardar):
        raise PortalErro("fora do ar")

    execucao = seq.Execucao([item("a", falha)], CNPJ)
    execucao.rodar()
    assert (execucao.itens()[0]["situacao"], execucao.itens()[0]["validade"]) == (None, None)


def test_itens_reais_tem_leitor():
    assert [i.ler for i in seq.ITENS] == [leitura.ler_cnd, leitura.ler_crf, leitura.ler_cndt]
