#!/usr/bin/env python3
"""PreToolUse hook (Bash and PowerShell): bench guard for embedded hardware, no AI cost.

Asks the human before a shell command that can destroy something on a board or a device
that a reflash does not bring back: mass erase, UICR erase (device identity), eFuse burn,
factory reset of an OpenWrt gateway. It never blocks: it answers "ask" with what is lost.

Also reads the script a command runs (.sh, .ps1, .bat, .cmd, .py, .jlink), one level deep,
because "bash flash.sh" hides the dangerous line from the command itself. Only a script in
run position counts: first word of a segment, after an interpreter (bash, pwsh, python...)
or after -File / -CommandFile. "git add flash.sh" or "cat flash.sh" do not read it.
Known limits: a "cd" earlier in the same command does not move the folder the script is
looked up in, and variables other than ~ and $HOME are not expanded.

Extra rules for a private setup (company tool names, key names) go in
bench_guard.local.json next to this file: [{"pattern": "regex", "warning": "text"}].
Invalid JSON or an invalid regex there is ignored.

Any error: exit 0 without output (the hook never gets in the way of normal use).
"""

from __future__ import annotations

import contextlib
import json
import re
import sys
from pathlib import Path

# A command segment stops at a newline or at a shell separator.
SEG = r"[^\n;|&]*"
# Start of a command: line start, shell separator or "sudo".
CMD_START = r"(?:^|[\n;|&(]|\bsudo\s)\s*"

RULES: list[tuple[str, str]] = [
    (
        rf"\bnrfjprog\b{SEG}(--recover|--eraseall|--chiperase|--sectoranduicrerase|--eraseuicr"
        rf"|--qspieraseall|\s-e\b)",
        "nrfjprog vai apagar o chip inteiro ou a UICR: a identidade do dispositivo (e o que estiver "
        "gravado nela) se perde. Antes: leia a protecao e salve a UICR.",
    ),
    (
        rf"\bwest\s+flash\b{SEG}(--recover|--erase)\b",
        "west flash com --recover/--erase faz apagamento total: UICR junto. Antes: salve a UICR.",
    ),
    (
        rf"\bnrfutil\b{SEG}\bdevice\s+(recover|erase)\b",
        "nrfutil device recover/erase apaga o chip inteiro, UICR junto. Antes: salve a UICR.",
    ),
    (
        # "JLink" only with this capitalization: the lowercase "jlink" is also a west runner name.
        r"(?-i:\bJLink\b)|\bjlink(exe|\.exe)\b",
        "J-Link Commander num chip com protecao de acesso (APPROTECT) pergunta 'unsecure?' e, com sim, "
        "faz mass erase com a UICR junto. Confira a protecao antes de conectar.",
    ),
    (
        # "pyocd erase" without --sector, or "pyocd flash --erase chip".
        rf"\bpyocd\s+erase\b(?!{SEG}(--sector|\s-s\b))|\bpyocd\b{SEG}--erase[=\s]+chip\b",
        "pyocd erase (chip ou mass) apaga a flash inteira. Antes: salve o que for identidade.",
    ),
    (
        # OpenOCD takes its commands in -c "init; ...; exit": ";" does not end the segment here.
        r"\bopenocd\b[^\n]*\bmass_erase\b",
        "mass_erase do OpenOCD apaga a flash inteira. Antes: salve o que for identidade.",
    ),
    (
        rf"\b(esptool(\.py)?|idf\.py)\b{SEG}\berase[_-](flash|region)\b",
        "erase_flash apaga a flash do ESP32 inteira, NVS junto (calibracao, credenciais, identidade).",
    ),
    (
        rf"\besptool(\.py)?\b{SEG}\bwrite[_-]flash\b{SEG}(--erase-all\b|\s-e\b)",
        "write_flash --erase-all apaga a flash do ESP32 inteira antes de gravar, NVS junto.",
    ),
    (
        rf"\bespefuse(\.py)?\b{SEG}\bburn[_-]",
        "espefuse burn grava eFuse: IRREVERSIVEL. Um eFuse errado pode inutilizar o chip.",
    ),
    (
        rf"\bsysupgrade\b{SEG}\s-\w*n\b",
        "sysupgrade -n descarta a configuracao do gateway (senha, rede, comissionamento).",
    ),
    (
        # Only as a command: "grep firstboot" or "cat firstboot.log" stay silent.
        rf"(?:{CMD_START}|\bssh\b{SEG}?[\s\"'])firstboot\b(?![.\w-])",
        "firstboot volta o gateway ao padrao de fabrica: perde configuracao e comissionamento.",
    ),
]

