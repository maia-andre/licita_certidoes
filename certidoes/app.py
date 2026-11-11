"""Tela em pywebview. Os métodos públicos de Api ficam expostos ao JavaScript da tela."""
import os
import pathlib
import subprocess
import sys
import threading

import webview

from certidoes import empresa
from certidoes.cnpj import CnpjInvalido, cnpj_da_matriz, formatar, normalizar
from certidoes.empresa import ErroIdentificacao
from certidoes.sequencia import ITENS, Execucao

TELA = pathlib.Path(__file__).parent / "ui" / "index.html"


def _abrir_arquivo(caminho: pathlib.Path) -> None:
    """Abre o arquivo no programa padrão do sistema."""
    if sys.platform == "win32":
        os.startfile(caminho)
    else:
        subprocess.Popen(["xdg-open", str(caminho)])


def _em_segundo_plano(funcao) -> None:
    threading.Thread(target=funcao, daemon=True).start()


AVISO_FILIAL = ("Você escolheu a filial. A certidão de falência deve seguir o distribuidor da sede "
                "(art. 69, II, da Lei 14.133/2021).")
NAO_ATENDIDA = "Empresa com CNPJ de {uf}: não atendida nesta versão, que cobre apenas CNPJ de SP. Nenhum portal foi aberto."
EM_ANDAMENTO = "Já existe uma consulta em andamento."


class Api:
    def __init__(self, itens=ITENS, abrir=_abrir_arquivo, executar=_em_segundo_plano, consultar=empresa.consultar):
        self._itens = itens
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
        with self._trava:
            self._opcoes = opcoes
        return resposta

    def emitir(self, cnpj):
        """Inicia a sequência para um CNPJ identificado e atendido (REQ-04). A tela acompanha por estado()."""
        with self._trava:
            escolhida = self._opcoes.get(cnpj) if isinstance(cnpj, str) else None
            if escolhida is None:
                return {"ok": False, "mensagem": "Identifique a empresa antes de emitir as certidões."}
            if not escolhida.atendida:
                return {"ok": False, "mensagem": NAO_ATENDIDA.format(uf=escolhida.uf)}
            if self._rodando:
                return {"ok": False, "mensagem": EM_ANDAMENTO}
            self._rodando = True
            self._execucao = Execucao(self._itens, cnpj)
            execucao = self._execucao
        self._em_fundo(execucao.rodar)
        return {"ok": True, "cnpj": formatar(cnpj), "aviso": None if escolhida.matriz else AVISO_FILIAL}

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
    webview.create_window("Certidões", html=TELA.read_text(encoding="utf-8"), js_api=Api(), width=980, height=600)
    webview.start()
