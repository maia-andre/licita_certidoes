"""Validação de CNPJ, numérico ou alfanumérico (IN RFB 2.229/2024)."""
import re

_FORMATO = re.compile(r"[0-9A-Z]{12}[0-9]{2}")
_SEPARADORES = re.compile(r"[.\-/\s]")
_PESOS = (6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)


class CnpjInvalido(ValueError):
    pass


def _digito(base: str) -> str:
    pesos = _PESOS[-len(base):]
    soma = sum((ord(c) - 48) * p for c, p in zip(base, pesos))
    resto = soma % 11
    return "0" if resto < 2 else str(11 - resto)


def normalizar(texto) -> str:
    """Devolve o CNPJ só com letras maiúsculas e dígitos, ou levanta CnpjInvalido."""
    if not isinstance(texto, str):
        raise CnpjInvalido("CNPJ inválido.")
    cnpj = _SEPARADORES.sub("", texto).upper()
    if not _FORMATO.fullmatch(cnpj) or len(set(cnpj)) == 1:
        raise CnpjInvalido("CNPJ inválido.")
    primeiro = _digito(cnpj[:12])
    if cnpj[12:] != primeiro + _digito(cnpj[:12] + primeiro):
        raise CnpjInvalido("CNPJ inválido.")
    return cnpj
