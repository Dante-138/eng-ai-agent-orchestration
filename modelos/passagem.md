# Modelo de passagem de sessão

Quando o contexto fica pesado (sessão longa, várias frentes, respostas mais lentas ou
erradas), a sessão escreve esta passagem num arquivo e uma sessão nova começa dele. A
sessão nova lê o arquivo, o `git log` e o estado do PR; não herda o histórico.

Onde guardar: fora do repositório (pasta de notas da equipe de sessões), um arquivo por
frente, com a data no topo. Nunca dentro do commit.

```markdown
# Passagem: <frente> (<data e hora>)

## Objetivo

<uma frase>. Pedido do dono: "<palavras dele, literais>"

## Estado

- Branch: <nome>, último commit <hash curto>
- PR: <link> (<rascunho, em revisão, aprovado>)
- Check local: <comando> <verde ou vermelho, com a falha>

## Feito

- <item, com arquivo e commit>

## Falta

1. <próximo passo concreto, na ordem>

## Decidido (não reabrir)

- <decisão> porque <motivo>

## Tentado e descartado

- <tentativa> falhou porque <evidência>

## Não verificado

- <o que ninguém conferiu ainda>

## Primeiro comando da sessão nova

<comando que mostra o estado em segundos, por exemplo git status e o check>
```

## Por que arquivo, e não "continue de onde parou"

- Sessão nova com um resumo bom custa menos que uma sessão gigante: cada mensagem reenvia
  o histórico inteiro, e o histórico longo também piora a atenção do modelo.
- "Tentado e descartado" impede a sessão nova de repetir o mesmo caminho.
- "Não verificado" impede que uma suposição vire fato na passagem seguinte.
