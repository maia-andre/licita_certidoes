"""Situação e validade lidas do texto do PDF (REQ-10, RN-03, RN-04).

Regra geral: na dúvida, "Conferir no PDF". O programa nunca presume situação nem calcula prazo.
"""
import dataclasses
import datetime as dt
import re
import unicodedata

CONFERIR = "Conferir no PDF"
NEGATIVA = "Negativa"
POSITIVA_EFEITO_NEGATIVA = "Positiva com efeitos de negativa"
POSITIVA = "Positiva"
REGULAR = "Regular"

_DATA = r"(\d{2}/\d{2}/\d{4})"
_CNPJ_NO_TEXTO = re.compile(r"([0-9A-Z]{2})\.?([0-9A-Z]{3})\.?([0-9A-Z]{3})/[0-9A-Z]{4}-?\d{2}")


@dataclasses.dataclass(frozen=True)
class Leitura:
    situacao: str = CONFERIR
    validade: dt.date | None = None  # None = "Conferir no PDF"


def normalizar(texto: str) -> str:
    """Maiúsculas, sem acentos e com espaços simples, para comparar padrões."""
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return " ".join(sem_acento.upper().split())


def _data_unica(texto: str, padrao: str) -> dt.date | None:
    """A data do padrão, se aparecer uma única data distinta e válida; senão None."""
    achadas = set(re.findall(padrao, texto))
    if len(achadas) != 1:
        return None
    try:
        return dt.datetime.strptime(achadas.pop(), "%d/%m/%Y").date()
    except ValueError:
        return None


def _titulo(texto: str) -> str:
    """Trecho logo após o primeiro "CERTIDAO NEGATIVA/POSITIVA", até "NOME:" ou 160 caracteres."""
    achado = re.search(r"CERTIDAO (NEGATIVA|POSITIVA)\b", texto)
    if not achado:
        return ""
    trecho = texto[achado.start(): achado.start() + 160]
    return trecho.split("NOME:", 1)[0]


def _situacao_pelo_titulo(titulo: str) -> str:
    if re.search(r"^CERTIDAO POSITIVA\b.*\bCOM EFEITOS? DE NEGATIVA\b", titulo):
        return POSITIVA_EFEITO_NEGATIVA
    if titulo.startswith("CERTIDAO POSITIVA"):
        return POSITIVA
    if titulo.startswith("CERTIDAO NEGATIVA"):
        return NEGATIVA
    return CONFERIR


def cnpj_confere(texto: str, cnpj: str) -> bool:
    """True se algum CNPJ do texto tem a mesma raiz (8 primeiros caracteres) do CNPJ consultado."""
    return any("".join(m.groups()) == cnpj[:8] for m in _CNPJ_NO_TEXTO.finditer(normalizar(texto)))


def ler_cnd(texto: str) -> Leitura:
    t = normalizar(texto)
    titulo = _titulo(t)
    if "TRIBUTOS FEDERAIS" not in titulo:
        return Leitura()
    return Leitura(_situacao_pelo_titulo(titulo), _data_unica(t, r"VALIDA ATE " + _DATA))


def ler_cndt(texto: str) -> Leitura:
    t = normalizar(texto)
    titulo = _titulo(t)
    if "DEBITOS TRABALHISTAS" not in titulo:
        return Leitura()
    return Leitura(_situacao_pelo_titulo(titulo), _data_unica(t, r"VALIDADE: " + _DATA))


def ler_crf(texto: str) -> Leitura:
    t = normalizar(texto)
    if "CERTIFICADO DE REGULARIDADE DO FGTS" not in t:
        return Leitura()
    situacao = REGULAR if "ENCONTRA-SE EM SITUACAO REGULAR" in t else CONFERIR
    return Leitura(situacao, _data_unica(t, r"VALIDADE: \d{2}/\d{2}/\d{4} A " + _DATA))


def ler(leitor, texto: str, cnpj: str) -> Leitura:
    """Aplica o leitor do tipo de certidão, exigindo que o CNPJ do documento confira."""
    if not texto.strip() or not cnpj_confere(texto, cnpj):
        return Leitura()
    return leitor(texto)
