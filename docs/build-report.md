# Build report — 2026-11-11
Spec: docs/spec.md, versão 1.4
Incremento: INC-07 — Pular e repetir itens
Rodada: construção
Testes: 150 passando / 150 total — `.venv\Scripts\python -m pytest -q` (Windows 11, Python 3.14.6)

## Requisitos atendidos
- **REQ-07** — Atendido — botão "Pular" no item em andamento ("Em andamento" ou "Aguardando servidor"); `Api.pular` → `Execucao.pular` → `SinalServidor.pular` (`certidoes/portais/comum.py`). Os portais verificam o sinal enquanto esperam: o modo navegador a cada 1 s (`aguardar_arquivo`) e o TST a cada 0,5 s (`tst._esperar_download`, que substituiu a espera única de 5 min). O item fica "Pulada" ("Pulada pelo servidor.") e a sequência segue. `tests/test_sequencia.py::test_servidor_pula_o_item_em_andamento_e_a_sequencia_segue`, `::test_so_pula_o_item_em_andamento`, `tests/test_tst.py::test_servidor_pula_o_item_enquanto_o_tst_espera`, `tests/test_navegador_servidor.py::test_servidor_pula_enquanto_espera_o_pdf`.
- **REQ-14** — Atendido — botão "Repetir" em item "Falha técnica", "Não emitida" ou "Pulada", com a consulta parada; `Api.repetir` → `Execucao.repetir` roda só aquele item, limpando estado, situação e validade anteriores. `tests/test_sequencia.py::test_repete_so_o_item_que_falhou`, `::test_repete_item_pulado_e_nao_emitido`, `::test_repetir_item_obtido_ou_inexistente_nao_faz_nada`, `::test_repeticao_limpa_situacao_e_validade_anteriores`, `tests/test_app.py::test_pular_e_repetir_pela_api`.

## Casos extremos cobertos
- **CE-08** — Chromium do TST fechado durante a espera (aba ou navegador inteiro): "Falha técnica" com "A janela do portal foi fechada antes da emissão." e a tela continua aberta. Testado com Playwright real fechando a página e o navegador: `tests/test_tst.py::test_janela_fechada_durante_a_espera_vira_erro_claro` (2 casos). No modo navegador do servidor, o programa não vê o navegador; o servidor usa "Pular" ou espera o tempo-limite (CE-13).

## Outras mudanças
- `SinalNaoEmitida` virou `SinalServidor` (pular ou "o portal não emitiu"; a primeira ação vale); `Pulada` é a nova exceção. Todo item recebe o sinal; "não emitiu" continua valendo só no modo navegador.
- `Execucao.rodar` foi dividida em `_rodar_item`, reaproveitada pela repetição.

## Perguntas em aberto / pendências
- Nenhuma.
