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
NADA_CONSTA = "Nada consta"

_DATA = r"(\d{2}/\d{2}/\d{4})"
_CNPJ_NO_TEXTO = re.compile(r"([0-9A-Z]{2})\.?([0-9A-Z]{3})\.?([0-9A-Z]{3})/[0-9A-Z]{4}-?\d{2}")


@dataclasses.dataclass(frozen=True)
class Leitura:
    situacao: str = CONFERIR
    validade: dt.date | None = None  # None = "Conferir no PDF"
    emissao: dt.date | None = None  # só em certidão que não imprime validade (falência, sanções)
    detalhe: str | None = None  # resultado por cadastro, quando o documento reúne vários (sanções no TCU)


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


_MESES = ("JANEIRO", "FEVEREIRO", "MARCO", "ABRIL", "MAIO", "JUNHO", "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO",
          "NOVEMBRO", "DEZEMBRO")
_DATA_EXTENSO = re.compile(r"\b(\d{1,2}) DE (" + "|".join(_MESES) + r") DE (\d{4})\b")


def _data_extenso_unica(texto: str) -> dt.date | None:
    """A data por extenso ("12 DE NOVEMBRO DE 2026"), se houver uma única e válida; senão None."""
    achadas = set(_DATA_EXTENSO.findall(texto))
    if len(achadas) != 1:
        return None
    dia, mes, ano = achadas.pop()
    try:
        return dt.date(int(ano), _MESES.index(mes) + 1, int(dia))
    except ValueError:
        return None


def ler_falencia(texto: str) -> Leitura:
    """Certidão de distribuição de falências do e-SAJ: não imprime validade; lê só "nada consta" e a emissão."""
    t = normalizar(texto)
    if "CERTIDAO ESTADUAL DE DISTRIBUICOES CIVEIS" not in t or "PEDIDOS DE FALENCIA" not in t:
        return Leitura()
    situacao = NADA_CONSTA if "VERIFICOU NADA CONSTAR" in t else CONFERIR
    return Leitura(situacao, None, _data_extenso_unica(t))


# Consulta Consolidada do TCU: cada cadastro vem como "Órgão Gestor: … Cadastro: … Resultado da consulta: …".
_BLOCO_TCU = re.compile(
    r"[ÓO]rg[ãa]o Gestor:\s*(?P<orgao>.+?)\s*Cadastro:\s*(?P<cadastro>.+?)\s*Resultado da consulta:\s*(?P<resultado>.+?)"
    r"(?=\s*Para acessar|\s*[ÓO]rg[ãa]o Gestor:|\s*Obs:|$)",
    re.IGNORECASE,
)
# Nome curto e link de consulta manual de cada cadastro (CE-14), na ordem do documento.
_CADASTROS_TCU = (
    (("LICITANTES INIDONEOS",), "TCU (Licitantes Inidôneos)", "https://certidoes.apps.tcu.gov.br/lista-inidoneos"),
    (("CNIA", "IMPROBIDADE"), "CNJ (CNIA, improbidade)", "https://www.cnj.jus.br/improbidade_adm/consultar_requerido.php"),
    (("CEIS", "INIDONEAS E SUSPENSAS"), "CEIS", "https://portaldatransparencia.gov.br/sancoes/ceis"),
    (("CNEP", "EMPRESAS PUNIDAS"), "CNEP", "https://portaldatransparencia.gov.br/sancoes/cnep"),
)


def _cadastro_tcu(orgao: str, cadastro: str) -> tuple[str, str | None]:
    chave = normalizar(cadastro)
    for marcas, nome, link in _CADASTROS_TCU:
        if any(marca in chave for marca in marcas):
            return nome, link
    return f"{orgao} ({cadastro})", None


def ler_sancoes_tcu(texto: str) -> Leitura:
    """Consulta Consolidada de Pessoa Jurídica: "Nada consta" só se os quatro cadastros disserem "Nada Consta"."""
    t = normalizar(texto)
    if "CONSULTA CONSOLIDADA DE PESSOA JURIDICA" not in t:
        return Leitura()
    partes, nomes, todos_nada_consta = [], set(), True
    for bloco in _BLOCO_TCU.finditer(" ".join(texto.split())):
        nome, link = _cadastro_tcu(bloco["orgao"], bloco["cadastro"])
        resultado = bloco["resultado"].strip().rstrip(".")
        nomes.add(nome)
        if normalizar(resultado) == "NADA CONSTA":
            partes.append(f"{nome}: Nada consta.")
        else:
            todos_nada_consta = False
            partes.append(f"{nome}: {resultado}" + (f" (consulta manual: {link})." if link else "."))
    esperados = {nome for _, nome, _ in _CADASTROS_TCU}
    situacao = NADA_CONSTA if todos_nada_consta and nomes == esperados and len(partes) == 4 else CONFERIR
    emissao = _data_unica(t, _DATA + r" \d{2}:\d{2}:\d{2}")
    return Leitura(situacao, None, emissao, " ".join(partes) or None)


def ler(leitor, texto: str, cnpj: str) -> Leitura:
    """Aplica o leitor do tipo de certidão, exigindo que o CNPJ do documento confira."""
    if not texto.strip() or not cnpj_confere(texto, cnpj):
        return Leitura()
    return leitor(texto)
