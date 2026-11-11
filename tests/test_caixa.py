import datetime as dt
import threading

import pytest

from certidoes.portais import caixa
from certidoes.portais.comum import NaoEmitida, PortalErro, Pulada, SinalServidor
from tests.conftest import pdf_com_texto

CNPJ = "17051740000150"
AGORA = dt.datetime(2026, 11, 11, 16, 0, 0)


def crf(inscricao="17.051.740/0001-50"):
    return pdf_com_texto("Certificado de Regularidade", "do FGTS - CRF", f"Inscricao: {inscricao}",
                         "Validade: 09/11/2026 a 08/12/2026")


class Navegador:
    """Simula o servidor salvando arquivos em Downloads depois de abrir o portal."""

    def __init__(self, pasta, arquivos, atraso=0.15):
        self.pasta, self.arquivos, self.atraso = pasta, arquivos, atraso
        self.urls = []

    def __call__(self, url):
        self.urls.append(url)

        def salvar():
            for nome, dados in self.arquivos:
                (self.pasta / nome).write_bytes(dados)

        if self.arquivos:
            threading.Timer(self.atraso, salvar).start()
        return True


@pytest.fixture
def pastas(tmp_path):
    downloads = tmp_path / "Downloads"
    downloads.mkdir()
    return downloads, tmp_path / "Certidoes"


def obter(pastas, navegador, **kw):
    downloads, certidoes = pastas
    opcoes = dict(pasta_base=certidoes, pasta=downloads, abrir_url=navegador, copiar=lambda t: True,
                  tempo_limite_s=3, intervalo_s=0.05, agora=AGORA)
    opcoes.update(kw)
    return caixa.obter_crf(CNPJ, **opcoes)


def test_reconhece_o_crf_salvo_pela_impressao_e_guarda_na_pasta_do_cnpj(pastas):
    downloads, certidoes = pastas
    navegador = Navegador(downloads, [("Consulta Regularidade do Empregador.pdf", crf())])
    arquivo = obter(pastas, navegador)
    assert navegador.urls == [caixa.URL]
    assert arquivo == certidoes / CNPJ / "crf-20261111-160000.pdf"
    assert arquivo.read_bytes() == crf()
    assert list(downloads.iterdir()) == []


def test_aceita_crf_com_nome_escolhido_pelo_servidor(pastas):
    downloads, _ = pastas
    arquivo = obter(pastas, Navegador(downloads, [("fgts viacao teste 1.pdf", crf())]))
    assert arquivo.name.startswith("crf-")


def test_ignora_pdf_novo_que_nao_e_crf_e_crf_de_outro_cnpj(pastas):
    downloads, _ = pastas
    outros = [("boleto.pdf", pdf_com_texto("Boleto bancario", "17.051.740/0001-50")),
              ("Consulta Regularidade do Empregador.pdf", crf("99.999.999/0001-91"))]
    navegador = Navegador(downloads, outros + [("Consulta Regularidade do Empregador (1).pdf", crf())])
    arquivo = obter(pastas, navegador)
    assert arquivo.read_bytes() == crf()
    assert {p.name for p in downloads.iterdir()} == {n for n, _ in outros}


def test_sem_crf_do_cnpj_termina_em_tempo_esgotado(pastas):
    downloads, _ = pastas
    navegador = Navegador(downloads, [("boleto.pdf", pdf_com_texto("Boleto bancario"))])
    with pytest.raises(PortalErro, match="Tempo esgotado"):
        obter(pastas, navegador, tempo_limite_s=0.6)


def test_servidor_informa_que_o_portal_nao_emitiu(pastas):
    downloads, _ = pastas
    sinal = SinalServidor()

    def abrir(url):
        threading.Timer(0.1, lambda: sinal.informar_nao_emitida("Empregador nao cadastrado.")).start()
        return True

    with pytest.raises(NaoEmitida, match="Empregador nao cadastrado."):
        obter(pastas, abrir, sinal=sinal)


def test_e_crf_do_cnpj():
    assert caixa.e_crf_do_cnpj(crf(), CNPJ)
    assert not caixa.e_crf_do_cnpj(crf("99.999.999/0001-91"), CNPJ)
    assert not caixa.e_crf_do_cnpj(pdf_com_texto("Outro documento 17.051.740/0001-50"), CNPJ)
    assert not caixa.e_crf_do_cnpj(b"%PDF-quebrado", CNPJ)
