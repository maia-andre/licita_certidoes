"""Peças comuns aos portais: erro de portal e gravação do PDF na pasta do CNPJ."""
import datetime as dt
import pathlib

PASTA_PADRAO = pathlib.Path.home() / "Certidoes"


class PortalErro(Exception):
    """Falha ao obter a certidão. A mensagem vai direto para a tela."""


def guardar_pdf(dados: bytes, cnpj: str, pasta_base, prefixo: str, agora: dt.datetime) -> pathlib.Path:
    """Grava o PDF em <pasta_base>/<CNPJ>/<prefixo>-<data-hora>.pdf e devolve o caminho."""
    if dados[:4] != b"%PDF":
        raise PortalErro("O arquivo recebido do portal não é um PDF.")
    pasta = pathlib.Path(pasta_base) / cnpj
    pasta.mkdir(parents=True, exist_ok=True)
    destino = pasta / f"{prefixo}-{agora:%Y%m%d-%H%M%S}.pdf"
    destino.write_bytes(dados)
    return destino
