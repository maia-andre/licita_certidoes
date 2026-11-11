import pathlib

from certidoes import sequencia as seq
from certidoes.portais.comum import PortalErro

CNPJ = "11222333000181"


def item(chave, obter, instrucao="Faça a sua parte para {cnpj}."):
    return seq.Item(chave, chave.upper(), f"Portal {chave}", obter, instrucao)


def obtem(caminho):
    def obter(cnpj, ao_aguardar):
        ao_aguardar()
        return pathlib.Path(caminho)
    return obter


def test_itens_seguem_a_ordem_da_rn01():
    assert [i.chave for i in seq.ITENS] == ["cnd", "cndt"]


def test_estado_inicial_e_aguardando():
    execucao = seq.Execucao([item("a", obtem("/a.pdf"))], CNPJ)
    assert execucao.itens() == [{"chave": "a", "nome": "A", "portal": "Portal a", "estado": "Aguardando",
                                 "mensagem": "", "arquivo": None}]


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
