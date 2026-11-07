"""Tela em pywebview. Os métodos públicos de Api ficam expostos ao JavaScript da tela."""
import pathlib
import subprocess
import threading

import webview

from certidoes.cnpj import CnpjInvalido, normalizar
from certidoes.portais.tst import PortalErro, obter_cndt

TELA = pathlib.Path(__file__).parent / "ui" / "index.html"


def _abrir_arquivo(caminho: pathlib.Path) -> None:
    subprocess.Popen(["xdg-open", str(caminho)])


class Api:
    def __init__(self, obter=obter_cndt, abrir=_abrir_arquivo):
        self._obter = obter
        self._abrir = abrir
        self._arquivo = None
        self._consulta = threading.Lock()

    def emitir(self, texto):
        try:
            cnpj = normalizar(texto)
        except CnpjInvalido as erro:
            return {"ok": False, "mensagem": str(erro)}
        if not self._consulta.acquire(blocking=False):
            return {"ok": False, "mensagem": "Já existe uma consulta em andamento."}
        try:
            self._arquivo = self._obter(cnpj)
        except PortalErro as erro:
            return {"ok": False, "mensagem": str(erro)}
        finally:
            self._consulta.release()
        return {"ok": True, "mensagem": "CNDT obtida.", "arquivo": str(self._arquivo)}

    def abrir_pdf(self):
        if self._arquivo is None:
            return False
        self._abrir(self._arquivo)
        return True


def iniciar():
    webview.create_window("Certidões", html=TELA.read_text(encoding="utf-8"), js_api=Api(), width=560, height=420)
    webview.start()
