# Verify report — 2026-11-12
Incremento: INC-10 — Validação com 10 CNPJs reais (e INC-14) | Build report: 2026-11-12
Plataforma: Windows 11, Python 3.14.6, janela real do programa (pywebview)
Suíte de testes: 268 passando

## Como foi feita
- **Amostra:** 10 CNPJs reais informados pelo servidor:
  - 2 filiais, uma delas baixada;
  - 1 empresa de outra UF (RJ, em liquidação extrajudicial);
  - 2 entes públicos;
  - 5 empresas de SP.
- **Execução:** o servidor usou a janela real do programa, em três blocos. Um registro local guardou o estado que a tela recebeu em cada item.
- **Conferência:** cada PDF salvo foi lido de novo e comparado com o que a tela mostrou.
- **Anonimização:** as empresas aparecem como "Empresa 1" a "Empresa 10". CNPJs, razões sociais e PDFs ficaram só no computador do servidor.

## Resultado por empresa (estado final de cada item)
Legenda: NC = Nada consta; PEN = Positiva com efeitos de negativa; NE = Não emitida (mensagem do portal); NSA = Não se aplica; PF = Pedido feito: acompanhar.

| Empresa | Perfil | CND federal | CRF | CNDT | Falência | Sanções (TCU)* | Improbidade (CNJ)** | TCE-SP |
|---|---|---|---|---|---|---|---|---|
| 1 | SP, matriz | NE | NE | Negativa | PF (antes da correção) | NC | NC | NC |
| 2 | SP, filial baixada | NE (pedia a matriz) | NE | Negativa | NC | NC | NC | NC |
| 3 | RJ, matriz | NE | Regular | Positiva | NSA | NC | NC | NC |
| 4 | SP, matriz | PEN | Regular | Negativa | NC | NC | NC | NC |
| 5 | SP, matriz | PEN | Regular | Negativa | NC | NC | NC | NC |
| 6 | SP, filial ativa | Pulada (pedia a matriz) | Regular | Negativa | NC | NC | NC | NC |
| 7 | SP, matriz | PEN | Regular | Negativa | NC | NC | NC | NC |
| 8 | SP, matriz | PEN | Regular | Negativa | NC | NC | NC | NC |
| 9 | SP, ente público | PEN | Regular | Negativa | PF (em processamento) | NC | NC | NC |
| 10 | SP, ente público | PEN | Regular | Negativa | NC | NC | NC | NC |

\* Na hora da validação, as sanções apareceram como "Conferir no PDF" nos 10, porque o CNJ veio indisponível. Relidos com a regra corrigida (spec 1.12), os 10 PDFs dão "Nada consta".
\*\* Item criado depois dos blocos (INC-14) e rodado sozinho, por consulta direta, nos 10 CNPJs.

Em todos os itens obtidos, situação e validade na tela conferem com o PDF.

## Fluxos dirigidos
| Item | Fluxo exercitado | Evidência | Resultado |
|------|------------------|-----------|-----------|
| Definição de concluído | 10 CNPJs reais, com 2 filiais e 1 de outra UF, na janela real | Estado final coerente com o portal em todos os itens; nenhuma divergência entre tela e PDF | FUNCIONA |
| RN-03 | Situações reais variadas | 6 CND "Positiva com efeitos de negativa", 1 CNDT positiva, 9 CNDT negativas, 8 CRF regulares, NC em falência, TCE-SP e CNJ | FUNCIONA |
| REQ-04 / RN-01 | Empresa do RJ | Falência "Não se aplica" desde o início, com a indicação do tribunal da sede, sem abrir o e-SAJ | FUNCIONA |
| REQ-12 (correção) | Pedidos reais no e-SAJ depois da correção | 7 certidões baixadas sozinhas da janela nova; ente público "em processamento" ficou em "Pedido feito" | FUNCIONA |
| REQ-19 (INC-14) | Item do CNJ nos 10 CNPJs, sem ação do servidor | 10 PDFs "Certidão Negativa", situação "Nada consta" e data de emissão | FUNCIONA |
| RN-07 (correção) | CND federal de filial ativa de empresa cuja matriz tem certidão | Instrução com o CNPJ da matriz; PDF da matriz salvo na pasta da filial; "Positiva com efeitos de negativa" lida corretamente | FUNCIONA |
| RN-07 (correção) | CND federal de outra filial, com matriz sem certidão pela internet | Programa copiou o CNPJ da matriz; a Receita respondeu "erro 101" para a matriz | FUNCIONA (a recusa é do portal) |
| CE-03 | Filial baixada | Situação "BAIXADA" em destaque, consulta permitida | FUNCIONA |
| CE-10 | CND e CRF não emitidos | "Não emitida" com a mensagem colada pelo servidor | FUNCIONA |

## Falhas encontradas (corrigidas nesta rodada)
1. **Falência:** a certidão liberada abria em janela nova e não era reconhecida. Corrigido (REQ-12).
2. **Sanções:** o CNJ veio indisponível pelo TCU em 20 de 20 consultas, o que deixava o item 7 sempre em "Conferir no PDF". Corrigido com o item 10 e a nova regra do item 7 (RN-11).
3. **CND de filial:** a Receita recusou as duas filiais. Corrigido: agora a CND é pedida com o CNPJ da matriz (RN-07).

## Não verificável de ponta a ponta
- **CNJ com condenações:** nenhum caso real na amostra. O programa pede a certidão com registros e mostra "Conferir no PDF".
- **Mensagem "em processamento" do e-SAJ:** ainda não aparece na tela, que mostra a orientação geral de acompanhar o pedido.
