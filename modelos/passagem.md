# Modelo de passagem de sessão

Quando o contexto passa de 2/3 da janela, ou antes de uma fase nova, a sessão que sai
escreve esta passagem num arquivo, e a sessão que entra lê esse arquivo primeiro. A sessão
nova lê também o `git log` e o estado dos PRs; não herda o histórico.

Onde guardar: numa pasta de dados do projeto, fora do repositório, um arquivo por frente.
A memória do projeto aponta para ele, para a sessão nova achar sem procurar. Nunca dentro
de um commit.

```markdown
# Passagem: <frente> (<data e hora>)

## Objetivo

<uma frase>. Pedido do dono: "<palavras dele, literais>"

## Regras do repositório

- <as que mais pegam: destino do PR, idioma, quem dá o merge, o que nunca entra>

## PRs abertos

| PR   | Branch   | Estado                           | Falta         |
| ---- | -------- | -------------------------------- | ------------- |
| <nº> | <branch> | <rascunho, em revisão, aprovado> | <o que falta> |

## Como compilar e testar

- Build: <comando>, com a trava: <comando da trava>
- Teste no aparelho: <passos ou roteiro>

## Fila

1. <próximo item, na ordem; marque os já aprovados pelo dono>

## Decisões pendentes do dono

- <pergunta, com as opções>

## Decidido (não reabrir)

- <decisão> porque <motivo>

## Tentado e descartado

- <tentativa> falhou porque <evidência>

## Armadilhas conhecidas

- <comando que trava, ferramenta que engana, e o contorno>

## Deixado pela metade

- <o que estava em andamento, em que arquivo e em que ponto>

## Não verificado

- <o que ninguém conferiu ainda>

## Primeiro comando da sessão nova

<comando que mostra o estado em segundos, por exemplo git status e o check>
```

## Por que arquivo, e não "continue de onde parou"

- Sessão nova com um resumo bom custa menos que uma sessão gigante: cada mensagem reenvia
  o histórico inteiro, e o histórico longo também piora a atenção do modelo.
- "Tentado e descartado" impede a sessão nova de repetir o mesmo caminho.
- "Deixado pela metade" e "Não verificado" impedem que uma suposição vire fato na passagem
  seguinte.
