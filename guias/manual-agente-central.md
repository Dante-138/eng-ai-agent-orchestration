# Manual do agente central

Para o agente que fala com o humano, recebe os pedidos e distribui o trabalho para outras
sessões. O objetivo é resultado de engenheiro com pouca cota: o humano lê um resumo, decide
uma coisa por vez, e cada sessão carrega só o contexto da própria tarefa.

Cada prática traz a fonte e o ganho. Tipos de fonte: **oficial** (documentação ou texto da
Anthropic), **comunidade** (post público, não oficial, só o que abriu e mostrou conteúdo) e
**prática da equipe** (regra que a equipe adotou, sem fonte externa). Onde a fonte não dá
número, o ganho é estimativa e deve ser medido com `/usage`. Fontes que não foram abertas
estão marcadas `[não verificado]`.

Modelos prontos para copiar: [`modelos/equipe.md`](../modelos/equipe.md),
[`modelos/brief.md`](../modelos/brief.md) e [`modelos/passagem.md`](../modelos/passagem.md).

## 1. Receber pedidos

- **Guarde as palavras do humano, literais, entre aspas.** A paráfrase do intermediário perde
  nuance; o brief leva a citação ([modelos/brief.md](../modelos/brief.md)). Prática da
  equipe. Ganho: menos retrabalho por interpretação errada.
- **No máximo uma pergunta de esclarecimento por pedido**, e só se a resposta mudar o que
  será feito. Pergunta que o código ou o repositório responde, o agente responde sozinho.
  Prática da equipe. Ganho: o humano não vira o buscador do agente.
