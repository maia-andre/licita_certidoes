"""Textos modelados nas certidões reais, com empresa e CNPJ fictícios."""
import datetime as dt

import pytest

from certidoes import leitura as lt

CNPJ = "11222333000181"

CND_PCEN = """MINISTÉRIO DA FAZENDA
Secretaria da Receita Federal do Brasil
Procuradoria-Geral da Fazenda Nacional
CERTIDÃO POSITIVA COM EFEITOS DE NEGATIVA DE DÉBITOS RELATIVOS AOS TRIBUTOS
FEDERAIS E À DÍVIDA ATIVA DA UNIÃO

Nome: EMPRESA FICTICIA LTDA
CNPJ: 11.222.333/0001-81
Conforme disposto nos arts. 205 e 206 do CTN, este documento tem os mesmos efeitos da certidão
negativa.
Emitida às 07:49:56 do dia 10/08/2026 <hora e data de Brasília>.
Válida até 06/02/2027.
Código de controle da certidão: 5D5B.EEBD.66AA.BD31
"""

CND_NEGATIVA = CND_PCEN.replace("CERTIDÃO POSITIVA COM EFEITOS DE NEGATIVA DE DÉBITOS",
                                "CERTIDÃO NEGATIVA DE DÉBITOS")
CND_POSITIVA = CND_PCEN.replace("CERTIDÃO POSITIVA COM EFEITOS DE NEGATIVA DE DÉBITOS",
                                "CERTIDÃO POSITIVA DE DÉBITOS")

CNDT_NEGATIVA = """CERTIDÃO NEGATIVA DE DÉBITOS TRABALHISTAS

Nome: EMPRESA FICTICIA LTDA (MATRIZ E FILIAIS)
CNPJ: 11.222.333/0001-81
Certidão nº: 12345678/2026
Expedição: 11/11/2026, às 16:02:50
Validade: 10/05/2027 - 180 (cento e oitenta) dias, contados da data
de sua expedição.
Certifica-se que EMPRESA FICTICIA LTDA, inscrito(a) no CNPJ sob o nº 11.222.333/0001-81,
NÃO CONSTA como inadimplente no Banco Nacional de Devedores Trabalhistas.
"""

CNDT_PCEN = CNDT_NEGATIVA.replace("CERTIDÃO NEGATIVA DE DÉBITOS TRABALHISTAS",
                                  "CERTIDÃO POSITIVA DE DÉBITOS TRABALHISTAS COM EFEITO DE NEGATIVA")
CNDT_POSITIVA = CNDT_NEGATIVA.replace("CERTIDÃO NEGATIVA DE DÉBITOS TRABALHISTAS",
                                      "CERTIDÃO POSITIVA DE DÉBITOS TRABALHISTAS")

CRF = """Certificado de Regularidade
do FGTS - CRF
Inscrição: 11.222.333/0001-81
Razão
social: EMPRESA FICTICIA LTDA
A Caixa Econômica Federal, no uso da atribuição que lhe confere o Art.
7, da Lei 8.036, de 11 de maio de 1990, certifica que, nesta data, a
empresa acima identificada encontra-se em situação regular perante o
Fundo de Garantia do Tempo de Servico - FGTS.
Validade: 09/11/2026 a 08/12/2026
Certificação Número: 2026110909171991092590
Informação obtida em 11/11/2026 15:52:06
"""


@pytest.mark.parametrize("texto, situacao", [
    (CND_NEGATIVA, lt.NEGATIVA),
    (CND_PCEN, lt.POSITIVA_EFEITO_NEGATIVA),
    (CND_POSITIVA, lt.POSITIVA),
])
def test_cnd_situacao_pelo_titulo_e_validade(texto, situacao):
    assert lt.ler(lt.ler_cnd, texto, CNPJ) == lt.Leitura(situacao, dt.date(2027, 2, 6))


def test_cnd_positiva_nao_vira_efeito_de_negativa_por_causa_do_corpo():
    # O corpo diz "mesmos efeitos da certidão negativa"; só o título conta.
    assert lt.ler_cnd(CND_POSITIVA).situacao == lt.POSITIVA


@pytest.mark.parametrize("texto, situacao", [
    (CNDT_NEGATIVA, lt.NEGATIVA),
    (CNDT_PCEN, lt.POSITIVA_EFEITO_NEGATIVA),
    (CNDT_POSITIVA, lt.POSITIVA),
])
def test_cndt_situacao_pelo_titulo_e_validade(texto, situacao):
    assert lt.ler(lt.ler_cndt, texto, CNPJ) == lt.Leitura(situacao, dt.date(2027, 5, 10))


def test_crf_regular_com_a_data_final_da_validade():
    assert lt.ler(lt.ler_crf, CRF, CNPJ) == lt.Leitura(lt.REGULAR, dt.date(2026, 12, 8))


def test_crf_sem_a_frase_de_regularidade_pede_conferencia():
    texto = CRF.replace("encontra-se em situação regular", "encontra-se em situação a verificar")
    assert lt.ler_crf(texto).situacao == lt.CONFERIR


@pytest.mark.parametrize("leitor, texto", [
    (lt.ler_cnd, CNDT_NEGATIVA),  # documento de outro tipo
    (lt.ler_cndt, CND_NEGATIVA),
    (lt.ler_crf, CND_NEGATIVA),
    (lt.ler_cnd, "Texto qualquer sem certidão 11.222.333/0001-81"),
])
def test_documento_de_outro_tipo_pede_conferencia(leitor, texto):
    assert lt.ler(leitor, texto, CNPJ) == lt.Leitura(lt.CONFERIR, None)


def test_cnpj_de_outra_empresa_pede_conferencia():
    outro = CNDT_NEGATIVA.replace("11.222.333/0001-81", "99.999.999/0001-91")
    assert lt.ler(lt.ler_cndt, outro, CNPJ) == lt.Leitura()


def test_filial_da_mesma_empresa_confere_pela_raiz():
    assert lt.ler(lt.ler_cndt, CNDT_NEGATIVA, "11222333000262").situacao == lt.NEGATIVA


def test_texto_vazio_pede_conferencia():
    assert lt.ler(lt.ler_cnd, "", CNPJ) == lt.Leitura()
    assert lt.ler(lt.ler_cnd, "   \n ", CNPJ) == lt.Leitura()


def test_sem_data_de_validade_pede_conferencia_sem_calcular_prazo():
    texto = CND_NEGATIVA.replace("Válida até 06/02/2027.", "")
    assert lt.ler_cnd(texto) == lt.Leitura(lt.NEGATIVA, None)


def test_duas_datas_de_validade_diferentes_pedem_conferencia():
    texto = CND_NEGATIVA + "\nVálida até 07/03/2027.\n"
    assert lt.ler_cnd(texto).validade is None


def test_data_invalida_pede_conferencia():
    texto = CND_NEGATIVA.replace("06/02/2027", "31/02/2027")
    assert lt.ler_cnd(texto).validade is None


def test_normalizar_tira_acentos_e_espacos():
    assert lt.normalizar("Certidão  Negativa\nde  Débitos") == "CERTIDAO NEGATIVA DE DEBITOS"


def test_cnpj_confere_com_cnpj_alfanumerico():
    assert lt.cnpj_confere("CNPJ: 12.ABC.345/01DE-35", "12ABC34501DE35")
    assert not lt.cnpj_confere("CNPJ: 12.ABC.346/01DE-35", "12ABC34501DE35")
