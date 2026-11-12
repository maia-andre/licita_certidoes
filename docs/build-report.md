# Build report — 2026-11-12
Spec: docs/spec.md, versão 1.8
Incremento: INC-11 — Sanções federais pela Consulta Consolidada do TCU
Rodada: construção
Testes: 233 passando / 233 total — `.venv\Scripts\python -m pytest -q` (Windows 11, Python 3.14.6)

## Requisitos atendidos
- **REQ-16** — Atendido — novo portal `certidoes/portais/tcu.py`, no novo modo "consulta direta" (RN-09). `obter_consulta` pede o PDF da Consulta Consolidada de Pessoa Jurídica pela API pública que a própria página do TCU usa (`/api/rest/publico/certidoes/<CNPJ>`, `Accept: application/pdf`). Não abre navegador e não pede nada ao servidor. O PDF é salvo como `sancoes-tcu-<data-hora>.pdf` na pasta do CNPJ. A identificação é genérica (`User-Agent: licita_certidoes`), sem dados do usuário.

  `leitura.ler_sancoes_tcu` lê os quatro cadastros do documento: Licitantes Inidôneos (TCU), CNIA (CNJ), CEIS e CNEP.
  - Mostra "Nada consta" só se os quatro aparecerem e todos disserem "Nada Consta"; em qualquer outro caso, "Conferir no PDF".
  - Na mensagem do item, mostra o resultado de cada cadastro.
  - Na validade, mostra "Não impressa (emitida em dd/mm/aaaa)", com a data da consulta (RN-04).

  Testes: `tests/test_tcu.py` (7), `tests/test_leitura.py::test_sancoes_*` (5, um sobre o texto real) e `tests/test_sequencia.py::test_sancoes_*` (3).
- **RN-11** — Atendida — CEIS e CNEP vêm da Consulta Consolidada do TCU. O Portal da Transparência pede captcha (AWS WAF); o TCU, não.

## Casos extremos cobertos
- **CE-14** — Um cadastro indisponível ou com registro mantém o item "Obtida", mostra "Conferir no PDF" e põe na mensagem o nome do cadastro, o resultado e o link de consulta manual. Testes:
  - `tests/test_leitura.py::test_sancoes_real_com_cnj_indisponivel_pede_conferencia_e_aponta_o_cadastro`;
  - `::test_sancoes_com_registro_pede_conferencia_com_o_link_do_cadastro`;
  - `::test_sancoes_sem_um_dos_cadastros_pede_conferencia`;
  - `tests/test_sequencia.py::test_sancoes_com_cadastro_indisponivel_ficam_obtidas_para_conferir`.
- **CE-05** — Erro HTTP, portal fora do ar e resposta que não é PDF viram "Falha técnica", com mensagem clara (`tests/test_tcu.py`).

## Outras mudanças
- `Leitura.detalhe`: resultado por cadastro, que vai para a mensagem do item obtido.
- A tela mostra a mensagem do item junto com "Salva em: …". Antes, o caminho do arquivo escondia a mensagem.
- "Pular" vale até a consulta começar. Depois que o PDF chega, o resultado é mantido.
- Os testes do TCU dispensam o proxy do Windows para o portal falso local (`NO_PROXY=127.0.0.1`). Na rede da prefeitura, o proxy do sistema interceptava até `127.0.0.1`.

## Perguntas em aberto / pendências
- O CNJ (CNIA) esteve indisponível nas duas consultas reais de 12/11/2026. Se isso for frequente, o item vai aparecer quase sempre como "Conferir no PDF", com o link do CNJ.
- O texto de um cadastro com registro não foi visto em documento real. Qualquer resultado diferente de "Nada Consta" vira "Conferir no PDF".
