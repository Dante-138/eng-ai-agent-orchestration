# Economia de cota

Resumo: a cota não estoura por pedir muito, e sim por manter sessões grandes abertas.
Cada mensagem reenvia o contexto inteiro, então o custo é, grosso modo, o tamanho da
sessão vezes o número de mensagens. Uma sessão de 300 mil tokens com 50 mensagens
reenvia dezenas de milhões de tokens (o cache reduz o preço, não elimina o consumo).

## Limites

- 150 mil tokens de contexto: aviso. Termine o passo atual, escreva a passagem e abra sessão nova.
- 300 mil tokens: o hook bloqueia o prompt. Passam sempre os comandos com `/` e os pedidos
  que citam "passagem", para dar para escrever a passagem mesmo bloqueado.
- Os números são ajustáveis pelas variáveis de ambiente `CTX_WARN` e `CTX_BLOCK`.

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
`brief`, e o hook `ctx_guard.py`, que ele registra no `settings.json` (evento
`UserPromptSubmit`) sem apagar as outras chaves. Rodar de novo não altera nada. Arquivo seu
que difira do repositório é salvo como `NOME.bak-AAAAMMDD-HHMMSS` antes de ser substituído.

Para a `/passagem` definir onde gravar, crie a variável `CLAUDE_NOTAS` com uma pasta fora
do repositório e fora de pasta sincronizada; sem ela, a skill pergunta o caminho.

O hook falha aberto: qualquer erro nele é ignorado e o prompt segue normal.

## Fontes

- Hooks (`UserPromptSubmit`, `transcript_path`, `decision: block`):
  <https://code.claude.com/docs/en/hooks>
- Subagentes e skills: <https://code.claude.com/docs/en/sub-agents> e
  <https://code.claude.com/docs/en/skills>
- Não conferi o formato exato do `usage` do transcript nem o nome do campo em versões
  novas do Claude Code `[não verificado]`: o hook ignora o que não reconhece.
