"""Tela em pywebview. Os métodos públicos de Api ficam expostos ao JavaScript da tela."""
import os
import pathlib
import subprocess
import sys
import threading

import webview

from certidoes.cnpj import CnpjInvalido, formatar, normalizar
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


class Api:
    def __init__(self, itens=ITENS, abrir=_abrir_arquivo, executar=_em_segundo_plano):
        self._itens = itens
        self._abrir = abrir
        self._executar = executar
        self._trava = threading.Lock()
        self._execucao = None
        self._rodando = False

    def emitir(self, texto):
        """Valida o CNPJ e inicia a sequência em segundo plano. A tela acompanha por estado()."""
        try:
            cnpj = normalizar(texto)
        except CnpjInvalido as erro:
            return {"ok": False, "mensagem": str(erro)}
        with self._trava:
            if self._rodando:
                return {"ok": False, "mensagem": "Já existe uma consulta em andamento."}
            self._rodando = True
            self._execucao = Execucao(self._itens, cnpj)
            execucao = self._execucao

        def rodar():
            try:
                execucao.rodar()
            finally:
                with self._trava:
                    self._rodando = False

        self._executar(rodar)
        return {"ok": True, "cnpj": formatar(cnpj)}

    def estado(self):
        with self._trava:
            execucao, rodando = self._execucao, self._rodando
        itens = execucao.itens() if execucao else []
        for item in itens:
            item["arquivo"] = str(item["arquivo"]) if item["arquivo"] else None
        return {"rodando": rodando, "itens": itens}

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
    webview.create_window("Certidões", html=TELA.read_text(encoding="utf-8"), js_api=Api(), width=720, height=560)
    webview.start()
