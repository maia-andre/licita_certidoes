"""Sequência de itens (REQ-05) com o estado de cada um (RN-02, REQ-09) e a leitura do PDF (REQ-10)."""
import dataclasses
import datetime as dt
import pathlib
import threading
from typing import Callable

from certidoes import leitura
from certidoes.cnpj import formatar
from certidoes.pdf import texto_do_pdf
from certidoes.portais import caixa, cnj, esaj, receita, tcesp, tcu, tst
from certidoes.portais.comum import NaoEmitida, Pedido, PortalErro, Pulada, SinalServidor

AGUARDANDO = "Aguardando"
EM_ANDAMENTO = "Em andamento"
AGUARDANDO_SERVIDOR = "Aguardando servidor"
OBTIDA = "Obtida"
NAO_EMITIDA = "Não emitida"
PULADA = "Pulada"
FALHA = "Falha técnica"
PEDIDO_FEITO = "Pedido feito: acompanhar"
NAO_SE_APLICA = "Não se aplica"  # portal de outra UF (REQ-04); nunca indica irregularidade
REPETIVEIS = (FALHA, NAO_EMITIDA, PULADA)  # REQ-14

# Modos de acesso (RN-09)
AUTOMATIZADO = "automatizado"
NAVEGADOR = "navegador"
DIRETO = "direto"  # consulta direta ao portal, sem navegador e sem captcha (TCU)

LIMITE_MENSAGEM = 1000


@dataclasses.dataclass(frozen=True)
class Item:
    chave: str
    nome: str
    portal: str
    obter: Callable  # obter(cnpj, ao_aguardar=..., sinal=SinalServidor, **dados) -> Path | Pedido;
    #                  levanta PortalErro/NaoEmitida/Pulada
    instrucao: str  # texto mostrado em "Aguardando servidor"; aceita {cnpj}
    modo: str = AUTOMATIZADO
    ler: Callable | None = None  # ler(texto) -> leitura.Leitura
    # Dados da consulta repassados a obter(), p. ex. ("razao_social", "email"). "avisar" é especial:
    # recebe avisar(mensagem), que atualiza a mensagem do item em andamento.
    precisa: tuple = ()
    uf: str | None = None  # UF atendida pelo portal; None = qualquer UF (REQ-04)
    fora_da_uf: str = ""  # mensagem de "Não se aplica"; aceita {uf}
    # Com "matriz" em `precisa`, filial é consultada pelo CNPJ da matriz (RN-07); esta mensagem aceita {matriz}.
    aviso_matriz: str = ""


def aplica(item: Item, uf: str | None) -> bool:
    """O item vale para o CNPJ da UF informada (REQ-04). Sem UF conhecida, vale."""
    return item.uf is None or uf is None or uf.upper() == item.uf


# Ordem da RN-01. Adiados (RN-10): Certidão Única estadual (item 4), eproc (item 6) e CND de SJC (item 9).
ITENS = (
    Item("cnd", "CND federal", "Receita Federal", receita.obter_cnd, receita.INSTRUCAO, NAVEGADOR, leitura.ler_cnd,
         precisa=("matriz",), aviso_matriz=receita.AVISO_MATRIZ),
    Item("crf", "CRF FGTS", "Caixa", caixa.obter_crf, caixa.INSTRUCAO, NAVEGADOR, leitura.ler_crf),
    Item("cndt", "CNDT", "TST", tst.obter_cndt, tst.INSTRUCAO, AUTOMATIZADO, leitura.ler_cndt),
    Item("falencia", "Falência, concordatas e recuperações", "e-SAJ/TJSP", esaj.obter_pedido_falencia,
         esaj.INSTRUCAO, AUTOMATIZADO, leitura.ler_falencia, precisa=("razao_social", "email", "avisar"), uf="SP",
         fora_da_uf="CNPJ de {uf}: o e-SAJ do TJSP não emite esta certidão. Peça-a ao distribuidor do Tribunal de "
                    "Justiça da sede (art. 69, II, da Lei 14.133/2021)."),
    Item("sancoes", "Sanções: TCU, CEIS e CNEP", "TCU", tcu.obter_consulta, tcu.INSTRUCAO, DIRETO,
         leitura.ler_sancoes_tcu),
    Item("improbidade", "Improbidade (CNJ)", "CNJ", cnj.obter_certidao, cnj.INSTRUCAO, DIRETO,
         leitura.ler_improbidade_cnj),
    Item("apenados", "Apenados do TCE-SP", "TCE-SP", tcesp.obter_certidao, tcesp.INSTRUCAO, NAVEGADOR,
         leitura.ler_apenados_tcesp),
)


