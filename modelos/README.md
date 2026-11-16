# Modelos

Arquivos prontos para copiar num projeto novo ou numa tarefa nova. Troque o que estiver
entre `<>` e apague o que não se aplica.

| Modelo                                                 | Vai para                          | Quando usar                                                                                |
| ------------------------------------------------------ | --------------------------------- | ------------------------------------------------------------------------------------------ |
| [`AGENTS-modelo.md`](AGENTS-modelo.md)                 | raiz do projeto, como `AGENTS.md` | sempre: regras que todo agente segue, de qualquer ferramenta                               |
| [`CLAUDE-modelo.md`](CLAUDE-modelo.md)                 | raiz do projeto, como `CLAUDE.md` | projeto usado com o Claude Code: importa o `AGENTS.md`                                     |
| [`brief.md`](brief.md)                                 | mensagem para a sessão            | toda tarefa entregue a uma sessão de agente                                                |
| [`pedido-de-revisao.md`](pedido-de-revisao.md)         | mensagem para a sessão revisora   | todo PR antes de sair do rascunho                                                          |
| [`revisao.md`](revisao.md)                             | lido pela sessão revisora         | checklist da revisão                                                                       |
| [`passagem.md`](passagem.md)                           | arquivo fora do repositório       | contexto pesado: a sessão nova começa daqui, não do histórico                              |
| [`relatorio-de-testador.md`](relatorio-de-testador.md) | comentário no PR                  | teste no dispositivo real                                                                  |
| [`agentes/revisor.md`](agentes/revisor.md)             | `.claude/agents/revisor.md`       | subagente revisor só de leitura: lê o diff, mas não roda teste (vai para "Não verifiquei") |
| [`equipe.md`](equipe.md)                               | notas do projeto                  | agente central, nomes de sessão, relatório em 4 linhas, modelo por papel, limites de cota  |

Regras de uso:

- Copie e corte. Modelo comprido demais custa contexto em toda tarefa; o que não se aplica
  ao projeto sai.
- Os dois modelos têm o sufixo `-modelo` para o Claude Code não carregá-los como regra
  quando uma sessão trabalha nesta pasta. No projeto, viram `AGENTS.md` e `CLAUDE.md`.
- O `AGENTS.md` e o `CLAUDE.md` ficam curtos (a documentação do Claude Code recomenda menos
  de 200 linhas por arquivo de memória). Procedimento longo vira skill ou guia, lido só
  quando precisa.
- Nada de prompt de terceiro copiado às cegas: leia, reduza ao necessário e teste num
  repositório descartável antes.
