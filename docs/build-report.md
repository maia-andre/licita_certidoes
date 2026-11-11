# Build report — 2026-11-11
Spec: docs/spec.md, versão 1.3
Incremento: INC-04 — Situação e validade na tela
Rodada: construção
Testes: 112 passando / 112 total — `.venv\Scripts\python -m pytest -q` (Windows 11, Python 3.14.6)

## Requisitos atendidos
- **REQ-10** — Atendido — `certidoes/leitura.py` (`ler_cnd`, `ler_crf`, `ler_cndt`, `ler`) e `Execucao._registrar_leitura` (`certidoes/sequencia.py`); colunas "Situação" e "Validade" na tela. `tests/test_leitura.py`, `tests/test_sequencia.py::test_certidao_obtida_mostra_situacao_e_validade_lidas_do_pdf`.
- **REQ-15** — Atendido — aviso permanente `#aviso` em `certidoes/ui/index.html`. `tests/test_app.py::test_aviso_permanente_de_que_a_decisao_cabe_ao_servidor`.
- **RNF-05** — Atendido — leitura com `pypdf`, local, sem IA e sem serviços externos (`certidoes/pdf.py`).
- **RN-03** — Atendido — situação lida só do título da certidão ("CERTIDÃO NEGATIVA/POSITIVA ..."), nunca do corpo; "Positiva com efeitos de negativa" é testada antes de "Positiva"; CRF "Regular" pela frase "encontra-se em situação regular". Em qualquer dúvida, "Conferir no PDF". `tests/test_leitura.py::test_cnd_positiva_nao_vira_efeito_de_negativa_por_causa_do_corpo`, `::test_documento_de_outro_tipo_pede_conferencia`.
- **RN-04** — Atendido — validade é a data impressa ("Válida até", "Validade:", data final do CRF); sem data, com datas divergentes ou com data inválida, "Conferir no PDF", sem calcular prazo. `tests/test_leitura.py::test_sem_data_de_validade_pede_conferencia_sem_calcular_prazo`, `::test_duas_datas_de_validade_diferentes_pedem_conferencia`, `::test_data_invalida_pede_conferencia`.
- **RN-06** — Atendido — a tela mostra só a situação impressa e a validade; não há termos de habilitação, inabilitação ou bloqueio.

## Casos extremos cobertos
- **CE-09** — PDF ilegível, arquivo sumido ou leitura com erro: o item continua "Obtida" e mostra "Conferir no PDF". `tests/test_sequencia.py::test_pdf_ilegivel_continua_obtida_e_pede_conferencia`, `::test_arquivo_que_sumiu_pede_conferencia`.
- **CE-11** — validade anterior a hoje aparece com "(Vencida)"; validade igual a hoje ainda não está vencida. `tests/test_sequencia.py::test_certidao_com_validade_anterior_a_hoje_aparece_vencida`, `::test_validade_igual_a_hoje_ainda_nao_esta_vencida`.

## Proteção adicional (RN-03)
- Se nenhum CNPJ do PDF tiver a mesma raiz (8 primeiros caracteres) do CNPJ consultado, a tela mostra "Conferir no PDF". A raiz cobre CND e CNDT emitidas para matriz e filiais. `tests/test_leitura.py::test_cnpj_de_outra_empresa_pede_conferencia`, `::test_filial_da_mesma_empresa_confere_pela_raiz`.

## Calibração com certidões reais
Leitura dos 6 PDFs reais emitidos em 11/11/2026: CND "Positiva com efeitos de negativa" até 06/02/2027 (2 arquivos), CNDT "Negativa" até 10/05/2027 (3), CRF "Regular" até 08/12/2026 (1). Os testes usam textos modelados nesses PDFs, com empresa e CNPJ fictícios.

## Perguntas em aberto / pendências
- As variantes "Positiva" da CND e "Positiva com efeito de negativa" e "Positiva" da CNDT foram escritas a partir do padrão dos títulos, sem PDF real dessas situações. Se o título real for diferente, a tela mostra "Conferir no PDF" (nunca uma situação errada); conferir na validação com 10 CNPJs (INC-10).
