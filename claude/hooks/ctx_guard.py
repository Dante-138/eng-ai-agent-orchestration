#!/usr/bin/env python3
"""UserPromptSubmit hook: guarda de tamanho de contexto (sem custo de IA).

Cada mensagem reenvia o contexto inteiro da sessao. Este script le o ultimo
`usage` do transcript e:
  - >= CTX_WARN  (150k): injeta aviso para escrever PASSAGEM-<tema>.md e abrir sessao nova;
  - >= CTX_BLOCK (300k): bloqueia o prompt e manda abrir sessao nova.
Prompts que comecam com "/" (ex.: /clear, /compact) e prompts que citam "passagem"
passam sempre, para dar para escrever a passagem mesmo no bloqueio.
Qualquer erro: sai com 0 sem mexer em nada (nunca trava o uso).
Limites podem ser trocados pelas variaveis de ambiente CTX_WARN e CTX_BLOCK.
"""

import contextlib
import json
import os
import sys

WARN = int(os.environ.get("CTX_WARN", "150000"))
BLOCK = int(os.environ.get("CTX_BLOCK", "300000"))
CHUNK = 1024 * 1024
MAX_BACK = 64 * 1024 * 1024


def last_context_tokens(path):
    """Soma input + cache_read + cache_creation do ultimo uso do assistente."""
    size = os.path.getsize(path)
    with open(path, "rb") as f:
        pos = size
        tail = b""
        while pos > 0 and (size - pos) < MAX_BACK:
            step = min(CHUNK, pos)
            pos -= step
            f.seek(pos)
            tail = f.read(step) + tail
            lines = tail.split(b"\n")
            # a primeira linha pode estar cortada, a menos que seja o inicio do arquivo
            start = 0 if pos == 0 else 1
            for raw in reversed(lines[start:]):
                if b"cache_read_input_tokens" not in raw:
                    continue
                try:
                    obj = json.loads(raw)
                except ValueError:
                    continue
                if obj.get("isSidechain"):
                    continue
                msg = obj.get("message")
                usage = msg.get("usage") if isinstance(msg, dict) else None
                if not isinstance(usage, dict):
                    continue
                return (
                    int(usage.get("input_tokens") or 0)
                    + int(usage.get("cache_read_input_tokens") or 0)
                    + int(usage.get("cache_creation_input_tokens") or 0)
                )
            if pos == 0:
                break
    return None


def main():
    data = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    path = data.get("transcript_path")
    if not path or not os.path.isfile(path):
        return
    tokens = last_context_tokens(path)
    if tokens is None or tokens < WARN:
        return

    prompt = (data.get("prompt") or "").strip()
    k = tokens // 1000
    exempt = prompt.startswith("/") or "passagem" in prompt.lower()

    if tokens >= BLOCK and not exempt:
        print(
            json.dumps(
                {
                    "decision": "block",
                    "reason": (
                        f"Contexto em {k} mil tokens (limite {BLOCK // 1000} mil): cada mensagem "
                        "reenvia tudo. Peça 'escreva a passagem' (liberado) e abra sessão nova."
                    ),
                }
            )
        )
        return

    note = (
        f"AVISO DE COTA: o contexto desta sessão está em {k} mil tokens (aviso em "
        f"{WARN // 1000} mil, bloqueio em {BLOCK // 1000} mil). Cada mensagem reenvia tudo. "
        "Se ainda não fez nesta sessão: termine o passo atual, escreva PASSAGEM-<tema>.md "
        "(até 30 linhas: estado, decisões, próximo passo, arquivos) e diga ao usuário, em "
        "uma linha, para abrir sessão nova e arquivar esta. Não comece trabalho novo."
    )
    print(
        json.dumps(
            {
                "systemMessage": f"Contexto em {k} mil tokens: hora de passagem e sessão nova.",
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": note,
                },
            }
        )
    )


if __name__ == "__main__":
    with contextlib.suppress(Exception):
        main()
    sys.exit(0)
