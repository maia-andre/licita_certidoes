# Verify report — 2026-11-11
Incremento: INC-04 — Situação e validade na tela | Build report: 2026-11-11
Plataforma: Windows 11, Python 3.14.6, pywebview 6.2.1 (WebView2), pypdf 7.0.1
Suíte de testes: 112 passando

## Fluxos dirigidos
| Item | Fluxo exercitado | Evidência | Resultado |
|------|------------------|-----------|-----------|
| REQ-10, RN-03, RN-04 | Leitura dos 6 PDFs reais da pasta `Certidoes\<CNPJ>\` | CND: Positiva com efeitos de negativa, 06/02/2027 (×2); CNDT: Negativa, 10/05/2027 (×3); CRF: Regular, 08/12/2026. Confere com o texto impresso em cada PDF | FUNCIONA |
| REQ-10 | Janela real; portais falsos devolvendo cópias dos 3 PDFs reais da última sequência | Tabela: `CND federal / Obtida / Positiva com efeitos de negativa / 06/02/2027`, `CRF FGTS / Obtida / Regular / 08/12/2026`, `CNDT / Obtida / Negativa / 10/05/2027` | FUNCIONA |
| REQ-15 | Mesma janela | `#aviso` visível: "Este programa só reúne informações dos portais. A análise dos documentos e a decisão cabem ao servidor. Sempre confira o PDF." | FUNCIONA |

## Falhas encontradas (para o /build)
Nenhuma.

## Não verificável de ponta a ponta
- CE-11 (Vencida) e certidões positivas: sem PDF real nessas situações; cobertos pela suíte.
- A obtenção nos portais não mudou neste incremento e foi verificada no INC-03.
