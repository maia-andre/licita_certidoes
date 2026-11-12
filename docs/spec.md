# Spec: Obtenção assistida de certidões de fornecedores
Versão: 1.9 — 2026-11-12 | Status: aprovada
Alterações: 1.1 — Windows passa a ser a plataforma principal (RNF-01). 1.2 — Modo "navegador do servidor" para portais que recusam navegador automatizado (REQ-05, REQ-06, RNF-01, RN-09, CE-13). 1.3 — Caixa também no modo navegador do servidor; reconhecimento do PDF pelo conteúdo; "Não emitida" informada pelo servidor nesse modo (REQ-11, RN-09). 1.4 — Certidão Única estadual (item 4, RN-08, CE-07) adiada: o SIDEB exige login gov.br para emitir. 1.5 — e-SAJ testado: aceita navegador automatizado (RN-09); prazo do TJSP informado (pergunta 4). 1.6 — Falência: consulta imediata em "Visualizar Certidão" e download do PDF quando já liberado (REQ-12); situação "Nada consta" (RN-03); data de emissão no lugar da validade não impressa (RN-04); e-mail salvo no computador (REQ-12). 1.7 — Complemento do eproc (item 6, REQ-13) adiado: o pedido exige login gov.br nível ouro ou prata (RN-10). 1.8 — Entram no escopo as consultas de sanções exigidas em todas as minutas de edital da prefeitura (CEIS e CNEP, pela Consulta Consolidada do TCU, e Relação de Apenados do TCE-SP) e a CND municipal de São José dos Campos (itens 7 a 9, REQ-16 a REQ-18, RN-11, CE-14 e CE-15). A CND de SJC fica adiada enquanto o novo sistema tributário da prefeitura não a oferecer (RN-10). 1.9 — Apenados do TCE-SP (item 8) no modo navegador do servidor: o Turnstile recusou o Chromium automatizado (CE-15); a certidão imprime validade (RN-04).

## Objetivo
Em cada habilitação e a cada nota fiscal de contrato, servidores da Prefeitura de São José dos Campos (pregoeiros, gestores e fiscais) reúnem à mão, em portais diferentes, as certidões de regularidade do fornecedor. O projeto é um programa local em código aberto no qual o servidor digita um CNPJ, resolve apenas os captchas e logins que os portais exigirem e vê, em uma tela simples, a situação e a validade de cada certidão, com o PDF à mão. A primeira versão atende empresas com CNPJ de SP.

## Escopo

