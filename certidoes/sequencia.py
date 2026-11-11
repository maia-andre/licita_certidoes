"""Sequência de itens (REQ-05) com o estado de cada um (RN-02, REQ-09)."""
import dataclasses
import threading
from typing import Callable

from certidoes.cnpj import formatar
from certidoes.portais import caixa, receita, tst
from certidoes.portais.comum import NaoEmitida, PortalErro, SinalNaoEmitida

AGUARDANDO = "Aguardando"
EM_ANDAMENTO = "Em andamento"
AGUARDANDO_SERVIDOR = "Aguardando servidor"
OBTIDA = "Obtida"
NAO_EMITIDA = "Não emitida"
FALHA = "Falha técnica"

# Modos de acesso (RN-09)
AUTOMATIZADO = "automatizado"
NAVEGADOR = "navegador"

LIMITE_MENSAGEM = 1000


@dataclasses.dataclass(frozen=True)
class Item:
    chave: str
    nome: str
    portal: str
    obter: Callable  # obter(cnpj, ao_aguardar=..., [nao_emitida=...]) -> Path; levanta PortalErro/NaoEmitida
    instrucao: str  # texto mostrado em "Aguardando servidor"; aceita {cnpj}
    modo: str = AUTOMATIZADO


# Ordem da RN-01. Os demais itens entram nos próximos incrementos.
ITENS = (
    Item("cnd", "CND federal", "Receita Federal", receita.obter_cnd, receita.INSTRUCAO, NAVEGADOR),
    Item("crf", "CRF FGTS", "Caixa", caixa.obter_crf, caixa.INSTRUCAO, NAVEGADOR),
    Item("cndt", "CNDT", "TST", tst.obter_cndt, tst.INSTRUCAO, AUTOMATIZADO),
)


def _mensagem_nao_emitida(texto: str) -> str:
    texto = " ".join(texto.split())[:LIMITE_MENSAGEM]
    if texto:
        return f"Mensagem do portal, informada pelo servidor: {texto}"
    return "Informado pelo servidor. Confira a mensagem no portal."


class Execucao:
    """Percorre os itens para um CNPJ. Uma falha em um item não interrompe os demais (CE-05)."""

    def __init__(self, itens, cnpj):
        self._itens = tuple(itens)
        self._cnpj = cnpj
        self._trava = threading.Lock()
        self._sinais = {item.chave: SinalNaoEmitida() for item in self._itens if item.modo == NAVEGADOR}
        self._estado = {
            item.chave: {"chave": item.chave, "nome": item.nome, "portal": item.portal, "modo": item.modo,
                         "estado": AGUARDANDO, "mensagem": "", "arquivo": None}
            for item in self._itens
        }

    def _marcar(self, chave, estado, mensagem="", arquivo=None):
        with self._trava:
            self._estado[chave].update(estado=estado, mensagem=mensagem, arquivo=arquivo)

    def rodar(self):
        for item in self._itens:
            self._marcar(item.chave, EM_ANDAMENTO)
            instrucao = item.instrucao.format(cnpj=formatar(self._cnpj))
            opcoes = {"nao_emitida": self._sinais[item.chave]} if item.chave in self._sinais else {}
            try:
                arquivo = item.obter(
                    self._cnpj,
                    ao_aguardar=lambda chave=item.chave, texto=instrucao: self._marcar(chave, AGUARDANDO_SERVIDOR, texto),
                    **opcoes,
                )
            except NaoEmitida as aviso:
                self._marcar(item.chave, NAO_EMITIDA, _mensagem_nao_emitida(str(aviso)))
            except PortalErro as erro:
                self._marcar(item.chave, FALHA, str(erro))
            except Exception as erro:  # noqa: BLE001 — qualquer falha vira "Falha técnica" e a sequência segue
                self._marcar(item.chave, FALHA, f"Erro inesperado: {erro}")
            else:
                self._marcar(item.chave, OBTIDA, "", arquivo)

    def informar_nao_emitida(self, chave, mensagem=""):
        """O servidor avisa que o portal não emitiu. Só vale para item no navegador do servidor que aguarda o servidor."""
        with self._trava:
            item = self._estado.get(chave)
            if item is None or chave not in self._sinais or item["estado"] != AGUARDANDO_SERVIDOR:
                return False
            self._sinais[chave].informar(mensagem)
            return True

    def itens(self):
        """Cópia do estado atual, na ordem da sequência."""
        with self._trava:
            return [dict(self._estado[item.chave]) for item in self._itens]

    def arquivo(self, chave):
        with self._trava:
            item = self._estado.get(chave)
            return item["arquivo"] if item else None
