"""Tela em pywebview. Os métodos públicos de Api ficam expostos ao JavaScript da tela."""
import datetime as dt
import os
import pathlib
import subprocess
import sys
import threading

import webview

from certidoes import capa, empresa
from certidoes.cnpj import CnpjInvalido, cnpj_da_matriz, formatar, normalizar
from certidoes.empresa import ErroIdentificacao
from certidoes.portais.comum import PASTA_PADRAO
from certidoes.portais.esaj import email_valido
from certidoes.portais.navegador_servidor import copiar_para_area_de_transferencia
from certidoes.preferencias import Preferencias
from certidoes.sequencia import ITENS, Execucao, aplica

TELA = pathlib.Path(__file__).parent / "ui" / "index.html"


def _abrir_arquivo(caminho: pathlib.Path) -> None:
    """Abre o arquivo no programa padrão do sistema."""
    if sys.platform == "win32":
        os.startfile(caminho)
    else:
        subprocess.Popen(["xdg-open", str(caminho)])


def _em_segundo_plano(funcao) -> None:
    threading.Thread(target=funcao, daemon=True).start()


AVISO_FILIAL = ("Você escolheu a filial. A CND federal será pedida com o CNPJ da matriz, que a Receita exige, e a "
                "certidão de falência deve seguir o distribuidor da sede (art. 69, II, da Lei 14.133/2021).")
EM_ANDAMENTO = "Já existe uma consulta em andamento."
EMAIL_INVALIDO = ("Informe um e-mail válido para o pedido de falência no e-SAJ: o TJSP envia para ele as "
                  "instruções de emissão.")


