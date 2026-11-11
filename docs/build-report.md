# Build report — 2026-11-11
Spec: docs/spec.md, versão 1.2
Incremento: INC-02 — CND federal e sequência de itens
Rodada: construção
Testes: 66 passando / 66 total — `.venv\Scripts\python -m pytest -q` (Windows 11, Python 3.14.6; inclui Chromium headless contra portal falso local)

## Antes da construção: viabilidade da Receita
- Duas tentativas assistidas em Chromium do Playwright: o hCaptcha passa, mas a API responde `400 {"statusValidacao":"CaptchaFalhaValidacao","codigo":"023"}` em `Emissao/verificar` e `consulta/validar-contribuinte`.
- Controle: no Edge/Chrome normal do servidor, o mesmo CNPJ funcionou na mesma tarde.
- Decisão aprovada: modo "navegador do servidor" (spec 1.2, RN-09), sem esconder a automação.

## Requisitos atendidos
- **REQ-05** — Atendido para os itens deste incremento (CND federal, CNDT) — `certidoes/sequencia.py` (`ITENS`, `Execucao`); `tests/test_sequencia.py::test_percorre_os_itens_em_sequencia_e_marca_obtida`, `tests/test_sequencia.py::test_itens_seguem_a_ordem_da_rn01`.
- **REQ-09** — Atendido — tabela na tela (`certidoes/ui/index.html`) acompanha `Api.estado()` a cada 0,7 s; `tests/test_app.py::test_estado_mostra_cada_item_com_o_arquivo_como_texto`, `tests/test_app.py::test_emitir_roda_em_segundo_plano`.
- **RNF-04** — Atendido — cada portal em seu módulo (`portais/tst.py`, `portais/receita.py`); o mecanismo do navegador do servidor fica em `portais/navegador_servidor.py`, reaproveitável pela Caixa.
- **RN-02** — Parcial, como previsto — usa "Aguardando", "Em andamento", "Aguardando servidor", "Obtida" e "Falha técnica". "Não emitida", "Pulada" e "Pedido feito: acompanhar" entram nos INC-03, 07 e 08. `tests/test_sequencia.py::test_estados_durante_a_execucao`.
- **RN-09** — Atendido — `portais/navegador_servidor.py`: abre a URL no navegador padrão, copia o CNPJ (`clip` no Windows), vigia a pasta Downloads (pasta conhecida do Windows, inclusive redirecionada), reconhece `Certidao-<CNPJ>*.pdf` modificado após o início, espera o tamanho estabilizar e move o PDF para a pasta do CNPJ. `tests/test_navegador_servidor.py`.
- **REQ-06** (ajuste da spec 1.2) — Atendido — no modo navegador do servidor, o programa continua quando o PDF chega; `tests/test_navegador_servidor.py::test_abre_o_portal_da_receita_copia_o_cnpj_e_guarda_o_pdf`.

## Casos extremos cobertos
- **CE-05** — `tests/test_sequencia.py::test_falha_de_portal_vira_falha_tecnica_e_a_sequencia_segue`, `tests/test_sequencia.py::test_erro_inesperado_tambem_vira_falha_tecnica_e_a_sequencia_segue`, `tests/test_app.py::test_falha_em_um_item_nao_interrompe_o_outro`
- **CE-06** — a recusa da Receita aparece como erro do portal; no TST, captcha que não conclui vira "Tempo esgotado" (`tests/test_tst.py::test_tempo_esgotado_gera_erro_claro`). Ambos viram "Falha técnica" pela sequência.
- **CE-13** — `tests/test_navegador_servidor.py::test_tempo_esgotado_informa_a_pasta_vigiada`, `::test_ignora_certidao_antiga_que_ja_estava_em_downloads`, `::test_ignora_pdf_de_outro_cnpj`, `::test_arquivo_que_nao_e_pdf_gera_erro_e_fica_em_downloads`

## Outras mudanças
- `portais/comum.py`: `PortalErro` e `guardar_pdf` compartilhados.
- `Api.emitir` roda a sequência em thread daemon; fechar a tela durante a consulta encerra o programa.
- `Api.abrir_pdf(chave)` devolve `False` se o arquivo sumiu, em vez de falhar em silêncio.

## Perguntas em aberto / pendências
- Se o navegador do servidor estiver configurado para perguntar onde salvar, o PDF só é reconhecido se for salvo em Downloads (CE-13 informa a pasta).
- A área de transferência no Linux depende de `wl-copy` ou `xclip`; sem eles, o servidor digita o CNPJ mostrado na tela.
