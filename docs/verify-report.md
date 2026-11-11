# Verify report — 2026-11-11
Incremento: INC-03 — CRF FGTS e certidão não emitida | Build report: 2026-11-11
Plataforma: Windows 11, Python 3.14.6, pywebview 6.2.1 (WebView2), Playwright 1.64.1, pypdf 7.0.1
Suíte de testes: 82 passando

## Fluxos dirigidos
| Item | Fluxo exercitado | Evidência | Resultado |
|------|------------------|-----------|-----------|
| RN-09 (Caixa) | Reconhecimento com o CRF real salvo pelo servidor no teste de controle | `e_crf_do_cnpj` → `True` para o CNPJ consultado, `False` para outro CNPJ | FUNCIONA |
| REQ-11, CE-10 | Janela real com item falso no navegador do servidor; mensagem colada no campo e clique em "O portal não emitiu" | Antes: "Aguardando servidor" com campo e botão visíveis. Depois: "Não emitida — Mensagem do portal, informada pelo servidor: Empregador nao cadastrado (teste).", campo oculto, "Consulta concluída." | FUNCIONA |
| REQ-05, RN-01 | Sequência real pelo servidor: CND (navegador), CRF (navegador, salvo por "Imprimir"), CNDT (Chromium) | `cnd-20261111-160210.pdf`, `crf-20261111-160237.pdf` (83 KB), `cndt-20261111-160251.pdf` em `Certidoes\<CNPJ>\`; o servidor abriu os três pela tela e confirmou que estão corretos | FUNCIONA |

## Falhas encontradas (para o /build)
Nenhuma.

## Não verificável de ponta a ponta
- "Não emitida" com empresa realmente irregular: depende de um CNPJ nessa situação; o fluxo foi verificado com portal falso em janela real.
- Resolução dos captchas: depende de uma pessoa (RN-05).
