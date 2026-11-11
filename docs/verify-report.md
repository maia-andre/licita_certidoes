# Verify report — 2026-11-11
Incremento: INC-05 — Identificação da empresa pela BrasilAPI | Build report: 2026-11-11
Plataforma: Windows 11, Python 3.14.6, pywebview 6.2.1 (WebView2)
Suíte de testes: 137 passando
Como rodei: janela real dirigida por JavaScript, com a **BrasilAPI real**; portais falsos devolvendo cópias dos PDFs reais.

## Fluxos dirigidos
| Item | Fluxo exercitado | Evidência | Resultado |
|------|------------------|-----------|-----------|
| REQ-02 | Matriz em SP (17.051.740/0001-50) | Cartão: razão social, "(matriz)", UF SP, situação ATIVA; botão "Emitir certidões"; sequência concluída com situação e validade | FUNCIONA |
| REQ-03, CE-04, RN-07 | Filial em SP com matriz no DF (Banco do Brasil, 00.000.000/0004-34) | Cartão: "(filial)", "Matriz 00.000.000/0001-91 — DF", "A matriz é de DF: não atendida nesta versão."; botões "Consultar a filial" (ativo) e "Consultar a matriz (fora de SP)" (desativado); ao escolher a filial, aviso "Você escolheu a filial. A certidão de falência deve seguir o distribuidor da sede (art. 69, II, da Lei 14.133/2021)." | FUNCIONA |
| REQ-04 | CNPJ do RS (11.222.333/0001-81) | "Empresa com CNPJ de RS: não atendida nesta versão, que cobre apenas CNPJ de SP."; nenhum botão de emissão | FUNCIONA |
| CE-02 | CNPJ válido inexistente (98.765.432/0001-98) | "CNPJ não encontrado na BrasilAPI.", cartão oculto | FUNCIONA |
| RN-03 (INC-04) | Portais falsos devolvendo PDFs de outra empresa na consulta da filial | Tabela mostrou "Conferir no PDF" em situação e validade | FUNCIONA |

## Falhas encontradas (para o /build)
Nenhuma.

## Não verificável de ponta a ponta
- CE-03 com empresa real não ativa: coberto pela suíte.
- BrasilAPI fora do ar: coberto pela suíte (falhas de rede simuladas).
