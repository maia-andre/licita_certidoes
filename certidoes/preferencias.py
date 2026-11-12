"""Preferências do servidor neste computador (hoje, só o e-mail do pedido no e-SAJ).

Ficam em um JSON na pasta de configuração do usuário: %APPDATA%\\licita_certidoes no Windows,
~/.config/licita_certidoes no Linux. Nunca guarda senha, token ou sessão (RNF-03).
"""
import json
import os
import pathlib
import sys


def arquivo_padrao() -> pathlib.Path:
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or pathlib.Path.home() / "AppData" / "Roaming"
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or pathlib.Path.home() / ".config"
    return pathlib.Path(base) / "licita_certidoes" / "preferencias.json"


class Preferencias:
    def __init__(self, arquivo=None):
        self._arquivo = pathlib.Path(arquivo) if arquivo else arquivo_padrao()

    def _ler(self) -> dict:
        try:
            dados = json.loads(self._arquivo.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        return dados if isinstance(dados, dict) else {}

    def email(self) -> str:
        email = self._ler().get("email")
        return email if isinstance(email, str) else ""

    def salvar_email(self, email: str) -> bool:
        """Grava o e-mail se mudou. Falha de gravação não impede a consulta: devolve False."""
        dados = self._ler()
        if dados.get("email") == email:
            return True
        dados["email"] = email
        try:
            self._arquivo.parent.mkdir(parents=True, exist_ok=True)
            self._arquivo.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError:
            return False
        return True
