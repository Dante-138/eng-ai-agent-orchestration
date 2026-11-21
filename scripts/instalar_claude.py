"""Instala a configuração genérica do Claude Code (subagentes, skills e hooks) em ~/.claude.

Uso (vale no PowerShell e no Git Bash):
    python scripts/instalar_claude.py [--home PASTA] [--sem-ctx-guard]

Sem --home, usa a pasta pessoal do usuário. Idempotente: rodar de novo não altera nada.
Nunca sobrescreve arquivo do usuário sem backup (NOME.bak-AAAAMMDD-HHMMSS ao lado).
Mescla os hooks no settings.json sem apagar as outras chaves: ctx_guard em UserPromptSubmit
e bench_guard em PreToolUse (Bash e PowerShell). Com --sem-ctx-guard, o ctx_guard é copiado
mas não é registrado (para quem já limita o contexto pelo autoCompactWindow).
Se o settings.json não for JSON válido, para sem mexer em nada.
Só a biblioteca padrão do Python (3.10 ou mais novo).
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
HOOK = "ctx_guard.py"
BANCADA = "bench_guard.py"
# Arquivo do hook -> (evento, matcher). Matcher None: o grupo não leva a chave "matcher".
HOOKS = {HOOK: ("UserPromptSubmit", None), BANCADA: ("PreToolUse", "Bash|PowerShell")}


def arquivos_origem() -> list[tuple[Path, str]]:
    """Pares (origem, destino relativo a ~/.claude). O revisor vem de modelos/: só existe um."""
    pares = [(p, f"agents/{p.name}") for p in sorted((RAIZ / "claude/agents").glob("*.md"))]
    pares.append((RAIZ / "modelos/agentes/revisor.md", "agents/revisor.md"))
    pares += [(p, f"skills/{p.parent.name}/SKILL.md") for p in sorted((RAIZ / "claude/skills").glob("*/SKILL.md"))]
    pares += [(RAIZ / "claude/hooks" / nome, f"hooks/{nome}") for nome in HOOKS]
    return pares


def backup(destino: Path, agora: str) -> Path:
    copia = destino.with_name(f"{destino.name}.bak-{agora}")
    shutil.copy2(destino, copia)
    return copia


def copiar(origem: Path, destino: Path, agora: str) -> str:
    if destino.exists():
        if destino.read_bytes() == origem.read_bytes():
            return "igual"
        backup(destino, agora)
        status = "atualizado (backup feito)"
    else:
        status = "criado"
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(origem, destino)
    return status


def comando_do_hook(destino: Path) -> str:
    python = "python" if sys.platform == "win32" else "python3"
    return f'{python} "{destino.as_posix()}"'


def mesclar_settings(caminho: Path, comandos: dict[str, str], agora: str) -> str:
    """Registra cada hook (nome do arquivo -> comando) no seu evento; o que já existe fica."""
    if caminho.exists():
        try:
            dados = json.loads(caminho.read_text(encoding="utf-8"))
        except ValueError:
            raise SystemExit(f"{caminho} não é JSON válido: nada foi alterado nele. Corrija e rode de novo.") from None
        if not isinstance(dados, dict):
            raise SystemExit(f"{caminho} não é um objeto JSON: nada foi alterado nele.")
    else:
        dados = {}
    hooks = dados.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise SystemExit(f"{caminho} tem 'hooks' em formato inesperado: nada foi alterado.")
    # Confere todos os eventos antes de mexer em qualquer um: formato ruim não deixa nada pela metade.
    for nome in comandos:
        evento = HOOKS[nome][0]
        if not isinstance(hooks.get(evento, []), list):
            raise SystemExit(f"{caminho} tem 'hooks.{evento}' em formato inesperado: nada foi alterado.")
    novos = []
    for nome, comando in comandos.items():
        evento, matcher = HOOKS[nome]
        grupos = hooks.setdefault(evento, [])
        if any(
            isinstance(h, dict) and nome in str(h.get("command", ""))
            for grupo in grupos
            if isinstance(grupo, dict)
            for h in grupo.get("hooks", [])
        ):
            continue
        grupo = {"hooks": [{"type": "command", "command": comando}]}
        if matcher is not None:
            grupo = {"matcher": matcher, **grupo}
        grupos.append(grupo)
        novos.append(nome)
    if not novos:
        return "igual"
    if caminho.exists():
        backup(caminho, agora)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(dados, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return "hook adicionado: " + ", ".join(novos)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--home", type=Path, default=Path.home(), help="pasta pessoal (padrão: a do usuário)")
    ap.add_argument("--sem-ctx-guard", action="store_true", help="copia o ctx_guard sem registrá-lo")
    args = ap.parse_args(argv)
    destino = args.home / ".claude"
    agora = datetime.now().strftime("%Y%m%d-%H%M%S")

    for origem, rel in arquivos_origem():
        print(f"{rel}: {copiar(origem, destino / rel, agora)}")
    nomes = [n for n in HOOKS if not (args.sem_ctx_guard and n == HOOK)]
    comandos = {n: comando_do_hook(destino / "hooks" / n) for n in nomes}
    print(f"settings.json: {mesclar_settings(destino / 'settings.json', comandos, agora)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
