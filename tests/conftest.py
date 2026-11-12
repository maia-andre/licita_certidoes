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

# e-SAJ falso: os campos da pessoa jurídica só aparecem depois do modelo e do tipo de pessoa,
# e o CNPJ tem máscara, como no portal real.
ESAJ_FORMULARIO = """<!doctype html><html><body>
{aviso}
<form action="/esaj-enviar" method="post">
  <select id="cdModelo" name="entity.cdModelo">
    <option value="">---- Selecione ----</option>
    <option value="58">CERT DIST - FALÊNCIAS, CONCORDATAS E RECUPERAÇÕES</option>
    <option value="6">CERT DIST - INVENTÁRIOS, ARROLAMENTOS E TESTAMENTOS</option>
  </select>
  <div id="pessoa" hidden>
    <input type="radio" id="tpPessoaF" name="entity.tpPessoa" value="F">
    <input type="radio" id="tpPessoaJ" name="entity.tpPessoa" value="J">
  </div>
  <div id="juridica" hidden>
    <input id="nmCadastroJ" name="entity.nmPesquisa" type="text">
    <input id="identity.nuCnpjFormatado" name="entity.nuCnpjFormatado" type="text">
  </div>
  <input id="identity.solicitante.deEmail" name="entity.solicitante.deEmail" type="text">
  <input type="checkbox" id="confirmacaoInformacoes" name="confirmacaoInformacoes">
  <input type="submit" id="pbEnviar" value="Enviar" disabled>
</form>
<script>
const $ = (id) => document.getElementById(id);
$('cdModelo').addEventListener('change', () => {{ $('pessoa').hidden = !$('cdModelo').value; }});
$('tpPessoaJ').addEventListener('change', () => {{ $('juridica').hidden = false; }});
$('confirmacaoInformacoes').addEventListener('change', () => {{ $('pbEnviar').disabled = !$('confirmacaoInformacoes').checked; }});
const cnpj = $('identity.nuCnpjFormatado');
cnpj.addEventListener('input', () => {{
  const d = cnpj.value.replace(/\\D/g, '').slice(0, 14);
  cnpj.value = d.replace(/^(\\d{{2}})(\\d{{3}})(\\d{{3}})(\\d{{4}})(\\d{{2}})$/, '$1.$2.$3/$4-$5');
}});
{script}
</script>
</body></html>"""

# Simula o servidor no e-SAJ: espera o programa terminar (foco na confirmação), registra o
# formulário, marca a confirmação e envia.
ESAJ_SERVIDOR = """
const t = setInterval(() => {
  if (document.activeElement.id !== 'confirmacaoInformacoes') return;
  clearInterval(t);
  const modelo = $('cdModelo');
  const q = new URLSearchParams({
    modelo: modelo.options[modelo.selectedIndex].text,
    pessoa: document.querySelector('[name="entity.tpPessoa"]:checked')?.value || '',
    razao: $('nmCadastroJ').value, cnpj: cnpj.value,
    email: $('identity.solicitante.deEmail').value,
    confirmado: String($('confirmacaoInformacoes').checked),
  });
  fetch('/registro?' + q).then(() => {
    $('confirmacaoInformacoes').click();
    $('pbEnviar').click();
  });
}, 20);
"""

# "Visualizar Certidão": número, data (com máscara), pessoa e CNPJ (com máscara). Sem captcha, como o real.
ESAJ_CONSULTA = """<!doctype html><html><body>
<form action="{acao}" method="post">
  <input id="identity.nuPedido" name="entity.nuPedido" type="text">
  <input id="identity.dtPedido" name="entity.dtPedido" type="text">
  <input type="radio" id="tpPessoaF" name="entity.tpPessoa" value="F">
  <input type="radio" id="tpPessoaJ" name="entity.tpPessoa" value="J">
  <input id="identity.nuCnpjFormatado" name="entity.nuCnpjFormatado" type="text">
  <input type="submit" id="pbConsultar" value="Consultar">
</form>
<script>
const data = document.getElementById('identity.dtPedido');
data.addEventListener('input', () => {{
  const d = data.value.replace(/\\D/g, '').slice(0, 8);
  data.value = d.replace(/^(\\d{{2}})(\\d{{2}})(\\d{{4}})$/, '$1/$2/$3');
}});
const cnpj = document.getElementById('identity.nuCnpjFormatado');
cnpj.addEventListener('input', () => {{
  const d = cnpj.value.replace(/\\D/g, '').slice(0, 14);
  cnpj.value = d.replace(/^(\\d{{2}})(\\d{{3}})(\\d{{3}})(\\d{{4}})(\\d{{2}})$/, '$1.$2.$3/$4-$5');
}});
</script>
</body></html>"""

