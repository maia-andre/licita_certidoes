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


# Texto extraído da certidão real de falências do e-SAJ (12/11/2026), com os espaços do PDF.
FALENCIA_REAL = """ 12/11/2026  0101890915
 P O D E R  J U D I C I Á R I O
 TRIBUNAL DE JUSTIÇA DO ESTADO DE SÃO PAULO
 CERTIDÃO ESTADUAL DE DISTRIBUIÇÕES CÍVEIS
 CERTIDÃO Nº:   6197960  FOLHA: 1/1
 CERTIFICA   E   DÁ   FÉ   que,   pesquisando   os   registros    de   distribuições   de     PEDIDOS   DE
 FALÊNCIA,   CONCORDATAS,   RECUPERAÇÕES   JUDICIAIS   E   EXTRAJUDICIAIS  ,   anteriores   a
 10/11/2026,  verificou   NADA CONSTAR   como réu/requerido/interessado em nome de: *****
 VIACAO   SAENS   PENA   LTDA  ,   CNPJ:   17.051.740/0001-50,   conforme   indicação   constante   do   pedido
 Esta certidão é sem custas.
 São Paulo, 12 de novembro de 2026.
"""


def test_falencia_real_nada_consta_sem_validade_impressa():
    lido = lt.ler(lt.ler_falencia, FALENCIA_REAL, "17051740000150")
    assert lido == lt.Leitura("Nada consta", None, dt.date(2026, 11, 12))


def test_falencia_de_outro_cnpj_pede_conferencia():
    assert lt.ler(lt.ler_falencia, FALENCIA_REAL, "11222333000181") == lt.Leitura()


def test_falencia_sem_nada_constar_pede_conferencia():
    # Certidão com apontamentos: o programa não presume a situação.
    texto = FALENCIA_REAL.replace("verificou   NADA CONSTAR", "verificou CONSTAR o(s) seguinte(s) processo(s)")
    assert lt.ler_falencia(texto).situacao == "Conferir no PDF"


def test_outro_modelo_do_esaj_nao_e_lido_como_falencia():
    texto = FALENCIA_REAL.replace("PEDIDOS   DE\n FALÊNCIA", "INVENTÁRIOS")
    assert lt.ler_falencia(texto) == lt.Leitura()


def test_falencia_com_duas_datas_por_extenso_fica_sem_emissao():
    texto = FALENCIA_REAL + " Brasília, 13 de novembro de 2026."
    assert lt.ler_falencia(texto).emissao is None


# Texto da Consulta Consolidada real de 12/11/2026, como a pypdf o extrai, com empresa e CNPJ fictícios.
TCU_REAL = """Consulta Consolidada de Pessoa Jurídica
Este relatório tem por objetivo apresentar os resultados consolidados de consultas eletrônicas realizadas
diretamente nos bancos de dados dos respectivos cadastros. A responsabilidade pela veracidade do resultado
da consulta é do Órgão gestor de cada cadastro consultado. A informação relativa à razão social da Pessoa
Jurídica é extraída do Cadastro Nacional da Pessoa Jurídica, mantido pela Receita Federal do Brasil.
12/11/2026 11:28:12Consulta realizada em:
Informações da Pessoa Jurídica:
Razão Social: EMPRESA FICTICIA LTDA
CNPJ: 11.222.333/0001-81
Resultados da Consulta Eletrônica:
Órgão Gestor: TCU
Cadastro: Licitantes Inidôneos
Resultado da consulta: Nada Consta
Para acessar a certidão original no portal do órgão gestor, clique .AQUI
Órgão Gestor: CNJ
Cadastro: CNIA - Cadastro Nacional de Condenações Cíveis por Ato de Improbidade Administrativa
e Inelegibilidade
Resultado da consulta: Sistema do CNJ está indisponível
Para acessar a certidão original no portal do órgão gestor, clique .AQUI
Órgão Gestor: Portal da Transparência
Cadastro: Cadastro Nacional de Empresas Inidôneas e Suspensas
Resultado da consulta: Nada Consta
Para acessar a certidão original no portal do órgão gestor, clique .AQUI
Órgão Gestor: Portal da Transparência
Cadastro: CNEP - Cadastro Nacional de Empresas Punidas
Resultado da consulta: Nada Consta
Para acessar a certidão original no portal do órgão gestor, clique .AQUI
Obs: A consulta consolidada de pessoa jurídica visa atender aos princípios de simplificação e racionalização
de serviços públicos digitais. Fundamento legal: Lei nº 12.965, de 23 de abril de 2014, Lei nº 13.460, de 26
de junho de 2017, Lei nº 13.726, de 8 de outubro de 2018, Decreto nº 8.638 de 15, de janeiro de 2016.
"""
TCU_NADA_CONSTA = TCU_REAL.replace("Sistema do CNJ está indisponível", "Nada Consta")


