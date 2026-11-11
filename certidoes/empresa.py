"""Identificação da empresa pela BrasilAPI (REQ-02, CE-02, CE-03)."""
import dataclasses
import json
import urllib.error
import urllib.request

from certidoes.cnpj import formatar

URL = "https://brasilapi.com.br/api/cnpj/v1/{cnpj}"
TEMPO_LIMITE_S = 20
UF_ATENDIDA = "SP"
# Identificação genérica, sem dados do usuário.
CABECALHOS = {"User-Agent": "licita_certidoes", "Accept": "application/json"}


class ErroIdentificacao(Exception):
    """Não foi possível identificar a empresa. A mensagem vai para a tela."""


@dataclasses.dataclass(frozen=True)
class Empresa:
    cnpj: str
    razao_social: str
    uf: str
    situacao_cadastral: str
    matriz: bool

    @property
    def ativa(self) -> bool:
        return self.situacao_cadastral.upper() == "ATIVA"

    @property
    def atendida(self) -> bool:
        return self.uf.upper() == UF_ATENDIDA

    def para_tela(self) -> dict:
        return {"cnpj": self.cnpj, "cnpj_formatado": formatar(self.cnpj), "razao_social": self.razao_social,
                "uf": self.uf, "situacao_cadastral": self.situacao_cadastral, "ativa": self.ativa,
                "matriz": self.matriz, "atendida": self.atendida}


def _buscar(url: str) -> dict:
    """GET JSON. Levanta ErroIdentificacao com mensagem clara."""
    pedido = urllib.request.Request(url, headers=CABECALHOS)
    try:
        with urllib.request.urlopen(pedido, timeout=TEMPO_LIMITE_S) as resposta:
            return json.loads(resposta.read().decode("utf-8"))
    except urllib.error.HTTPError as erro:
        if erro.code == 404:
            raise ErroIdentificacao("CNPJ não encontrado na BrasilAPI.") from erro
        raise ErroIdentificacao(
            f"Não foi possível identificar a empresa: a BrasilAPI respondeu com erro {erro.code}. Tente novamente."
        ) from erro
    except (urllib.error.URLError, TimeoutError, OSError) as erro:
        raise ErroIdentificacao(
            "Não foi possível identificar a empresa: a BrasilAPI não respondeu. Confira a internet e tente novamente."
        ) from erro
    except (json.JSONDecodeError, UnicodeDecodeError) as erro:
        raise ErroIdentificacao("Não foi possível identificar a empresa: resposta inesperada da BrasilAPI.") from erro


def consultar(cnpj: str, buscar=_buscar) -> Empresa:
    """Dados cadastrais de um CNPJ já normalizado."""
    dados = buscar(URL.format(cnpj=cnpj))
    try:
        return Empresa(
            cnpj=cnpj,
            razao_social=str(dados["razao_social"]).strip(),
            uf=str(dados["uf"]).strip().upper(),
            situacao_cadastral=str(dados.get("descricao_situacao_cadastral") or "Não informada").strip(),
            matriz=int(dados["identificador_matriz_filial"]) == 1,
        )
    except (KeyError, TypeError, ValueError) as erro:
        raise ErroIdentificacao("Não foi possível identificar a empresa: resposta incompleta da BrasilAPI.") from erro