# Inside a J-Link Commander script these lines erase or unlock (unlock = mass erase).
JLINK_SCRIPT_RULE = (
    r"(?im)^\s*(erase|unlock)\b",
    "o script J-Link tem erase/unlock: apaga a flash (unlock faz mass erase com a UICR junto).",
)

SCRIPT_EXT = r"sh|bash|ps1|psm1|bat|cmd|py|jlink"
SCRIPT_PATH = (
    rf"(?:\"(?P<dq>[^\"\n]+\.(?:{SCRIPT_EXT}))\""
    rf"|'(?P<sq>[^'\n]+\.(?:{SCRIPT_EXT}))'"
    rf"|(?P<bare>[^\s\"'`;|&<>()]+\.(?:{SCRIPT_EXT}))(?![\w.]))"
)
RUNNER = r"(?:\b(?:bash|sh|zsh|dash|ksh|source|pwsh|powershell|python3?|py|cmd)(?:\.exe)?|-CommandFile|-File)"
# Run position: first word of a segment (also ". x.sh" and "& x.ps1"), or after a runner and
# its flags ("pwsh -NoProfile -File x.ps1", "cmd /c x.bat").
SCRIPT_RUN = re.compile(
    rf"(?:(?:^|[\n;|&(])\s*(?:\.\s+)?|{RUNNER}\s+(?:[-/][\w-]+\s+)*){SCRIPT_PATH}",
    re.IGNORECASE,
)
# Line continuation: "\" at the end of a line (bash) or "`" (PowerShell).
CONTINUATION = re.compile(r"[\\`]\r?\n")
MAX_SCRIPT_BYTES = 512 * 1024


def load_extra_rules(folder: Path) -> list[tuple[str, str]]:
    """Private rules from bench_guard.local.json; anything malformed is skipped."""
    path = folder / "bench_guard.local.json"
    try:
        items = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    rules = []
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, dict):
            continue
        pattern, warning = item.get("pattern"), item.get("warning")
        if not isinstance(pattern, str) or not isinstance(warning, str):
            continue
        try:
            re.compile(pattern)
        except re.error:
            continue
        rules.append((pattern, warning))
    return rules


def join_continuations(text: str) -> str:
    return CONTINUATION.sub(" ", text)


def match_rules(text: str, rules: list[tuple[str, str]]) -> list[str]:
    text = join_continuations(text)
    return [warning for pattern, warning in rules if re.search(pattern, text, re.IGNORECASE)]


def resolve_script(name: str, cwd: Path | None, home: Path, windows: bool) -> Path:
    """Path of a script as the shell would see it: ~ and $HOME, Git Bash /c/..., relative to cwd."""
    name = re.sub(r"^(~|\$HOME|\$\{HOME\}|\$env:USERPROFILE)(?=[/\\]|$)", home.as_posix(), name)
    if windows:
        name = re.sub(r"^/([a-zA-Z])(?=/|$)", r"\1:", name)
    path = Path(name)
    if not path.is_absolute() and cwd is not None:
        path = cwd / path
    return path


def referenced_scripts(command: str, cwd: Path | None) -> list[Path]:
    """Script files the command runs (run position only) that exist on disk; no recursion."""
    found: list[Path] = []
    windows = sys.platform == "win32"
    for match in SCRIPT_RUN.finditer(join_continuations(command)):
        name = match.group("dq") or match.group("sq") or match.group("bare")
        path = resolve_script(name, cwd, Path.home(), windows)
        try:
            if path.is_file() and path.stat().st_size <= MAX_SCRIPT_BYTES and path not in found:
                found.append(path)
        except OSError:
            continue
    return found


def decide(command: str, cwd: Path | None, rules: list[tuple[str, str]]) -> dict | None:
    """Pure decision: the hook output for this command, or None to stay silent."""
    warnings = match_rules(command, rules)
    for script in referenced_scripts(command, cwd):
        try:
            content = script.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        inside = match_rules(content, rules)
        if script.suffix.lower() == ".jlink":
            inside += match_rules(content, [JLINK_SCRIPT_RULE])
        warnings += [f"{script.name}: {w}" for w in inside]
    if not warnings:
        return None
    unique = list(dict.fromkeys(warnings))
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": "TRAVA DE BANCADA: " + " | ".join(unique),
        }
    }


def main() -> None:
    data = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    tool_input = data.get("tool_input") or {}
    command = tool_input.get("command") or ""
    if not isinstance(command, str) or not command:
        return
    cwd = Path(data["cwd"]) if isinstance(data.get("cwd"), str) else None
    rules = RULES + load_extra_rules(Path(__file__).resolve().parent)
    out = decide(command, cwd, rules)
    if out:
        # ASCII escapes: a console code page can never break the output.
        print(json.dumps(out))


if __name__ == "__main__":
    with contextlib.suppress(Exception):
        main()
    sys.exit(0)
