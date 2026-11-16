---
name: brief
description: Monta o brief de uma tarefa para outra sessão ou subagente (escopo, fora do escopo, pronto quando, já decidido). Uso manual com /brief <tarefa>.
disable-model-invocation: true
---

Monte o brief da tarefa que o usuário descreveu, para outra sessão ou subagente executar sem o histórico desta.
O brief é tudo que o executor sabe além do repositório; precisa bastar sozinho.

Saída: um único bloco de texto, pronto para colar, até 30 linhas, nesta ordem:

- **Tarefa:** uma frase com o resultado esperado. Pedido do usuário entre aspas, literal.
- **Escopo:** o que fazer, com arquivos ou áreas e verbos concretos.
- **Fora do escopo:** o que não fazer, mesmo que pareça boa ideia.
- **Pronto quando:** critérios que um comando confere, com o resultado esperado. "Parece pronto" não vale.
- **Já decidido:** decisão e motivo; alternativa descartada e motivo.
- **Ler antes:** arquivos e guias, apontados e não copiados.
- **Restrições:** arquivos que são do executor (um editor por arquivo), modelo e esforço (padrão Sonnet
  médio), e "pare e pergunte se: ...".
- **Devolver:** link do PR ou caminho do arquivo primeiro, depois feito, rodado (comando e resultado) e não
  verificado, em até 15 linhas.

Regras: o que o código ou o repositório responde, descubra lendo em vez de perguntar. Se faltar uma
decisão que muda o escopo, faça no máximo uma pergunta ao usuário antes de montar. Não invente critério
nem decisão; o que faltar vira "A decidir". Só monte o texto: não abra sessão nem dispare subagente.
Sem emojis e sem travessão.
