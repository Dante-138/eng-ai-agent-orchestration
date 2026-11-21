"""Tests for the bench_guard.py hook (PreToolUse, Bash and PowerShell)."""

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
HOOK = RAIZ / "claude/hooks/bench_guard.py"


def carregar():
    spec = importlib.util.spec_from_file_location("bench_guard", HOOK)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def rodar(entrada: str, script: Path = HOOK) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-I", str(script)], input=entrada, capture_output=True, text=True, check=False
    )


def pedido(comando: str, cwd: Path | None = None) -> str:
    dados = {"tool_name": "Bash", "tool_input": {"command": comando}}
    if cwd is not None:
        dados["cwd"] = str(cwd)
    return json.dumps(dados)


PERIGOSOS = [
    "nrfjprog --recover -f NRF52",
    "nrfjprog -f NRF52 --eraseall",
    "nrfjprog -f NRF52 -e",
    "nrfjprog --program app.hex --chiperase --verify",
    "nrfjprog --program app.hex --sectoranduicrerase",
    "nrfjprog --eraseuicr",
    "cd build && nrfjprog --qspieraseall",
    "west flash --recover",
    "west flash -d build --erase",
    "nrfutil device recover --serial-number 123",
    "nrfutil device erase --all",
    "JLink.exe -device NRF52820_XXAA -if SWD",
    "JLinkExe -CommandFile x.txt",
    '& "C:/Program Files/SEGGER/JLink_V958/JLink.exe" -device NRF52',
    "pyocd erase --chip -t nrf52840",
    "pyocd flash --erase chip app.hex",
    'openocd -f board.cfg -c "init; nrf5 mass_erase; exit"',
    "esptool.py --chip esp32c6 erase_flash",
    "esptool.py write_flash --erase-all 0x0 app.bin",
    "esptool --port COM5 write-flash -e 0x0 app.bin",
    "idf.py -p COM5 erase-flash",
    "espefuse.py burn_efuse JTAG_DISABLE",
    "sysupgrade -n /tmp/fw.bin",
    "firstboot -y",
    "ssh root@192.168.1.1 firstboot -y",
    'ssh gw "firstboot -y && reboot"',
    "nrfjprog -f NRF52 \\\n  --recover",
    "nrfjprog -f NRF52 `\n  --eraseall",
]

SEGUROS = [
    "nrfjprog --ids",
    "nrfjprog -f NRF52 --program app.hex --sectorerase --verify",
    "west flash --runner jlink",
    "west build -b nrf52840dk/nrf52840",
    "JLinkGDBServer -device NRF52",
    "esptool.py --chip esp32 flash_id",
    "idf.py build flash monitor",
    "sysupgrade -v /tmp/fw.bin",
    "git log --oneline -n 5",
    "grep -rn erase src/",
    "esptool.py write_flash 0x0 app.bin",
    "pyocd flash --erase sector app.hex",
    "pyocd erase --sector 0x1000",
    "grep -rn mass_erase docs/",
    "grep -rn firstboot /etc",
    "cat firstboot.log",
]


@pytest.mark.parametrize("comando", PERIGOSOS)
def test_comando_perigoso_pede_confirmacao(comando):
    r = rodar(pedido(comando))
    assert r.returncode == 0
    saida = json.loads(r.stdout)["hookSpecificOutput"]
    assert saida["permissionDecision"] == "ask"
    assert saida["permissionDecisionReason"].startswith("TRAVA DE BANCADA: ")


@pytest.mark.parametrize("comando", SEGUROS)
def test_comando_seguro_passa_calado(comando):
    r = rodar(pedido(comando))
    assert r.returncode == 0 and r.stdout == ""


@pytest.mark.parametrize("entrada", ["", "nao e json", "[]", json.dumps({"tool_input": {"command": 3}})])
def test_entrada_invalida_sai_com_zero_sem_saida(entrada):
    r = rodar(entrada)
    assert r.returncode == 0 and r.stdout == ""


def test_script_chamado_por_caminho_e_lido(tmp_path):
    (tmp_path / "gravar.sh").write_text("#!/bin/sh\nnrfjprog --recover\n", encoding="utf-8")
    r = rodar(pedido("bash gravar.sh", cwd=tmp_path))
    motivo = json.loads(r.stdout)["hookSpecificOutput"]["permissionDecisionReason"]
    assert "gravar.sh: nrfjprog" in motivo


def test_script_com_espaco_no_caminho_e_lido(tmp_path):
    pasta = tmp_path / "pasta com espaco"
    pasta.mkdir()
    (pasta / "limpar.ps1").write_text("west flash --erase\n", encoding="utf-8")
    r = rodar(pedido(f'pwsh -File "{(pasta / "limpar.ps1").as_posix()}"'))
    assert "limpar.ps1: west flash" in json.loads(r.stdout)["hookSpecificOutput"]["permissionDecisionReason"]