def _mensagem_pedido(pedido: Pedido) -> str:
    partes = ["Pedido"]
    if pedido.numero:
        partes.append(f"nº {pedido.numero}")
    if pedido.data:
        partes.append(f"de {pedido.data}")
    texto = " ".join(partes) + " aceito pelo portal."
    if pedido.email:
        texto += f" As instruções para emitir a certidão vão para {pedido.email}."
    if pedido.prazo_dias:
        texto += f" Prazo máximo informado: {pedido.prazo_dias} dias."
    if pedido.observacao:
        texto += f" {pedido.observacao}"
    return texto


def _mensagem_nao_emitida(texto: str) -> str:
    texto = " ".join(texto.split())[:LIMITE_MENSAGEM]
    if texto:
        return f"Mensagem do portal, informada pelo servidor: {texto}"
    return "Informado pelo servidor. Confira a mensagem no portal."


class Execucao:
    """Percorre os itens para um CNPJ. Uma falha em um item não interrompe os demais (CE-05)."""

    def __init__(self, itens, cnpj, hoje=dt.date.today, dados=None, uf=None):
        self._itens = tuple(itens)
        self._uf = uf  # UF do CNPJ escolhido (REQ-04)
        self._dados = dict(dados or {})  # razão social, e-mail etc.; só em memória
        self._por_chave = {item.chave: item for item in self._itens}
        self._cnpj = cnpj
        self._hoje = hoje
        self._trava = threading.Lock()
        self._sinais = {}
        self._estado = {item.chave: self._estado_inicial(item) for item in self._itens}
        for item in self._itens:
            if not aplica(item, uf):
                self._estado[item.chave].update(estado=NAO_SE_APLICA, mensagem=item.fora_da_uf.format(uf=uf))

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
            if aplica(item, self._uf):
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
        matriz = self._dados.get("matriz") if "matriz" in item.precisa else None
        aviso_matriz = item.aviso_matriz.format(matriz=formatar(matriz)) if matriz else ""
        instrucao = " ".join(filter(None, [item.instrucao.format(cnpj=formatar(matriz or self._cnpj)), aviso_matriz]))
        try:
            extras = {nome: self._dados.get(nome) for nome in item.precisa if nome != "avisar"}
            if "avisar" in item.precisa:
                extras["avisar"] = lambda mensagem: self._marcar(item.chave, EM_ANDAMENTO, mensagem)
            resultado = item.obter(
                self._cnpj,
                ao_aguardar=lambda: self._marcar(item.chave, AGUARDANDO_SERVIDOR, instrucao),
                sinal=sinal,
                **extras,
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
            if isinstance(resultado, Pedido):
                self._marcar(item.chave, PEDIDO_FEITO, _mensagem_pedido(resultado))
            else:
                self._marcar(item.chave, OBTIDA, aviso_matriz, resultado)
                self._registrar_leitura(item, resultado)
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
        if lido.validade:
            validade = lido.validade.strftime("%d/%m/%Y")
        elif lido.emissao:  # certidão sem validade impressa (falência): mostra a emissão, sem calcular prazo
            validade = f"Não impressa (emitida em {lido.emissao:%d/%m/%Y})"
        else:
            validade = leitura.CONFERIR
        vencida = lido.validade is not None and lido.validade < self._hoje()
        with self._trava:
            self._estado[item.chave].update(situacao=lido.situacao, validade=validade, vencida=vencida)
            if lido.detalhe:  # resultado por cadastro (CE-14)
                self._estado[item.chave]["mensagem"] = lido.detalhe[:LIMITE_MENSAGEM]

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
