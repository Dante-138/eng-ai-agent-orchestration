# Economia de cota

Resumo: a cota não estoura por pedir muito, e sim por manter sessões grandes abertas.
Cada mensagem reenvia o contexto inteiro, então o custo é, grosso modo, o tamanho da
sessão vezes o número de mensagens. Uma sessão de 300 mil tokens com 50 mensagens
reenvia dezenas de milhões de tokens (o cache reduz o preço, não elimina o consumo).

## Limites

- 150 mil tokens de contexto: aviso. Termine o passo atual, escreva a passagem e abra sessão nova.
- 300 mil tokens: o hook bloqueia o prompt. Passam sempre os comandos com `/` e os pedidos
  que citam "passagem", para dar para escrever a passagem mesmo bloqueado.
- Os números são ajustáveis pelas variáveis de ambiente `CTX_WARN` e `CTX_BLOCK`. Valor que
  não seja um inteiro positivo é ignorado e vale o padrão.

Por que o bloqueio fica: é a rede de segurança para a sessão esquecida aberta, em que o aviso
de 150 mil passou sem ação e cada mensagem seguinte reenvia tudo. Ele não trava o trabalho,
porque `/clear`, `/compact` e os pedidos de passagem passam. Para mudar, defina `CTX_BLOCK`
(por exemplo `600000`) no ambiente de quem abre o Claude Code [não verificado: que o hook herde
esse ambiente]; um valor bem alto o desliga na prática, e o aviso em `CTX_WARN` continua. Se
`CTX_WARN` for maior que `CTX_BLOCK`, o bloqueio vale mesmo assim.

## Os 6 hábitos

1. Sessão curta com passagem: ao fim de um bloco, `/passagem` grava o estado em até 30
   linhas ([modelo](../modelos/passagem.md)); a sessão nova começa dali e a antiga é arquivada.
2. Leitura em massa no `leitor`: varrer muitos arquivos ou logs vai para esse subagente
   (modelo barato, só leitura), que devolve só a conclusão. Não use para o que um grep resolve.
3. `revisor` antes de fechar: o subagente lê o diff contra o pedido e o critério de pronto
   antes de o PR sair do rascunho.
4. Brief com "pronto quando": `/brief <tarefa>` monta o texto para outra sessão
   ([modelo](../modelos/brief.md)); critério que um comando confere evita retrabalho.
5. Sonnet com esforço médio como padrão: modelo maior só quando travar, investigação longa
   só quando justificar. Veja o [manual](manual-agente-central.md) para a regra por papel.
6. Índice de memória enxuto: o `MEMORY.md` e os `CLAUDE.md` são lidos em toda sessão. Uma
   linha por item, detalhe em arquivo lido só quando o assunto aparece.

## Instalar

Precisa de Python 3.10 ou mais novo. No PowerShell ou no Git Bash, na raiz do repositório:

```bash
python scripts/instalar_claude.py
```

Copia para `~/.claude`: os subagentes `leitor` e `revisor`, as skills manuais `passagem` e
`brief`, e os hooks `ctx_guard.py` (evento `UserPromptSubmit`) e `bench_guard.py` (evento
`PreToolUse`, matcher `Bash|PowerShell`), que ele registra no `settings.json` sem apagar as
outras chaves. Rodar de novo não altera nada. Arquivo seu que difira do repositório é salvo
como `NOME.bak-AAAAMMDD-HHMMSS` antes de ser substituído.

Com `--sem-ctx-guard`, o `ctx_guard.py` é copiado mas não é registrado: serve para quem já
limita o contexto pelo `autoCompactWindow` do `settings.json` (a sessão compacta sozinha
perto do teto) [não verificado na documentação oficial]. Dois limites de contexto ao mesmo tempo confundem: escolha um.

## Trava de bancada (firmware)

O `bench_guard.py` pede confirmação antes de comando de shell que destrói o que uma
regravação não devolve: apagamento total ou da UICR (`nrfjprog --recover`, `--eraseall`,
`-e`, `west flash --recover/--erase`, `nrfutil device recover/erase`), J-Link Commander
(num chip protegido, "unsecure?" com sim apaga tudo), `pyocd erase`, `mass_erase`,
`erase_flash` e `write_flash --erase-all` do ESP32, `espefuse burn` (irreversível) e reset de
fábrica de gateway OpenWrt (`sysupgrade -n`, `firstboot`). Junta as linhas continuadas (`\` no
bash, crase no PowerShell) antes de procurar.

Também lê o script que o comando executa (`bash gravar.sh`, `./gravar.sh`, `pwsh -File
gravar.ps1`, um `.jlink` com `erase` ou `unlock`), um nível só. Só conta o script em posição
de execução: `git add gravar.sh` ou `cat gravar.sh` não o leem. Entende `~`, `$HOME` e o
caminho `/c/...` do Git Bash. Limites conhecidos: um `cd` antes, no mesmo comando, não muda a
pasta onde o script é procurado, e outras variáveis não são expandidas.

Ele não bloqueia: responde "ask" com o que se perde, e a decisão é de quem está na bancada.
Regras privadas (nome de ferramenta interna, nome de chave) ficam fora do repositório, em
`~/.claude/hooks/bench_guard.local.json`, no formato
`[{"pattern": "regex", "warning": "texto"}]`; arquivo ou regex inválidos são ignorados.

Para a `/passagem` definir onde gravar, crie a variável `CLAUDE_NOTAS` com uma pasta fora
do repositório e fora de pasta sincronizada; sem ela, a skill pergunta o caminho.

O hook falha aberto: qualquer erro nele é ignorado e o prompt segue normal.

## Fontes

- Hooks (`UserPromptSubmit`, `PreToolUse`, `transcript_path`, `decision: block`,
  `permissionDecision: ask`): <https://code.claude.com/docs/en/hooks>
- Subagentes e skills: <https://code.claude.com/docs/en/sub-agents> e
  <https://code.claude.com/docs/en/skills>
- Não conferi o formato exato do `usage` do transcript nem o nome do campo em versões
  novas do Claude Code `[não verificado]`: o hook ignora o que não reconhece.
