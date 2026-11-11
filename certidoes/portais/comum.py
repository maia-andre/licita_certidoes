"""Peças comuns aos portais: erro de portal e gravação do PDF na pasta do CNPJ."""
import datetime as dt
import pathlib
import threading

PASTA_PADRAO = pathlib.Path.home() / "Certidoes"


class PortalErro(Exception):
    """Falha ao obter a certidão. A mensagem vai direto para a tela."""


class NaoEmitida(Exception):
    """O portal não emitiu a certidão (CE-10). Nunca é "Falha técnica"."""


class Pulada(Exception):
    """O servidor pulou o item pela tela (REQ-07). Nunca indica irregularidade."""


class SinalServidor:
    """Ação do servidor, pela tela, sobre o item em andamento.

    O portal chama `verificar()` enquanto espera; a primeira ação vale:
    pular (REQ-07) levanta Pulada; "o portal não emitiu" (REQ-11) levanta NaoEmitida.
    """

    def __init__(self):
        self._trava = threading.Lock()
        self._acao = None
        self.mensagem = ""

    def pular(self) -> None:
        with self._trava:
            if self._acao is None:
                self._acao = "pular"

    def informar_nao_emitida(self, mensagem: str = "") -> None:
        with self._trava:
            if self._acao is None:
                self._acao = "nao_emitida"
                self.mensagem = mensagem

    def verificar(self) -> None:
        with self._trava:
            acao = self._acao
        if acao == "pular":
            raise Pulada()
        if acao == "nao_emitida":
            raise NaoEmitida(self.mensagem)


def guardar_pdf(dados: bytes, cnpj: str, pasta_base, prefixo: str, agora: dt.datetime) -> pathlib.Path:
    """Grava o PDF em <pasta_base>/<CNPJ>/<prefixo>-<data-hora>.pdf e devolve o caminho."""
    if dados[:4] != b"%PDF":
        raise PortalErro("O arquivo recebido do portal não é um PDF.")
    pasta = pathlib.Path(pasta_base) / cnpj
    pasta.mkdir(parents=True, exist_ok=True)
    destino = pasta / f"{prefixo}-{agora:%Y%m%d-%H%M%S}.pdf"
    destino.write_bytes(dados)
    return destino
