# Build report — 2026-11-12
Spec: docs/spec.md, versão 1.6
Incremento: INC-08 — Pedido de falência no e-SAJ
Rodada: construção
Testes: 218 passando / 218 total — `.venv\Scripts\python -m pytest -q` (Windows 11, Python 3.14.6)

## Requisitos atendidos
- **REQ-12** — Atendido — novo portal `certidoes/portais/esaj.py`, em modo automatizado. O fluxo tem três etapas.

  **1. Pedido.** `obter_pedido_falencia` abre o e-SAJ no Chromium visível e preenche:
  - o modelo "CERT DIST - FALÊNCIAS, CONCORDATAS E RECUPERAÇÕES";
  - pessoa jurídica;
  - a razão social da BrasilAPI;
  - o CNPJ, digitado tecla a tecla por causa da máscara e conferido depois;
  - o e-mail.

  O servidor marca a confirmação, resolve o reCAPTCHA e envia. O programa reconhece a página de resultado e lê número, data e prazo do pedido.

  **2. Consulta imediata.** No mesmo Chromium, o programa abre "Visualizar Certidão", preenche número, data, pessoa jurídica e CNPJ e clica em "Consultar". Essa tela não tem captcha. São até 3 tentativas, com 10 s de intervalo; durante a consulta, a tela mostra "Pedido nº … aceito. Consultando se a certidão já foi liberada...".
  - Se o PDF vier, o arquivo é salvo como `falencia-<data-hora>.pdf` e o item fica "Obtida".
  - Se não vier, o item fica "Pedido feito: acompanhar", com número, data, e-mail, prazo e a orientação de acompanhar pelo e-mail ou por "Visualizar Certidão".
  - Uma falha na consulta, ou um "Pular" durante ela, nunca apaga o pedido já feito.

  **3. Leitura.** `leitura.ler_falencia` mostra "Nada consta" quando a certidão diz "verificou NADA CONSTAR" e o CNPJ confere; em qualquer outro texto, mostra "Conferir no PDF". Na validade, mostra "Não impressa (emitida em dd/mm/aaaa)", porque a certidão não imprime validade e o programa não calcula prazo (RN-04, spec 1.6).

  **E-mail salvo.** `certidoes/preferencias.py` grava o e-mail em `%APPDATA%\licita_certidoes\preferencias.json` (no Linux, em `~/.config/licita_certidoes/`). A tela abre com ele preenchido (`Api.email_salvo`). Só um e-mail válido é gravado, e uma falha de gravação não impede a consulta.

  Testes:
  - pedido: `tests/test_esaj.py::test_preenche_os_dados_conhecidos_e_deixa_confirmacao_e_envio_para_o_servidor`;
  - certidão liberada: `::test_certidao_ja_liberada_e_baixada_logo_apos_o_pedido`;
  - certidão não liberada: `::test_certidao_nao_liberada_tenta_algumas_vezes_e_fica_o_pedido`;
  - "Pular" durante a consulta: `::test_pular_durante_a_consulta_encerra_a_consulta_e_mantem_o_pedido`;
  - leitura sobre o texto real: `tests/test_leitura.py::test_falencia_real_nada_consta_sem_validade_impressa`;
  - sequência: `tests/test_sequencia.py::test_falencia_baixada_mostra_nada_consta_e_a_emissao_no_lugar_da_validade`;
  - e-mail salvo: `tests/test_preferencias.py` (7) e `tests/test_app.py::test_email_valido_fica_salvo_para_as_proximas_consultas`.

## Casos extremos cobertos
- **CE-12** — Com o e-mail vazio ou inválido, `Api.emitir` recusa antes de abrir qualquer portal (`"campo": "email"`). A tela marca o campo e põe o cursor nele, e o e-mail salvo não é substituído. Testes: `tests/test_app.py::test_email_vazio_ou_invalido_nao_inicia_a_consulta`, `::test_email_invalido_nao_substitui_o_salvo`, `tests/test_esaj.py::test_email_invalido_nao_abre_o_portal` e `::test_email_valido`.

## Outras mudanças
- `Pedido` (em `certidoes/portais/comum.py`) é o resultado de portal que só registra o pedido. O campo `observacao` entra na mensagem do item.
- `Item.precisa` lista os dados da consulta repassados ao portal; `"avisar"` dá ao portal uma função que atualiza a mensagem do item.
- "Pedido feito: acompanhar" não é repetível, porque repetir mandaria outro pedido ao TJSP.
- O e-SAJ falso (`tests/conftest.py`) reproduz o pedido e "Visualizar Certidão", com as máscaras de data e CNPJ. A consulta devolve o PDF só quando os quatro campos conferem.

## Perguntas em aberto / pendências
- O texto de uma certidão com apontamentos ainda não foi visto. Nesse caso, o programa mostra "Conferir no PDF".
- O e-SAJ e a própria certidão pedem complemento pela certidão do eproc (item 6, INC-09), que exige gov.br.
- A certidão diz que abrange a matriz e as filiais. Vale rever o aviso da RN-07 (filial → sede) quando o INC-10 validar filiais.
- Acompanhar depois um pedido não liberado (digitar número e data na tela) fica para depois, se fizer falta.
