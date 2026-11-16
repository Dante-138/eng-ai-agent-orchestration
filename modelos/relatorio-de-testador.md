# Modelo de relatório de testador

O testador é a sessão dona do dispositivo (celular, placa, emulador). Só ele instala e
roda no aparelho; os editores pedem o teste a ele. Publique como comentário no PR.

```markdown
## Teste no dispositivo: PR <link>, commit <hash curto>

Dispositivo: <modelo, sistema e versão>. Build: <artefato do PR ou build local, com hash>.

| Passo | Esperado | Obtido | Resultado |
| ----- | -------- | ------ | --------- |
| <1>   | <...>    | <...>  | passou    |
| <2>   | <...>    | <...>  | falhou    |

Evidência: <print com dado de demonstração, log curto, vídeo>

Falhas:

- <passo>: <o que aconteceu, como reproduzir, com que frequência>

Não testado:

- <o que ficou de fora e por quê>
```

## Regras

- Testa o commit que o PR aponta agora, não um build antigo. O hash vai no título.
- Dado de demonstração em print e log. Nada pessoal.
- Comando que fala com o aparelho vai com `timeout`: aparelho que dorme ou perde a conexão
  deixa o comando esperando para sempre e trava a sessão.
- Uma falha que só aparece às vezes é falha: diga a frequência ("2 em 10").
