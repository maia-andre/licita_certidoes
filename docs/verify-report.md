# Verify report — 2026-11-11
Incremento: INC-07 — Pular e repetir itens | Build report: 2026-11-11
Plataforma: Windows 11, Python 3.14.6, pywebview 6.2.1 (WebView2), Playwright 1.64.1
Suíte de testes: 150 passando

## Fluxos dirigidos
| Item | Fluxo exercitado | Evidência | Resultado |
|------|------------------|-----------|-----------|
| REQ-07 | Janela real; portal falso que espera o servidor; clique em "Pular" pela tela | Durante: "Item A: Aguardando servidor [Pular]". Depois: "Item A: Pulada [Repetir]", "Item B: Obtida" | FUNCIONA |
| REQ-14 | Mesma janela; clique em "Repetir" no item pulado | Status "Repetindo: Item A..."; ao final "Item A: Obtida", "Item B: Obtida"; item A rodou 2 vezes e o B, 1 | FUNCIONA |
| REQ-07 (TST) | Playwright real contra portal falso parado; pular 0,3 s depois de preencher o CNPJ | `Pulada` levantada em menos de 10 s (tempo-limite de 20 s); nenhum PDF | FUNCIONA |
| CE-08 | Playwright real: fechar a aba e fechar o Chromium inteiro durante a espera | "A janela do portal foi fechada antes da emissão." nos dois casos; nenhum PDF | FUNCIONA |

## Falhas encontradas (para o /build)
Nenhuma.

## Não verificável de ponta a ponta
- Pular nos portais reais: o mecanismo é o mesmo verificado acima; não repeti os captchas reais.
