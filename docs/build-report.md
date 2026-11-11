# Build report — 2026-11-11
Spec: docs/spec.md, versão 1.3
Incremento: INC-03 — CRF FGTS e certidão não emitida
Rodada: construção
Testes: 82 passando / 82 total — `.venv\Scripts\python -m pytest -q` (Windows 11, Python 3.14.6)

## Antes da construção: viabilidade da Caixa
- Um único acesso de leitura em Chromium headless foi redirecionado para o bloqueio de robôs da Caixa (Radware/ShieldSquare: "Estamos detectando comportamento malicioso no acesso"). Sem novas tentativas automatizadas, para não marcar o IP da prefeitura.
- Controle no navegador normal: o CRF é uma página com link e botão "Imprimir"; o servidor salva como PDF, com nome livre (sugestão do navegador: "Consulta Regularidade do Empregador.pdf").
- O texto do PDF salvo é legível pela `pypdf` e traz "Certificado de Regularidade do FGTS - CRF", a inscrição e a validade.
- Decisões aprovadas (spec 1.3): CRF no modo navegador do servidor, PDF reconhecido pelo conteúdo; botão "O portal não emitiu" com campo opcional para a mensagem.

## Requisitos atendidos
- **REQ-11** — Atendido no modo navegador do servidor — botão e campo na linha do item em "Aguardando servidor" (`certidoes/ui/index.html`), `Api.informar_nao_emitida` (`certidoes/app.py`), `Execucao.informar_nao_emitida` e estado "Não emitida" (`certidoes/sequencia.py`), `SinalNaoEmitida`/`NaoEmitida` (`certidoes/portais/comum.py`). `tests/test_sequencia.py::test_servidor_informa_nao_emitida_com_a_mensagem_do_portal`, `::test_nao_emitida_sem_mensagem_pede_para_conferir_no_portal`, `::test_nao_emitida_so_vale_para_item_do_navegador_que_aguarda_o_servidor`, `tests/test_app.py::test_informar_nao_emitida_repassa_para_o_item_que_aguarda_o_servidor`.
- **RN-09** (Caixa) — Atendido — `certidoes/portais/caixa.py`: abre o portal, copia o CNPJ e aceita qualquer PDF novo em Downloads cujo texto traga o título do CRF e o CNPJ. `tests/test_caixa.py`.
- **RN-01** — A sequência agora tem CND federal, CRF FGTS e CNDT, nessa ordem. `tests/test_sequencia.py::test_itens_seguem_a_ordem_da_rn01_com_o_modo_de_cada_portal`.

## Casos extremos cobertos
- **CE-10** — "Não emitida" nunca vira "Falha técnica": `NaoEmitida` é tratada antes de `PortalErro` em `Execucao.rodar`. `tests/test_sequencia.py::test_servidor_informa_nao_emitida_com_a_mensagem_do_portal`, `tests/test_caixa.py::test_servidor_informa_que_o_portal_nao_emitiu`.
- **CE-13** (Caixa) — PDF novo que não é CRF, ou CRF de outro CNPJ, é ignorado e fica em Downloads; sem CRF do CNPJ, tempo esgotado. `tests/test_caixa.py::test_ignora_pdf_novo_que_nao_e_crf_e_crf_de_outro_cnpj`, `::test_sem_crf_do_cnpj_termina_em_tempo_esgotado`.

## Outras mudanças
- `certidoes/pdf.py`: `texto_do_pdf` e `contem_cnpj`, locais e sem IA (RNF-05); base para o INC-04.
- `navegador_servidor.aguardar_arquivo`: conferência opcional do conteúdo (arquivo recusado não é relido) e encerramento pelo aviso de "Não emitida".
- `requirements.txt`: `pypdf==7.0.1`.
- `tests/conftest.py`: `pdf_com_texto` gera PDFs de teste com texto, sem certidões reais (RNF-06).

## Perguntas em aberto / pendências
- Mapear os cerca de 4 cliques da Caixa até salvar o PDF, para deixar a instrução da tela mais precisa.
- "Não emitida" lida automaticamente do portal só será possível em portais automatizados; nos do navegador do servidor, depende do aviso do servidor.
