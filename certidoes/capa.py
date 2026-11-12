"""Capa da consulta em PDF (REQ-20): resumo para instruir o processo, com a hora de cada consulta
e o código de integridade (SHA-256) de cada certidão. Gerada no Chromium do Playwright, já usado pelo programa.

A capa só reúne o que a tela mostrou e não emite juízo de habilitação (RN-06).
"""
import datetime as dt
import hashlib
import html
import pathlib

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

from certidoes import __version__

AVISO = ("Este resumo só reúne informações dos portais. A análise dos documentos e a decisão sobre habilitação ou "
         "pagamento cabem ao servidor (Lei 14.133/2021). Confira cada certidão anexa. Os horários são do computador "
         "em que a consulta foi feita.")
LIMITE_OBSERVACAO = 240


class CapaErro(Exception):
    """Não foi possível gerar a capa. A mensagem vai para a tela."""


def sha256(caminho) -> str:
    resumo = hashlib.sha256()
    with open(caminho, "rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1 << 16), b""):
            resumo.update(bloco)
    return resumo.hexdigest()


def _validade(item) -> str:
    validade = item.get("validade") or ""
    if validade.startswith("Não impressa (emitida em ") and validade.endswith(")"):
        return "Emitida em " + validade[len("Não impressa (emitida em "):-1]
    if validade and item.get("vencida"):
        return validade + " (vencida)"
    return validade or "—"


def _linha(item) -> str:
    e = html.escape
    situacao = (item.get("situacao") or "Conferir no PDF") if item["estado"] == "Obtida" else item["estado"]
    observacao = (item.get("mensagem") or "").strip()
    if len(observacao) > LIMITE_OBSERVACAO:
        observacao = observacao[:LIMITE_OBSERVACAO].rsplit(" ", 1)[0] + "…"
    arquivo = pathlib.Path(item["arquivo"]).name if item.get("arquivo") else "—"
    return (f"<tr><td><b>{e(item['nome'])}</b><br><span class=s>{e(item['portal'])}</span></td>"
            f"<td>{e(situacao)}" + (f"<br><span class=s>{e(observacao)}</span>" if observacao else "") + "</td>"
            f"<td>{e(_validade(item))}</td><td>{e(item.get('hora') or '—')}</td><td class=s>{e(arquivo)}</td></tr>")


def montar_html(empresa, identificado_em, itens, inicio, gerado_em, codigos) -> str:
    """HTML da capa. `empresa` é o dicionário da tela; `codigos` é [(nome do arquivo, SHA-256)]."""
    e = html.escape
    horas = [dt.datetime.strptime(i["hora"], "%d/%m/%Y %H:%M:%S") for i in itens if i.get("hora")]
    fim = max(horas) if horas else None
    periodo = f"de {inicio:%d/%m/%Y %H:%M}" + (f" a {fim:%d/%m/%Y %H:%M}" if fim else "")
    tipo = "matriz" if empresa["matriz"] else "filial"
    anexo = "".join(f"<tr><td>{e(nome)}</td><td class=hash>{e(codigo)}</td></tr>" for nome, codigo in codigos)
    return f"""<!doctype html><html lang="pt-BR"><meta charset="utf-8"><style>
body {{ font: 10.5pt/1.4 "Segoe UI", system-ui, sans-serif; color: #1b1f24; margin: 0; }}
h1 {{ font-size: 15pt; margin: 0; }} h2 {{ font-size: 12pt; margin: 0 0 8px; }}
.sub {{ color: #5b6470; margin: 2px 0 14px; }}
.caixa {{ border: 1px solid #c9ced5; border-radius: 6px; padding: 10px 12px; margin-bottom: 12px; }}
dl {{ display: grid; grid-template-columns: max-content 1fr; gap: 3px 14px; margin: 0; }}
dt {{ color: #5b6470; }} dd {{ margin: 0; font-weight: 600; }}
table {{ width: 100%; border-collapse: collapse; }}
th {{ text-align: left; font-size: 8.5pt; text-transform: uppercase; color: #5b6470; border-bottom: 1.5px solid #1b1f24; padding: 4px 6px; }}
td {{ padding: 6px; border-bottom: 1px solid #dfe3e8; vertical-align: top; }} tr {{ page-break-inside: avoid; }}
.s {{ font-size: 8.5pt; color: #5b6470; }} .hash {{ font: 8pt Consolas, monospace; overflow-wrap: anywhere; }}
.aviso {{ margin-top: 12px; font-size: 9pt; border-left: 3px solid #4a525c; padding: 6px 10px; background: #f4f5f7; }}
.assinaturas {{ margin-top: 28px; display: grid; grid-template-columns: 1.6fr 1fr 1fr; gap: 18px; font-size: 9pt; color: #5b6470; }}
.assinaturas div {{ border-top: 1px solid #1b1f24; padding-top: 4px; }}
.rodape {{ margin-top: 14px; font-size: 8pt; color: #5b6470; }}
.anexo {{ page-break-before: always; }}
</style>
<h1>Certidões do Fornecedor — resumo da consulta</h1>
<p class="sub">Documento gerado pelo programa Certidões do Fornecedor para instruir o processo. Não substitui as certidões, que seguem anexas.</p>
<div class="caixa"><dl>
<dt>Razão social</dt><dd>{e(empresa["razao_social"])}</dd>
<dt>CNPJ consultado</dt><dd>{e(empresa["cnpj_formatado"])} ({tipo}) · UF {e(empresa["uf"])}</dd>
<dt>Situação cadastral</dt><dd>{e(empresa["situacao_cadastral"])} (BrasilAPI, consultada em {identificado_em:%d/%m/%Y %H:%M})</dd>
<dt>Consulta</dt><dd>{periodo}</dd>
</dl></div>
<table><thead><tr><th>Certidão</th><th>Situação</th><th>Validade</th><th>Consultada em</th><th>Arquivo</th></tr></thead>
<tbody>{"".join(_linha(i) for i in itens)}</tbody></table>
<p class="aviso">{e(AVISO)}</p>
<div class="assinaturas"><div>Responsável pela conferência</div><div>Matrícula</div><div>Data</div></div>
<p class="rodape">Gerado em {gerado_em:%d/%m/%Y %H:%M:%S} por Certidões do Fornecedor {e(__version__)}.
Código de integridade (SHA-256) de cada certidão no anexo.</p>
<section class="anexo"><h2>Anexo — código de integridade das certidões (SHA-256)</h2>
<p class="sub">Cada código identifica um arquivo PDF exatamente como o programa o guardou. Para conferir no Windows:
<code>certutil -hashfile "arquivo.pdf" SHA256</code></p>
<table><thead><tr><th>Arquivo</th><th>SHA-256</th></tr></thead><tbody>{anexo or "<tr><td colspan=2>Nenhuma certidão obtida.</td></tr>"}</tbody></table>
</section>
</html>"""


def renderizar_pdf(conteudo_html: str, destino: pathlib.Path) -> None:
    """Imprime o HTML em PDF A4 no Chromium do Playwright, sem janela."""
    try:
        with sync_playwright() as p:
            navegador = p.chromium.launch(headless=True)
            try:
                pagina = navegador.new_page()
                pagina.set_content(conteudo_html, wait_until="load")
                pagina.pdf(path=str(destino), format="A4", print_background=True,
                           margin={"top": "18mm", "bottom": "18mm", "left": "16mm", "right": "16mm"})
            finally:
                navegador.close()
    except PlaywrightError as erro:
        raise CapaErro("Não foi possível gerar a capa: o Chromium do Playwright não abriu.") from erro


def gerar_capa(empresa, identificado_em, itens, inicio, pasta, agora=None, renderizar=renderizar_pdf) -> pathlib.Path:
    """Gera capa-<data-hora>.pdf na pasta da consulta e devolve o caminho."""
    agora = agora or dt.datetime.now()
    pasta = pathlib.Path(pasta)
    codigos = []
    for item in itens:
        if item.get("arquivo"):
            try:
                codigos.append((pathlib.Path(item["arquivo"]).name, sha256(item["arquivo"])))
            except OSError as erro:
                raise CapaErro(f"Não foi possível ler {pathlib.Path(item['arquivo']).name} para a capa.") from erro
    try:
        pasta.mkdir(parents=True, exist_ok=True)
    except OSError as erro:
        raise CapaErro(f"Não foi possível criar a pasta {pasta}.") from erro
    destino = pasta / f"capa-{agora:%Y%m%d-%H%M%S}.pdf"
    renderizar(montar_html(empresa, identificado_em, itens, inicio, agora, codigos), destino)
    return destino
