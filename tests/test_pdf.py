from certidoes.pdf import contem_cnpj, texto_do_pdf
from tests.conftest import pdf_com_texto


def test_le_o_texto_de_um_pdf():
    texto = texto_do_pdf(pdf_com_texto("Certificado de Regularidade", "Inscricao: 17.051.740/0001-50"))
    assert "Certificado de Regularidade" in texto
    assert "17.051.740/0001-50" in texto


def test_pdf_ilegivel_devolve_texto_vazio():
    assert texto_do_pdf(b"%PDF-1.4 quebrado") == ""
    assert texto_do_pdf(b"nao e pdf") == ""


def test_encontra_cnpj_com_ou_sem_pontuacao():
    assert contem_cnpj("Inscrição: 17.051.740/0001-50", "17051740000150")
    assert contem_cnpj("CNPJ 17051740000150", "17051740000150")
    assert contem_cnpj("CNPJ 12.abc.345/01de-35", "12ABC34501DE35")
    assert not contem_cnpj("Inscrição: 17.051.740/0001-51", "17051740000150")
