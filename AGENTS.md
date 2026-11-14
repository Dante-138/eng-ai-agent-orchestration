# Agentes neste repositório

Regras para qualquer agente que edite este repositório. O Claude Code lê este arquivo pelo
`CLAUDE.md` (`@AGENTS.md`).

## O repositório

- Público. Nada de empresa, cliente, colega, produto ou sistema interno de ninguém, nem
  como exemplo. Lição de caso real entra contada de forma genérica.
- Documentação em português, sem emoji e sem travessão (use hífen, vírgula, dois-pontos
  ou parêntese). Código, commits e títulos de PR em inglês.
- Toda prática citada traz a fonte (link). O que não foi conferido na fonte leva
  `[não verificado]`. Nada de número, flag ou campo de configuração tirado da memória.

## Branch, commit e PR

- Branch novo a partir da `main` atualizada. Um PR por assunto, pequeno.
- Todo PR aponta para a `main`, em rascunho até a revisão de outra sessão estar publicada
  no PR. Quem escreveu não aprova. O merge é do dono.
- Conventional Commits em inglês, assunto com até 72 caracteres, sem ponto final, sem
  coautoria e sem assinatura de ferramenta.
- Título e descrição do PR viram a mensagem do commit na `main` (squash): escreva a
  descrição como mensagem final.

## Antes do push

- `npm run check` verde (o hook `pre-push` roda). Mexeu em workflow: `npm run lint:actions`
  (precisa do Docker).
- Hash de action sai da fonte (`gh api`), nunca da memória.
