import datetime as dt
import os
import sys
import threading
import time

import pytest

from certidoes.portais import navegador_servidor as ns
from certidoes.portais import receita
from certidoes.portais.comum import PortalErro

CNPJ = "11222333000181"
AGORA = dt.datetime(2026, 11, 11, 15, 40, 0)
PDF = b"%PDF-1.5\n% cnd de teste\n%%EOF\n"


class Navegador:
    """Simula o servidor: ao abrir a URL, 'baixa' um arquivo na pasta Downloads depois de um tempo."""

    def __init__(self, pasta, nome=f"Certidao-{CNPJ}.pdf", dados=PDF, atraso=0.2, abre=True):
        self.pasta, self.nome, self.dados, self.atraso, self.abre = pasta, nome, dados, atraso, abre
        self.urls = []

    def __call__(self, url):
        self.urls.append(url)
        if self.nome:
            threading.Timer(self.atraso, lambda: (self.pasta / self.nome).write_bytes(self.dados)).start()
        return self.abre


def obter(downloads, certidoes, navegador, copiados=None, **kw):
    copiados = [] if copiados is None else copiados
    opcoes = dict(pasta_base=certidoes, pasta=downloads, abrir_url=navegador, copiar=copiados.append,
                  tempo_limite_s=3, intervalo_s=0.05, agora=AGORA)
    opcoes.update(kw)
    return receita.obter_cnd(CNPJ, **opcoes)


@pytest.fixture
def pastas(tmp_path):
    downloads, certidoes = tmp_path / "Downloads", tmp_path / "Certidoes"
    downloads.mkdir()
    return downloads, certidoes


def test_abre_o_portal_da_receita_copia_o_cnpj_e_guarda_o_pdf(pastas):
    downloads, certidoes = pastas
    navegador, copiados = Navegador(downloads), []
    arquivo = obter(downloads, certidoes, navegador, copiados)
    assert navegador.urls == [receita.URL]
    assert copiados == [CNPJ]
    assert arquivo == certidoes / CNPJ / "cnd-20261111-154000.pdf"
    assert arquivo.read_bytes() == PDF


def test_pdf_e_movido_para_fora_de_downloads(pastas):
    downloads, certidoes = pastas
    obter(downloads, certidoes, Navegador(downloads))
    assert list(downloads.iterdir()) == []


def test_avisa_que_aguarda_o_servidor_depois_de_abrir_o_portal(pastas):
    downloads, certidoes = pastas
    eventos = []
    navegador = Navegador(downloads)

    def abrir(url):
        eventos.append("abriu")
        return navegador(url)

    obter(downloads, certidoes, abrir, ao_aguardar=lambda: eventos.append("aguardando"))
    assert eventos == ["abriu", "aguardando"]


def test_aceita_nome_com_sufixo_quando_o_arquivo_ja_existia(pastas):
    downloads, certidoes = pastas
    arquivo = obter(downloads, certidoes, Navegador(downloads, nome=f"Certidao-{CNPJ} (1).pdf"))
    assert arquivo.read_bytes() == PDF


def test_ignora_certidao_antiga_que_ja_estava_em_downloads(pastas):
    downloads, certidoes = pastas
    antigo = downloads / f"Certidao-{CNPJ}.pdf"
    antigo.write_bytes(b"%PDF-antigo")
    uma_hora_atras = time.time() - 3600
    os.utime(antigo, (uma_hora_atras, uma_hora_atras))
    arquivo = obter(downloads, certidoes, Navegador(downloads, nome=f"Certidao-{CNPJ} (1).pdf"))
    assert arquivo.read_bytes() == PDF
    assert antigo.exists()


def test_ignora_pdf_de_outro_cnpj(pastas):
    downloads, certidoes = pastas
    with pytest.raises(PortalErro, match="Tempo esgotado"):
        obter(downloads, certidoes, Navegador(downloads, nome="Certidao-99999999000191.pdf"), tempo_limite_s=0.6)


