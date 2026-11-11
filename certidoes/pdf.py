"""Leitura de texto de PDF, local e sem IA (RNF-05)."""
import io
import logging
import re

from pypdf import PdfReader
from pypdf.errors import PyPdfError

logging.getLogger("pypdf").setLevel(logging.ERROR)
_NAO_ALFANUMERICO = re.compile(r"[^0-9A-Z]")


def texto_do_pdf(dados: bytes) -> str:
    """Texto de todas as páginas, ou "" se o arquivo não puder ser lido."""
    try:
        leitor = PdfReader(io.BytesIO(dados))
        return "\n".join(pagina.extract_text() or "" for pagina in leitor.pages)
    except (PyPdfError, ValueError, OSError, KeyError, TypeError):
        return ""


def contem_cnpj(texto: str, cnpj: str) -> bool:
    """True se o CNPJ normalizado aparece no texto, com ou sem pontuação."""
    return cnpj in _NAO_ALFANUMERICO.sub("", texto.upper())
