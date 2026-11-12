import datetime as dt
import threading

import pytest

from certidoes.portais import tcesp
from certidoes.portais.comum import PortalErro, Pulada, SinalServidor
from tests.conftest import TCESP_CERTIDAO, pdf_com_texto

CNPJ = "11222333000181"
AGORA = dt.datetime(2026, 11, 12, 13, 58, 25)


def certidao(cnpj="11.222.333/0001-81"):
    return pdf_com_texto(*(linha.replace("11.222.333/0001-81", cnpj) for linha in TCESP_CERTIDAO))


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
    return tcesp.obter_certidao(CNPJ, **opcoes)


def test_abre_o_formulario_do_tcesp_e_guarda_a_certidao_na_pasta_do_cnpj(pastas):
    downloads, certidoes = pastas
    navegador = Navegador(downloads, [("Certidão Apenados.pdf", certidao())])
    arquivo = obter(pastas, navegador)
    assert navegador.urls == [tcesp.URL]
    assert arquivo == certidoes / CNPJ / "apenados-tcesp-20261112-135825.pdf"
    assert arquivo.read_bytes() == certidao()
    assert list(downloads.iterdir()) == []


def test_copia_o_cnpj_e_avisa_que_aguarda_o_servidor(pastas):
    downloads, _ = pastas
    copiados, avisos = [], []
    obter(pastas, Navegador(downloads, [("Certidão Apenados (1).pdf", certidao())]),
          copiar=lambda t: copiados.append(t) or True, ao_aguardar=lambda: avisos.append("aguardando"))
    assert (copiados, avisos) == ([CNPJ], ["aguardando"])


def test_ignora_pdf_novo_que_nao_e_a_certidao_e_certidao_de_outro_cnpj(pastas):
    downloads, _ = pastas
    outros = [("boleto.pdf", pdf_com_texto("Boleto bancario", "11.222.333/0001-81")),
              ("Certidão Apenados.pdf", certidao("99.999.999/0001-91"))]
    arquivo = obter(pastas, Navegador(downloads, outros + [("Certidão Apenados (1).pdf", certidao())]))
    assert arquivo.read_bytes() == certidao()
    assert {p.name for p in downloads.iterdir()} == {n for n, _ in outros}


def test_sem_a_certidao_termina_em_tempo_esgotado(pastas):
    downloads, _ = pastas
    with pytest.raises(PortalErro, match="Tempo esgotado"):
        obter(pastas, Navegador(downloads, [("boleto.pdf", pdf_com_texto("Boleto bancario"))]), tempo_limite_s=0.6)


def test_navegador_que_nao_abre_gera_erro_claro(pastas):
    with pytest.raises(PortalErro, match="Não foi possível abrir o portal do TCE-SP"):
        obter(pastas, lambda url: False)


def test_servidor_pula_o_item_enquanto_o_programa_espera(pastas):
    sinal = SinalServidor()

    def abrir(url):
        threading.Timer(0.1, sinal.pular).start()
        return True

    with pytest.raises(Pulada):
        obter(pastas, abrir, sinal=sinal)


def test_e_certidao_do_cnpj():
    assert tcesp.e_certidao_do_cnpj(certidao(), CNPJ)
    assert not tcesp.e_certidao_do_cnpj(certidao("99.999.999/0001-91"), CNPJ)
    assert not tcesp.e_certidao_do_cnpj(pdf_com_texto("Outro documento 11.222.333/0001-81"), CNPJ)
    assert not tcesp.e_certidao_do_cnpj(b"%PDF-quebrado", CNPJ)