def test_sancoes_real_com_cnj_indisponivel_decidem_por_tcu_ceis_e_cnep():
    # O CNJ tem item próprio; aqui ele só aparece na mensagem, apontando para esse item.
    lido = lt.ler(lt.ler_sancoes_tcu, TCU_REAL, CNPJ)
    assert (lido.situacao, lido.validade, lido.emissao) == (lt.NADA_CONSTA, None, dt.date(2026, 11, 12))
    assert lido.detalhe == (
        "TCU (Licitantes Inidôneos): Nada consta. "
        "CNJ (CNIA, improbidade): Sistema do CNJ está indisponível (confira o item de improbidade do CNJ). "
        "CEIS: Nada consta. CNEP: Nada consta.")


def test_sancoes_nada_consta_nos_quatro_cadastros():
    lido = lt.ler(lt.ler_sancoes_tcu, TCU_NADA_CONSTA, CNPJ)
    assert (lido.situacao, lido.emissao) == (lt.NADA_CONSTA, dt.date(2026, 11, 12))
    assert lido.detalhe == ("TCU (Licitantes Inidôneos): Nada consta. "
                            "CNJ (CNIA, improbidade): Nada consta (confira o item de improbidade do CNJ). "
                            "CEIS: Nada consta. CNEP: Nada consta.")


def test_sancoes_com_cadastro_desconhecido_pedem_conferencia():
    novo = "Órgão Gestor: Outro\nCadastro: Cadastro Novo\nResultado da consulta: Nada Consta\nObs:"
    texto = TCU_NADA_CONSTA.replace("Obs:", novo)
    assert lt.ler_sancoes_tcu(texto).situacao == lt.CONFERIR


def test_sancoes_com_registro_pede_conferencia_com_o_link_do_cadastro():
    texto = TCU_NADA_CONSTA.replace(
        "Empresas Punidas\nResultado da consulta: Nada Consta", "Empresas Punidas\nResultado da consulta: Consta")
    lido = lt.ler_sancoes_tcu(texto)
    assert lido.situacao == lt.CONFERIR
    assert "CNEP: Consta (consulta manual: https://portaldatransparencia.gov.br/sancoes/cnep)." in lido.detalhe


def test_sancoes_sem_um_dos_cadastros_pede_conferencia():
    sem_cnep = TCU_NADA_CONSTA.split("Órgão Gestor: Portal da Transparência\nCadastro: CNEP")[0]
    lido = lt.ler_sancoes_tcu(sem_cnep)
    assert lido.situacao == lt.CONFERIR
    assert "CNEP" not in lido.detalhe


def test_sancoes_de_outro_cnpj_ou_outro_documento_nao_sao_lidas():
    assert lt.ler(lt.ler_sancoes_tcu, TCU_NADA_CONSTA, "99888777000166") == lt.Leitura()
    assert lt.ler_sancoes_tcu(CNDT_NEGATIVA) == lt.Leitura()


