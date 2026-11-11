# Build report — 2026-11-11
Spec: docs/spec.md, versão 1.3
Incremento: INC-05 — Identificação da empresa pela BrasilAPI
Rodada: construção
Testes: 137 passando / 137 total — `.venv\Scripts\python -m pytest -q` (Windows 11, Python 3.14.6)

## Requisitos atendidos
- **REQ-02** — Atendido — `certidoes/empresa.py` (`consultar`, `Empresa`) consulta `https://brasilapi.com.br/api/cnpj/v1/{cnpj}` com User-Agent genérico (`licita_certidoes`) e lê razão social, UF, situação cadastral e matriz/filial (`identificador_matriz_filial`). `Api.identificar` (`certidoes/app.py`) e cartão `#empresa` na tela. `tests/test_empresa.py`, `tests/test_app.py::test_identificar_mostra_os_dados_da_matriz`.
- **REQ-03** — Atendido — para filial, `Api.identificar` consulta também a matriz (`cnpj_da_matriz` em `certidoes/cnpj.py`) e a tela oferece "Consultar a filial" e "Consultar a matriz". `tests/test_app.py::test_filial_mostra_a_matriz_e_permite_escolher`, `tests/test_cnpj.py::test_cnpj_da_matriz`.
- **REQ-04** — Atendido — `Api.emitir` só aceita CNPJ identificado e de SP; fora de SP, nenhum portal é aberto e a tela não mostra botão de emissão. `tests/test_app.py::test_empresa_fora_de_sp_nao_abre_nenhum_portal`, `::test_emitir_sem_identificar_e_recusado`.
- **RN-07** — Atendido — ao escolher a filial, a tela mostra o aviso de que a certidão de falência segue o distribuidor da sede (art. 69, II). `tests/test_app.py::test_escolher_a_filial_mostra_o_aviso_da_falencia_pela_sede`.

## Casos extremos cobertos
- **CE-02** — BrasilAPI fora do ar, erro HTTP, CNPJ inexistente (404) ou resposta inválida: mensagem clara, nenhum portal liberado, nova tentativa possível. `tests/test_empresa.py::test_falhas_da_brasilapi_geram_erro_claro`, `tests/test_app.py::test_brasilapi_fora_do_ar_informa_e_nao_libera_portais`, `::test_nova_tentativa_depois_de_falha_da_brasilapi`.
- **CE-03** — situação cadastral diferente de ATIVA aparece em destaque ("atenção: empresa não está ativa") e a emissão continua permitida. `tests/test_app.py::test_situacao_cadastral_nao_ativa_aparece_e_permite_continuar`.
- **CE-04** — filial em SP com matriz fora: matriz escolhida é recusada (REQ-04); filial escolhida segue com o aviso da RN-07. Se a matriz não puder ser identificada, a filial continua disponível. `tests/test_app.py::test_filial_em_sp_com_matriz_fora_de_sp`, `::test_matriz_nao_identificada_ainda_permite_a_filial`.

## Outras mudanças
- A tela passou a ter duas etapas: "Identificar empresa" e, depois, a escolha/emissão.
- Uma nova identificação descarta as opções anteriores; identificar durante uma consulta é recusado.

## Perguntas em aberto / pendências
- Nenhuma.