class Api:
    def __init__(self, itens=ITENS, abrir=_abrir_arquivo, executar=_em_segundo_plano, consultar=empresa.consultar,
                 preferencias=None, pasta_base=PASTA_PADRAO, copiar=copiar_para_area_de_transferencia,
                 gerar_capa=capa.gerar_capa, relogio=dt.datetime.now):
        self._itens = itens
        self._pasta_base = pathlib.Path(pasta_base)
        self._copiar = copiar
        self._gerar_capa = gerar_capa
        self._relogio = relogio
        self._identificado_em = {}  # CNPJ -> hora da consulta à BrasilAPI (vai para a capa)
        self._escolhida = None
        self._preferencias = preferencias or Preferencias()
        self._abrir = abrir
        self._executar = executar
        self._consultar = consultar
        self._trava = threading.Lock()
        self._execucao = None
        self._rodando = False
        self._opcoes = {}  # CNPJ -> Empresa identificada que o servidor pode escolher

    def identificar(self, texto):
        """Valida o CNPJ (REQ-01) e consulta a BrasilAPI (REQ-02). Filial traz também a matriz (REQ-03)."""
        try:
            cnpj = normalizar(texto)
        except CnpjInvalido as erro:
            return {"ok": False, "mensagem": str(erro)}
        with self._trava:
            if self._rodando:
                return {"ok": False, "mensagem": EM_ANDAMENTO}
            self._opcoes = {}
        try:
            principal = self._consultar(cnpj)
        except ErroIdentificacao as erro:
            return {"ok": False, "mensagem": str(erro)}
        opcoes = {principal.cnpj: principal}
        resposta = {"ok": True, "empresa": principal.para_tela(), "matriz": None, "erro_matriz": None}
        if not principal.matriz:
            try:
                matriz = self._consultar(cnpj_da_matriz(cnpj))
                opcoes[matriz.cnpj] = matriz
                resposta["matriz"] = matriz.para_tela()
            except ErroIdentificacao as erro:
                resposta["erro_matriz"] = f"Matriz {formatar(cnpj_da_matriz(cnpj))}: {erro}"
        agora = self._relogio()
        with self._trava:
            self._opcoes = opcoes
            self._identificado_em = {numero: agora for numero in opcoes}
        return resposta

    def emitir(self, cnpj, email=None):
        """Inicia a sequência para um CNPJ identificado (REQ-05). A tela acompanha por estado().

        O e-mail vai só para o pedido no e-SAJ (REQ-12) e fica salvo nas preferências deste computador.
        Itens de portal de outra UF ficam "Não se aplica" (REQ-04).
        """
        with self._trava:
            escolhida = self._opcoes.get(cnpj) if isinstance(cnpj, str) else None
            if escolhida is None:
                return {"ok": False, "mensagem": "Identifique a empresa antes de emitir as certidões."}
            precisa_email = any("email" in item.precisa for item in self._itens if aplica(item, escolhida.uf))
            if self._rodando:
                return {"ok": False, "mensagem": EM_ANDAMENTO}
            if precisa_email and not email_valido(email):
                return {"ok": False, "mensagem": EMAIL_INVALIDO, "campo": "email"}
            dados = {"razao_social": escolhida.razao_social, "email": email.strip() if precisa_email else None,
                     "matriz": None if escolhida.matriz else cnpj_da_matriz(cnpj)}
            self._rodando = True
            self._escolhida = escolhida
            self._execucao = Execucao(self._itens, cnpj, dados=dados, uf=escolhida.uf,
                                      pasta_consulta=self._pasta_da_consulta(cnpj), relogio=self._relogio)
            execucao = self._execucao
        if precisa_email:
            self._preferencias.salvar_email(dados["email"])
        self._em_fundo(execucao.rodar)
        return {"ok": True, "cnpj": formatar(cnpj), "aviso": None if escolhida.matriz else AVISO_FILIAL}

    def email_salvo(self):
        """E-mail do último pedido no e-SAJ feito neste computador, para a tela já abrir preenchida."""
        return self._preferencias.email()

    def _em_fundo(self, funcao):
        """Roda `funcao` em segundo plano e libera nova consulta ao terminar (já com _rodando=True)."""
        def rodar():
            try:
                funcao()
            finally:
                with self._trava:
                    self._rodando = False

        self._executar(rodar)

    def pular(self, chave):
        """Botão "Pular" do item em andamento (REQ-07)."""
        with self._trava:
            execucao = self._execucao
        return bool(execucao and execucao.pular(chave))

    def repetir(self, chave):
        """Botão "Repetir" de um item em "Falha técnica", "Não emitida" ou "Pulada" (REQ-14)."""
        with self._trava:
            execucao = self._execucao
            if execucao is None:
                return {"ok": False, "mensagem": "Não há consulta para repetir."}
            if self._rodando:
                return {"ok": False, "mensagem": EM_ANDAMENTO}
            if not execucao.pode_repetir(chave):
                return {"ok": False, "mensagem": "Só dá para repetir item em falha técnica, não emitido ou pulado."}
            self._rodando = True
        self._em_fundo(lambda: execucao.repetir(chave))
        return {"ok": True}

    def estado(self):
        with self._trava:
            execucao, rodando = self._execucao, self._rodando
        itens = execucao.itens() if execucao else []
        for item in itens:
            item["arquivo"] = str(item["arquivo"]) if item["arquivo"] else None
        return {"rodando": rodando, "itens": itens}

    def informar_nao_emitida(self, chave, mensagem=""):
        """Botão "O portal não emitiu" (REQ-11, modo navegador do servidor)."""
        with self._trava:
            execucao = self._execucao
        if execucao is None or not isinstance(mensagem, str):
            return False
        return execucao.informar_nao_emitida(chave, mensagem)

    def _pasta_da_consulta(self, cnpj):
        """Certidoes/<CNPJ>/<aaaa-mm-dd hhhmm>/: uma subpasta por consulta (REQ-08)."""
        agora = self._relogio()
        pasta = self._pasta_base / cnpj / f"{agora:%Y-%m-%d %Hh%M}"
        if pasta.exists():
            pasta = self._pasta_base / cnpj / f"{agora:%Y-%m-%d %Hh%Mm%S}"
        return pasta

    def copiar_cnpj(self, chave):
        """Botão "Copiar o CNPJ de novo" do item que aguarda o servidor (o da matriz na CND de filial)."""
        with self._trava:
            execucao = self._execucao
        if execucao is None or not isinstance(chave, str):
            return False
        return bool(self._copiar(execucao.cnpj_do_item(chave)))

    def abrir_pasta(self):
        """Botão "Abrir pasta": a subpasta da consulta, ou a pasta do CNPJ se nada foi salvo."""
        with self._trava:
            execucao = self._execucao
        if execucao is None:
            return False
        for pasta in (execucao.pasta_consulta, self._pasta_base / execucao.cnpj):
            if pasta is not None and pasta.is_dir():
                try:
                    self._abrir(pasta)
                except OSError:
                    return False
                return True
        return False

    def gerar_capa(self):
        """Botão "Gerar capa em PDF" (REQ-20): resumo da consulta na pasta da consulta, aberto em seguida."""
        with self._trava:
            execucao, rodando, escolhida = self._execucao, self._rodando, self._escolhida
            identificado_em = self._identificado_em.get(escolhida.cnpj) if escolhida else None
        if rodando:
            return {"ok": False, "mensagem": EM_ANDAMENTO}
        if execucao is None or escolhida is None:
            return {"ok": False, "mensagem": "Faça uma consulta antes de gerar a capa."}
        try:
            destino = self._gerar_capa(escolhida.para_tela(), identificado_em or execucao.inicio, execucao.itens(),
                                       execucao.inicio, execucao.pasta_consulta or self._pasta_base / escolhida.cnpj)
        except capa.CapaErro as erro:
            return {"ok": False, "mensagem": str(erro)}
        try:
            self._abrir(destino)
        except OSError:
            pass  # a capa está salva; o servidor abre pela pasta
        return {"ok": True, "arquivo": str(destino)}

    def abrir_pdf(self, chave):
        with self._trava:
            execucao = self._execucao
        arquivo = execucao.arquivo(chave) if execucao else None
        if arquivo is None:
            return False
        try:
            self._abrir(arquivo)
        except OSError:
            return False
        return True


def iniciar():
    webview.create_window("Certidões do Fornecedor", html=TELA.read_text(encoding="utf-8"), js_api=Api(), width=980, height=720)
    webview.start()
