# Modelo de equipe: um agente central e papéis com nome

Como uma pessoa trabalha com várias sessões de agente sem ler o texto de todas. Copie para
as notas do projeto (ou para o `CLAUDE.md` do agente central) e ajuste os nomes.

## O agente central

O humano fala com um agente só, o **Agente Management**: ele recebe os pedidos, escreve os
briefs, distribui para as outras sessões, junta os relatórios e devolve um resumo. Funciona
como um diretor técnico: decide com o humano o que fazer e quem faz; não escreve o código
dos editores.

Por quê:

- **Um ponto de contato.** O humano lê um resumo, não o histórico de cinco sessões.
- **Contexto separado.** O Management guarda pedidos, decisões e a fila; cada editor guarda
  só a tarefa dele. É o padrão orquestrador e trabalhadores
  ([Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)).
- **Decisões num lugar.** Agentes em paralelo tomam decisões implícitas diferentes
  ([Cognition](https://cognition.com/blog/dont-build-multi-agents)); o Management escreve as
  decisões no brief de cada um.

Custo: é a sessão que mais acumula histórico, e cada mensagem reenvia o histórico inteiro
([custos](https://code.claude.com/docs/en/costs)). Por isso ele recebe relatório curto e
troca de sessão pela passagem quando o contexto pesa.

## Nomes de sessão

Padrão: `Agente <Papel> - <Projeto>` (hífen, sem travessão). O nome diz o papel e o projeto
na lista de sessões, sem abrir nenhuma.

| Nome                               | Papel                                                                    |
| ---------------------------------- | ------------------------------------------------------------------------ |
| `Agente Management`                | fala com o humano, distribui e resume; pode ganhar um nome próprio curto |
| `Agente Editor <Área> - <Projeto>` | implementa uma área, no próprio worktree; um editor por arquivo          |
| `Agente Revisor - <Projeto>`       | revisa os PRs e publica no PR; não escreveu o código                     |
| `Agente Testador - <Projeto>`      | dono do dispositivo; instala, roda o roteiro, publica o relatório        |
| `Agente Planejador - <Tema>`       | pesquisa e plano antes de uma frente nova; não implementa                |
| `Arquivo - <Projeto>`              | sessão parada que só guarda histórico; ninguém manda tarefa para ela     |

Quando uma sessão é substituída (passagem), a antiga vira `Arquivo - <...>` e avisa a quem
mandava mensagem para ela qual é a sessão nova.

## Relatório em 4 linhas

Os agentes mandam relatório ao Management só quando o estado muda: pronto, bloqueado ou
decisão do humano. Progresso não vira mensagem.

```text
ST: pronto|bloq|decisao
FEITO: <PR, commit ou arquivo, em uma linha>
PROX: <em uma linha>
PRECISA: <o que falta do humano ou do Management, ou "nada">
```

- Detalhe vai num arquivo (notas do projeto, comentário no PR) e a mensagem leva o caminho.
- Nada de código, log ou saída de comando na mensagem: é texto que o Management paga de
  novo a cada passo dali em diante.
- Revisão vai para o Agente Revisor, com o link do PR; para o Management, só bloqueio e
  decisão.

## Modelo e esforço por papel

Recomendação a partir da documentação, não medição; meça com `/usage`.

| Papel                | Modelo | Esforço | Sobe quando                                              |
| -------------------- | ------ | ------- | -------------------------------------------------------- |
| Agente Management    | Sonnet | médio   | decisão de rumo com o humano                             |
| Agente Planejador    | Opus   | alto    | é o papel de arquitetura                                 |
| Agente Editor        | Sonnet | médio   | migração de formato de dado, bug em código alheio        |
| Agente Revisor       | Sonnet | médio   | PR que muda formato de dado ou segurança                 |
| Agente Testador      | Sonnet | baixo   | falha intermitente que precisa de diagnóstico            |
| Subagente de leitura | Haiku  | baixo   | não sobe: tarefa que precisa de juízo não é de subagente |

Base: Sonnet resolve a maioria das tarefas por menos que Opus, Opus fica para arquitetura e
raciocínio de vários passos, Haiku para subagentes simples
([custos](https://code.claude.com/docs/en/costs)); esforço médio é o padrão e "pense
bastante" no prompt não muda o esforço
([modelos](https://code.claude.com/docs/en/model-config)).

## Limites de cota

- **Limite geral:** o humano escolhe a porcentagem do uso semanal de todos os modelos em
  que tudo para. Cada agente confere o uso entre itens de trabalho (no começo de um item
  novo e antes de um build), não em todo turno. Passou: termina o item atual, escreve a
  passagem, manda `ST: bloq` e para. O Management confere antes de abrir sessão nova.
- **Limite por modelo:** uma porcentagem menor do modelo mais caro, que avisa o Management
  para passar sessões a um modelo mais barato.

## Passagem de sessão

Quando o contexto passa de 2/3 da janela, ou antes de uma fase nova, a sessão escreve a
passagem ([`passagem.md`](passagem.md)) e uma sessão nova começa dela.
