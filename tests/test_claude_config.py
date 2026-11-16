"""Testes do hook ctx_guard.py e do instalador da configuração do Claude Code."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
HOOK = RAIZ / "claude/hooks/ctx_guard.py"
INSTALADOR = RAIZ / "scripts/instalar_claude.py"


def transcript(tmp_path: Path, tokens: int) -> Path:
    caminho = tmp_path / "t.jsonl"
    uso = {"input_tokens": 1, "cache_read_input_tokens": tokens, "cache_creation_input_tokens": 0}
    caminho.write_text(json.dumps({"message": {"usage": uso}}) + "\n", encoding="utf-8")
    return caminho


def rodar_hook(entrada: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-I", str(HOOK)], input=entrada, capture_output=True, text=True, check=False)


def prompt(caminho: Path, texto: str = "oi") -> str:
    return json.dumps({"transcript_path": str(caminho), "prompt": texto})


def test_abaixo_do_aviso_fica_calado(tmp_path):
    r = rodar_hook(prompt(transcript(tmp_path, 100_000)))
    assert r.returncode == 0 and r.stdout == ""


def test_acima_de_150_mil_avisa(tmp_path):
    r = rodar_hook(prompt(transcript(tmp_path, 200_000)))
    assert r.returncode == 0
    assert "AVISO DE COTA" in json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"]


def test_acima_de_300_mil_bloqueia_mas_libera_passagem(tmp_path):
    t = transcript(tmp_path, 400_000)
    assert json.loads(rodar_hook(prompt(t)).stdout)["decision"] == "block"
    assert "decision" not in json.loads(rodar_hook(prompt(t, "escreva a passagem")).stdout)


@pytest.mark.parametrize("entrada", ["{nao e json", "", "[]"])
def test_entrada_invalida_sai_com_zero(entrada):
    r = rodar_hook(entrada)
    assert r.returncode == 0 and r.stdout == ""


def instalar(home: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(INSTALADOR), "--home", str(home)], capture_output=True, text=True, check=False
    )


def test_instalador_idempotente_e_preserva_settings(tmp_path):
    settings = tmp_path / ".claude/settings.json"
    settings.parent.mkdir()
    settings.write_text(json.dumps({"model": "sonnet", "hooks": {"Stop": [{"hooks": []}]}}), encoding="utf-8")
    assert instalar(tmp_path).returncode == 0
    depois = settings.read_text(encoding="utf-8")
    dados = json.loads(depois)
    assert dados["model"] == "sonnet" and "Stop" in dados["hooks"] and "UserPromptSubmit" in dados["hooks"]
    antes_backups = sorted(p.name for p in settings.parent.glob("settings.json.bak-*"))
    assert len(antes_backups) == 1
    r = instalar(tmp_path)
    assert r.returncode == 0 and "criado" not in r.stdout and "atualizado" not in r.stdout
    assert settings.read_text(encoding="utf-8") == depois
    assert sorted(p.name for p in settings.parent.glob("settings.json.bak-*")) == antes_backups


def test_instalador_faz_backup_de_arquivo_alterado_pelo_usuario(tmp_path):
    instalar(tmp_path)
    leitor = tmp_path / ".claude/agents/leitor.md"
    leitor.write_text("meu", encoding="utf-8")
    instalar(tmp_path)
    assert len(list(leitor.parent.glob("leitor.md.bak-*"))) == 1


def test_instalador_recusa_settings_invalido(tmp_path):
    settings = tmp_path / ".claude/settings.json"
    settings.parent.mkdir()
    settings.write_text("{quebrado", encoding="utf-8")
    assert instalar(tmp_path).returncode != 0
    assert settings.read_text(encoding="utf-8") == "{quebrado"
