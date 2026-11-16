"""Instala a configuração genérica do Claude Code (subagentes, skills e hook) em ~/.claude.

Uso (vale no PowerShell e no Git Bash):
    python scripts/instalar_claude.py [--home PASTA]

Sem --home, usa a pasta pessoal do usuário. Idempotente: rodar de novo não altera nada.
Nunca sobrescreve arquivo do usuário sem backup (NOME.bak-AAAAMMDD-HHMMSS ao lado).
Mescla o hook UserPromptSubmit no settings.json sem apagar as outras chaves.
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


def arquivos_origem() -> list[tuple[Path, str]]:
    """Pares (origem, destino relativo a ~/.claude). O revisor vem de modelos/: só existe um."""
    pares = [(p, f"agents/{p.name}") for p in sorted((RAIZ / "claude/agents").glob("*.md"))]
    pares.append((RAIZ / "modelos/agentes/revisor.md", "agents/revisor.md"))
    pares += [(p, f"skills/{p.parent.name}/SKILL.md") for p in sorted((RAIZ / "claude/skills").glob("*/SKILL.md"))]
    pares.append((RAIZ / "claude/hooks" / HOOK, f"hooks/{HOOK}"))
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


def mesclar_settings(caminho: Path, comando: str, agora: str) -> str:
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
    grupos = hooks.setdefault("UserPromptSubmit", []) if isinstance(hooks, dict) else None
    if not isinstance(grupos, list):
        raise SystemExit(f"{caminho} tem 'hooks.UserPromptSubmit' em formato inesperado: nada foi alterado.")
    for grupo in grupos:
        for h in grupo.get("hooks", []) if isinstance(grupo, dict) else []:
            if isinstance(h, dict) and HOOK in str(h.get("command", "")):
                return "igual"
    grupos.append({"hooks": [{"type": "command", "command": comando}]})
    if caminho.exists():
        backup(caminho, agora)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(dados, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return "hook adicionado"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--home", type=Path, default=Path.home(), help="pasta pessoal (padrão: a do usuário)")
    args = ap.parse_args(argv)
    destino = args.home / ".claude"
    agora = datetime.now().strftime("%Y%m%d-%H%M%S")

    for origem, rel in arquivos_origem():
        print(f"{rel}: {copiar(origem, destino / rel, agora)}")
    comando = comando_do_hook(destino / "hooks" / HOOK)
    print(f"settings.json: {mesclar_settings(destino / 'settings.json', comando, agora)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
