"""Certidão de improbidade do CNJ (CNIA), por consulta direta (RN-09): sem navegador e sem captcha.

A Consulta Consolidada do TCU respondeu "Sistema do CNJ está indisponível" em 20 de 20 consultas de
12/11/2026, enquanto o próprio site do CNJ emitia a certidão normalmente. Por isso o CNJ virou item próprio.

O programa faz o que a página do CNJ faz:
1. pergunta se o CNPJ tem condenações (função `verificaRequeridoPossuiCertidao`, a mesma da página);
2. sem condenações, baixa a "Certidão Negativa"; com condenações, baixa a certidão com os registros.
Resposta inesperada vira erro, nunca certidão presumida.
"""
import datetime as dt
import pathlib
import re
import time
import urllib.error
import urllib.parse
import urllib.request

from certidoes.portais.comum import PASTA_PADRAO, PortalErro, guardar_pdf

__all__ = ["obter_certidao", "INSTRUCAO", "PortalErro"]

URL_BASE = "https://www.cnj.jus.br/improbidade_adm"
TEMPO_LIMITE_S = 60
CABECALHOS = {"User-Agent": "licita_certidoes"}  # identificação genérica, sem dados do usuário
INSTRUCAO = "Consulta direta ao CNJ, sem captcha: não é preciso fazer nada."
SEM_RESPOSTA = "O portal do CNJ não respondeu. Confira a internet e repita o item."
MUDOU = "O portal do CNJ respondeu de um jeito inesperado. Confira manualmente em {url}/consultar_requerido.php."
_RESPOSTA = re.compile(r"\+:var res = '([^']*)';")


def _pedir(url, dados=None, tempo_limite_s=TEMPO_LIMITE_S) -> bytes:
    corpo = urllib.parse.urlencode(dados).encode("ascii") if dados is not None else None
    pedido = urllib.request.Request(url, data=corpo, headers=CABECALHOS)
    try:
        with urllib.request.urlopen(pedido, timeout=tempo_limite_s) as resposta:
            return resposta.read()
    except urllib.error.HTTPError as erro:
        raise PortalErro(f"O portal do CNJ respondeu com erro {erro.code}. Repita o item mais tarde.") from erro
    except (urllib.error.URLError, TimeoutError, OSError) as erro:
        raise PortalErro(SEM_RESPOSTA) from erro


def quantidade_de_condenacoes(cnpj, url_base=URL_BASE, tempo_limite_s=TEMPO_LIMITE_S) -> int:
    """0 se o CNPJ não tem condenações no CNIA; o número informado pelo CNJ, se tiver."""
    dados = [("rs", "verificaRequeridoPossuiCertidao"), ("rst", ""), ("rsrnd", str(int(time.time() * 1000)))]
    for argumento in (cnpj, "", "J", "I", "POSICAO_INICIAL_PAGINACAO_PHP0", "QUANTIDADE_REGISTROS_PAGINACAO15"):
        dados.append(("rsargs[]", argumento))
    texto = _pedir(f"{url_base}/consultar_requerido.php?validar=form", dados, tempo_limite_s).decode("iso-8859-1")
    achado = _RESPOSTA.search(texto)
    if not achado:
        raise PortalErro(MUDOU.format(url=url_base))
    valor = achado.group(1).strip()
    if valor == "":
        return 0
    if valor.isdigit() and int(valor) > 0:
        return int(valor)
    raise PortalErro(MUDOU.format(url=url_base))


def obter_certidao(cnpj, ao_aguardar=None, sinal=None, *, pasta_base=PASTA_PADRAO, url_base=URL_BASE,
                   tempo_limite_s=TEMPO_LIMITE_S, agora=None) -> pathlib.Path:
    """Baixa a certidão do CNIA para o CNPJ e guarda o PDF como improbidade-cnj-<data-hora>.pdf."""
    if sinal is not None:
        sinal.verificar()
    tipo = "P" if quantidade_de_condenacoes(cnpj, url_base, tempo_limite_s) else "N"
    consulta = urllib.parse.urlencode({"tipoCertidao": tipo, "cpfCnpj": cnpj, "tipoPessoa": "J"})
    dados = _pedir(f"{url_base}/certidao.php?{consulta}", tempo_limite_s=tempo_limite_s)
    return guardar_pdf(dados, cnpj, pasta_base, "improbidade-cnj", agora or dt.datetime.now())
