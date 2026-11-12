# Verify report — 2026-11-12
Incremento: INC-15 — Tela revisada e capa da consulta | Build report: 2026-11-12
Plataforma: Windows 11, Python 3.14.6
Suíte de testes: 283 passando

## Fluxos dirigidos
| Item | Fluxo exercitado | Evidência | Resultado |
|------|------------------|-----------|-----------|
| REQ-09 / REQ-21 | Tela nova com os estados reais de uma consulta da validação (empresa de outra UF), num navegador de teste com a API simulada | Capturas com o item da Caixa no cartão "Sua vez", a linha realçada, o progresso "2 de 7", as etiquetas e o resumo final "5 obtidas · 1 não emitida · 1 não se aplica" | FUNCIONA |
| REQ-09 | Tela nova na janela real do programa (pywebview e WebView2) | Janela aberta para o servidor | FUNCIONA |
| REQ-20 | Capa gerada com os PDFs reais da mesma empresa | PDF de 2 páginas, com resumo e anexo; o SHA-256 da CNDT na capa é igual ao calculado pelo `Get-FileHash` do Windows | FUNCIONA |
| REQ-08 / REQ-20 / REQ-21 | Consulta completa feita pelo servidor na janela real, com a tela nova (empresa de SP, matriz) | 6 certidões e a capa na subpasta `<CNPJ>/2026-11-12 17h55/`; a falência foi pulada pelo servidor e aparece como "Pulada" na capa; todos os horários preenchidos; os SHA-256 do anexo conferem com todos os PDFs da pasta | FUNCIONA |

## Falhas encontradas (para o /build)
Nenhuma.

## Não verificável de ponta a ponta
Nada pendente neste incremento.

O relatório da validação com 10 CNPJs reais (INC-10) está no histórico do repositório, no commit d8d21ef.