### Requisitos funcionais
- **REQ-01** — A tela permite digitar um CNPJ e valida formato e dígitos verificadores antes de qualquer consulta externa.
- **REQ-02** — Com um CNPJ válido, o programa consulta a BrasilAPI e mostra razão social, UF, situação cadastral e se o CNPJ é de matriz ou filial.
- **REQ-03** — Se o CNPJ for de filial, a tela mostra o CNPJ da matriz e pede que o servidor escolha qual dos dois consultar.
- **REQ-04** — Se a UF do CNPJ escolhido não for SP, o programa informa que a empresa não é atendida nesta versão e não abre nenhum portal.
- **REQ-05** — Para CNPJ atendido, o programa percorre em sequência os itens da RN-01. Conforme o modo de acesso do portal (RN-09), abre um Chromium visível e preenche os dados conhecidos, ou abre o portal no navegador do servidor com o CNPJ na área de transferência.
- **REQ-06** — Quando um portal exigir captcha, o programa aguarda o servidor resolvê-lo no navegador e continua sozinho depois disso. No modo "navegador do servidor", o programa continua quando o PDF do portal chega à pasta Downloads.
- **REQ-07** — O servidor pode pular o item em andamento, e o programa segue para o próximo.
- **REQ-08** — O programa guarda localmente o PDF de cada certidão obtida, e a tela oferece um botão para abri-lo.
- **REQ-09** — A tela mostra cada item da RN-01 com seu estado (RN-02), atualizado durante a execução.
- **REQ-10** — Para certidão obtida, o programa lê o texto do PDF e mostra a situação e a data de validade (RN-03 e RN-04).
- **REQ-11** — Quando o portal não emitir a certidão, a tela mostra o estado "Não emitida" e a mensagem informada pelo portal. No modo "navegador do servidor", o programa não vê o portal: a tela oferece o botão "O portal não emitiu" e um campo opcional para o servidor colar a mensagem do portal.
- **REQ-12** — Na falência pelo e-SAJ, o programa preenche o pedido com os dados conhecidos e o e-mail informado pelo servidor e aguarda o captcha. Enviado o pedido, consulta logo em "Visualizar Certidão" (número, data e CNPJ do pedido; sem captcha), em até 3 tentativas. Se a certidão já estiver liberada, guarda o PDF e o item fica "Obtida"; senão, o item fica "Pedido feito: acompanhar", com número, data e prazo do pedido. O e-mail fica salvo nas preferências do usuário no computador e volta preenchido na próxima consulta.
- **REQ-13** — *(Adiado; ver RN-10.)* Na falência pelo eproc, o programa abre o portal para o servidor entrar com o gov.br e fazer o pedido. Quando o servidor confirmar na tela, o item fica como "Pedido feito: acompanhar".
- **REQ-14** — O servidor pode repetir apenas um item que tenha ficado em "Falha técnica", "Não emitida" ou "Pulada", sem refazer os demais.
- **REQ-15** — A tela mostra um aviso permanente de que o programa só reúne informações e de que a análise e a decisão cabem ao servidor.
- **REQ-16** — No item 7, o programa consulta a Consulta Consolidada de Pessoa Jurídica do TCU pelo CNPJ (sem captcha), guarda o PDF e mostra o resultado de cada cadastro: Licitantes Inidôneos (TCU), CNIA (CNJ), CEIS e CNEP.
- **REQ-17** — No item 8, o programa abre no navegador do servidor o formulário da Certidão de Apenados de Impedimentos de Licitação/Contrato do TCE-SP, com o CNPJ na área de transferência (RN-09). O servidor gera a certidão, resolve o captcha (Cloudflare Turnstile) e baixa o PDF, que é guardado e lido como os demais.
- **REQ-18** — *(Adiado; ver RN-10.)* No item 9, se a sede da empresa for em São José dos Campos (município da BrasilAPI), o programa obtém a CND municipal (tributos mobiliários/ISS). Para empresa de outro município, o item mostra que a CND municipal deve ser obtida na prefeitura da sede, sem abrir portal.

### Requisitos não-funcionais
- **RNF-01** — Stack: Python, pywebview para a tela, Playwright com Chromium para os portais que aceitam navegador automatizado e o navegador padrão do servidor para os demais (RN-09). Plataforma principal: Windows, onde o programa será usado; Linux como alternativa.
- **RNF-02** — O uso do programa acontece pela tela, sem digitar comandos durante a consulta.
- **RNF-03** — O programa não guarda senhas, tokens ou sessões gov.br entre execuções.
- **RNF-04** — O código de cada portal fica isolado, para que a mudança em um portal não exija alterar os demais.
- **RNF-05** — A leitura de PDF funciona sem IA e sem enviar os documentos a serviços externos.
- **RNF-06** — A suíte automatizada roda sem acessar os portais reais, usando PDFs e respostas de exemplo.

## Regras de negócio
- **RN-01** — Itens da primeira versão, para CNPJ de SP:

  | # | Item | Portal | Modo |
  |---|---|---|---|
  | 1 | CND federal | Receita Federal | Fluxo principal |
  | 2 | CRF FGTS | Caixa | Fluxo principal |
  | 3 | CNDT | TST | Fluxo principal |
  | 4 | Certidão Única estadual | SIDEB (Sefaz-SP/PGE-SP) | **Adiado** (exige login gov.br; ver RN-10) |
  | 5 | Falência, concordatas e recuperações | e-SAJ/TJSP | Assistido (REQ-12) |
  | 6 | Complemento cível de primeiro grau | eproc/TJSP | **Adiado** (exige login gov.br; ver RN-10) |
  | 7 | Sanções: TCU, CNJ, CEIS e CNEP | Certidões APF (TCU) | Consulta direta (REQ-16) |
  | 8 | Apenados do TCE-SP | Sistema de Apenados (TCE-SP) | Navegador do servidor (REQ-17) |
  | 9 | CND municipal (ISS) de São José dos Campos | iiTributário (PMSJC) | **Adiado** (sistema em migração; ver RN-10) |

