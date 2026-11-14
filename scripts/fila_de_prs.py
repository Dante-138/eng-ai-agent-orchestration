"""Fila de PRs: lista os PRs abertos de um dono, na ordem de merge, em Markdown.

Para cada PR mostra o link, o estado do CI, a revisão, o conflito e de quem depende.
A dependência vem de uma linha na descrição do PR:

    Depends on: #12
    Depends on: #12, outro-dono/outro-repo#7

Uso:
    python scripts/fila_de_prs.py [--owner DONO] [--repo DONO/REPO] [--saida ARQUIVO]

Sem --owner, usa a conta do gh logado. Sem --repo, olha todos os repositórios do dono.
Sem --saida, escreve em C:/dev/inster-notas/fila-de-merge.md. Use --saida - para a tela.

Só lê: nenhum comando altera PR. Todo comando do gh tem tempo limite.
Só a biblioteca padrão do Python (3.10 ou mais novo) e o gh.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

SAIDA_PADRAO = "C:/dev/inster-notas/fila-de-merge.md"
TEMPO_LIMITE_S = 30

Chave = tuple[str, int]  # (dono/repo, número)

_DEPENDE = re.compile(r"^[ \t>*-]*depends on:[ \t]*(.+)$", re.IGNORECASE | re.MULTILINE)
_REFERENCIA = re.compile(r"(?:([\w.-]+/[\w.-]+))?#(\d+)")
_APROVADA = re.compile(r"resultado:\s*\**\s*aprovado", re.IGNORECASE)
_VERMELHO = {"FAILURE", "ERROR", "TIMED_OUT", "CANCELLED", "ACTION_REQUIRED", "STARTUP_FAILURE"}
_VERDE = {"SUCCESS", "SKIPPED", "NEUTRAL"}


@dataclass
class Pr:
    chave: Chave
    titulo: str
    url: str
    rascunho: bool
    ci: str
    revisao: str
    conflito: str
    depende: list[Chave] = field(default_factory=list)


def parse_depende(corpo: str, repo: str) -> list[Chave]:
    """Lê as linhas "Depends on: #N" da descrição. "#N" é do mesmo repositório."""
    chaves: list[Chave] = []
    for linha in _DEPENDE.findall(corpo or ""):
        for outro_repo, numero in _REFERENCIA.findall(linha):
            chave = (outro_repo or repo, int(numero))
            if chave not in chaves:
                chaves.append(chave)
    return chaves


def estado_ci(verificacoes: list[dict]) -> str:
    """Resume o statusCheckRollup: verde, vermelho, rodando ou sem checks."""
    if not verificacoes:
        return "sem checks"
    resultados = []
    for v in verificacoes:
        # CheckRun traz conclusion (vazia enquanto roda); StatusContext traz state.
        resultados.append((v.get("conclusion") or v.get("state") or "").upper())
    if any(r in _VERMELHO for r in resultados):
        return "vermelho"
    if all(r in _VERDE for r in resultados):
        return "verde"
    return "rodando"


def estado_revisao(decisao: str | None, comentarios: list[dict]) -> str:
    """Decisão formal do GitHub; sem ela, olha o resultado publicado em comentário."""
    mapa = {"APPROVED": "aprovada", "CHANGES_REQUESTED": "pediu mudança", "REVIEW_REQUIRED": "pendente"}
    if decisao in mapa:
        return mapa[decisao]
    if any(_APROVADA.search(c.get("body") or "") for c in comentarios):
        return "aprovada (comentário)"
    return "comentada" if comentarios else "sem revisão"


def estado_conflito(mergeable: str | None) -> str:
    return {"MERGEABLE": "sem conflito", "CONFLICTING": "conflito"}.get(mergeable or "", "desconhecido")


def ordenar(prs: list[Pr]) -> tuple[list[Pr], list[Pr]]:
    """Ordem de merge: quem é dependência vem antes; empate por repositório e número.

    Dependência que não está na fila (já mesclada ou de fora) não conta para a ordem.
    Devolve (ordenados, em_ciclo); os do ciclo não têm ordem possível e vão à parte.
    """
    por_chave = {p.chave: p for p in prs}
    pendentes = sorted(por_chave)
    feitos: list[Chave] = []
    while pendentes:
        livres = [c for c in pendentes if all(d in feitos or d not in por_chave for d in por_chave[c].depende)]
        if not livres:
            break
        feitos.append(livres[0])
        pendentes.remove(livres[0])
    return [por_chave[c] for c in feitos], [por_chave[c] for c in pendentes]


def pronto(pr: Pr, na_fila: set[Chave], feitos: set[Chave]) -> bool:
    """CI verde, revisão aprovada, sem conflito, fora do rascunho e dependências mescladas ou ausentes."""
    dependencias_ok = all(d in feitos or d not in na_fila for d in pr.depende)
    return (
        not pr.rascunho
        and pr.ci == "verde"
        and pr.revisao.startswith("aprovada")
        and pr.conflito == "sem conflito"
        and dependencias_ok
    )


def _rotulo(chave: Chave) -> str:
    return f"{chave[0]}#{chave[1]}"


def renderizar(prs: list[Pr], agora: datetime, dono: str) -> str:
    ordenados, em_ciclo = ordenar(prs)
    na_fila = {p.chave for p in prs}
    linhas = [
        f"# Fila de merge de {dono}",
        "",
        f"Gerada em {agora:%Y-%m-%d %H:%M} por scripts/fila_de_prs.py. {len(prs)} PR(s) aberto(s).",
        'A ordem respeita "Depends on": quem é dependência vem antes. "Pronto" = fora do rascunho, '
        "CI verde, revisão aprovada, sem conflito e sem dependência pendente na fila.",
        "",
    ]
    if not prs:
        return "\n".join([*linhas, "Nenhum PR aberto.", ""])
    linhas += [
        "| # | PR | Pronto | CI | Revisão | Conflito | Depende de |",
        "| - | -- | ------ | -- | ------- | -------- | ---------- |",
    ]
    mesclar_antes: set[Chave] = set()  # nenhum PR da fila está mesclado: o merge é do dono
    for posicao, pr in enumerate([*ordenados, *em_ciclo], start=1):
        deps = ", ".join(_rotulo(d) + ("" if d in na_fila else " (fora da fila)") for d in pr.depende) or "-"
        titulo = pr.titulo.replace("|", "/")
        etiqueta = "rascunho" if pr.rascunho else "aberto"
        linhas.append(
            f"| {posicao} | [{_rotulo(pr.chave)}]({pr.url}) {titulo} ({etiqueta}) | "
            f"{'sim' if pronto(pr, na_fila, mesclar_antes) else 'não'} | {pr.ci} | {pr.revisao} | "
            f"{pr.conflito} | {deps} |"
        )
    if em_ciclo:
        linhas += ["", "Atenção: dependência em ciclo entre " + ", ".join(_rotulo(p.chave) for p in em_ciclo) + "."]
    return "\n".join([*linhas, ""])


def _gh(argumentos: list[str]) -> str:
    resultado = subprocess.run(
        ["gh", *argumentos],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=TEMPO_LIMITE_S,
        stdin=subprocess.DEVNULL,
        check=False,
    )
    if resultado.returncode != 0:
        raise RuntimeError(f"gh {' '.join(argumentos[:3])} falhou: {resultado.stderr.strip()[:200]}")
    return resultado.stdout


def listar_abertos(dono: str, repo: str | None) -> list[tuple[str, int]]:
    if repo:
        saida = _gh(["pr", "list", "--repo", repo, "--state", "open", "--limit", "100", "--json", "number"])
        return [(repo, p["number"]) for p in json.loads(saida)]
    saida = _gh(["search", "prs", "--owner", dono, "--state", "open", "--limit", "100", "--json", "repository,number"])
    return [(p["repository"]["nameWithOwner"], p["number"]) for p in json.loads(saida)]


def carregar(repo: str, numero: int) -> Pr:
    campos = "title,url,isDraft,body,mergeable,reviewDecision,statusCheckRollup,comments"
    dado = json.loads(_gh(["pr", "view", str(numero), "--repo", repo, "--json", campos]))
    return Pr(
        chave=(repo, numero),
        titulo=dado["title"],
        url=dado["url"],
        rascunho=bool(dado["isDraft"]),
        ci=estado_ci(dado.get("statusCheckRollup") or []),
        revisao=estado_revisao(dado.get("reviewDecision"), dado.get("comments") or []),
        conflito=estado_conflito(dado.get("mergeable")),
        depende=parse_depende(dado.get("body") or "", repo),
    )


def principal(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Fila de PRs abertos na ordem de merge (só leitura).")
    parser.add_argument("--owner", help="dono dos PRs; padrão: conta do gh logado")
    parser.add_argument("--repo", help="só este repositório (DONO/REPO)")
    parser.add_argument("--saida", default=SAIDA_PADRAO, help='arquivo de saída; "-" escreve na tela')
    args = parser.parse_args(argv)
    try:
        dono = args.owner or _gh(["api", "user", "--jq", ".login"]).strip()
        prs = [carregar(repo, numero) for repo, numero in listar_abertos(dono, args.repo)]
    except (RuntimeError, subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as erro:
        print(f"erro: {erro}", file=sys.stderr)
        return 1
    texto = renderizar(prs, datetime.now(), dono)
    if args.saida == "-":
        print(texto)
        return 0
    destino = Path(args.saida)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(texto, encoding="utf-8")
    print(f"fila escrita em {destino} ({len(prs)} PR(s))")
    return 0


if __name__ == "__main__":
    sys.exit(principal(sys.argv[1:]))
