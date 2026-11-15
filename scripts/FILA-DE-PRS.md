# Fila de PRs

[`fila_de_prs.py`](fila_de_prs.py) lê pelo `gh` os PRs abertos de um dono e escreve um
Markdown na ordem de merge: link, estado do CI, revisão, conflito e de quem depende. Só lê;
nenhum comando altera PR. O merge continua sendo de quem é dono do repositório.

## Como usar

```sh
python scripts/fila_de_prs.py                          # na tela, todos os repos da conta do gh logado
python scripts/fila_de_prs.py --owner outro-dono       # outro dono
python scripts/fila_de_prs.py --repo dono/repo         # um repositório só
python scripts/fila_de_prs.py --saida fila.md          # grava num arquivo
```

Sem `--saida`, escreve na tela. Com `--saida ARQUIVO`, grava no arquivo e **sobrescreve** o que
houver nele: não aponte para uma fila mantida à mão.

Precisa do Python 3.10 ou mais novo e do `gh` logado. Só a biblioteca padrão: não instala
nada. Cada chamada ao `gh` tem tempo limite de 30 segundos.

## Como copiar para outro projeto

Copie `scripts/fila_de_prs.py`, `tests/test_fila_de_prs.py` e `pyproject.toml` (ruff e
pytest). Rode `python -m pytest` e `python -m ruff check .` antes de usar.

## "Depends on" na descrição do PR

O script lê uma linha como estas na descrição:

```text
Depends on: #12
Depends on: #12, outro-dono/outro-repo#7
```

`#N` é do mesmo repositório. Quem é dependência vem antes na fila. Dependência que não está
na fila (já mesclada ou de fora) não bloqueia a ordem e aparece como "fora da fila". Ciclo
entre PRs aparece à parte, com aviso.

## O que cada coluna quer dizer

| Coluna   | Valores                                                                                |
| -------- | -------------------------------------------------------------------------------------- |
| Pronto   | sim = fora do rascunho, CI verde, revisão aprovada, sem conflito, sem dependência na fila |
| CI       | verde, vermelho, rodando ou sem checks (lido do rollup de checks do PR, só a execução mais recente de cada check: as canceladas por concorrência ou refeitas não contam)                 |
| Revisão  | decisão formal do GitHub; sem ela, vale o **último** comentário com `Resultado:`: "aprovado" dá "aprovada (comentário)", "aprovado com pedido" dá "aprovada com pedido" (não é pronto), outro resultado dá "pediu mudança"; sem esse formato, "comentada" ou "sem revisão" |
| Conflito | sem conflito, conflito ou desconhecido (o GitHub ainda calcula)                         |

`Resultado: aprovado` é o formato da revisão publicada pelo Agente Revisor deste projeto. Se
a sua equipe publica a revisão de outro jeito, ajuste `_RESULTADO` no script.

## Limites

- A lista vem da busca do GitHub, com no máximo 100 PRs por consulta.
- "Sem checks" não é "verde": PR sem workflow rodando nunca aparece como pronto.
- Trabalho que depende de PR ainda não mesclado e está só em branch local não aparece:
  não há PR para o `gh` ler.
