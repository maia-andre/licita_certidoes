import datetime as dt
import hashlib

import pytest

from certidoes import __version__, capa
from certidoes.pdf import texto_do_pdf

EMPRESA = {"cnpj": "11222333000181", "cnpj_formatado": "11.222.333/0001-81", "razao_social": "EMPRESA <FICTICIA> LTDA",
           "uf": "SP", "situacao_cadastral": "ATIVA", "ativa": True, "matriz": True}
IDENTIFICADA = dt.datetime(2026, 11, 12, 16, 35, 0)
INICIO = dt.datetime(2026, 11, 12, 16, 35, 10)
AGORA = dt.datetime(2026, 11, 12, 16, 40, 12)


def itens(pdf):
    return [
        {"chave": "cnd", "nome": "CND federal", "portal": "Receita Federal", "estado": "Obtida",
         "situacao": "Positiva com efeitos de negativa", "validade": "24/03/2027", "vencida": False,
         "mensagem": "Pedida com o CNPJ da matriz.", "arquivo": str(pdf), "hora": "12/11/2026 16:36:40"},
        {"chave": "sancoes", "nome": "Sanções: TCU, CEIS e CNEP", "portal": "TCU", "estado": "Obtida",
         "situacao": "Nada consta", "validade": "Não impressa (emitida em 12/11/2026)", "vencida": False,
         "mensagem": "", "arquivo": None, "hora": "12/11/2026 16:37:30"},
        {"chave": "falencia", "nome": "Falência", "portal": "e-SAJ/TJSP", "estado": "Não se aplica",
         "situacao": None, "validade": None, "vencida": False, "mensagem": "CNPJ de RJ: peça na sede.",
         "arquivo": None, "hora": None},
    ]


@pytest.fixture
def pdf(tmp_path):
    arquivo = tmp_path / "cnd-20261112-163640.pdf"
    arquivo.write_bytes(b"%PDF-1.4 certidao de teste")
    return arquivo


def test_html_reune_empresa_itens_horas_e_aviso_sem_juizo(pdf):
    conteudo = capa.montar_html(EMPRESA, IDENTIFICADA, itens(pdf), INICIO, AGORA, [(pdf.name, "abc123")])
    assert "EMPRESA &lt;FICTICIA&gt; LTDA" in conteudo and "<FICTICIA>" not in conteudo  # texto escapado
    assert "11.222.333/0001-81 (matriz) · UF SP" in conteudo
    assert "BrasilAPI, consultada em 12/11/2026 16:35" in conteudo
    assert "de 12/11/2026 16:35 a 12/11/2026 16:37" in conteudo
    assert "Positiva com efeitos de negativa" in conteudo and "Pedida com o CNPJ da matriz." in conteudo
    assert "Emitida em 12/11/2026" in conteudo
    assert "Não se aplica" in conteudo and "12/11/2026 16:36:40" in conteudo
    assert "abc123" in conteudo and pdf.name in conteudo
    assert "A análise dos documentos e a decisão sobre habilitação ou pagamento cabem ao servidor" in conteudo
    assert f"Certidões do Fornecedor {__version__}" in conteudo


def test_validade_vencida_aparece_na_capa(pdf):
    item = dict(itens(pdf)[0], validade="01/11/2026", vencida=True)
    assert "01/11/2026 (vencida)" in capa.montar_html(EMPRESA, IDENTIFICADA, [item], INICIO, AGORA, [])


def test_gerar_capa_calcula_o_sha256_de_cada_certidao_e_salva_na_pasta(pdf, tmp_path):
    recebidos = {}

    def renderizar(conteudo, destino):
        recebidos.update(conteudo=conteudo, destino=destino)

    pasta = tmp_path / "11222333000181" / "2026-11-12 16h35"
    destino = capa.gerar_capa(EMPRESA, IDENTIFICADA, itens(pdf), INICIO, pasta, agora=AGORA, renderizar=renderizar)
    assert destino == pasta / "capa-20261112-164012.pdf" == recebidos["destino"]
    assert pasta.is_dir()
    assert hashlib.sha256(pdf.read_bytes()).hexdigest() in recebidos["conteudo"]


def test_certidao_que_sumiu_gera_erro_claro(tmp_path):
    sumida = tmp_path / "nao-existe.pdf"
    with pytest.raises(capa.CapaErro, match="nao-existe.pdf"):
        capa.gerar_capa(EMPRESA, IDENTIFICADA, itens(sumida), INICIO, tmp_path, agora=AGORA,
                        renderizar=lambda c, d: None)


def test_capa_real_em_pdf_tem_o_resumo_e_o_anexo(pdf, tmp_path):
    destino = capa.gerar_capa(EMPRESA, IDENTIFICADA, itens(pdf), INICIO, tmp_path, agora=AGORA)
    dados = destino.read_bytes()
    assert dados[:4] == b"%PDF"
    texto = " ".join(texto_do_pdf(dados).split())
    assert "resumo da consulta" in texto
    assert hashlib.sha256(pdf.read_bytes()).hexdigest()[:16] in texto.replace(" ", "")
