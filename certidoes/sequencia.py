"""Sequência de itens (REQ-05) com o estado de cada um (RN-02, REQ-09)."""
import dataclasses
import threading
from typing import Callable

from certidoes.cnpj import formatar
from certidoes.portais import receita, tst
from certidoes.portais.comum import PortalErro

AGUARDANDO = "Aguardando"
EM_ANDAMENTO = "Em andamento"
AGUARDANDO_SERVIDOR = "Aguardando servidor"
OBTIDA = "Obtida"
FALHA = "Falha técnica"


@dataclasses.dataclass(frozen=True)
class Item:
    chave: str
    nome: str
    portal: str
    obter: Callable  # obter(cnpj, ao_aguardar=callable) -> Path; levanta PortalErro
    instrucao: str  # texto mostrado em "Aguardando servidor"; aceita {cnpj}


# Ordem da RN-01. Os demais itens entram nos próximos incrementos.
ITENS = (
    Item("cnd", "CND federal", "Receita Federal", receita.obter_cnd, receita.INSTRUCAO),
    Item("cndt", "CNDT", "TST", tst.obter_cndt, tst.INSTRUCAO),
)


class Execucao:
    """Percorre os itens para um CNPJ. Uma falha em um item não interrompe os demais (CE-05)."""

    def __init__(self, itens, cnpj):
        self._itens = tuple(itens)
        self._cnpj = cnpj
        self._trava = threading.Lock()
        self._estado = {
            item.chave: {"chave": item.chave, "nome": item.nome, "portal": item.portal,
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
            try:
                arquivo = item.obter(
                    self._cnpj,
                    ao_aguardar=lambda chave=item.chave, texto=instrucao: self._marcar(chave, AGUARDANDO_SERVIDOR, texto),
                )
            except PortalErro as erro:
                self._marcar(item.chave, FALHA, str(erro))
            except Exception as erro:  # noqa: BLE001 — qualquer falha vira "Falha técnica" e a sequência segue
                self._marcar(item.chave, FALHA, f"Erro inesperado: {erro}")
            else:
                self._marcar(item.chave, OBTIDA, "", arquivo)

    def itens(self):
        """Cópia do estado atual, na ordem da sequência."""
        with self._trava:
            return [dict(self._estado[item.chave]) for item in self._itens]

    def arquivo(self, chave):
        with self._trava:
            item = self._estado.get(chave)
            return item["arquivo"] if item else None
