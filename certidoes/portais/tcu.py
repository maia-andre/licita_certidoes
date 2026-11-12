"""Consulta Consolidada de Pessoa Jurídica do TCU (REQ-16, RN-11): Licitantes Inidôneos (TCU), CNIA (CNJ), CEIS e CNEP.

Consulta direta, sem navegador: o portal público não tem captcha e entrega o PDF pela mesma API que a sua página
usa (`Accept: application/pdf`). Nada do servidor é enviado além do CNPJ consultado.
"""
import datetime as dt
import pathlib
import urllib.error
import urllib.request

from certidoes.portais.comum import PASTA_PADRAO, PortalErro, guardar_pdf

__all__ = ["obter_consulta", "PortalErro", "INSTRUCAO"]

URL = "https://certidoes-apf.apps.tcu.gov.br/api/rest/publico/certidoes/{cnpj}"
TEMPO_LIMITE_S = 60
# Identificação genérica, sem dados do usuário.
CABECALHOS = {"User-Agent": "licita_certidoes", "Accept": "application/pdf"}
INSTRUCAO = "Consulta direta ao TCU, sem captcha: não é preciso fazer nada."
SEM_RESPOSTA = "O portal do TCU não respondeu. Confira a internet e repita o item."


def _baixar(url: str, tempo_limite_s: float) -> bytes:
    pedido = urllib.request.Request(url, headers=CABECALHOS)
    try:
        with urllib.request.urlopen(pedido, timeout=tempo_limite_s) as resposta:
            return resposta.read()
    except urllib.error.HTTPError as erro:
        raise PortalErro(f"O portal do TCU respondeu com erro {erro.code}. Repita o item mais tarde.") from erro
    except (urllib.error.URLError, TimeoutError, OSError) as erro:
        raise PortalErro(SEM_RESPOSTA) from erro


def obter_consulta(
    cnpj,
    ao_aguardar=None,
    sinal=None,
    *,
    pasta_base=PASTA_PADRAO,
    url=URL,
    tempo_limite_s=TEMPO_LIMITE_S,
    agora=None,
) -> pathlib.Path:
    """Baixa o PDF da Consulta Consolidada e o guarda na pasta do CNPJ.

    Não há captcha, então `ao_aguardar` nunca é chamado. `sinal` permite pular antes da consulta;
    depois que o PDF chega, o resultado é mantido.
    """
    if sinal is not None:
        sinal.verificar()
    dados = _baixar(url.format(cnpj=cnpj), tempo_limite_s)
    return guardar_pdf(dados, cnpj, pasta_base, "sancoes-tcu", agora or dt.datetime.now())
