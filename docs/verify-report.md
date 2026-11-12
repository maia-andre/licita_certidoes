# Verify report — 2026-11-12
Incremento: INC-11 — Sanções federais pela Consulta Consolidada do TCU | Build report: 2026-11-12
Plataforma: Windows 11, Python 3.14.6
Suíte de testes: 233 passando

## Fluxos dirigidos
| Item | Fluxo exercitado | Evidência | Resultado |
|------|------------------|-----------|-----------|
| REQ-16 | Item "sanções" do programa (`ITENS` e `Execucao`, como a tela) contra o TCU real, CNPJ 17.051.740/0001-50 | PDF `sancoes-tcu-20261112-114138.pdf` salvo; estado "Obtida"; validade "Não impressa (emitida em 12/11/2026)" | FUNCIONA |
| CE-14 | Mesma consulta: o CNJ respondeu "Sistema do CNJ está indisponível" | Situação "Conferir no PDF"; mensagem com TCU, CEIS e CNEP "Nada consta" e o CNJ indisponível, com o link de consulta manual | FUNCIONA |
| RN-11 | Reconhecimento do Portal da Transparência e do TCU | Transparência: página "Vamos confirmar que você é humano" (AWS WAF). TCU: resposta sem captcha | CONFIRMADO |

## Falhas encontradas (para o /build)
Nenhuma.

## Não verificável de ponta a ponta
- "Nada consta" nos quatro cadastros em documento real: o CNJ estava indisponível nas consultas de hoje. A leitura foi testada com o texto real, trocando só o resultado do CNJ.
- Cadastro com registro: nenhum exemplo real disponível.
- A janela pywebview não foi aberta neste incremento. A mudança na tela (mensagem junto com "Salva em") é de uma linha.
