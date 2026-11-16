"""Testes do hook ctx_guard.py e do instalador da configuração do Claude Code."""

import importlib.util
import json
import os
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


def rodar_hook(entrada: str, script: Path = HOOK, **limites: str) -> subprocess.CompletedProcess:
    """Roda o hook com CTX_WARN e CTX_BLOCK controlados: os do ambiente de quem testa não entram."""
    ambiente = {k: v for k, v in os.environ.items() if k not in ("CTX_WARN", "CTX_BLOCK")}
    ambiente.update(limites)
    return subprocess.run(
        [sys.executable, "-I", str(script)], input=entrada, capture_output=True, text=True, check=False, env=ambiente
    )


def carregar_hook():
    """Importa o hook como módulo para testar a lógica pura, sem subprocesso."""
    spec = importlib.util.spec_from_file_location("ctx_guard", HOOK)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


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


def test_transcript_inexistente_sai_com_zero_sem_erro(tmp_path):
    r = rodar_hook(prompt(tmp_path / "nao-existe.jsonl"))
    assert r.returncode == 0 and r.stdout == "" and r.stderr == ""


# Textos que não são um inteiro positivo: o hook tem de ignorá-los e usar o padrão.
LIMITES_INVALIDOS = ["abc", "", "  ", "-5", "0", "1.5", "150k", "nan"]


@pytest.mark.parametrize("valor", LIMITES_INVALIDOS)
def test_ctx_warn_invalido_cai_no_padrao(tmp_path, valor):
    r = rodar_hook(prompt(transcript(tmp_path, 200_000)), CTX_WARN=valor)
    assert r.returncode == 0 and r.stderr == ""
    nota = json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"]
    assert "aviso em 150 mil" in nota
    abaixo = rodar_hook(prompt(transcript(tmp_path, 100_000)), CTX_WARN=valor)
    assert abaixo.returncode == 0 and abaixo.stdout == "" and abaixo.stderr == ""


@pytest.mark.parametrize("valor", LIMITES_INVALIDOS)
def test_ctx_block_invalido_cai_no_padrao(tmp_path, valor):
    r = rodar_hook(prompt(transcript(tmp_path, 400_000)), CTX_BLOCK=valor)
    assert r.returncode == 0 and r.stderr == ""
    saida = json.loads(r.stdout)
    assert saida["decision"] == "block" and "limite 300 mil" in saida["reason"]
    sem_bloqueio = rodar_hook(prompt(transcript(tmp_path, 250_000)), CTX_BLOCK=valor)
    assert "decision" not in json.loads(sem_bloqueio.stdout)


def test_limites_validos_do_ambiente_valem(tmp_path):
    avisa = rodar_hook(prompt(transcript(tmp_path, 100_000)), CTX_WARN="50000")
    assert "AVISO DE COTA" in json.loads(avisa.stdout)["hookSpecificOutput"]["additionalContext"]
    livre = rodar_hook(prompt(transcript(tmp_path, 400_000)), CTX_BLOCK="500000")
    assert "decision" not in json.loads(livre.stdout)


def test_parse_limit_devolve_o_padrao_para_valor_ruim():
    hook = carregar_hook()
    assert hook.parse_limit("200000", 150_000) == 200_000
    assert hook.parse_limit(" 200000 ", 150_000) == 200_000
    for ruim in (None, "", "abc", "0", "-1", "1.5", "1e5", "150k", "nan"):
        assert hook.parse_limit(ruim, 150_000) == 150_000


def test_decide_separa_a_regra_da_entrada_e_saida():
    hook = carregar_hook()
    assert hook.decide(None, "oi", 150_000, 300_000) is None
    assert hook.decide(100_000, "oi", 150_000, 300_000) is None
    assert "hookSpecificOutput" in hook.decide(200_000, "oi", 150_000, 300_000)
    assert hook.decide(400_000, "oi", 150_000, 300_000)["decision"] == "block"
    assert "decision" not in hook.decide(400_000, "escreva a Passagem", 150_000, 300_000)
    assert "decision" not in hook.decide(400_000, "/clear", 150_000, 300_000)


