# Modelo de brief

O brief é tudo que a sessão sabe da tarefa além do repositório. Copie o bloco, preencha e
mande. Cada parte tem um motivo; não corte as quatro primeiras.

```markdown
## Tarefa

<uma frase com o resultado esperado>

Pedido do dono: "<palavras dele, literais, entre aspas>"

## Escopo

- <o que fazer, com arquivos ou áreas; verbos concretos: adicionar, corrigir, remover>

## Fora do escopo

- <o que não fazer, mesmo que pareça boa ideia>

## Pronto quando

- [ ] <critério verificável por comando, com o resultado esperado>
- [ ] Teste novo que falha sem a mudança
- [ ] `<npm run check>` verde e CI verde
- [ ] PR contra a main, em rascunho, com "O que muda", "Por que" e "Como testar"

## Já decidido

- <decisão> porque <motivo>
- Descartado: <alternativa> porque <motivo>

## Ler antes

- <arquivos, guias, issues: aponte, não copie>

## Restrições

- Seguir o AGENTS.md
- Arquivos que são seus: <lista>. Os outros têm outro editor.
- Modelo e esforço: <ex.: modelo médio, esforço médio>
- Pare e pergunte se: <ex.: precisar mexer em formato de dado salvo>

## Devolver

Link do PR primeiro. Depois: o que foi feito, o que foi rodado (comando e resultado) e o
que não foi verificado. Até 15 linhas.
```

## Por que cada parte

- **Palavras do dono entre aspas:** a paráfrase de quem repassa perde nuance; a citação
  deixa o agente ler a fonte.
- **Fora do escopo:** é a parte que mais evita retrabalho. Agente tende a "aproveitar e
  arrumar" o que está em volta.
- **Pronto quando:** critério que um comando confere. "Parece pronto" não é critério.
- **Já decidido:** agente que não sabe o que foi decidido toma a própria decisão, e duas
  sessões em paralelo tomam decisões diferentes.
- **Arquivos que são seus:** um editor por arquivo; é o que evita duas sessões
  sobrescrevendo uma à outra.
- **Devolver curto:** o relatório volta para o contexto de quem orquestra e é pago de novo
  a cada mensagem dali em diante.
