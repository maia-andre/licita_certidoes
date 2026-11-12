"""Modo "navegador do servidor" (RN-09).

Para portais que recusam navegador automatizado: o programa abre o portal no navegador
padrão do servidor, deixa o CNPJ na área de transferência e espera o PDF chegar à pasta
Downloads. Nada é preenchido nem automatizado dentro do portal.
"""
import datetime as dt
import fnmatch
import pathlib
import subprocess
import sys
import time
import uuid
import webbrowser

from certidoes.portais.comum import PASTA_PADRAO, PortalErro, guardar_pdf

TEMPO_LIMITE_S = 5 * 60
INTERVALO_S = 1.0
# Margem para a resolução do relógio do sistema de arquivos.
FOLGA_S = 2.0
_FOLDERID_DOWNLOADS = uuid.UUID("374DE290-123F-4565-9164-39C4925E467B")


def _downloads_windows() -> pathlib.Path:
    import ctypes

    guid = ctypes.create_string_buffer(_FOLDERID_DOWNLOADS.bytes_le, 16)
    caminho = ctypes.c_wchar_p()
    if ctypes.windll.shell32.SHGetKnownFolderPath(guid, 0, None, ctypes.byref(caminho)) != 0:
        raise OSError("SHGetKnownFolderPath falhou")
    try:
        return pathlib.Path(caminho.value)
    finally:
        ctypes.windll.ole32.CoTaskMemFree(caminho)


def pasta_downloads() -> pathlib.Path:
    """Pasta Downloads do usuário, inclusive quando redirecionada no Windows."""
    try:
        if sys.platform == "win32":
            return _downloads_windows()
        saida = subprocess.run(["xdg-user-dir", "DOWNLOAD"], capture_output=True, text=True, timeout=5)
        if saida.returncode == 0 and saida.stdout.strip():
            return pathlib.Path(saida.stdout.strip())
    except (OSError, subprocess.SubprocessError):
        pass
    return pathlib.Path.home() / "Downloads"


def copiar_para_area_de_transferencia(texto: str) -> bool:
    """Tenta copiar o texto. Devolve False se não conseguir; a tela mostra o CNPJ de qualquer forma."""
    if sys.platform == "win32":
        comandos = [["clip"]]
    else:
        comandos = [["wl-copy"], ["xclip", "-selection", "clipboard"]]
    for comando in comandos:
        try:
            extra = {"creationflags": subprocess.CREATE_NO_WINDOW} if sys.platform == "win32" else {}
            subprocess.run(comando, input=texto.encode("ascii"), check=True, timeout=5, **extra)
            return True
        except (OSError, subprocess.SubprocessError):
            continue
    return False


def _candidatos(pasta: pathlib.Path, padrao: str, desde: float):
    padrao = padrao.lower()
    for arquivo in pasta.iterdir():
        try:
            if (
                fnmatch.fnmatchcase(arquivo.name.lower(), padrao)
                and arquivo.is_file()
                and arquivo.stat().st_mtime >= desde - FOLGA_S
            ):
                yield arquivo
        except OSError:
            continue


def aguardar_arquivo(pasta, padrao, desde, tempo_limite_s=TEMPO_LIMITE_S, intervalo_s=INTERVALO_S,
                     relogio=time.monotonic, dormir=time.sleep, aceitar=None, sinal=None) -> pathlib.Path:
    """Espera um arquivo novo cujo nome case com `padrao` e cujo tamanho pare de mudar.

    `desde` é o instante (time.time) a partir do qual o arquivo conta como novo.
    `aceitar(dados)`, se informado, confere o conteúdo; arquivos recusados são ignorados.
    `sinal` (SinalServidor): se o servidor pular ou informar que o portal não emitiu, a espera termina.
    """
    fim = relogio() + tempo_limite_s
    tamanhos = {}
    recusados = set()
    while True:
        if sinal is not None:
            sinal.verificar()
        for arquivo in _candidatos(pathlib.Path(pasta), padrao, desde):
            try:
                tamanho = arquivo.stat().st_size
            except OSError:
                continue
            if (arquivo, tamanho) in recusados:
                continue
            if tamanho > 0 and tamanhos.get(arquivo) == tamanho:
                if aceitar is None:
                    return arquivo
                try:
                    if aceitar(arquivo.read_bytes()):
                        return arquivo
                except OSError:
                    continue
                recusados.add((arquivo, tamanho))
            tamanhos[arquivo] = tamanho
        if relogio() >= fim:
            raise PortalErro(
                f"Tempo esgotado: o PDF não chegou à pasta {pasta}. "
                "Confira se o navegador salva os downloads nessa pasta."
            )
        dormir(intervalo_s)


def obter_pelo_navegador(
    cnpj,
    *,
    url,
    padrao,
    prefixo,
    nome_portal,  # com artigo: "da Receita Federal", "do TCE-SP"
    ao_aguardar=None,
    sinal=None,
    aceitar=None,
    pasta_base=PASTA_PADRAO,
    pasta=None,
    abrir_url=webbrowser.open,
    copiar=copiar_para_area_de_transferencia,
    tempo_limite_s=TEMPO_LIMITE_S,
    intervalo_s=INTERVALO_S,
    agora=None,
) -> pathlib.Path:
    """Abre `url` no navegador do servidor e move o PDF baixado para a pasta do CNPJ."""
    pasta = pathlib.Path(pasta) if pasta else pasta_downloads()
    if not pasta.is_dir():
        raise PortalErro(f"Pasta Downloads não encontrada: {pasta}")
    desde = time.time()
    copiar(cnpj)
    if not abrir_url(url):
        raise PortalErro(f"Não foi possível abrir o portal {nome_portal} no navegador.")
    if ao_aguardar:
        ao_aguardar()
    arquivo = aguardar_arquivo(pasta, padrao, desde, tempo_limite_s, intervalo_s,
                               aceitar=aceitar, sinal=sinal)
    destino = guardar_pdf(arquivo.read_bytes(), cnpj, pasta_base, prefixo, agora or dt.datetime.now())
    try:
        arquivo.unlink()
    except OSError:
        pass  # a cópia já está guardada; o original fica em Downloads
    return destino
