# Plan: Obtenção assistida de certidões de fornecedores
Spec: docs/spec.md, versão 1.8 | Gerado: 2026-11-06
Progresso: 8/13 incrementos concluídos (3 adiados)

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
Status: concluído (2026-11-11)
Itens da spec: REQ-11 | CE-10
Depende de: INC-02
Entrega verificável: um CNPJ real obtém o CRF (navegador do servidor, PDF salvo pela opção "Imprimir"), e o servidor consegue marcar um item como "Não emitida" com a mensagem do portal.

### INC-04 — Situação e validade na tela
Status: concluído (2026-11-11)
Itens da spec: REQ-10, REQ-15 | RNF-05 | RN-03, RN-04, RN-06 | CE-09, CE-11
Depende de: INC-03
Entrega verificável: as certidões obtidas mostram situação e validade iguais às do PDF, ou "Conferir no PDF", com o aviso de que a decisão cabe ao servidor.

### INC-05 — Identificação da empresa pela BrasilAPI
Status: concluído (2026-11-11)
Itens da spec: REQ-02, REQ-03, REQ-04 | RN-07 | CE-02, CE-03, CE-04
Depende de: INC-04
Entrega verificável: a tela mostra os dados da empresa, pede a escolha em caso de filial e recusa um CNPJ fora de SP sem abrir nenhum portal.

### INC-06 — Certidão Única estadual no SIDEB
Status: adiado (2026-11-11) — o SIDEB exige login gov.br para emitir (spec 1.4, RN-10)
Itens da spec: RN-08 | CE-07
Depende de: INC-05
Entrega verificável: um CNPJ real de SP obtém a Certidão Única pelo SIDEB, e fora do horário do sistema o item mostra "Falha técnica" com essa explicação.

### INC-07 — Pular e repetir itens
Status: concluído (2026-11-11)
Itens da spec: REQ-07, REQ-14 | CE-08
Depende de: INC-05 (INC-06 adiado)
Entrega verificável: o servidor pula um item, repete só esse item depois e, ao fechar o navegador no meio do fluxo, a tela continua aberta com o item em "Falha técnica".

### INC-08 — Pedido de falência no e-SAJ
Status: concluído (2026-11-12)
Itens da spec: REQ-12 | CE-12
Depende de: INC-07
Entrega verificável: um CNPJ real tem o pedido de falência enviado ao e-SAJ com o e-mail informado, e o item fica em "Pedido feito: acompanhar".

### INC-09 — Complemento no eproc e lista completa
Status: adiado (2026-11-12) — o pedido no eproc exige login gov.br nível ouro ou prata (spec 1.7, RN-10)
Itens da spec: REQ-13 | RNF-03 | RN-01
Depende de: INC-08
Entrega verificável: o eproc abre para o servidor entrar com o gov.br, o item fica em "Pedido feito: acompanhar" após a confirmação e os seis itens aparecem na tela, sem credenciais guardadas ao reiniciar o programa.

### INC-11 — Sanções federais pela Consulta Consolidada do TCU
Status: concluído (2026-11-12)
Itens da spec: REQ-16 | RN-11 | CE-14
Depende de: INC-08
Entrega verificável: um CNPJ real tem o PDF da Consulta Consolidada salvo, com o resultado de TCU, CNJ, CEIS e CNEP na tela, e um cadastro indisponível aparece como "Conferir no PDF" com o nome do cadastro e o link de consulta manual.

### INC-12 — Apenados do TCE-SP
Status: pendente
Itens da spec: REQ-17 | CE-15
Depende de: INC-11
Entrega verificável: em teste assistido, um CNPJ real tem a certidão de apenados do TCE-SP salva depois que o servidor resolve o captcha, com a situação lida na tela; se o Turnstile recusar o Chromium automatizado, o item passa ao modo navegador do servidor.

### INC-13 — CND municipal de São José dos Campos
Status: adiado (2026-11-12) — o novo sistema tributário (iiTributário) exige login por CPF e ainda não oferece a CND mobiliária (spec 1.8, RN-10)
Itens da spec: REQ-18
Depende de: INC-12
Entrega verificável: para empresa com sede em SJC, a CND municipal fica salva e lida na tela; para outro município, o item informa que a certidão vem da prefeitura da sede, sem abrir portal.

### INC-10 — Validação com 10 CNPJs reais
Status: pendente
Itens da spec: Definição de concluído
Depende de: INC-12 (INC-09 e INC-13 adiados)
Entrega verificável: um relatório mostra o resultado dos 10 CNPJs reais de SP, nos itens ativos da RN-01 (1, 2, 3, 5, 7 e 8), incluindo ao menos 1 filial, conferido com os PDFs.

