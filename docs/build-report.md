# Build report — 2026-11-06
Spec: docs/spec.md, versão 1
Incremento: INC-01 — CNDT de ponta a ponta
Rodada: construção
Testes: 36 passando / 36 total — `.venv/bin/python -m pytest -q` (inclui Chromium headless contra portal falso local)

## Requisitos atendidos
- **REQ-01** — Atendido — `certidoes/cnpj.py`, `certidoes/app.py`; `tests/test_cnpj.py`, `tests/test_app.py::test_cnpj_invalido_mostra_erro_sem_consulta_externa`. Aceita CNPJ numérico e alfanumérico.
- **REQ-06** — Atendido — implementado em `certidoes/portais/tst.py` e coberto por `tests/test_tst.py` contra portal falso. Emissão real feita em 2026-11-06, com captcha resolvido pelo servidor.
- **REQ-08** — Parcial — guarda o PDF em `~/Certidoes/<CNPJ>/` e a tela o abre (`certidoes/app.py`); coberto por `tests/test_tst.py` e `tests/test_app.py`. O PDF real do TST foi salvo em 2026-11-06. Falta confirmar o botão "Abrir PDF" com esse arquivo.
- **RNF-01** — Atendido nesta etapa — Python, pywebview e Playwright com Chromium em Linux; `requirements.txt`. O venv usa `--system-site-packages` para acessar o GTK/WebKit do sistema.
- **RNF-02** — Atendido — tela em `certidoes/ui/index.html`, sem comandos durante a consulta; `tests/test_app.py::test_tela_tem_campo_botoes_e_nao_usa_innerhtml`. O programa ainda é iniciado por comando, pois o executável está fora de escopo.
- **RNF-06** — Atendido — `tests/conftest.py` serve um portal falso local.
- **RN-05** — Atendido — o programa não preenche o captcha; `tests/test_tst.py::test_preenche_cnpj_e_deixa_o_captcha_para_o_servidor`.

## Casos extremos cobertos
- **CE-01** — `tests/test_cnpj.py::test_recusa_cnpj_invalido`, `tests/test_app.py::test_cnpj_invalido_mostra_erro_sem_consulta_externa`

## Perguntas em aberto / pendências
- Fechamento da janela é testado com mock, porque não dá para provocá-lo por script no portal falso; o tipo de erro foi confirmado em Chromium real.
- Não confirmado no portal real: se o TST aceita CNPJ alfanumérico.
