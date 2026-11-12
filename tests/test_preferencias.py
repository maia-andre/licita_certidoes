import json
import pathlib

from certidoes import preferencias as pref


def test_sem_arquivo_nao_ha_email(tmp_path):
    assert pref.Preferencias(tmp_path / "p.json").email() == ""


def test_salva_e_le_o_email(tmp_path):
    arquivo = tmp_path / "pasta" / "p.json"
    assert pref.Preferencias(arquivo).salvar_email("compras@exemplo.gov.br") is True
    assert pref.Preferencias(arquivo).email() == "compras@exemplo.gov.br"
    assert json.loads(arquivo.read_text(encoding="utf-8")) == {"email": "compras@exemplo.gov.br"}


def test_preserva_outras_preferencias(tmp_path):
    arquivo = tmp_path / "p.json"
    arquivo.write_text('{"outra": 1, "email": "velho@x.com"}', encoding="utf-8")
    pref.Preferencias(arquivo).salvar_email("novo@x.com")
    assert json.loads(arquivo.read_text(encoding="utf-8")) == {"outra": 1, "email": "novo@x.com"}


def test_arquivo_corrompido_ou_estranho_e_ignorado(tmp_path):
    arquivo = tmp_path / "p.json"
    for conteudo in ("{quebrado", "[1, 2]", '{"email": 42}'):
        arquivo.write_text(conteudo, encoding="utf-8")
        assert pref.Preferencias(arquivo).email() == ""


def test_falha_ao_gravar_nao_derruba_a_consulta(tmp_path):
    pasta_no_lugar_do_arquivo = tmp_path / "p.json"
    pasta_no_lugar_do_arquivo.mkdir()
    assert pref.Preferencias(pasta_no_lugar_do_arquivo).salvar_email("a@b.com") is False


def test_arquivo_padrao_no_windows_fica_em_appdata(monkeypatch, tmp_path):
    monkeypatch.setattr(pref.sys, "platform", "win32")
    monkeypatch.setenv("APPDATA", str(tmp_path))
    assert pref.arquivo_padrao() == tmp_path / "licita_certidoes" / "preferencias.json"


def test_arquivo_padrao_no_linux_fica_em_config(monkeypatch, tmp_path):
    monkeypatch.setattr(pref.sys, "platform", "linux")
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.setattr(pref.pathlib.Path, "home", lambda: pathlib.Path(tmp_path))
    assert pref.arquivo_padrao() == tmp_path / ".config" / "licita_certidoes" / "preferencias.json"