# Certidão de Apenados do TCE-SP: texto real de 12/11/2026 (pypdf), com CNPJ fictício.
TCESP_REAL = """CERTIDÃO DE APENADOS
O Tribunal de Contas do Estado de São Paulo CERTIFICA que, de acordo com seus assentamentos, ressalvando-se os atos que sobrevenham a
esta  pesquisa,  NÃO  constam,  até  a  presente  data,  12/11/2026,  às  13h58,  IMPEDIMENTOS  DE  LICITAÇÃO/CONTRATO/CHAMAMENTO
PÚBLICO/CELEBRAÇÃO DE PARCERIA relacionados ao CNPJ 11.222.333/0001-81  informado.

Este documento foi certificado digitalmente e é válido até 12/11/2026, às 13h58.
Para conferência:
acesse o site https://www4.tce.sp.gov.br/apenados/publico
e informe o código: 9b41dab9-bf90-4ff6-9738-24b5dc2a863c
ou acesse utilizando o QR Code

Av. Rangel Pestana, 315 - Centro - SP - CEP 01017-906
 Telefone: (11) 3292-3266             www.tce.sp.gov.br
Página: 1 de 1
"""


def test_apenados_tcesp_real_nada_consta_com_validade_impressa():
    lido = lt.ler(lt.ler_apenados_tcesp, TCESP_REAL, CNPJ)
    assert lido == lt.Leitura(lt.NADA_CONSTA, dt.date(2026, 11, 12))


def test_apenados_tcesp_com_impedimentos_pede_conferencia():
    texto = TCESP_REAL.replace(
        "NÃO  constam,  até  a  presente  data,  12/11/2026,  às  13h58,  IMPEDIMENTOS",
        "CONSTA(M),  até  a  presente  data,  12/11/2026,  às  13h58,  o(s) IMPEDIMENTO(S)")
    lido = lt.ler_apenados_tcesp(texto)
    assert (lido.situacao, lido.validade) == (lt.CONFERIR, dt.date(2026, 11, 12))
    assert "impedimento" in lido.detalhe


def test_apenados_tcesp_com_texto_desconhecido_pede_conferencia():
    texto = TCESP_REAL.replace("NÃO  constam", "constam")
    assert lt.ler_apenados_tcesp(texto).situacao == lt.CONFERIR


def test_apenados_tcesp_de_outro_cnpj_ou_outro_documento_nao_sao_lidos():
    assert lt.ler(lt.ler_apenados_tcesp, TCESP_REAL, "99888777000166") == lt.Leitura()
    assert lt.ler_apenados_tcesp(CNDT_NEGATIVA) == lt.Leitura()


# Certidão do CNIA (CNJ): texto real de 12/11/2026 (pypdf), com CNPJ fictício.
CNJ_REAL = """Certidão Negativa
Certifico que nesta data (12/11/2026 às 17:24) NÃO CONSTA no Cadastro Nacional de Condenações Cíveis por Ato de
Improbidade Administrativa e Inelegibilidade registros de condenação com trânsito em julgado ou sanção ativa
quanto ao CNPJ nº 11.222.333/0001-81.
A condenação por atos de improbidade administrativa não implica automático e necessário reconhecimento da
inelegibilidade do condenado. Para consultas sobre inelegibilidade acesse portal do TSE em http://divulgacandcontas.tse.jus.br/
Esta certidão é expedida gratuitamente.
Sua autenticidade pode ser por meio do número de controle ZPRN.NZEI.9MH9.D776 no seguinte endereço:
https://www.cnj.jus.br/improbidade_adm/autenticar
"""


def test_improbidade_cnj_real_nada_consta_com_data_de_emissao():
    lido = lt.ler(lt.ler_improbidade_cnj, CNJ_REAL, CNPJ)
    assert lido == lt.Leitura(lt.NADA_CONSTA, None, dt.date(2026, 11, 12))


def test_improbidade_cnj_sem_certidao_negativa_pede_conferencia():
    texto = CNJ_REAL.replace("Certidão Negativa", "Certidão").replace("NÃO CONSTA no", "CONSTA no")
    lido = lt.ler_improbidade_cnj(texto)
    assert (lido.situacao, lido.emissao) == (lt.CONFERIR, dt.date(2026, 11, 12))
    assert "registros" in lido.detalhe


def test_improbidade_cnj_de_outro_cnpj_ou_outro_documento_nao_e_lida():
    assert lt.ler(lt.ler_improbidade_cnj, CNJ_REAL, "99888777000166") == lt.Leitura()
    assert lt.ler_improbidade_cnj(CNDT_NEGATIVA) == lt.Leitura()
