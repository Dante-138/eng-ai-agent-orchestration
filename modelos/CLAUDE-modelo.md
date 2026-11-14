@AGENTS.md

<!-- Modelo: copie para a raiz do projeto como CLAUDE.md (sem o sufixo -modelo). A linha acima importa as regras
comuns a todas as ferramentas; abaixo, só o que é do Claude Code. -->

## Claude Code

- Subagente só para leitura ampla (busca em muitos arquivos, logs longos) ou revisão com
  contexto limpo. Busca simples é direta, sem subagente.
- Tarefa nova sem relação com a anterior: `/clear`. Duas correções que não funcionaram:
  `/clear` e um brief melhor, não uma terceira tentativa.

# Compact instructions

Ao compactar, preserve: o brief (com as palavras do dono entre aspas), os arquivos tocados,
o estado de cada critério de pronto, os comandos rodados com o resultado e o que ainda não
foi verificado.
