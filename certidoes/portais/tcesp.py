"""Certidão de Apenados do TCE-SP (modo "navegador do servidor", RN-09).

O captcha do portal (Cloudflare Turnstile) recusa navegador automatizado: no Chromium do Playwright,
falhou com o erro 600010 nas duas tentativas assistidas de 12/11/2026 (CE-15). Por isso o servidor
gera a certidão no próprio navegador e o programa recolhe o PDF da pasta Downloads.

O portal salva o arquivo como "Certidão Apenados.pdf" (com sufixo, se já existir); o PDF é
reconhecido pelo texto e pelo CNPJ, para não depender do nome.
"""
from certidoes.leitura import normalizar
from certidoes.pdf import contem_cnpj, texto_do_pdf
from certidoes.portais.navegador_servidor import obter_pelo_navegador

URL = "https://www4.tce.sp.gov.br/apenados/publico/#/publicas/certificado/add"
INSTRUCAO = (
    'No seu navegador, cole o CNPJ {cnpj} (Ctrl+V) no campo CNPJ, clique em "Gerar", conclua a verificação '
    'e clique em "OK". Na certidão, clique no ícone de PDF e salve na pasta Downloads.'
)


def e_certidao_do_cnpj(dados: bytes, cnpj: str) -> bool:
    texto = texto_do_pdf(dados)
    return "CERTIDAO DE APENADOS" in normalizar(texto) and contem_cnpj(texto, cnpj)


def obter_certidao(cnpj, ao_aguardar=None, sinal=None, **opcoes):
    return obter_pelo_navegador(
        cnpj,
        url=URL,
        padrao="*.pdf",
        prefixo="apenados-tcesp",
        nome_portal="do TCE-SP",
        ao_aguardar=ao_aguardar,
        sinal=sinal,
        aceitar=lambda dados: e_certidao_do_cnpj(dados, cnpj),
        **opcoes,
    )
