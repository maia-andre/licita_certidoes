# Política de segurança

## Versões atendidas

Só a versão mais recente recebe correções de segurança. As versões publicadas estão em [Releases](https://github.com/maia-andre/licita_certidoes/releases).

## Como relatar uma vulnerabilidade

**Não abra uma issue pública.** Use o canal privado do GitHub:

1. Na aba **Security** do repositório, clique em **Report a vulnerability**.
2. Descreva o problema, como reproduzi-lo e o impacto que você enxerga.

Se não puder usar o GitHub, escreva para andre.maia@sjc.sp.gov.br.

O relato é confirmado assim que possível. O projeto é mantido por uma só pessoa, sem equipe de plantão, então a correção pode levar alguns dias. Quem relatar recebe crédito na correção, se quiser.

## O que interessa relatar

O programa roda no computador do servidor, guarda PDFs localmente e acessa portais públicos. São especialmente relevantes:

- vazamento de dados para fora do computador (PDFs, CNPJs consultados, e-mail guardado nas preferências);
- execução de código a partir de um PDF, de uma página de portal ou de uma resposta de API;
- gravação de arquivos fora da pasta de certidões;
- qualquer caminho em que o programa guarde senha, token ou sessão do gov.br (proibido pela especificação, RNF-03).

## Fora do escopo

- Falhas dos portais consultados (Receita, Caixa, TST, TJSP, TCU, TCE-SP). Relate-as ao próprio órgão.
- Formas de contornar captchas: o programa não faz isso de propósito (RN-05).