## Cobertura
Cada REQ, RNF, RN e CE da spec aparece em exatamente um incremento: REQ-01 a REQ-18, RNF-01 a RNF-06, RN-01 a RN-09 e RN-11, e CE-01 a CE-15. A RN-10 registra os adiamentos e não tem incremento próprio.

O INC-02 antecipa o maior risco técnico (hCaptcha em navegador automatizado). Se a Receita ou a Caixa recusarem o navegador, o plano deve ser revisto antes de seguir.

## Revisões
- **2026-11-11 — Receita recusa navegador automatizado.** No Chromium do Playwright, o hCaptcha passa, mas a API da Receita responde `CaptchaFalhaValidacao` (código 023) em "Emitir" e em "Consultar". No navegador normal do servidor, o mesmo CNPJ funcionou. Decisão aprovada: criar o modo "navegador do servidor" (spec 1.2, RN-09) para a CND federal, sem tentar contornar a recusa. O TST continua automatizado.
- **2026-11-11 — Caixa bloqueia navegador automatizado.** Um único acesso de leitura em Chromium headless foi barrado pelo bot manager da Caixa (Radware/ShieldSquare). Sem novas tentativas automatizadas, para não marcar o IP da prefeitura. Teste de controle no navegador normal: o CRF é uma página, salva como PDF pela opção "Imprimir", com nome livre. Decisão aprovada (spec 1.3): CRF no modo navegador do servidor, PDF reconhecido pelo texto, e botão "O portal não emitiu" com campo opcional para a mensagem.
- **2026-11-11 — Certidão Única estadual adiada.** O SIDEB (`https://www4.fazenda.sp.gov.br/SIDEB/CertidaoNegativaDebitos`) aceita navegador automatizado na página inicial, mas "Emitir eCND" leva ao login gov.br, com hCaptcha. Decisão do servidor: deixar o item de fora por enquanto (spec 1.4, RN-10). O INC-07 depende só dos itens já existentes. O INC-09 (eproc) também envolve gov.br e deve ser reavaliado antes de começar.
- **2026-11-12 — e-SAJ aceita navegador automatizado.** Sem login e sem bloqueio de robôs. Em teste assistido, o programa preencheu o pedido (modelo de falências, pessoa jurídica, razão social, CNPJ e e-mail) e o servidor marcou a confirmação e enviou; o reCAPTCHA aceitou o Chromium do Playwright e o TJSP registrou o pedido. A falência segue no modo automatizado, como o TST (spec 1.5).
- **2026-11-12 — Certidão de falência baixada na hora.** A tela "Visualizar Certidão" do e-SAJ (número, data e CNPJ do pedido) não tem captcha. O pedido de teste já estava liberado, com "NADA CONSTAR". A pedido do servidor, o INC-08 passou a consultar logo após o pedido e a baixar o PDF quando liberado, e o e-mail passou a ficar salvo no computador (spec 1.6).
- **2026-11-12 — Complemento do eproc adiado.** `https://certidoes.tjsp.jus.br/` exige gov.br nível ouro ou prata para registrar o pedido; só a página de download (número do pedido e CPF/CNPJ) é aberta. Decisão do servidor: não mexer com gov.br agora (spec 1.7, RN-10). O INC-10 passa a depender do INC-08 e valida os quatro itens ativos. RN-01 e RNF-03 continuam valendo: a lista da tela segue a RN-01 sem os itens adiados, e o programa não guarda nada do gov.br.
- **2026-11-12 — Novas certidões a partir das minutas de edital.** Nas 10 minutas padrão lidas (`LICITACOES\Editais - 2026`), todas exigem CEIS, CNEP e Relação de Apenados do TCE-SP (consulta do pregoeiro) e quase todas exigem CND municipal (ISS) da sede. Decisão do servidor: incluir CEIS, CNEP, TCE-SP e CND de SJC (spec 1.8). Reconhecimento só de leitura:
  - o Portal da Transparência pede captcha (AWS WAF);
  - a Consulta Consolidada do TCU respondeu sem captcha e gerou o PDF, com CEIS, CNEP, inidôneos do TCU e CNIA do CNJ (o CNJ estava indisponível no teste);
  - o TCE-SP gera a certidão de apenados com Cloudflare Turnstile;
  - o sistema tributário de SJC migrou em 03/11/2026 para o iiTributário, com login por CPF, e a CND mobiliária ainda não foi liberada.

  Novos incrementos: INC-11 (TCU), INC-12 (TCE-SP) e INC-13 (SJC, adiado). O INC-10 passa para depois deles.
- **2026-11-12 — TCU sem navegador.** A página do TCU busca o resultado e o PDF numa API pública (`/api/rest/publico/certidoes/<CNPJ>`, com `Accept: application/pdf`). Pedir o PDF direto, sem Chromium, é mais simples e leve. Novo modo "consulta direta" na RN-09. No Windows da prefeitura, a consulta passa pelo proxy configurado no sistema, como a da BrasilAPI.
