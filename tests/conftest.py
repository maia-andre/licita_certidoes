"""Portal falso, servido localmente: nenhum teste acessa os portais reais (RNF-06)."""
import http.server
import threading
import urllib.parse

import pytest

FORMULARIO = """<!doctype html><html><body>
{aviso}
<form action="{acao}" method="post">
  <input id="cpfCnpj" name="cpfCnpj" type="text">
  <img id="captcha-imagem" alt="captcha">
  <input id="captcha-resposta" name="resposta" type="text">
  <input id="botao-emitir" type="submit" value="Emitir Certidão">
</form>
<script>{script}</script>
</body></html>"""

# Simula o servidor: espera o programa preencher o CNPJ, registra o estado do
# captcha e só então "digita" o captcha e clica em emitir.
SERVIDOR_HUMANO = """
const t = setInterval(() => {
  const cnpj = document.getElementById('cpfCnpj').value;
  if (!cnpj || document.activeElement.id !== 'captcha-resposta') return;
  clearInterval(t);
  const captcha = document.getElementById('captcha-resposta');
  const q = new URLSearchParams({
    cnpj, captcha: captcha.value, foco: document.activeElement.id,
  });
  fetch('/registro?' + q).then(() => {
    captcha.value = 'digitado-pelo-servidor';
    document.getElementById('botao-emitir').click();
  });
}, 20);
"""

NOVA_TENTATIVA = "document.getElementById('botao-emitir').click();"

PDF = b"%PDF-1.4\n% certidao de teste\n%%EOF\n"


class _Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _html(self, corpo):
        dados = corpo.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(dados)))
        self.end_headers()
        self.wfile.write(dados)

    def _anexo(self, dados, tipo="application/pdf"):
        self.send_response(200)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Disposition", 'attachment; filename="certidao.pdf"')
        self.send_header("Content-Length", str(len(dados)))
        self.end_headers()
        self.wfile.write(dados)

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        if url.path == "/registro":
            self.server.registro = dict(urllib.parse.parse_qsl(url.query, keep_blank_values=True))
            self._html("ok")
        elif url.path == "/ok":
            self._html(FORMULARIO.format(aviso="", acao="/pdf", script=SERVIDOR_HUMANO))
        elif url.path == "/captcha-errado":
            self._html(FORMULARIO.format(aviso="", acao="/erro-captcha", script=SERVIDOR_HUMANO))
        elif url.path == "/nao-pdf":
            self._html(FORMULARIO.format(aviso="", acao="/html", script=SERVIDOR_HUMANO))
        elif url.path == "/parado":
            self._html(FORMULARIO.format(aviso="", acao="/pdf", script=""))
        elif url.path == "/sem-formulario":
            self._html("<html><body>Portal em manutenção</body></html>")
        else:
            self.send_error(404)

    def do_POST(self):
        self.rfile.read(int(self.headers.get("Content-Length", 0)))
        if self.path == "/pdf":
            self._anexo(PDF)
        elif self.path == "/html":
            self._anexo(b"<html>nao sou pdf</html>", "text/html")
        elif self.path == "/erro-captcha":
            # Captcha errado: o portal mostra o formulário de novo e o servidor tenta outra vez.
            self._html(FORMULARIO.format(aviso="<p>Captcha incorreto</p>", acao="/pdf", script=NOVA_TENTATIVA))
        else:
            self.send_error(404)


@pytest.fixture
def portal():
    servidor = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    servidor.registro = None
    thread = threading.Thread(target=servidor.serve_forever, daemon=True)
    thread.start()
    servidor.url = f"http://127.0.0.1:{servidor.server_address[1]}"
    yield servidor
    servidor.shutdown()
    servidor.server_close()


def pdf_com_texto(*linhas: str) -> bytes:
    """PDF mínimo de uma página com as linhas em Helvetica, legível pela pypdf. Só ASCII."""
    def escapar(texto):
        return texto.replace("\\", "\\\\").replace("(", "\(").replace(")", "\)")

    comandos = ["BT", "/F1 11 Tf", "14 TL", "50 780 Td"]
    for linha in linhas:
        comandos.append(f"({escapar(linha)}) Tj T*")
    comandos.append("ET")
    conteudo = "\n".join(comandos).encode("ascii")
    objetos = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
        b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length " + str(len(conteudo)).encode() + b" >>\nstream\n" + conteudo + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    saida = bytearray(b"%PDF-1.4\n")
    posicoes = []
    for numero, objeto in enumerate(objetos, start=1):
        posicoes.append(len(saida))
        saida += f"{numero} 0 obj\n".encode() + objeto + b"\nendobj\n"
    inicio_xref = len(saida)
    saida += f"xref\n0 {len(objetos) + 1}\n0000000000 65535 f \n".encode()
    for posicao in posicoes:
        saida += f"{posicao:010d} 00000 n \n".encode()
    saida += f"trailer\n<< /Size {len(objetos) + 1} /Root 1 0 R >>\nstartxref\n{inicio_xref}\n%%EOF\n".encode()
    return bytes(saida)