ESAJ_CONSULTA_ESPERADA = {"entity.nuPedido": "101890915", "entity.dtPedido": "12/11/2026",
                          "entity.tpPessoa": "J", "entity.nuCnpjFormatado": "11.222.333/0001-81"}

# Texto essencial da certidão real de 12/11/2026, em ASCII (o leitor normaliza acentos).
ESAJ_CERTIDAO = (
    "PODER JUDICIARIO", "CERTIDAO ESTADUAL DE DISTRIBUICOES CIVEIS", "CERTIDAO N: 6197960 FOLHA: 1/1",
    "CERTIFICA E DA FE que, pesquisando os registros de distribuicoes de PEDIDOS DE",
    "FALENCIA, CONCORDATAS, RECUPERACOES JUDICIAIS E EXTRAJUDICIAIS, anteriores a",
    "10/11/2026, verificou NADA CONSTAR como reu/requerido/interessado em nome de:",
    "EMPRESA FICTICIA LTDA, CNPJ: 11.222.333/0001-81, conforme indicacao constante do pedido",
    "Esta certidao e sem custas.", "Sao Paulo, 12 de novembro de 2026.",
)

# Estrutura da página de resultado real (rótulo, ":" e valor em células separadas).
ESAJ_RESULTADO = """<!doctype html><html><body>
<ul><li>O seu pedido foi cadastrado com sucesso. Para emissão da Certidão, serão encaminhadas instruções
no e-mail informado, ou anote o Número e a Data do seu Pedido, para posterior emissão da Certidão.</li>
<li>Prazo máximo para liberação da Certidão 05 dias.</li></ul>
<table>
<tr><td><label>Número do Pedido</label><div>: </div></td><td>101890915</td></tr>
<tr><td><label>Data do Pedido</label><div>: </div></td><td>12/11/2026</td></tr>
</table>
</body></html>"""


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
        elif url.path == "/esaj":
            self._html(ESAJ_FORMULARIO.format(aviso="", script=ESAJ_SERVIDOR))
        elif url.path == "/esaj-parado":
            self._html(ESAJ_FORMULARIO.format(aviso="", script=""))
        elif url.path == "/esaj-consulta":
            self._html(ESAJ_CONSULTA.format(acao="/esaj-baixar"))
        elif url.path == "/esaj-consulta-pendente":
            self._html(ESAJ_CONSULTA.format(acao="/esaj-pendente"))
        elif url.path == "/sem-formulario":
            self._html("<html><body>Portal em manutenção</body></html>")
        else:
            self.send_error(404)

    def do_POST(self):
        corpo = self.rfile.read(int(self.headers.get("Content-Length", 0))).decode()
        if self.path in ("/esaj-baixar", "/esaj-pendente"):
            self.server.consultas.append(dict(urllib.parse.parse_qsl(corpo, keep_blank_values=True)))
        if self.path == "/esaj-baixar":
            if self.server.consultas[-1] == ESAJ_CONSULTA_ESPERADA:
                self._anexo(pdf_com_texto(*ESAJ_CERTIDAO))
            else:
                self._html("<p>Pedido não encontrado.</p>")
        elif self.path == "/esaj-pendente":
            self._html("<p>A certidão ainda não está disponível.</p>")
        elif self.path == "/pdf":
            self._anexo(PDF)
        elif self.path == "/html":
            self._anexo(b"<html>nao sou pdf</html>", "text/html")
        elif self.path == "/esaj-enviar":
            self._html(ESAJ_RESULTADO)
        elif self.path == "/erro-captcha":
            # Captcha errado: o portal mostra o formulário de novo e o servidor tenta outra vez.
            self._html(FORMULARIO.format(aviso="<p>Captcha incorreto</p>", acao="/pdf", script=NOVA_TENTATIVA))
        else:
            self.send_error(404)


@pytest.fixture
def portal():
    servidor = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    servidor.registro = None
    servidor.consultas = []
    thread = threading.Thread(target=servidor.serve_forever, daemon=True)
    thread.start()
    servidor.url = f"http://127.0.0.1:{servidor.server_address[1]}"
    yield servidor
    servidor.shutdown()
    servidor.server_close()


def pdf_com_texto(*linhas: str) -> bytes:
    """PDF mínimo de uma página com as linhas em Helvetica, legível pela pypdf. Só ASCII."""
    def escapar(texto):
        return texto.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

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
