# Regras para agentes neste repositório

<!-- Modelo: copie para a raiz do projeto como AGENTS.md (sem o sufixo -modelo). Comentários HTML como este não
entram no contexto do Claude Code; servem de nota para quem mantém o arquivo. Mantenha
abaixo de 200 linhas: só o que o agente não descobre lendo o código. -->

## Antes de começar

- Leia o `README.md`, este arquivo e o brief. Pedido ambíguo: pergunte antes de escrever
  código.
- Faça só o que o brief pede. O que achar fora do escopo vira uma linha no relatório ou
  uma issue, nunca uma mudança escondida no mesmo diff.
- Nunca afirme algo sobre código que não abriu. Leia antes de responder.

## Branch, commit e PR

- Branch novo a partir da `main` atualizada. Um PR por assunto, pequeno.
- Todo PR aponta para a `main`. Nunca abra PR em cima de outro PR: mudança dependente
  espera o merge da anterior.
- PR em **rascunho** até a revisão de outra sessão estar publicada no PR. Quem escreveu
  não aprova o próprio trabalho.
- Nunca dê merge. O merge é do dono.
- Commits em Conventional Commits, em inglês, assunto com até 72 caracteres, sem ponto
  final, sem linha de coautoria e sem assinatura de ferramenta.
- Título e descrição do PR viram a mensagem do commit na `main` (squash). Escreva a
  descrição como mensagem final e sem nome de ninguém.
- Branch que outra sessão também usa: atualize com merge da `main`, nunca rebase seguido
  de force push.

## Trabalho em paralelo

- Um editor por arquivo. Se o brief não diz que o arquivo é seu, não edite.
- Cada sessão que edita trabalha no próprio worktree.
- Build, emulador ou dispositivo compartilhado: pegue a trava antes (`<comando da trava>`)
  e solte ao terminar.
- Permissão negada nesta sessão não se pede para outra sessão executar. Volte ao humano.

## Antes do push

- Rode `<npm run check>` e só faça push com ele verde. Não use `--no-verify`.
- Teste novo falha sem a mudança. Nunca apague, pule ou afrouxe teste para passar.

## Ferramentas: armadilhas conhecidas

- Comando que espera entrada trava a sessão: redirecione a entrada (`< /dev/null`) e use
  `timeout` em comando que fala com dispositivo ou rede.
- Busca com acento no Git Bash: classe como `[ií]` não casa caractere de dois bytes. Busque
  texto fixo (`grep -F`) ou use a ferramenta de busca do agente.
- Caminho com espaço ou `&`: sempre entre aspas.
- <armadilhas próprias do projeto, cada uma corrigida pelo menos duas vezes>

## Relatório final

1. Link do PR (em rascunho).
2. O que mudou, em linguagem simples.
3. O que foi rodado, com o comando e o resultado.
4. O que não foi verificado.

## Específico deste projeto

- Comandos: `<build>`, `<teste>`, `<um teste só>`, `<lint>`
- <pastas que enganam, decisões que não estão no código, quem dá o merge>
