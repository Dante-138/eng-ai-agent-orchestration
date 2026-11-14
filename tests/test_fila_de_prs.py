import sys
from datetime import datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import fila_de_prs as f

REPO = "dono/app"
AGORA = datetime(2026, 11, 14, 22, 0)


def pr(numero, depende=(), ci="verde", revisao="aprovada", conflito="sem conflito", rascunho=False, repo=REPO):
    return f.Pr(
        chave=(repo, numero),
        titulo=f"mudanca {numero}",
        url=f"https://github.com/{repo}/pull/{numero}",
        rascunho=rascunho,
        ci=ci,
        revisao=revisao,
        conflito=conflito,
        depende=list(depende),
    )


class TestParseDepende:
    def test_le_numero_do_mesmo_repo(self):
        assert f.parse_depende("texto\nDepends on: #12\nmais", REPO) == [(REPO, 12)]

    def test_le_varios_e_de_outro_repo(self):
        corpo = "Depends on: #3, outro/lib#7 e #3"
        assert f.parse_depende(corpo, REPO) == [(REPO, 3), ("outro/lib", 7)]

    def test_ignora_maiuscula_marcadores_e_linha_sem_a_palavra(self):
        assert f.parse_depende("- depends ON: #5", REPO) == [(REPO, 5)]
        assert f.parse_depende("Este PR corrige o #5 e depende do #6", REPO) == []

    def test_corpo_vazio(self):
        assert f.parse_depende("", REPO) == []
        assert f.parse_depende(None, REPO) == []


class TestEstados:
    @pytest.mark.parametrize(
        ("rollup", "esperado"),
        [
            ([], "sem checks"),
            ([{"conclusion": "SUCCESS"}, {"conclusion": "SKIPPED"}], "verde"),
            ([{"conclusion": "SUCCESS"}, {"conclusion": "FAILURE"}], "vermelho"),
            ([{"conclusion": "SUCCESS"}, {"conclusion": "", "status": "IN_PROGRESS"}], "rodando"),
            ([{"state": "SUCCESS"}], "verde"),
            ([{"state": "PENDING"}], "rodando"),
            ([{"state": "ERROR"}], "vermelho"),
        ],
    )
    def test_ci(self, rollup, esperado):
        assert f.estado_ci(rollup) == esperado

    def test_revisao_formal_tem_prioridade(self):
        assert f.estado_revisao("APPROVED", []) == "aprovada"
        assert f.estado_revisao("CHANGES_REQUESTED", [{"body": "Resultado: aprovado"}]) == "pediu mudança"

    def test_revisao_por_comentario(self):
        aprovado = [{"body": "## Revisão\n\n**Resultado: aprovado com pedido.**"}]
        assert f.estado_revisao(None, aprovado) == "aprovada (comentário)"
        assert f.estado_revisao("", [{"body": "ficou bom"}]) == "comentada"
        assert f.estado_revisao(None, []) == "sem revisão"

    @pytest.mark.parametrize(
        ("mergeable", "esperado"),
        [
            ("MERGEABLE", "sem conflito"),
            ("CONFLICTING", "conflito"),
            ("UNKNOWN", "desconhecido"),
            (None, "desconhecido"),
        ],
    )
    def test_conflito(self, mergeable, esperado):
        assert f.estado_conflito(mergeable) == esperado


class TestOrdem:
    def test_dependencia_vem_antes_mesmo_com_numero_maior(self):
        ordenados, ciclo = f.ordenar([pr(5, depende=[(REPO, 9)]), pr(9), pr(2)])
        assert [p.chave[1] for p in ordenados] == [2, 9, 5]
        assert ciclo == []

    def test_empate_por_repositorio_e_numero(self):
        ordenados, _ = f.ordenar([pr(1, repo="b/x"), pr(2, repo="a/x"), pr(1, repo="a/x")])
        assert [p.chave for p in ordenados] == [("a/x", 1), ("a/x", 2), ("b/x", 1)]

    def test_dependencia_fora_da_fila_nao_trava(self):
        ordenados, ciclo = f.ordenar([pr(4, depende=[(REPO, 99)])])
        assert [p.chave[1] for p in ordenados] == [4]
        assert ciclo == []

    def test_ciclo_vai_a_parte(self):
        ordenados, ciclo = f.ordenar([pr(1, depende=[(REPO, 2)]), pr(2, depende=[(REPO, 1)]), pr(3)])
        assert [p.chave[1] for p in ordenados] == [3]
        assert sorted(p.chave[1] for p in ciclo) == [1, 2]


