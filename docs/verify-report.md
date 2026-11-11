# Verify report — 2026-11-11
Incremento: INC-02 — CND federal e sequência de itens | Build report: 2026-11-11
Plataforma: Windows 11, Python 3.14.6, pywebview 6.2.1 (WebView2), Playwright 1.64.1
Suíte de testes: 66 passando

## Fluxos dirigidos
| Item | Fluxo exercitado | Evidência | Resultado |
|------|------------------|-----------|-----------|
| REQ-09 | Janela real com portais falsos (um lento, um com falha), dirigida por JavaScript | Tabela passou por `Em andamento` → `Aguardando servidor` (com instrução e CNPJ formatado) → `Obtida` com "Abrir PDF"; segundo item `Em andamento` → `Falha técnica`; status final "Consulta concluída." e botão reabilitado | FUNCIONA |
| CE-05 | Mesmo fluxo | Falha do segundo item não alterou o primeiro | FUNCIONA |
| REQ-05, RN-09 | Sequência real pelo servidor: CND federal no navegador normal, depois CNDT no Chromium | `Certidoes\<CNPJ>\cnd-20261111-154333.pdf` (78 KB, `%PDF-1.4`) e `cndt-20261111-154350.pdf` (86 KB, `%PDF-1.5`); o servidor confirmou os dois PDFs | FUNCIONA |
| CE-13 (parte) | PDF antigo da mesma empresa já em Downloads | O arquivo antigo (15:31) continuou em Downloads; o PDF guardado tem hash diferente, ou seja, veio do download novo, que saiu de Downloads | FUNCIONA |
| RN-09 | Recusa da Receita em navegador automatizado | `CaptchaFalhaValidacao` 023 em 4+ tentativas; mesma emissão funcionou no navegador normal | CONFIRMADO |

## Falhas encontradas (para o /build)
Nenhuma.

## Não verificável de ponta a ponta
- Resolução dos captchas: depende de uma pessoa (RN-05).
- Tempo esgotado sem download real (CE-13) e falha real de portal (CE-05): cobertos pela suíte, não provocados nos portais reais.
