# Spec: Obtenção assistida de certidões de fornecedores
Versão: 1.2 — 2026-11-11 | Status: aprovada
Alterações: 1.1 — Windows passa a ser a plataforma principal (RNF-01). 1.2 — Modo "navegador do servidor" para portais que recusam navegador automatizado (REQ-05, REQ-06, RNF-01, RN-09, CE-13).

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
- **REQ-11** — Quando o portal não emitir a certidão, a tela mostra o estado "Não emitida" e a mensagem informada pelo portal.
- **REQ-12** — Na falência pelo e-SAJ, o programa preenche o pedido com os dados conhecidos e o e-mail informado pelo servidor, aguarda o captcha e, enviado o pedido, marca o item como "Pedido feito: acompanhar".
- **REQ-13** — Na falência pelo eproc, o programa abre o portal para o servidor entrar com o gov.br e fazer o pedido. Quando o servidor confirmar na tela, o item fica como "Pedido feito: acompanhar".
- **REQ-14** — O servidor pode repetir apenas um item que tenha ficado em "Falha técnica", "Não emitida" ou "Pulada", sem refazer os demais.
- **REQ-15** — A tela mostra um aviso permanente de que o programa só reúne informações e de que a análise e a decisão cabem ao servidor.

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
  | 4 | Certidão Única estadual | SIDEB (Sefaz-SP/PGE-SP) | Fluxo principal |
  | 5 | Falência, concordatas e recuperações | e-SAJ/TJSP | Assistido (REQ-12) |
  | 6 | Complemento cível de primeiro grau | eproc/TJSP | Assistido (REQ-13) |

- **RN-02** — Estados de um item: "Aguardando", "Em andamento", "Aguardando servidor", "Obtida", "Não emitida", "Falha técnica", "Pulada" e "Pedido feito: acompanhar". "Falha técnica" e "Pulada" nunca indicam irregularidade da empresa.
- **RN-03** — Situação exibida: "Negativa", "Positiva com efeitos de negativa", "Positiva", "Regular" (CRF) ou "Conferir no PDF". O programa usa "Conferir no PDF" sempre que não identificar a situação com segurança e nunca a presume.
- **RN-04** — A validade exibida é a data impressa no documento. Sem data identificável, o programa mostra "Conferir no PDF", em vez de calcular um prazo padrão.
- **RN-05** — O programa não resolve nem contorna captcha, não usa serviço de terceiros para isso e não usa agregador pago.
- **RN-06** — O programa não emite juízo de habilitação, inabilitação ou bloqueio de pagamento. Base: arts. 63, III; 68; 69, II; 91, §4º; e 92, XVI, da Lei 14.133/2021.
- **RN-07** — A verificação de UF (REQ-04) usa o CNPJ escolhido pelo servidor. Se ele escolher uma filial, a tela avisa que a certidão de falência deve seguir o distribuidor da sede (art. 69, II).
- **RN-08** — A certidão estadual de SP segue a Resolução Conjunta SFP-PGE nº 1/2026, vigente desde 14/10/2026: o programa pede apenas a Certidão Única, e não as duas antigas.
- **RN-09** — Modos de acesso aos portais:
  - **Automatizado:** o programa abre um Chromium visível pelo Playwright, preenche os dados e recebe o PDF. Usado nos portais que aceitam navegador automatizado (TST).
  - **Navegador do servidor:** o programa abre o portal no navegador padrão do servidor, coloca o CNPJ na área de transferência e mostra o CNPJ na tela. O servidor cola o CNPJ, resolve o captcha e baixa o PDF. O programa vigia a pasta Downloads, reconhece o arquivo pelo nome que o portal usa e o move para a pasta do CNPJ. Usado nos portais que recusam navegador automatizado (Receita Federal: `CaptchaFalhaValidacao`, código 023, testado em 11/11/2026).
  - O programa nunca tenta esconder a automação de um portal (RN-05).

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

## Fora de escopo
- Destino das certidões, dossiê, anexação em processo e integração com sistemas existentes, incluindo o Gestor de Contratos Públicos
- CND municipal, CEIS, CNEP e outras consultas de sanções
- Empresas com CNPJ fora de SP
- Agregadores pagos, APIs do Serpro e do Conecta gov.br
- Leitura de caixa de e-mail e download automático da certidão de falência
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
- [ ] Nesses 10 CNPJs, os itens 5 e 6 terminam em "Pedido feito: acompanhar", exceto se pulados ou com falha informada.

## Perguntas em aberto
1. **Pasta dos PDFs:** esta spec adota uma pasta local por CNPJ apenas para o REQ-08 funcionar. O destino definitivo segue fora de escopo.
2. **Viabilidade dos portais:** TST aceita navegador automatizado; Receita recusa (RN-09). Falta testar Caixa, SIDEB, e-SAJ e eproc, inclusive quais campos o SIDEB e o e-SAJ pedem.
3. **eproc para terceiros:** não confirmei se o login gov.br do servidor permite pedir certidão de outro CNPJ. Se não permitir, o item 6 passa a ser apenas um aviso com o link.
4. **Prazo e custo no TJSP:** não encontrei prazo nem confirmei gratuidade dos itens 5 e 6.
