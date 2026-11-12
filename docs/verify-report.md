# Verify report — 2026-11-12
Incremento: INC-08 — Pedido de falência no e-SAJ | Build report: 2026-11-12
Plataforma: Windows 11, Python 3.14.6, pywebview 6.2.1 (WebView2), Playwright 1.64.1
Suíte de testes: 218 passando

## Fluxos dirigidos
| Item | Fluxo exercitado | Evidência | Resultado |
|------|------------------|-----------|-----------|
| REQ-12 (pedido) | e-SAJ real, teste assistido, CNPJ 17.051.740/0001-50. O programa preencheu os campos; o servidor confirmou, passou pelo reCAPTCHA e enviou | "O seu pedido foi cadastrado com sucesso", pedido nº 101890915, de 12/11/2026, prazo máximo de 5 dias | FUNCIONA |
| REQ-12 (consulta) | `esaj._baixar_certidao`, o código do programa, contra o e-SAJ real, com o pedido 101890915 | PDF de 43.546 bytes, certidão nº 6197960; leitura: "Nada consta", emitida em 12/11/2026 | FUNCIONA |
| REQ-12 (tela) | Janela real com portais falsos | Falência em "Pedido feito: acompanhar", com número e e-mail; o portal recebeu a razão social da BrasilAPI e o e-mail | FUNCIONA |
| CE-12 | Mesma janela, com o e-mail vazio | "Informe um e-mail válido…", campo marcado, cursor no campo, nenhum portal chamado | FUNCIONA |

## Falhas encontradas (para o /build)
Nenhuma.

## Não verificável de ponta a ponta
- A sequência completa pela tela, com pedido e consulta reais juntos, ainda não foi feita: ela envia um novo pedido real ao TJSP.
- Certidão com apontamentos: nenhum exemplo real disponível.
