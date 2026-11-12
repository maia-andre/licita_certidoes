# Verify report — 2026-11-12
Incremento: INC-12 — Apenados do TCE-SP | Build report: 2026-11-12
Plataforma: Windows 11, Python 3.14.6
Suíte de testes: 246 passando

## Fluxos dirigidos
| Item | Fluxo exercitado | Evidência | Resultado |
|------|------------------|-----------|-----------|
| CE-15 | Teste assistido no Chromium do Playwright (CNPJ 17.051.740/0001-50): o programa preencheu o CNPJ e clicou em "Gerar"; o servidor tentou a verificação | Duas tentativas. Console: "Erro no Turnstile: 600010"; o servidor viu a tela "Solução de problemas" da Cloudflare | RECUSA CONFIRMADA → modo navegador do servidor |
| REQ-17 | `tcesp.obter_certidao` real: portal aberto no navegador padrão do servidor, CNPJ na área de transferência | O servidor gerou e baixou a certidão; o programa a recolheu de Downloads como `apenados-tcesp-20261112-135825.pdf` (886 KB) | FUNCIONA |
| RN-03 / RN-04 | `leitura.ler` com `ler_apenados_tcesp` sobre esse PDF real | Situação "Nada consta"; validade 12/11/2026 | FUNCIONA |

## Falhas encontradas (para o /build)
Nenhuma.

## Não verificável de ponta a ponta
- Certidão com impedimentos: nenhum exemplo real disponível. A leitura foi testada com o modelo da página do portal.
- A janela pywebview não foi aberta neste incremento. O item usa os mesmos componentes de tela da Receita e da Caixa (instrução, CNPJ e "O portal não emitiu").
