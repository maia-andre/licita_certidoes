"""Sequência de itens (REQ-05) com o estado de cada um (RN-02, REQ-09) e a leitura do PDF (REQ-10)."""
import dataclasses
import datetime as dt
import pathlib
import threading
from typing import Callable

from certidoes import leitura
from certidoes.cnpj import formatar
from certidoes.pdf import texto_do_pdf
from certidoes.portais import caixa, receita, tst
from certidoes.portais.comum import NaoEmitida, PortalErro, Pulada, SinalServidor

AGUARDANDO = "Aguardando"
EM_ANDAMENTO = "Em andamento"
AGUARDANDO_SERVIDOR = "Aguardando servidor"
OBTIDA = "Obtida"
NAO_EMITIDA = "Não emitida"
PULADA = "Pulada"
FALHA = "Falha técnica"
REPETIVEIS = (FALHA, NAO_EMITIDA, PULADA)  # REQ-14

# Modos de acesso (RN-09)
AUTOMATIZADO = "automatizado"
NAVEGADOR = "navegador"

LIMITE_MENSAGEM = 1000


@dataclasses.dataclass(frozen=True)
class Item:
    chave: str
    nome: str
    portal: str
    obter: Callable  # obter(cnpj, ao_aguardar=..., sinal=SinalServidor) -> Path; levanta PortalErro/NaoEmitida/Pulada
    instrucao: str  # texto mostrado em "Aguardando servidor"; aceita {cnpj}
    modo: str = AUTOMATIZADO
    ler: Callable | None = None  # ler(texto) -> leitura.Leitura


# Ordem da RN-01. Os demais itens entram nos próximos incrementos.
ITENS = (
    Item("cnd", "CND federal", "Receita Federal", receita.obter_cnd, receita.INSTRUCAO, NAVEGADOR, leitura.ler_cnd),
    Item("crf", "CRF FGTS", "Caixa", caixa.obter_crf, caixa.INSTRUCAO, NAVEGADOR, leitura.ler_crf),
    Item("cndt", "CNDT", "TST", tst.obter_cndt, tst.INSTRUCAO, AUTOMATIZADO, leitura.ler_cndt),
)


def _mensagem_nao_emitida(texto: str) -> str:
    texto = " ".join(texto.split())[:LIMITE_MENSAGEM]
    if texto:
        return f"Mensagem do portal, informada pelo servidor: {texto}"
    return "Informado pelo servidor. Confira a mensagem no portal."


class Execucao:
    """Percorre os itens para um CNPJ. Uma falha em um item não interrompe os demais (CE-05)."""

    def __init__(self, itens, cnpj, hoje=dt.date.today):
        self._itens = tuple(itens)
        self._por_chave = {item.chave: item for item in self._itens}
        self._cnpj = cnpj
        self._hoje = hoje
        self._trava = threading.Lock()
        self._sinais = {}
        self._estado = {item.chave: self._estado_inicial(item) for item in self._itens}

    @staticmethod
    def _estado_inicial(item):
        return {"chave": item.chave, "nome": item.nome, "portal": item.portal, "modo": item.modo,
                "estado": AGUARDANDO, "mensagem": "", "arquivo": None,
                "situacao": None, "validade": None, "vencida": False}

    def _marcar(self, chave, estado, mensagem="", arquivo=None):
        with self._trava:
            self._estado[chave].update(estado=estado, mensagem=mensagem, arquivo=arquivo)

    def rodar(self):
        for item in self._itens:
            self._rodar_item(item)

    def pode_repetir(self, chave):
        with self._trava:
            item = self._estado.get(chave)
            return item is not None and item["estado"] in REPETIVEIS

    def repetir(self, chave):
        """Roda de novo só um item em "Falha técnica", "Não emitida" ou "Pulada" (REQ-14)."""
        if not self.pode_repetir(chave):
            return
        with self._trava:
            self._estado[chave] = self._estado_inicial(self._por_chave[chave])
        self._rodar_item(self._por_chave[chave])

    def _rodar_item(self, item):
        sinal = SinalServidor()
        with self._trava:
            self._sinais[item.chave] = sinal
        self._marcar(item.chave, EM_ANDAMENTO)
        instrucao = item.instrucao.format(cnpj=formatar(self._cnpj))
        try:
            arquivo = item.obter(
                self._cnpj,
                ao_aguardar=lambda: self._marcar(item.chave, AGUARDANDO_SERVIDOR, instrucao),
                sinal=sinal,
            )
        except Pulada:
            self._marcar(item.chave, PULADA, "Pulada pelo servidor.")
        except NaoEmitida as aviso:
            self._marcar(item.chave, NAO_EMITIDA, _mensagem_nao_emitida(str(aviso)))
        except PortalErro as erro:
            self._marcar(item.chave, FALHA, str(erro))
        except Exception as erro:  # noqa: BLE001 — qualquer falha vira "Falha técnica" e a sequência segue
            self._marcar(item.chave, FALHA, f"Erro inesperado: {erro}")
        else:
            self._marcar(item.chave, OBTIDA, "", arquivo)
            self._registrar_leitura(item, arquivo)
        finally:
            with self._trava:
                self._sinais.pop(item.chave, None)

    def _registrar_leitura(self, item, arquivo):
        """Situação e validade do PDF; qualquer problema vira "Conferir no PDF" (CE-09)."""
        try:
            if item.ler:
                lido = leitura.ler(item.ler, texto_do_pdf(pathlib.Path(arquivo).read_bytes()), self._cnpj)
            else:
                lido = leitura.Leitura()
        except Exception:  # noqa: BLE001 — a certidão continua "Obtida"; só a leitura falhou
            lido = leitura.Leitura()
        validade = lido.validade.strftime("%d/%m/%Y") if lido.validade else leitura.CONFERIR
        vencida = lido.validade is not None and lido.validade < self._hoje()
        with self._trava:
            self._estado[item.chave].update(situacao=lido.situacao, validade=validade, vencida=vencida)

    def pular(self, chave):
        """O servidor pula o item em andamento (REQ-07)."""
        with self._trava:
            item = self._estado.get(chave)
            sinal = self._sinais.get(chave)
            if item is None or sinal is None or item["estado"] not in (EM_ANDAMENTO, AGUARDANDO_SERVIDOR):
                return False
            sinal.pular()
            return True

    def informar_nao_emitida(self, chave, mensagem=""):
        """O servidor avisa que o portal não emitiu. Só vale para item no navegador do servidor que aguarda o servidor."""
        with self._trava:
            item = self._estado.get(chave)
            sinal = self._sinais.get(chave)
            if item is None or sinal is None or item["modo"] != NAVEGADOR or item["estado"] != AGUARDANDO_SERVIDOR:
                return False
            sinal.informar_nao_emitida(mensagem)
            return True

    def itens(self):
        """Cópia do estado atual, na ordem da sequência."""
        with self._trava:
            return [dict(self._estado[item.chave]) for item in self._itens]

    def arquivo(self, chave):
        with self._trava:
            item = self._estado.get(chave)
            return item["arquivo"] if item else None
