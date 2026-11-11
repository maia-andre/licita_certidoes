import pytest

from certidoes.cnpj import CnpjInvalido, normalizar


@pytest.mark.parametrize(
    "entrada, esperado",
    [
        ("11222333000181", "11222333000181"),
        ("11.222.333/0001-81", "11222333000181"),
        ("  11.222.333/0001-81  ", "11222333000181"),
        ("12.ABC.345/01DE-35", "12ABC34501DE35"),
        ("12abc34501de35", "12ABC34501DE35"),
    ],
)
def test_aceita_cnpj_valido(entrada, esperado):
    assert normalizar(entrada) == esperado


@pytest.mark.parametrize(
    "entrada",
    [
        "",
        "   ",
        "1122233300018",  # curto
        "112223330001811",  # longo
        "11222333000182",  # dígito errado
        "11222333000191",  # primeiro dígito errado
        "12ABC34501DE36",  # dígito errado, alfanumérico
        "12ABC34501DEAB",  # dígitos verificadores devem ser numéricos
        "11111111111111",  # dígitos corretos, mas repetidos
        "00000000000000",
        "11222333/0001@81",
        "../../etc/passwd",
        "١١٢٢٢٣٣٣٠٠٠١٨١",  # dígitos não ASCII
    ],
)
def test_recusa_cnpj_invalido(entrada):
    with pytest.raises(CnpjInvalido):
        normalizar(entrada)


@pytest.mark.parametrize("entrada", [None, 11222333000181])
def test_recusa_entrada_que_nao_e_texto(entrada):
    with pytest.raises(CnpjInvalido):
        normalizar(entrada)


def test_formata_cnpj_normalizado():
    from certidoes.cnpj import formatar

    assert formatar("11222333000181") == "11.222.333/0001-81"
    assert formatar("12ABC34501DE35") == "12.ABC.345/01DE-35"
