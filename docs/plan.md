# Plan: Obtenção assistida de certidões de fornecedores
Spec: docs/spec.md, versão 1.2 | Gerado: 2026-11-06
Progresso: 2/10 incrementos concluídos

## Backlog

### INC-01 — CNDT de ponta a ponta
Status: concluído (2026-11-11)
Itens da spec: REQ-01, REQ-06, REQ-08 | RNF-01, RNF-02, RNF-06 | RN-05 | CE-01
Depende de: —
Entrega verificável: na tela pywebview, um CNPJ real abre o portal do TST no Chromium, o servidor resolve o captcha e o PDF da CNDT fica salvo e pode ser aberto pela tela.

### INC-02 — CND federal e sequência de itens
Status: concluído (2026-11-11)
Itens da spec: REQ-05, REQ-09 | RNF-04 | RN-02, RN-09 | CE-05, CE-06, CE-13
Depende de: INC-01
Entrega verificável: um CNPJ real percorre CND federal (navegador do servidor) e CNDT (automatizado) em sequência, com o estado de cada item na tela, e uma falha em um item aparece como "Falha técnica" sem interromper o outro.

### INC-03 — CRF FGTS e certidão não emitida
Status: pendente
Itens da spec: REQ-11 | CE-10
Depende de: INC-02
Entrega verificável: um CNPJ real obtém o CRF, e uma empresa sem CRF disponível aparece como "Não emitida" com a mensagem do portal.
Primeiro passo: testar se a Caixa aceita navegador automatizado; se recusar, usar o modo "navegador do servidor" (RN-09).

### INC-04 — Situação e validade na tela
Status: pendente
Itens da spec: REQ-10, REQ-15 | RNF-05 | RN-03, RN-04, RN-06 | CE-09, CE-11
Depende de: INC-03
Entrega verificável: as certidões obtidas mostram situação e validade iguais às do PDF, ou "Conferir no PDF", com o aviso de que a decisão cabe ao servidor.

### INC-05 — Identificação da empresa pela BrasilAPI
Status: pendente
Itens da spec: REQ-02, REQ-03, REQ-04 | RN-07 | CE-02, CE-03, CE-04
Depende de: INC-04
Entrega verificável: a tela mostra os dados da empresa, pede a escolha em caso de filial e recusa um CNPJ fora de SP sem abrir nenhum portal.

### INC-06 — Certidão Única estadual no SIDEB
Status: pendente
Itens da spec: RN-08 | CE-07
Depende de: INC-05
Entrega verificável: um CNPJ real de SP obtém a Certidão Única pelo SIDEB, e fora do horário do sistema o item mostra "Falha técnica" com essa explicação.

### INC-07 — Pular e repetir itens
Status: pendente
Itens da spec: REQ-07, REQ-14 | CE-08
Depende de: INC-06
Entrega verificável: o servidor pula um item, repete só esse item depois e, ao fechar o navegador no meio do fluxo, a tela continua aberta com o item em "Falha técnica".

### INC-08 — Pedido de falência no e-SAJ
Status: pendente
Itens da spec: REQ-12 | CE-12
Depende de: INC-07
Entrega verificável: um CNPJ real tem o pedido de falência enviado ao e-SAJ com o e-mail informado, e o item fica em "Pedido feito: acompanhar".

### INC-09 — Complemento no eproc e lista completa
Status: pendente
Itens da spec: REQ-13 | RNF-03 | RN-01
Depende de: INC-08
Entrega verificável: o eproc abre para o servidor entrar com o gov.br, o item fica em "Pedido feito: acompanhar" após a confirmação e os seis itens aparecem na tela, sem credenciais guardadas ao reiniciar o programa.

### INC-10 — Validação com 10 CNPJs reais
Status: pendente
Itens da spec: Definição de concluído
Depende de: INC-09
Entrega verificável: um relatório mostra o resultado dos 10 CNPJs reais de SP, incluindo ao menos 1 filial, conferido com os PDFs.

## Cobertura
Cada REQ, RNF, RN e CE da spec aparece em exatamente um incremento: REQ-01 a REQ-15, RNF-01 a RNF-06, RN-01 a RN-09 e CE-01 a CE-13.

O INC-02 antecipa o maior risco técnico (hCaptcha em navegador automatizado). Se a Receita ou a Caixa recusarem o navegador, o plano deve ser revisto antes de seguir.

## Revisões
- **2026-11-11 — Receita recusa navegador automatizado.** No Chromium do Playwright, o hCaptcha passa, mas a API da Receita responde `CaptchaFalhaValidacao` (código 023) em "Emitir" e em "Consultar". No navegador normal do servidor, o mesmo CNPJ funcionou. Decisão aprovada: criar o modo "navegador do servidor" (spec 1.2, RN-09) para a CND federal, sem tentar contornar a recusa. O TST continua automatizado.
