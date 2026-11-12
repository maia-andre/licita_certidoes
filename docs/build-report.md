# Build report — 2026-11-12
Spec: docs/spec.md, versão 1.14
Incremento: INC-15 — Tela revisada e capa da consulta
Rodada: construção
Testes: 283 passando / 283 total — `.venv\Scripts\python -m pytest -q` (Windows 11, Python 3.14.6)

## Requisitos atendidos
- **REQ-09 — Tela revisada** (`certidoes/ui/index.html`, reescrita a partir da proposta aprovada em capturas).
  - Cada certidão tem uma etiqueta: o estado enquanto roda; a situação depois de obtida.
  - Cores:
    - verde para Negativa, Regular, Nada consta e Positiva com efeitos de negativa;
    - vermelho para Positiva;
    - âmbar para "Conferir no PDF", "Não emitida" e "Falha técnica";
    - azul para "Consultando…" e "Aguardando você";
    - cinza para "Na fila", "Pulada" e "Não se aplica".
  - Mostra o progresso ("3 de 7 concluídas") e, no fim, um resumo por estado.
  - Depois de "Emitir certidões", a empresa ocupa uma linha só.
  - O caminho do arquivo saiu de cada linha. Mensagens longas ficam recolhidas.
  - O campo de e-mail do e-SAJ só aparece quando o CNPJ ou a matriz é de SP.
- **REQ-21 — Cartão "Sua vez".**
  - Mostra a instrução do item que aguarda o servidor, com os botões "Copiar o CNPJ de novo", "Pular esta certidão" e "O portal não emitiu".
  - `Api.copiar_cnpj` usa `Execucao.cnpj_do_item`, que devolve o CNPJ da matriz na CND de filial.
- **REQ-08 — Subpasta por consulta.**
  - `Api.emitir` cria a `Execucao` com `pasta_consulta = Certidoes/<CNPJ>/<aaaa-mm-dd hhhmm>`, com os segundos acrescentados se a pasta já existir.
  - A `Execucao` move cada PDF obtido para essa subpasta. A subpasta só é criada quando há arquivo.
  - `Api.abrir_pasta` abre a subpasta.
- **REQ-20 — Capa em PDF** (`certidoes/capa.py`).
  - **Conteúdo:**
    - empresa, com a hora da consulta à BrasilAPI;
    - período da consulta;
    - tabela com situação, validade ou emissão, data e hora de cada item e nome do arquivo;
    - aviso da RN-06;
    - campos de responsável, matrícula e data;
    - anexo com o SHA-256 de cada certidão e o comando `certutil` para conferir.
  - **Como é gerada:** em HTML, impressa em A4 pelo Chromium do Playwright, sem dependência nova. O nome é `capa-<data-hora>.pdf`, na subpasta da consulta.
  - **Botão:** `Api.gerar_capa` não roda durante a consulta e abre a capa depois de gerada.
  - **Horários:** `Execucao` registra a hora em que cada item chega a um estado final.
- `certidoes/__init__.py` traz `__version__ = "0.3.0"`, que aparece no rodapé da capa.

## Testes
- `tests/test_capa.py` (5): conteúdo e escape do HTML, vencida, SHA-256 e pasta, arquivo ausente, PDF real com o anexo.
- `tests/test_app.py`: subpasta com data e hora, copiar o CNPJ certo, abrir a pasta, gerar e abrir a capa, capa bloqueada durante a consulta, elementos da tela nova.
- `tests/test_sequencia.py`: hora de cada item, PDF movido para a subpasta, PDF fora da subpasta sem pasta de consulta, CNPJ do item.

## Perguntas em aberto / pendências
- Nenhuma. A consulta completa na janela real, do CNPJ à capa, foi feita pelo servidor em 12/11/2026.
