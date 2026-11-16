# Modelo de pedido de revisão

Mande para uma sessão que não escreveu o código. Ela recebe o pedido original e o PR, não
a explicação de quem implementou: a explicação carrega o mesmo ponto cego que produziu o
erro.

```markdown
## Revisão do PR <link>

Pedido original do dono: "<palavras dele, literais>"

Critério de pronto do brief:

- <copiado do brief>

Revise com o checklist em <caminho>/revisao.md. Rode os testes e confira o comportamento
(app, artefato do PR ou dispositivo), não só o diff. Reporte o que afeta a correção e o
pedido; estilo que o portão não pega é `Nit:` e não bloqueia.

Publique a revisão como comentário no PR, em três blocos: confere, precisa mudar (arquivo,
linha e o que fazer) e não verifiquei. Não edite o código do PR.
```

## Por que assim

- Revisor mandado "achar problemas" sempre acha alguma coisa, e o PR ganha camadas e testes
  que ninguém pediu. Pedir o que afeta a correção e marcar polimento como `Nit:` mantém a
  revisão no que importa.
- A revisão publicada no PR fica com o PR. Revisão só no chat se perde com a sessão.