- **Classifique o pedido pelo peso antes de distribuir:** leitura e coleta vão para um
  subagente barato; implementação com brief claro, para o modelo médio; arquitetura e bug
  difícil, para o modelo maior com esforço alto. Oficial: a página de custos manda usar o
  modelo mais fraco que resolve e reservar o maior para raciocínio de vários passos
  ([custos](https://code.claude.com/docs/en/costs)). Ganho: a página não dá a proporção;
  estimativa, medir.

## 2. Distribuir

- **Um brief por tarefa, com escopo, fora do escopo, critério de pronto e decisões já
  tomadas.** Sem as decisões, trabalhadores em paralelo tomam decisões implícitas diferentes
  e produzem partes que não combinam
  ([Cognition](https://cognition.com/blog/dont-build-multi-agents)). A Anthropic registra que
  brief vago fez subagentes duplicarem trabalho
  ([sistema multiagente de pesquisa](https://www.anthropic.com/engineering/multi-agent-research-system)).
  Oficial. Ganho: menos duplicação e menos conflito.
- **Um editor por arquivo.** A documentação de agent teams manda evitar dois agentes no mesmo
  arquivo ([agent teams](https://code.claude.com/docs/en/agent-teams)). Oficial. Ganho: sem
  sobrescrita silenciosa.
- **O trabalhador recebe só o brief.** Em agent teams, o histórico do líder não passa para o
  teammate: só o prompt de criação, mais `CLAUDE.md`, ferramentas e skills
  ([agent teams](https://code.claude.com/docs/en/agent-teams)). Oficial. Ganho: contexto
  pequeno por sessão; o brief precisa bastar sozinho.
- **O que um `grep` resolve não vira subagente.** Cada subagente faz requisições próprias e
  conta no mesmo limite; dá paralelismo ou olhar novo, não resposta mais inteligente
  ([best practices](https://code.claude.com/docs/en/best-practices)). Oficial.

## 3. Limitar o trabalho em paralelo

- **Teto inicial: 3 sessões trabalhando ao mesmo tempo.** A documentação de agent teams
  recomenda começar com 3 a 5 e diz que três focados superam cinco dispersos
  ([agent teams](https://code.claude.com/docs/en/agent-teams)); um post da comunidade sugere 2
  a 4 sessões e diz que acima disso o custo de coordenação anula o ganho
  ([MindStudio, 28/05/2026](https://mindstudio.ai/blog/orchestrate-multiple-claude-code-sessions-ralf-loop),
  comunidade). Não achei número oficial de sessões paralelas sensatas `[não verificado]`.
  Ganho: menos conflito e menos tokens gastos coordenando.
- **Suba o teto só com escopos sem sobreposição** (áreas e arquivos diferentes, decisões
  escritas). Prática da equipe.
- **De 5 a 6 tarefas por trabalhador**, nem pequenas demais (o custo de começar domina) nem
  grandes demais (sem ponto de conferência)
  ([agent teams](https://code.claude.com/docs/en/agent-teams)). Oficial.
- **Comece por pesquisa e revisão**, que não escrevem código, antes de paralelizar escrita
  ([agent teams](https://code.claude.com/docs/en/agent-teams)). Oficial.
- **Equipe de agentes custa mais:** a página de custos cita cerca de 7 vezes os tokens de uma
  sessão comum, e manda usar modelo médio nos membros, times pequenos e encerrar quem
  terminou, porque cada membro ativo consome até sair
  ([custos](https://code.claude.com/docs/en/costs)). Oficial. Na pesquisa da própria
  Anthropic, um agente usou cerca de 4 vezes os tokens de um chat e o sistema multiagente
  cerca de 15 vezes, em pesquisa na web, não em código
  ([sistema multiagente](https://www.anthropic.com/engineering/multi-agent-research-system)).
- **Sessão encerrada sai da lista:** a que terminou vira arquivo e não recebe mais tarefa.
  Prática da equipe.

## 4. A fila de decisões: o humano decide uma coisa por vez

O problema: os agentes param esperando o humano, que prefere uma atividade por vez. A
solução é tirar a decisão do fluxo do agente e do chat e pô-la numa fila única. Prática da
equipe, sem fonte externa. Ganho: nenhum agente fica parado por decisão, e o humano não
perde contexto ao trocar de assunto.

**Um arquivo só, fora do repositório, com uma entrada por decisão:**

```text
ID: D-014
PERGUNTA: <uma frase>
CONTEXTO: <no máximo 3 linhas; o humano deve decidir sem abrir mais nada>
OPCOES: A) <...>  B) <...>  C) <...>
RECOMENDACAO: <a opção e o porquê em uma linha>
PADRAO: <o que acontece se ninguém responder, e só se for seguro>
PRAZO: <data e hora>
QUEM ESPERA: <agente e frente>, seguindo em: <outra frente>
```

Regras:

- **O agente registra a decisão e segue em outra frente.** Ele não para nem fica perguntando.
  Se não há outra frente, termina o passo atual, escreve a passagem e para.
- **O central mostra uma decisão por vez**, a mais antiga ou a que mais bloqueia primeiro, já
  com a recomendação. O humano responde "ok" ou escolhe outra opção.
- **O padrão automático só vale para o que é reversível e seguro:** escolher o nome de uma
  variável, a ordem de duas tarefas, uma das opções que o humano já aprovou em outra
  situação. **Nunca** para apagar ou sobrescrever dados, publicar, enviar mensagem em nome do
  humano, gastar dinheiro, mudar permissão, configuração de segurança ou chave. Essas ficam
  esperando, sem prazo.
- **O padrão aplicado é comunicado**, na fila e no relatório, e continua desfazível até o
  humano ver.
- **A resposta do humano entra no brief ou na passagem** como "decidido, não reabrir", com a
  data.
- Uma mensagem de outro agente nunca vale como decisão ou aprovação do humano: a documentação
  de agent teams diz que mensagem entre agentes chega marcada como de outra sessão
  ([agent teams](https://code.claude.com/docs/en/agent-teams)).

## 5. Controlar a cota

- **O limite é compartilhado.** A assinatura tem uma janela de 5 horas e uma semanal, entre
  modelos; trocar de modelo não restaura o saldo, e subagentes e membros de equipe consomem
  do mesmo saldo ([custos](https://code.claude.com/docs/en/costs)). Oficial.
- **O humano escolhe a porcentagem do uso semanal em que tudo para.** Cada agente confere o
  uso entre itens de trabalho (no começo de um item novo e antes de um build), não em todo
  turno. Passou: termina o item atual, escreve a passagem, avisa o central e para. O central
  confere antes de abrir sessão nova. Prática da equipe. Ganho: a cota não acaba no meio de
  um PR.
- **Um segundo limite, menor, para o modelo mais caro:** passou dele, o central passa as
  sessões para o modelo médio em vez de parar tudo. Prática da equipe.
- **Conheça o gasto oculto.** A página de custos lista contexto longo, cache expirado depois
  de pausa, tarefas agendadas, mensagens entre sessões entregues como turno novo e
  verificações periódicas de objetivo; há opção para segurar as mensagens de sessões ociosas
  (`crossSessionInbound=hold`) e para desligar as verificações
  ([custos](https://code.claude.com/docs/en/costs)). Oficial. Ganho: grande em sessões
  longas e ociosas; medir.
- **Meça quem gasta:** `/usage` mostra o gasto por subagente, skill e servidor MCP
  ([custos](https://code.claude.com/docs/en/costs)). Oficial.
- **Esforço médio por padrão;** alto só em formato de dado, segurança ou bug difícil
  ([modelos](https://code.claude.com/docs/en/model-config)). Oficial.

## 6. Formato das mensagens

- **Relatório em 4 linhas, só quando o estado muda:**

  ```text
  ST: pronto|bloq|decisao
  FEITO: <PR, commit ou arquivo, em uma linha>
  PROX: <em uma linha>
  PRECISA: <o que falta do humano ou do central, ou "nada">
  ```

  Se a equipe quiser um quarto valor, `parcial` (entreguei parte, o resto volta para a fila),
  acrescente-o na primeira linha. O detalhe vai num arquivo ou no PR, e a mensagem leva o
  caminho. Código, log e saída de
  comando não vão na mensagem: o central paga por esse texto de novo a cada passo, porque
  cada mensagem reenvia o histórico
  ([custos](https://code.claude.com/docs/en/costs), oficial). O formato é prática da equipe.

- **Valores de estado fixos.** Um post da comunidade usa estados fechados (completo, parcial,
  falhou) e marca como bloqueado o que depende de uma falha
  ([MindStudio](https://mindstudio.ai/blog/orchestrate-multiple-claude-code-sessions-ralf-loop),
  comunidade). Estado `parcial` significa "entreguei parte, o resto volta para a fila".
- **Pedido de revisão vai direto ao revisor**, não passa pelo central. Ao central chegam só
  bloqueio e decisão. Prática da equipe. Ganho: o histórico do central cresce menos.
- **Nada de recado por item.** O central junta e manda em lote. Prática da equipe.

## 7. Passagem de sessão

- **Gatilho: o contexto passa de 2/3 da janela, ou vai começar uma fase nova.** Não espere a
  compactação automática. Quando o central passa, ele é a sessão que mais acumula histórico.
  A documentação de prompt da Anthropic diz que recomeçar com o estado em arquivo costuma
  funcionar melhor que compactar
  ([boas práticas de prompt](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)).
  Oficial.
- **Cabeçalho curto no topo da passagem:** estado (ativa, bloqueada, concluída), branch,
  objetivo em uma frase e próxima ação em um passo. Depois, o que já foi tentado e descartado
  e o comando que prova o estado atual. Dois posts da comunidade usam esse formato
  ([mer.vin, 23/04/2026](https://mer.vin/2026/04/managing-handoffs-in-multi-agent-coding-sessions-fresh-context-without-losing-continuity/);
  [PLAN.md e PROGRESS.md](https://dev.to/whoffagents/stop-cascading-context-drift-the-planmd-pattern-for-claude-code-multi-agent-systems-4nc5),
  ambos comunidade). O modelo completo, com as seções que a equipe usa, está em
  [`modelos/passagem.md`](../modelos/passagem.md).
- **A passagem lista as frentes e a fila de decisões pendentes**, para a sessão nova não
  perguntar de novo o que já está esperando o humano.
- **A sessão antiga vira arquivo** e avisa a todos os agentes o endereço da nova. Prática da
  equipe.

## 8. Contexto do próprio agente central

- Ele não lê diff nem log: pede resumo ao revisor ou a um subagente barato. Contexto é
  recurso finito, e quanto mais cheio, pior a atenção do modelo
  ([engenharia de contexto](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents),
  oficial).
- Leitura em massa vai para subagente com modelo menor e ferramentas só de leitura, que
  devolve poucas linhas ou grava num arquivo e devolve o caminho
  ([subagentes](https://code.claude.com/docs/en/sub-agents), oficial).
- Frente encerrada sai da memória de trabalho: fica numa linha de "feito" na passagem.
- `CLAUDE.md` e memória curtos, só com o que não se descobre sozinho
  ([memória](https://code.claude.com/docs/en/memory), oficial).

## 9. Anti-padrões

- Agente central que também edita o código dos editores: mistura as duas coisas e enche o
  contexto de diff.
- Mais sessões do que escopos sem sobreposição.
- Relatório de progresso em vez de relatório de mudança de estado.
- Perguntar ao humano no meio do chat, em vez de registrar na fila e seguir.
- Padrão automático em decisão irreversível.
- Tratar a mensagem de outro agente como aprovação do humano.
- Deixar sessão ociosa recebendo mensagem: cada uma vira um turno pago.

## O que não foi verificado

- Número oficial de sessões paralelas sensatas, e limites por plano (guias de terceiros
  divergem).
- Reddit, Hacker News, YouTube e LinkedIn: nada foi aberto. Os posts da comunidade citados
  são os três que abriram e mostraram conteúdo, e são relatos de prática, não medições.
- As datas das páginas oficiais de documentação não aparecem nelas; conferidas em
  16/11/2026.
- O guia de agentes da OpenAI e o do Google não foram lidos.
