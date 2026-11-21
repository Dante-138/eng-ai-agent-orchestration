# Engenharia de Software: Agentes

Guia e modelos para orquestrar agentes de IA de código com resultado de engenheiro: tarefas
pequenas e verificáveis, revisão por quem não escreveu, o humano decidindo e dando o merge, e
pouca cota gasta.

Par do repositório
[eng-software-quality](https://github.com/Dante-138/eng-software-quality):
aquele cuida do portão que todo código passa; este cuida de como os agentes trabalham juntos
até chegar no portão.

- [Manual do agente central](guias/manual-agente-central.md): receber pedidos, distribuir, limitar
  o paralelismo, fila de decisões, cota, mensagens e passagem de sessão.
- [Economia de cota](guias/economia-de-cota.md): por que a cota estoura, limites de contexto,
  hábitos e o instalador dos hooks (contexto e trava de bancada), dos subagentes e das skills.
- [Modelos](modelos/README.md): arquivos prontos para copiar.
- [Fila de PRs](scripts/FILA-DE-PRS.md): script que lista os PRs abertos na ordem de merge.

Conteúdo em construção, um PR por vez.