class TestPronto:
    def test_todos_os_requisitos(self):
        assert f.pronto(pr(1), {(REPO, 1)}, set())

    @pytest.mark.parametrize(
        "mudanca",
        [{"rascunho": True}, {"ci": "vermelho"}, {"revisao": "sem revisão"}, {"conflito": "conflito"}],
    )
    def test_falta_um_requisito(self, mudanca):
        assert not f.pronto(pr(1, **mudanca), {(REPO, 1)}, set())

    def test_dependencia_na_fila_bloqueia_ate_ser_mesclada(self):
        p = pr(2, depende=[(REPO, 1)])
        na_fila = {(REPO, 1), (REPO, 2)}
        assert not f.pronto(p, na_fila, set())
        assert f.pronto(p, na_fila, {(REPO, 1)})


class TestRenderizar:
    def test_tabela_na_ordem_com_link_e_dependencia(self):
        texto = f.renderizar([pr(2, depende=[(REPO, 1)], ci="rodando"), pr(1)], AGORA, "dono")
        linhas = [x for x in texto.splitlines() if x.startswith("| ") and "mudanca" in x]
        assert linhas[0].startswith("| 1 | [dono/app#1](https://github.com/dono/app/pull/1) mudanca 1 (aberto) | sim |")
        assert linhas[1].startswith("| 2 | [dono/app#2]")
        assert "| não | rodando | aprovada | sem conflito | dono/app#1 |" in linhas[1]
        assert "Gerada em 2026-11-14 22:00" in texto

    def test_marca_dependencia_fora_da_fila_e_rascunho(self):
        texto = f.renderizar([pr(3, depende=[(REPO, 8)], rascunho=True)], AGORA, "dono")
        assert "dono/app#8 (fora da fila)" in texto
        assert "mudanca 3 (rascunho) | não |" in texto

    def test_barra_no_titulo_nao_quebra_a_tabela(self):
        p = pr(1)
        p.titulo = "a | b"
        assert "a / b" in f.renderizar([p], AGORA, "dono")

    def test_sem_pr_e_com_ciclo(self):
        assert "Nenhum PR aberto." in f.renderizar([], AGORA, "dono")
        texto = f.renderizar([pr(1, depende=[(REPO, 2)]), pr(2, depende=[(REPO, 1)])], AGORA, "dono")
        assert "dependência em ciclo entre dono/app#1, dono/app#2" in texto


class TestPrincipal:
    def test_escreve_o_arquivo_com_gh_simulado(self, monkeypatch, tmp_path):
        respostas = {
            "api": "dono\n",
            "search": '[{"repository": {"nameWithOwner": "dono/app"}, "number": 7}]',
            "pr": (
                '{"title": "x", "url": "https://github.com/dono/app/pull/7", "isDraft": false, '
                '"body": "Depends on: #6", "mergeable": "MERGEABLE", "reviewDecision": "APPROVED", '
                '"statusCheckRollup": [{"conclusion": "SUCCESS"}], "comments": []}'
            ),
        }
        monkeypatch.setattr(f, "_gh", lambda argumentos: respostas[argumentos[0]])
        saida = tmp_path / "pasta" / "fila.md"
        assert f.principal(["--saida", str(saida)]) == 0
        assert "dono/app#6 (fora da fila)" in saida.read_text(encoding="utf-8")

    def test_erro_do_gh_vira_codigo_1(self, monkeypatch, capsys):
        def falha(_argumentos):
            raise RuntimeError("sem rede")

        monkeypatch.setattr(f, "_gh", falha)
        assert f.principal(["--owner", "dono", "--saida", "-"]) == 1
        assert "erro: sem rede" in capsys.readouterr().err
