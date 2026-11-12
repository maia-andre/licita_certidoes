# Build report — 2026-11-12
Spec: docs/spec.md, versão 1.9
Incremento: INC-12 — Apenados do TCE-SP
Rodada: construção
Testes: 246 passando / 246 total — `.venv\Scripts\python -m pytest -q` (Windows 11, Python 3.14.6)

## Requisitos atendidos
- **REQ-17** — Atendido — novo portal `certidoes/portais/tcesp.py`, no modo "navegador do servidor" (RN-09).
  - `obter_certidao` abre no navegador padrão o formulário "Gerar Certidão" do TCE-SP e deixa o CNPJ na área de transferência.
  - O servidor cola o CNPJ, clica em "Gerar", conclui a verificação (Turnstile), clica em "OK" e baixa o PDF pelo ícone.
  - O programa reconhece o PDF em Downloads pelo texto "Certidão de Apenados" e pelo CNPJ, e não pelo nome ("Certidão Apenados.pdf", com sufixo se repetido). Em seguida, guarda o arquivo como `apenados-tcesp-<data-hora>.pdf` na pasta do CNPJ.

  `leitura.ler_apenados_tcesp` lê a certidão:
  - "Nada consta" quando ela diz "NÃO constam, até a presente data, <data>, (…) IMPEDIMENTOS DE LICITAÇÃO";
  - "Conferir no PDF" quando lista impedimentos ("CONSTA(M)", do modelo do portal), com aviso na mensagem;
  - "Conferir no PDF" também para qualquer outro texto;
  - a validade é a data de "válido até" (RN-04).

  Testes:
  - `tests/test_tcesp.py` (7);
  - `tests/test_leitura.py::test_apenados_*` (4, um sobre o texto real);
  - `tests/test_sequencia.py` (ordem e modo, item real, leitura com "Vencida" no dia seguinte).
- **RN-03 / RN-04** — Atualizadas na spec 1.9: "Nada consta" para apenados; validade impressa, igual à data da consulta.

## Casos extremos cobertos
- **CE-15** — Ocorreu: o Turnstile recusou o Chromium do Playwright (erro 600010) nas duas tentativas assistidas. O item passou ao modo navegador do servidor, sem tentativa de contorno. A versão automatizada escrita para o teste foi descartada.
- **CE-13** — PDF que não chega a Downloads vira "Falha técnica" por tempo esgotado (`test_sem_a_certidao_termina_em_tempo_esgotado`). PDF de outro CNPJ ou outro documento é ignorado (`test_ignora_pdf_novo_que_nao_e_a_certidao_e_certidao_de_outro_cnpj`).
- **CE-09** — Texto diferente do conhecido mantém "Obtida" com "Conferir no PDF" (`test_apenados_tcesp_com_texto_desconhecido_pede_conferencia`).

## Outras mudanças
- `navegador_servidor.obter_pelo_navegador`: o nome do portal agora vem com artigo ("da Receita Federal", "da Caixa", "do TCE-SP"), para a mensagem de erro sair correta.

## Perguntas em aberto / pendências
- O texto de uma certidão com impedimentos não foi visto em documento real. A leitura usa o modelo da página do portal ("CONSTA(M)") e, em qualquer caso diferente de "NÃO constam", mostra "Conferir no PDF".
- A validade impressa é o próprio dia da consulta. A partir do dia seguinte, a tela mostra "Vencida", o que é fiel ao documento, mas pode estranhar o servidor.
