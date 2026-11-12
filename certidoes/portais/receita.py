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


AVISO_MATRIZ = ("Pedida com o CNPJ da matriz, {matriz}: a Receita só emite a CND federal para a matriz, "
                "e ela vale para todos os estabelecimentos.")


def obter_cnd(cnpj, ao_aguardar=None, sinal=None, matriz=None, **opcoes):
    """O portal salva o PDF como Certidao-<CNPJ>.pdf (ou com sufixo, se já existir).

    Para filial, `matriz` traz o CNPJ da matriz: a Receita recusa a filial ("a certidão deve ser emitida para o
    CNPJ da matriz", visto em duas filiais em 12/11/2026). O PDF fica na pasta do CNPJ consultado.
    """
    cnpj_portal = matriz or cnpj
    return obter_pelo_navegador(
        cnpj,
        url=URL,
        padrao=f"Certidao-{cnpj_portal}*.pdf",
        cnpj_portal=cnpj_portal,
        prefixo="cnd",
        nome_portal="da Receita Federal",
        ao_aguardar=ao_aguardar,
        sinal=sinal,
        **opcoes,
    )
