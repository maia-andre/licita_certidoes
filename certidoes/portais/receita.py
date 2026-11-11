"""CND federal na Receita (modo "navegador do servidor", RN-09).

A Receita recusa o hCaptcha resolvido em navegador automatizado (CaptchaFalhaValidacao, 023),
por isso o servidor emite no próprio navegador e o programa recolhe o PDF da pasta Downloads.
"""
from certidoes.portais.navegador_servidor import obter_pelo_navegador

URL = "https://servicos.receitafederal.gov.br/servico/certidoes/#/home/cnpj"
INSTRUCAO = (
    'No seu navegador, cole o CNPJ {cnpj} (Ctrl+V) no campo, clique em "Emitir Certidão", '
    "resolva o captcha e baixe o PDF. O programa continua sozinho quando o PDF chegar a Downloads."
)


def obter_cnd(cnpj, ao_aguardar=None, nao_emitida=None, **opcoes):
    """O portal salva o PDF como Certidao-<CNPJ>.pdf (ou com sufixo, se já existir)."""
    return obter_pelo_navegador(
        cnpj,
        url=URL,
        padrao=f"Certidao-{cnpj}*.pdf",
        prefixo="cnd",
        nome_portal="Receita Federal",
        ao_aguardar=ao_aguardar,
        nao_emitida=nao_emitida,
        **opcoes,
    )
