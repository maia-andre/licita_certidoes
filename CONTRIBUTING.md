# Como contribuir

Obrigado pelo interesse! O Certidões do Fornecedor nasceu para a rotina de uma prefeitura, mas a dor é a mesma em qualquer órgão que contrata pela Lei 14.133/2021. Ele cresce com quem conhece os portais e as exigências da sua região.

Ao participar, você concorda em seguir o [Código de Conduta](CODE_OF_CONDUCT.md).

## Formas de contribuir

### Sem programar

| Contribuição | Onde |
|---|---|
| Portal da CND municipal do seu município | Formulário [CND municipal do meu município](https://github.com/maia-andre/licita_certidoes/issues/new?template=cnd-municipal.yml). Andamento na issue [#6](https://github.com/maia-andre/licita_certidoes/issues/6). |
| Portal da CND estadual do seu estado | Formulário [CND estadual do meu estado](https://github.com/maia-andre/licita_certidoes/issues/new?template=cnd-estadual.yml). Andamento na issue [#7](https://github.com/maia-andre/licita_certidoes/issues/7). |
| Exigência de habilitação que não está na tabela do README | Uma [issue](https://github.com/maia-andre/licita_certidoes/issues/new) com a exigência, o tipo de edital em que aparece e o portal que a emite. |
| Situação ou validade lida errado | Uma issue com o tipo de certidão, o que a tela mostrou e o que o PDF diz. |
| Erro do programa | Uma issue com os passos para reproduzir, o sistema operacional e a mensagem que apareceu. |

Para mapear um portal, não é preciso emitir a certidão: basta abrir o portal e descrever o que aparece.

**Cuidado com dados.** Não publique senhas, dados pessoais, nem PDFs ou CNPJs de empresas reais nas issues. Para mostrar um texto de certidão, troque o CNPJ e a razão social por dados fictícios.

### Com código

1. Comente na issue que você vai trabalhar nela, para evitar trabalho em dobro.
2. Faça um fork, crie um branch e prepare o ambiente (veja [Como rodar](README.md#como-rodar) no README).
3. Rode os testes antes de abrir o pull request:

   ```powershell
   .venv\Scripts\python -m pytest -q
   ```

4. Abra o pull request descrevendo o que mudou e como você testou. O GitHub Actions roda a suíte no Windows a cada pull request.

## Regras do projeto

A [especificação](docs/spec.md) é a referência. Estas regras valem para todo código novo:

- **Sem contornar captcha** (RN-05). Quem resolve é o servidor, num navegador visível. Nada de serviços de resolução, técnicas para esconder a automação ou insistir num portal que recusou o navegador automatizado.
- **Sem agregador pago** (RN-05). As certidões vêm direto dos portais oficiais.
- **Sem guardar senhas, tokens ou sessões** (RNF-03), inclusive do gov.br.
- **A decisão é do servidor** (RN-06). O programa não emite juízo de habilitação, inabilitação ou bloqueio de pagamento.
- **Na dúvida, "Conferir no PDF"** (RN-03 e RN-04). A leitura nunca presume situação nem calcula validade.
- **Testes sem portal real** (RNF-06). Os testes usam um portal falso local, em `tests/conftest.py`.

### Novo portal, passo a passo

1. **Reconhecimento só de leitura.** Abra o portal, veja se tem captcha ou login e como entrega o PDF, sem enviar nada.
2. **Escolha do modo de acesso** (RN-09):
   - **consulta direta**, se o portal é público e não tem captcha;
   - **automatizado**, se o portal aceita o Chromium do Playwright;
   - **navegador do servidor**, se o portal recusa navegador automatizado.

   Se o portal recusar a automação, mude de modo, sem tentar contornar a recusa.
3. **Teste assistido** com um CNPJ real, para obter o PDF verdadeiro e escrever a leitura a partir do texto dele.
4. **Testes automatizados** com o portal falso e com o texto real, trocando o CNPJ por um fictício.
5. **Documentação.** Atualize a spec, o plano e o README com o que o reconhecimento mostrou.

### Commits

Mensagens em português, no imperativo ou descritivas, com um prefixo:

- `feat:` funcionalidade nova;
- `fix:` correção;
- `docs:` documentação;
- `chore:` manutenção.

Exemplo: `feat: certidão de apenados do TCE-SP no navegador do servidor (INC-12)`.

## Licença das contribuições

O projeto é licenciado sob a [AGPL 3.0](LICENSE). Ao enviar uma contribuição, você concorda em licenciá-la nos mesmos termos.

## Contato

- Dúvidas e propostas: [issues](https://github.com/maia-andre/licita_certidoes/issues).
- Assuntos que não cabem numa issue pública: andre.maia@sjc.sp.gov.br.
- Vulnerabilidades: siga a [política de segurança](SECURITY.md).

O projeto é mantido por uma só pessoa, então as respostas podem levar alguns dias.