def test_tempo_esgotado_informa_a_pasta_vigiada(pastas):
    downloads, certidoes = pastas
    with pytest.raises(PortalErro, match="Tempo esgotado") as erro:
        obter(downloads, certidoes, Navegador(downloads, nome=None), tempo_limite_s=0.3)
    assert str(downloads) in str(erro.value)
    assert not certidoes.exists()


def test_arquivo_que_nao_e_pdf_gera_erro_e_fica_em_downloads(pastas):
    downloads, certidoes = pastas
    with pytest.raises(PortalErro, match="não é um PDF"):
        obter(downloads, certidoes, Navegador(downloads, dados=b"<html>erro</html>"))
    assert (downloads / f"Certidao-{CNPJ}.pdf").exists()


def test_navegador_que_nao_abre_gera_erro_claro(pastas):
    downloads, certidoes = pastas
    with pytest.raises(PortalErro, match="Não foi possível abrir o portal da Receita"):
        obter(downloads, certidoes, Navegador(downloads, nome=None, abre=False))


def test_pasta_downloads_inexistente_gera_erro_claro(tmp_path):
    with pytest.raises(PortalErro, match="Downloads não encontrada"):
        obter(tmp_path / "nao-existe", tmp_path / "Certidoes", Navegador(tmp_path))


def test_espera_o_tamanho_do_arquivo_parar_de_mudar(tmp_path):
    arquivo = tmp_path / f"Certidao-{CNPJ}.pdf"
    tamanhos = iter([b"%PDF", b"%PDF-1", b"%PDF-1.5", b"%PDF-1.5"])
    vistos = []

    def dormir(_):
        try:
            arquivo.write_bytes(next(tamanhos))
        except StopIteration:
            pass
        vistos.append(arquivo.stat().st_size)

    arquivo.write_bytes(b"%P")
    achado = ns.aguardar_arquivo(tmp_path, f"Certidao-{CNPJ}*.pdf", time.time() - 1, tempo_limite_s=5, dormir=dormir)
    assert achado == arquivo
    assert achado.read_bytes() == b"%PDF-1.5"


@pytest.mark.skipif(sys.platform != "win32", reason="pasta conhecida do Windows")
def test_pasta_downloads_no_windows_existe():
    assert ns.pasta_downloads().is_dir()


def test_aviso_de_nao_emitida_encerra_a_espera(tmp_path):
    from certidoes.portais.comum import NaoEmitida, SinalServidor

    sinal = SinalServidor()
    sinal.informar_nao_emitida("Informações insuficientes.")
    with pytest.raises(NaoEmitida, match="insuficientes"):
        ns.aguardar_arquivo(tmp_path, "*.pdf", time.time(), tempo_limite_s=5, dormir=lambda _: None,
                            sinal=sinal)


def test_arquivo_recusado_pelo_conteudo_nao_e_relido(tmp_path):
    (tmp_path / "outro.pdf").write_bytes(b"%PDF-outro")
    leituras = []

    def aceitar(dados):
        leituras.append(dados)
        return False

    with pytest.raises(PortalErro, match="Tempo esgotado"):
        ns.aguardar_arquivo(tmp_path, "*.pdf", time.time() - 1, tempo_limite_s=0.3, intervalo_s=0.02,
                            aceitar=aceitar)
    assert leituras == [b"%PDF-outro"]


def test_servidor_pula_enquanto_espera_o_pdf(tmp_path):
    from certidoes.portais.comum import Pulada, SinalServidor

    sinal = SinalServidor()
    sinal.pular()
    with pytest.raises(Pulada):
        ns.aguardar_arquivo(tmp_path, "*.pdf", time.time(), tempo_limite_s=5, dormir=lambda _: None, sinal=sinal)


def test_primeira_acao_do_servidor_vale():
    from certidoes.portais.comum import NaoEmitida, Pulada, SinalServidor

    sinal = SinalServidor()
    sinal.pular()
    sinal.informar_nao_emitida("ignorada")
    with pytest.raises(Pulada):
        sinal.verificar()
    outro = SinalServidor()
    outro.informar_nao_emitida("vale")
    outro.pular()
    with pytest.raises(NaoEmitida, match="vale"):
        outro.verificar()
    SinalServidor().verificar()  # sem ação: não levanta nada