def test_script_jlink_com_erase_ou_unlock(tmp_path):
    (tmp_path / "apagar.jlink").write_text("connect\nerase\nexit\n", encoding="utf-8")
    hook = carregar()
    # Sem regras de comando: só a leitura do .jlink pode gerar aviso.
    saida = hook.decide("JLink.exe -device NRF52 -CommandFile apagar.jlink", tmp_path, [])
    assert "apagar.jlink: o script J-Link tem erase/unlock" in saida["hookSpecificOutput"]["permissionDecisionReason"]
    (tmp_path / "ler.jlink").write_text("connect\nmem32 0x10001080 4\nexit\n", encoding="utf-8")
    assert hook.decide("JLink.exe -device NRF52 -CommandFile ler.jlink", tmp_path, []) is None


@pytest.mark.parametrize(
    "comando",
    [
        "./gravar.sh",
        "sh gravar.sh",
        "sudo bash gravar.sh",
        ". ./gravar.sh",
        "cd x; bash ./gravar.sh",
        "python gravar.py",
        "pwsh -NoProfile -File gravar.ps1",
        "cmd /c gravar.bat",
        "& 'gravar.ps1'",
    ],
)
def test_script_em_posicao_de_execucao_e_lido(tmp_path, comando):
    for nome in ("gravar.sh", "gravar.py", "gravar.ps1", "gravar.bat"):
        (tmp_path / nome).write_text("nrfjprog --recover\n", encoding="utf-8")
    hook = carregar()
    assert hook.decide(comando, tmp_path, hook.RULES) is not None


@pytest.mark.parametrize(
    "comando",
    [
        "git add gravar.sh",
        "cat gravar.sh",
        "ruff check gravar.py",
        "python -m pytest gravar.py",
        "grep -n recover gravar.sh",
        "code gravar.ps1",
    ],
)
def test_script_so_citado_nao_e_lido(tmp_path, comando):
    for nome in ("gravar.sh", "gravar.py", "gravar.ps1"):
        (tmp_path / nome).write_text("nrfjprog --recover\n", encoding="utf-8")
    hook = carregar()
    assert hook.decide(comando, tmp_path, hook.RULES) is None


def test_caminho_do_script_como_o_shell_ve(tmp_path):
    hook = carregar()
    casa = tmp_path / "casa"
    assert hook.resolve_script("~/x.sh", None, casa, False) == casa / "x.sh"
    assert hook.resolve_script("$HOME/b/x.sh", None, casa, False) == casa / "b/x.sh"
    assert hook.resolve_script("/c/dev/x.sh", None, casa, True) == Path("c:/dev/x.sh")
    assert hook.resolve_script("/c/dev/x.sh", None, casa, False) == Path("/c/dev/x.sh")
    assert hook.resolve_script("x.sh", tmp_path, casa, True) == tmp_path / "x.sh"


def test_script_inofensivo_e_inexistente_passam(tmp_path):
    (tmp_path / "build.sh").write_text("west build -b nrf52840dk/nrf52840\n", encoding="utf-8")
    assert rodar(pedido("bash build.sh", cwd=tmp_path)).stdout == ""
    assert rodar(pedido("bash nao-existe.sh", cwd=tmp_path)).stdout == ""


def test_regras_locais_valem_e_regra_invalida_e_ignorada(tmp_path):
    copia = tmp_path / "bench_guard.py"
    shutil.copyfile(HOOK, copia)
    locais = [
        {"pattern": r"\bminhaferramenta\b.*\bzerar\b", "warning": "zera a identidade"},
        {"pattern": "(", "warning": "regex quebrada"},
        {"pattern": 3, "warning": "tipo errado"},
        "nao e objeto",
    ]
    (tmp_path / "bench_guard.local.json").write_text(json.dumps(locais), encoding="utf-8")
    r = rodar(pedido("minhaferramenta zerar --tudo"), script=copia)
    assert "zera a identidade" in json.loads(r.stdout)["hookSpecificOutput"]["permissionDecisionReason"]
    assert rodar(pedido("nrfjprog --ids"), script=copia).stdout == ""


def test_arquivo_local_quebrado_nao_derruba_as_regras_padrao(tmp_path):
    copia = tmp_path / "bench_guard.py"
    shutil.copyfile(HOOK, copia)
    (tmp_path / "bench_guard.local.json").write_text("{ isto nao e json", encoding="utf-8")
    r = rodar(pedido("nrfjprog --recover"), script=copia)
    assert json.loads(r.stdout)["hookSpecificOutput"]["permissionDecision"] == "ask"


def test_avisos_repetidos_aparecem_uma_vez():
    hook = carregar()
    saida = hook.decide("nrfjprog --recover; nrfjprog --eraseall", None, hook.RULES)
    assert saida["hookSpecificOutput"]["permissionDecisionReason"].count("nrfjprog") == 1