- **RN-02** — Estados de um item: "Aguardando", "Em andamento", "Aguardando servidor", "Obtida", "Não emitida", "Falha técnica", "Pulada" e "Pedido feito: acompanhar". "Falha técnica" e "Pulada" nunca indicam irregularidade da empresa.
- **RN-03** — Situação exibida: "Negativa", "Positiva com efeitos de negativa", "Positiva", "Regular" (CRF), "Nada consta" (falência, quando a certidão diz "verificou NADA CONSTAR"; sanções do TCU, quando todos os cadastros do documento dizem "Nada Consta"; apenados do TCE-SP, quando a certidão diz que "NÃO constam" impedimentos) ou "Conferir no PDF". O programa usa "Conferir no PDF" sempre que não identificar a situação com segurança e nunca a presume.
- **RN-04** — A validade exibida é a data impressa no documento. Sem data identificável, o programa mostra "Conferir no PDF", em vez de calcular um prazo padrão. A certidão de falência do e-SAJ não imprime validade: o programa mostra "Não impressa (emitida em dd/mm/aaaa)", com a data de emissão do documento, e não calcula prazo. O mesmo vale para a consulta de sanções do TCU (item 7), que vale para o momento da consulta. A certidão do TCE-SP (item 8) imprime "válido até" com a própria data da consulta; o programa mostra essa data, que aparece como "Vencida" a partir do dia seguinte.
- **RN-05** — O programa não resolve nem contorna captcha, não usa serviço de terceiros para isso e não usa agregador pago.
- **RN-06** — O programa não emite juízo de habilitação, inabilitação ou bloqueio de pagamento. Base: arts. 63, III; 68; 69, II; 91, §4º; e 92, XVI, da Lei 14.133/2021.
- **RN-07** — A verificação de UF (REQ-04) usa o CNPJ escolhido pelo servidor. Se ele escolher uma filial, a tela avisa que a certidão de falência deve seguir o distribuidor da sede (art. 69, II).
- **RN-08** — A certidão estadual de SP segue a Resolução Conjunta SFP-PGE nº 1/2026, vigente desde 14/10/2026: o programa pede apenas a Certidão Única, e não as duas antigas.
- **RN-09** — Modos de acesso aos portais:
  - **Automatizado:** o programa abre um Chromium visível pelo Playwright, preenche os dados e recebe o PDF. Usado nos portais que aceitam navegador automatizado: TST e e-SAJ. No e-SAJ, o reCAPTCHA aceitou o Chromium do Playwright em 12/11/2026; o programa preenche o pedido, e o servidor marca a confirmação, resolve o reCAPTCHA e envia. O pedido é reconhecido pela página de resultado ("pedido foi cadastrado com sucesso", com número e data).
  - **Navegador do servidor:** o programa abre o portal no navegador padrão do servidor, coloca o CNPJ na área de transferência e mostra o CNPJ na tela. O servidor cola o CNPJ, resolve o captcha e baixa o PDF. O programa vigia a pasta Downloads, reconhece o arquivo pelo nome que o portal usa ou pelo texto do PDF (tipo de certidão e CNPJ) e o move para a pasta do CNPJ. Usado nos portais que recusam navegador automatizado:
    - Receita Federal: `CaptchaFalhaValidacao`, código 023, testado em 11/11/2026. PDF reconhecido pelo nome `Certidao-<CNPJ>.pdf`.
    - Caixa: bloqueio de robôs (Radware/ShieldSquare) já no primeiro acesso, testado em 11/11/2026. O CRF é uma página que o servidor salva como PDF pela opção "Imprimir"; o PDF é reconhecido pelo texto "Certificado de Regularidade do FGTS" e pelo CNPJ. Não repetir acessos automatizados à Caixa: a página de bloqueio registra o IP da rede da prefeitura.
    - TCE-SP: o Turnstile falhou com o erro 600010 no Chromium do Playwright nas duas tentativas assistidas de 12/11/2026 e funcionou no navegador normal. O formulário abre direto na página "Gerar Certidão"; o PDF ("Certidão Apenados.pdf") é reconhecido pelo texto "Certidão de Apenados" e pelo CNPJ.
  - **Consulta direta:** sem navegador e sem ação do servidor, para portal público sem captcha que entrega o PDF por endereço próprio. Usado no TCU: o programa pede o PDF da Consulta Consolidada pelo CNPJ, pela mesma API pública que a página do TCU usa, e se identifica de forma genérica, sem dados do usuário. Testado em 12/11/2026.
  - O programa nunca tenta esconder a automação de um portal (RN-05).