def test_bloqueio_vale_mesmo_com_aviso_acima_do_bloqueio():
    hook = carregar_hook()
    # CTX_WARN maior que CTX_BLOCK: o bloqueio não pode ficar mudo entre os dois valores
    assert hook.decide(200_000, "oi", 500_000, 100_000)["decision"] == "block"
    # liberado (passagem) abaixo do aviso: passa calado, sem aviso
    assert hook.decide(200_000, "escreva a passagem", 500_000, 100_000) is None
    # abaixo dos dois: calado
    assert hook.decide(50_000, "oi", 500_000, 100_000) is None


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


ARQUIVOS_INSTALADOS = [
    "agents/leitor.md",
    "agents/revisor.md",
    "skills/passagem/SKILL.md",
    "skills/brief/SKILL.md",
    "hooks/ctx_guard.py",
]


def comandos_do_hook(settings: Path) -> list[str]:
    grupos = json.loads(settings.read_text(encoding="utf-8"))["hooks"]["UserPromptSubmit"]
    return [h["command"] for g in grupos for h in g["hooks"] if h.get("type") == "command"]


def test_instalacao_limpa_cria_os_arquivos_e_registra_o_hook(tmp_path):
    r = instalar(tmp_path)
    assert r.returncode == 0
    base = tmp_path / ".claude"
    for rel in ARQUIVOS_INSTALADOS:
        assert (base / rel).is_file(), rel
        assert f"{rel}: criado" in r.stdout
    assert (base / "hooks/ctx_guard.py").read_bytes() == HOOK.read_bytes()
    assert (base / "agents/revisor.md").read_bytes() == (RAIZ / "modelos/agentes/revisor.md").read_bytes()
    comandos = comandos_do_hook(base / "settings.json")
    assert len(comandos) == 1 and (base / "hooks/ctx_guard.py").as_posix() in comandos[0]
    assert "settings.json: hook adicionado" in r.stdout
    # numa pasta nova não há o que salvar, e nada é criado fora de .claude
    assert list(base.rglob("*.bak-*")) == []
    assert [p.name for p in tmp_path.iterdir()] == [".claude"]


def test_hook_instalado_funciona(tmp_path):
    instalar(tmp_path)
    instalado = tmp_path / ".claude/hooks/ctx_guard.py"
    entrada = prompt(transcript(tmp_path, 200_000))
    r = rodar_hook(entrada, script=instalado)
    assert r.returncode == 0
    assert "AVISO DE COTA" in json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"]


def test_instalador_acrescenta_sem_trocar_hook_de_outra_origem(tmp_path):
    settings = tmp_path / ".claude/settings.json"
    settings.parent.mkdir()
    outro = {"hooks": {"UserPromptSubmit": [{"hooks": [{"type": "command", "command": "outro-hook.sh"}]}]}}
    settings.write_text(json.dumps(outro), encoding="utf-8")
    assert instalar(tmp_path).returncode == 0
    comandos = comandos_do_hook(settings)
    assert comandos[0] == "outro-hook.sh" and len(comandos) == 2 and "ctx_guard.py" in comandos[1]


def test_instalador_nao_duplica_hook_ja_registrado(tmp_path):
    settings = tmp_path / ".claude/settings.json"
    settings.parent.mkdir()
    ja = {"hooks": {"UserPromptSubmit": [{"hooks": [{"type": "command", "command": 'python "meu/ctx_guard.py"'}]}]}}
    texto = json.dumps(ja)
    settings.write_text(texto, encoding="utf-8")
    r = instalar(tmp_path)
    assert r.returncode == 0 and "settings.json: igual" in r.stdout
    assert settings.read_text(encoding="utf-8") == texto
    assert list(settings.parent.glob("settings.json.bak-*")) == []
