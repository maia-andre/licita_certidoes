# Build report — 2026-11-12
Spec: docs/spec.md, versão 1.12
Incremento: INC-10 — Validação com 10 CNPJs reais (com as correções que ela exigiu e o INC-14)
Rodada: construção
Testes: 268 passando / 268 total — `.venv\Scripts\python -m pytest -q` (Windows 11, Python 3.14.6); também no GitHub Actions

## Correções feitas a partir da validação
- **REQ-12 — Falência aberta em janela nova.**
  - **O que acontecia:** no Chromium visível, o e-SAJ abre a certidão liberada numa janela nova, no visualizador de PDF, sem download. O programa só esperava download, consultava 3 vezes e deixava o item em "Pedido feito: acompanhar".
  - **Correção:** `esaj._consultar_uma_vez` intercepta a resposta de `realizarDownload.do` (`context.route`), guarda os bytes do PDF e entrega a resposta à janela sem mudança. Depois fecha a janela que o portal abriu. O download continua aceito.
  - **Teste:** `tests/test_esaj.py::test_certidao_aberta_em_janela_nova_com_pdf_inline_tambem_e_baixada`, com um portal falso que abre a certidão em janela nova.
- **REQ-19 / RN-11 — Improbidade no CNJ (INC-14).**
  - **Novo portal `certidoes/portais/cnj.py`, em consulta direta:**
    1. verifica as condenações com a mesma chamada da página do CNJ (`verificaRequeridoPossuiCertidao`);
    2. baixa a "Certidão Negativa" (`certidao.php?tipoCertidao=N`), ou a certidão com registros (`P`) quando há condenações.

    Resposta inesperada vira "Falha técnica".
  - **Leitura `leitura.ler_improbidade_cnj`:** "Nada consta" só na "Certidão Negativa" que diz "NÃO CONSTA"; nos demais casos, "Conferir no PDF". Mostra a data de emissão.
  - **Item 7:** `leitura.ler_sancoes_tcu` passa a decidir só por TCU, CEIS e CNEP. O resultado do CNJ fica na mensagem, apontando para o item 10. Um cadastro desconhecido ou repetido continua levando a "Conferir no PDF".
  - **Testes:**
    - `tests/test_cnj.py` (7);
    - `tests/test_leitura.py::test_improbidade_*` (3, um sobre o texto real) e `::test_sancoes_*` (ajustados);
    - `tests/test_sequencia.py::test_improbidade_*` e `::test_sancoes_*`.
- **RN-07 — CND federal de filial pela matriz.**
  - **Mudança:**
    - o item da CND tem `precisa=("matriz",)`;
    - para filial, `Execucao` passa o CNPJ da matriz a `receita.obter_cnd`, mostra-o na instrução e explica o motivo;
    - o PDF fica na pasta da filial;
    - a tela de escolha da filial avisa isso;
    - o CRF continua com o CNPJ da filial.
  - **Testes:**
    - `tests/test_sequencia.py::test_filial_pede_a_cnd_com_o_cnpj_da_matriz_e_explica_na_tela`;
    - `::test_matriz_pede_a_cnd_com_o_proprio_cnpj_sem_aviso`;
    - `tests/test_navegador_servidor.py::test_filial_copia_o_cnpj_da_matriz_e_guarda_o_pdf_na_pasta_da_filial`;
    - `tests/test_app.py::test_filial_escolhida_passa_o_cnpj_da_matriz_para_a_sequencia`.

## Perguntas em aberto / pendências
- Não foi vista uma certidão real do CNJ com condenações. O programa pede a certidão com registros e mostra "Conferir no PDF".
- Uma certidão de falência de ente público fica "em processamento" no e-SAJ. O item fica corretamente em "Pedido feito: acompanhar", mas a mensagem do portal ("Certidão em processamento") ainda não aparece na tela.