- **RN-10** — Itens adiados, por exigirem login gov.br, que o programa não automatiza:
  - Certidão Única estadual (item 4): em 11/11/2026, o botão "Emitir eCND" do SIDEB levou ao login gov.br (com hCaptcha). RN-08 e CE-07 voltam a valer se o item for retomado.
  - Complemento do eproc (item 6): em 12/11/2026, `https://certidoes.tjsp.jus.br/` exigiu gov.br nível ouro ou prata para registrar o pedido. A página de download (`/download`, número do pedido e CPF/CNPJ) não pede login. REQ-13 volta a valer se o item for retomado.
  - CND municipal de SJC (item 9): em 12/11/2026, o formulário antigo (`servicos.sjc.sp.gov.br/CND`) redirecionava ao novo sistema iiTributário (`sjc.iitributario.com.br`), em migração desde 03/11/2026. O sistema novo exige cadastro e login por CPF, com reCAPTCHA, e a CND mobiliária ainda não constava entre os serviços liberados. Não é gov.br, mas segue a mesma regra: o programa não guarda senha nem sessão (RNF-03). REQ-18 volta a valer quando houver um caminho de emissão para CNPJ de terceiro. Pista do servidor: o iiTributário de outros municípios (por exemplo, São Sebastião) tem uma consulta pública que pede o CNPJ e o motivo do pedido e gera o PDF quando não há impedimentos. Retomar depois que a implantação em SJC estabilizar.
  - Enquanto adiados, o servidor obtém esses itens fora do programa.
- **RN-11** — Consultas de sanções: o item 7 usa a Consulta Consolidada do TCU, que reúne CEIS e CNEP (do Portal da Transparência) com os Licitantes Inidôneos do TCU e o CNIA do CNJ, porque o Portal da Transparência exige captcha (AWS WAF) e o TCU não. O item 8 usa a certidão do próprio TCE-SP, citada nas minutas como "Relação de Apenados".

## Casos extremos
- **CE-01** (afeta REQ-01) — CNPJ com dígito verificador inválido: mostrar erro e não fazer consulta externa.
- **CE-02** (afeta REQ-02) — BrasilAPI fora do ar ou sem o CNPJ: informar que não foi possível identificar a empresa, permitir nova tentativa e não abrir portais.
- **CE-03** (afeta REQ-02) — Situação cadastral diferente de ativa: mostrar a situação em destaque e permitir continuar.
- **CE-04** (afeta REQ-03, RN-07) — Filial em SP com matriz em outra UF: se a matriz for escolhida, aplicar o REQ-04; se a filial for escolhida, continuar e mostrar o aviso da RN-07.
- **CE-05** (afeta REQ-05, REQ-09) — Falha ou indisponibilidade em um portal: marcar "Falha técnica" e seguir para o próximo item.
- **CE-06** (afeta REQ-06) — Portal recusar o navegador automatizado ou o captcha não concluir: marcar "Falha técnica" e permitir repetir. O programa não tenta contornar a recusa.
- **CE-07** (afeta REQ-05) — SIDEB fora do horário informado (dias úteis, das 6h às 21h): marcar "Falha técnica" com essa explicação.
- **CE-08** (afeta REQ-05) — Servidor fechar o navegador durante a execução: marcar o item em andamento como "Falha técnica", sem encerrar a tela.
- **CE-09** (afeta REQ-10) — PDF sem texto legível ou com layout desconhecido: manter "Obtida", mostrar "Conferir no PDF" e deixar o arquivo disponível.
- **CE-10** (afeta REQ-11) — Empresa irregular em portal que não gera certidão: mostrar "Não emitida" com a mensagem do portal, nunca "Falha técnica".
- **CE-11** (afeta REQ-10) — Certidão emitida com data de validade anterior ao dia atual: mostrar a data e o aviso "Vencida".
- **CE-12** (afeta REQ-12) — E-mail vazio ou inválido no e-SAJ: não enviar o pedido e pedir correção.
- **CE-13** (afeta REQ-06, RN-09) — No modo "navegador do servidor", o PDF não chega à pasta Downloads dentro do tempo-limite (o servidor desistiu, o navegador pergunta onde salvar ou salvou em outra pasta): marcar "Falha técnica", informar a pasta vigiada e seguir para o próximo item.
- **CE-14** (afeta REQ-16) — Um cadastro da Consulta Consolidada indisponível (em 12/11/2026, o CNJ veio como "Sistema do CNJ está indisponível") ou com registro: manter "Obtida", mostrar "Conferir no PDF", nomear o cadastro e o resultado na mensagem e oferecer o link de consulta manual que o TCU informa.
- **CE-15** (afeta REQ-17) — O Turnstile do TCE-SP não concluir no Chromium automatizado: tratar como na CE-06 e, se a recusa se repetir em teste, passar o item ao modo "navegador do servidor" (RN-09), sem tentar contornar. Ocorreu em 12/11/2026 (erro 600010 nas duas tentativas): o item 8 usa o navegador do servidor.

