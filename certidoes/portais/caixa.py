"""CRF FGTS na Caixa (modo "navegador do servidor", RN-09).

A Caixa bloqueia navegador automatizado (Radware/ShieldSquare) já no primeiro acesso. Não fazer
acessos automatizados a este portal: a página de bloqueio registra o IP da rede.

O CRF é uma página; o servidor o salva como PDF pela opção "Imprimir", com nome livre.
Por isso o PDF é reconhecido pelo texto, e não pelo nome.
"""
from certidoes.pdf import contem_cnpj, texto_do_pdf
from certidoes.portais.navegador_servidor import obter_pelo_navegador

URL = "https://consulta-crf.caixa.gov.br/consultacrf/pages/consultaEmpregador.jsf"
TITULO = "Certificado de Regularidade do FGTS"
INSTRUCAO = (
    "No seu navegador, cole o CNPJ {cnpj} (Ctrl+V), faça a consulta e abra o certificado pelo link. "
    'Na página do CRF, clique em "Imprimir" e escolha "Salvar como PDF" na pasta Downloads.'
)


def e_crf_do_cnpj(dados: bytes, cnpj: str) -> bool:
    texto = texto_do_pdf(dados)
    return TITULO.lower() in " ".join(texto.lower().split()) and contem_cnpj(texto, cnpj)


def obter_crf(cnpj, ao_aguardar=None, sinal=None, **opcoes):
    return obter_pelo_navegador(
        cnpj,
        url=URL,
        padrao="*.pdf",
        prefixo="crf",
        nome_portal="da Caixa",
        ao_aguardar=ao_aguardar,
        sinal=sinal,
        aceitar=lambda dados: e_crf_do_cnpj(dados, cnpj),
        **opcoes,
    )
