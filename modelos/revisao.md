# Checklist de revisão

Para a sessão revisora, que não escreveu o código. O portão já conferiu formato, tipos e
testes; a revisão confere o que máquina não confere.

Padrão de aprovação: aprovar quando a mudança melhora a saúde geral do código, mesmo que
não esteja perfeita. Polimento leva o prefixo `Nit:` e não bloqueia. (Guia de revisão do
Google: <https://google.github.io/eng-practices/review/reviewer/standard.html>)

## Escopo

- [ ] Faz o que o pedido pediu, nas palavras do dono, e nada além.
- [ ] Um assunto só. Mudança sem relação vira outro PR.
- [ ] Aponta para a `main` e está em rascunho até esta revisão ser publicada.
- [ ] Só toca os arquivos que o brief deu a este editor.

## Comportamento

- [ ] Rodei os testes e conferi o comportamento (app, artefato ou dispositivo). Revisor sem
      Bash (subagente só de leitura) não marca este item: ele vai em "Não verifiquei".
- [ ] Casos de borda: vazio, um item, muitos itens, limite de data, texto longo, entrada
      inválida.
- [ ] Dado salvo antes da mudança continua abrindo (migração testada, se o formato mudou).

## Código e testes

- [ ] Não é mais complexo do que precisa: nada "para o futuro", nenhuma abstração para uso
      único.
- [ ] Teste novo cobre o comportamento novo e falharia sem a mudança.
- [ ] Nenhum teste apagado, pulado ou afrouxado; nenhuma solução feita só para passar no
      teste.
- [ ] Nenhuma regra desligada (lint, tipos, cobertura, proteção) sem motivo escrito no PR.

## Dados e texto

- [ ] Sem segredo, token, senha, dado pessoal ou dado real em código, teste, print ou texto.
- [ ] Sem nome de pessoa, empresa ou cliente em commit, título, descrição ou comentário.
- [ ] A descrição do PR está pronta para virar o commit na `main`.
- [ ] "Como testar" executável por quem não leu o código.

## Como devolver

Comentário no PR com três blocos: **confere**, **precisa mudar** (arquivo, linha e o que
fazer) e **não verifiquei**. Sem rodeio e sem elogio genérico.