## Fora de escopo
- Destino das certidões, dossiê, anexação em processo e integração com sistemas existentes, incluindo o Gestor de Contratos Públicos
- CND municipal de outros municípios além de São José dos Campos
- Outras consultas e documentos de habilitação (CADIN, Sicaf, inscrição estadual ou municipal, certidão simplificada da Junta, registro no CREA/CAU, alvarás)
- Empresas com CNPJ fora de SP
- Agregadores pagos, APIs do Serpro e do Conecta gov.br
- Leitura de caixa de e-mail e acompanhamento posterior de pedidos de falência ainda não liberados
- Certidão anterior reaproveitada, histórico, alertas de vencimento e monitoramento de contratos
- Processamento de vários CNPJs em lote
- Uso de IA para ler documentos
- Aplicação web, extensão de navegador e login de usuários
- Executável, distribuição na rede e teste com colegas (ficam para depois que as certidões funcionarem)
- Escolha de licença e publicação do código

## Definição de concluído
- [ ] Todos os testes automatizados passam, sem acesso aos portais reais.
- [ ] Dado um CNPJ inválido, a tela mostra erro e nenhuma consulta externa é feita.
- [ ] Dado um CNPJ fora de SP, a tela informa que não é atendido e nenhum portal é aberto.
- [ ] Dado um CNPJ de filial, a tela mostra a matriz e pede a escolha.
- [ ] Com 10 CNPJs reais de SP, incluindo ao menos 1 filial, cada item termina em estado da RN-02 coerente com o ocorrido no portal.
- [ ] Nesses 10 CNPJs, em toda certidão obtida, a situação e a validade na tela conferem com o PDF, ou a tela mostra "Conferir no PDF".
- [ ] Nesses 10 CNPJs, o item 5 termina em "Obtida" ou "Pedido feito: acompanhar", exceto se pulado ou com falha informada.

## Perguntas em aberto
1. **Pasta dos PDFs:** esta spec adota uma pasta local por CNPJ apenas para o REQ-08 funcionar. O destino definitivo segue fora de escopo.
2. **Viabilidade dos portais:** TST e e-SAJ aceitam navegador automatizado; o TCU dispensa navegador (consulta direta); Receita, Caixa e TCE-SP recusam (RN-09); o SIDEB e o eproc exigem gov.br e o iiTributário de SJC exige login por CPF (RN-10). No TCE-SP, a recusa veio do Turnstile (erro 600010, CE-15).
3. **eproc para terceiros:** não confirmei se o login gov.br do servidor permite pedir certidão de outro CNPJ. Se não permitir, o item 6 passa a ser apenas um aviso com o link. Pergunta suspensa enquanto o item estiver adiado (RN-10).
5. **Certidão Única estadual:** retomar se o SIDEB oferecer emissão sem login, ou se o login gov.br do servidor permitir emitir para CNPJ de terceiro (o servidor entraria no gov.br no próprio navegador, no modo da RN-09). Não testado em 11/11/2026.
4. **Prazo e custo no TJSP:** no item 5, o e-SAJ informa "Prazo máximo para liberação da Certidão 05 dias" e não mostrou cobrança no pedido de 12/11/2026. Falta o item 6.
6. **CND de SJC:** congelada enquanto o iiTributário é implantado (início em 09/11/2026). Ao retomar, procurar a consulta pública por CNPJ e motivo do pedido que o sistema tem em outros municípios.
