# Verify report — 2026-11-06
Incremento: INC-01 — CNDT de ponta a ponta | Build report: 2026-11-06
Como rodei: script descartável que abre a janela pywebview real com `certidoes/ui/index.html` e a classe `Api`, e dirige a tela por JavaScript (preenche o campo, envia o formulário, clica em "Abrir PDF"). Sem variáveis de ambiente.
Suíte de testes: 36 passando (citado do build-report; os mesmos 36 passaram antes desta verificação)

## Fluxos dirigidos
| Item | Fluxo exercitado | Evidência (comando → saída) | Resultado |
|------|------------------|-----------------------------|-----------|
| REQ-01 | Tela: CNPJ válido com máscara é aceito e normalizado; campo vazio é recusado | Envio de `11.222.333/0001-81` → portal chamado com `11222333000181`; envio vazio → `CNPJ inválido.`, 0 chamadas ao portal | FUNCIONA |
| CE-01 | Tela: dígito verificador errado | Envio de `11.222.333/0001-82` → `{s: 'CNPJ inválido.', c: 'erro', abrir: False}`, 0 chamadas ao portal | FUNCIONA |
| REQ-06 | Tela → portal real do TST, em Chromium headless, sem resolver o captcha e com limite de 20 s | `Tempo esgotado aguardando a emissão da certidão.`, sem arquivo salvo. A mensagem indica que o campo do formulário real foi encontrado; sem ele, o erro seria "formulário mudou" | FUNCIONA |
| RN-05 | Mesmo fluxo: sem o servidor resolver o captcha, nada é emitido | Nenhuma certidão baixada (`arquivos= []`) | FUNCIONA |
| REQ-08 | PDF real emitido em 2026-11-06 → tela mostra o caminho e o botão; clique em "Abrir PDF" | `{s: 'CNDT obtida. Salva em: <PDF_REAL>', abrir: True}`; após o clique, `pgrep -af evince` → 1 processo com o arquivo. Conteúdo: `%PDF-`, `CERTIDÃO NEGATIVA DE DÉBITOS TRABALHISTAS`, `Validade: 05/05/2027` | FUNCIONA |
| RNF-01 | Janela pywebview e Chromium do Playwright no Linux | Mesma execução, encerrada com `exit=0` | FUNCIONA |
| RNF-02 | Consulta feita só pela tela, sem comandos durante o uso | Todos os fluxos acima usaram os elementos da tela | FUNCIONA |

## Falhas encontradas (para o /build)
Nenhuma.

## Não verificável de ponta a ponta
- **Resolução do captcha:** depende de uma pessoa (RN-05). Nesta rodada, a emissão bem-sucedida não foi repetida; a evidência é o PDF real emitido pelo servidor em 2026-11-06.
- **Abrir PDF:** confirmado pelo processo do visualizador com o arquivo, não por conferência visual do servidor.
- **CNPJ alfanumérico no portal real:** não há CNPJ alfanumérico real para testar.

---

# Verify report — 2026-11-11 (Windows)
Incremento: INC-01 — CNDT de ponta a ponta | Plataforma: Windows 11, Python 3.14.6, pywebview 6.2.1 (WebView2)
Suíte de testes: 39 passando (`.venv\Scripts\python -m pytest -q`)

## Mudanças desta rodada
- `certidoes/app.py`: "Abrir PDF" usa `os.startfile` no Windows e `xdg-open` no Linux.
- `certidoes/portais/tst.py`: falha ao abrir o Chromium vira `PortalErro` com mensagem clara, em vez de erro cru na tela.
- `tests/test_app.py`: caminho esperado independente do sistema; testes de abertura no Windows e no Linux.

## Fluxos dirigidos
| Item | Fluxo exercitado | Evidência | Resultado |
|------|------------------|-----------|-----------|
| RNF-01 | Janela pywebview real no Windows | Script descartável: `webview.guilib` = `winforms`, `window.pywebview.api.emitir` exposto | FUNCIONA |
| CE-01 | Tela: dígito verificador errado no Windows | Status `CNPJ inválido.` com classe `erro`, 0 chamadas ao portal | FUNCIONA |
| REQ-06 | Emissão real no portal do TST, captcha resolvido pelo servidor | PDF salvo às 15:09 em `Certidoes\<CNPJ>\cndt-20261111-150920.pdf` (86 KB, cabeçalho `%PDF-1.5`) | FUNCIONA |
| REQ-08 | Clique em "Abrir PDF" | O servidor confirmou que o PDF abriu no leitor padrão e é a CNDT | FUNCIONA |

## Revisão final — pontos menores não corrigidos
- Se a janela da tela for fechada durante uma consulta, o processo continua até o PDF ser emitido, o Chromium ser fechado ou o tempo-limite de 5 min esgotar (as chamadas do pywebview rodam em threads não daemon).
- "Abrir PDF" com o arquivo apagado no meio do caminho falha em silêncio.
- Se o campo do captcha do TST mudar de id, a mensagem será "Tempo esgotado" em vez de "formulário mudou".
