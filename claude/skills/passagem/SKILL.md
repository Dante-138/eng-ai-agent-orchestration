---
name: passagem
description: Escreve a passagem de sessão (PASSAGEM-<tema>.md, até 30 linhas) para abrir uma sessão nova sem herdar o histórico. Uso manual com /passagem.
disable-model-invocation: true
---

Escreva a passagem desta sessão para uma sessão nova continuar sem herdar o histórico.

1. Arquivo: `<pasta de notas>/PASSAGEM-<tema>.md`. A pasta de notas é o valor da variável de
   ambiente `CLAUDE_NOTAS`; se ela não existir, pergunte o caminho ao usuário uma vez. `<tema>` em
   minúsculas, com hífen, curto. Fora do repositório e fora de pasta sincronizada (nuvem); nunca
   dentro de um commit. Se já existir um com o mesmo tema, mostre ao usuário antes de sobrescrever.
2. Até 30 linhas, com estas seções, nesta ordem, e só o que não está no código nem no `git log`:
   - **Objetivo:** uma frase e o pedido do usuário entre aspas, literal.
   - **Estado:** branch, PRs abertos e o que falta em cada um.
   - **Fila:** próximos itens, na ordem.
   - **Decidido (não reabrir):** decisão e motivo.
   - **Tentado e descartado:** tentativa e a evidência de por que falhou.
   - **Armadilhas:** comando que trava ou ferramenta que engana, e o contorno.
   - **Deixado pela metade / Não verificado:** o que ficou em andamento ou sem conferir. Dado que falta
     vira lacuna declarada; nunca suposição escrita como fato.
   - **Primeiro comando da sessão nova:** o que mostra o estado em segundos.
3. Sem chave, senha, token nem identificador de dispositivo. Sem emojis e sem travessão.
4. Termine dizendo, em uma linha: o caminho do arquivo e "abra sessão nova, cole o caminho e arquive esta".
   Não continue o trabalho depois disso.
