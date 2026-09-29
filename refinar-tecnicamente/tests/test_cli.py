import argparse
import json
from pathlib import Path

import pytest

from refinar_tecnicamente.cli import executar

_ENV = {
    "AZURE_DEVOPS_ORGANIZACAO": "minha-org",
    "AZURE_DEVOPS_PROJETO": "meu-projeto",
    "AZURE_DEVOPS_TOKEN": "token",
}

_SPEC = """# Spec

## Lacunas e perguntas abertas

- **N3 · Negócio** — Pergunta de negócio?
- **T2 · Técnico** — Pergunta técnica?
"""


def test_ler_lacunas_imprime_so_as_tecnicas(tmp_path: Path, capsys: object) -> None:
    spec = tmp_path / "spec.md"
    spec.write_text(_SPEC, encoding="utf-8")
    codigo = executar(["ler-lacunas", str(spec)], env=_ENV)
    saida = capsys.readouterr().out  # type: ignore[attr-defined]
    lacunas = json.loads(saida)
    assert codigo == 0
    assert len(lacunas) == 1
    assert lacunas[0]["id"] == "T2"


def test_ler_lacunas_com_arquivo_inexistente_devolve_codigo_de_erro(capsys: object) -> None:
    codigo = executar(["ler-lacunas", "/caminho/que/nao/existe.md"], env=_ENV)
    assert codigo != 0


def test_ler_lacunas_com_lacuna_ambigua_devolve_mensagem_limpa(
    tmp_path: Path, capsys: object
) -> None:
    spec = tmp_path / "spec.md"
    spec.write_text(
        "# Spec\n\n## Lacunas e perguntas abertas\n\n- **rótulo quebrado** sem o padrão exato\n",
        encoding="utf-8",
    )
    codigo = executar(["ler-lacunas", str(spec)], env=_ENV)
    saida = capsys.readouterr().out  # type: ignore[attr-defined]
    assert codigo == 1
    assert "Traceback" not in saida


def test_gravar_spec_tecnica_sem_confirmacao_exata_nao_chama_rede(
    tmp_path: Path, capsys: object
) -> None:
    spec = tmp_path / "spec.md"
    spec.write_text("# Spec\n", encoding="utf-8")
    codigo = executar(
        [
            "gravar-spec-tecnica",
            "--demanda",
            "13959",
            "--spec",
            str(spec),
        ],
        env=_ENV,
        entrada=lambda _prompt: "resposta errada",
    )
    saida = capsys.readouterr().out  # type: ignore[attr-defined]
    assert codigo != 0
    assert "13959" in saida  # a frase esperada foi mostrada, nomeando a Demanda


def test_gravar_spec_tecnica_mostra_o_markdown_antes_da_frase_de_confirmacao(
    tmp_path: Path, capsys: object
) -> None:
    spec = tmp_path / "spec.md"
    spec.write_text("# Título\n\nParágrafo da spec.\n", encoding="utf-8")
    codigo = executar(
        ["gravar-spec-tecnica", "--demanda", "13959", "--spec", str(spec)],
        env=_ENV,
        entrada=lambda _prompt: "resposta errada",
    )
    saida = capsys.readouterr().out  # type: ignore[attr-defined]
    assert codigo != 0
    indice_markdown = saida.index("# Título\n\nParágrafo da spec.")
    indice_frase = saida.index("AUTORIZAR GRAVAÇÃO SPEC TÉCNICA #13959")
    assert indice_markdown < indice_frase  # o Markdown original aparece antes da confirmação
    assert "<h1>" not in saida


def test_gravar_spec_tecnica_usa_campo_configurado_por_padrao(
    tmp_path: Path, capsys: object
) -> None:
    spec = tmp_path / "spec.md"
    spec.write_text("# Spec\n", encoding="utf-8")
    env = {**_ENV, "AZURE_DEVOPS_CAMPO_SPEC_TECNICA": "Custom.OutroCampo"}
    codigo = executar(
        ["gravar-spec-tecnica", "--demanda", "13959", "--spec", str(spec)],
        env=env,
        entrada=lambda _prompt: "resposta errada",
    )
    saida = capsys.readouterr().out  # type: ignore[attr-defined]
    assert codigo != 0
    assert "Custom.OutroCampo" in saida


def test_gravar_spec_tecnica_com_arquivo_inexistente_devolve_codigo_de_erro(
    capsys: object,
) -> None:
    def _entrada_nao_deveria_ser_chamada(_prompt: str) -> str:
        raise AssertionError(
            "entrada() não deveria ser chamada quando a spec não existe"
        )

    codigo = executar(
        [
            "gravar-spec-tecnica",
            "--demanda",
            "13959",
            "--spec",
            "/caminho/que/nao/existe.md",
        ],
        env=_ENV,
        entrada=_entrada_nao_deveria_ser_chamada,
    )
    saida = capsys.readouterr().out  # type: ignore[attr-defined]
    assert codigo != 0
    assert "/caminho/que/nao/existe.md" in saida


def test_gravar_spec_tecnica_com_backlog_anexa_backlog_md(
    tmp_path: Path, capsys: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    from refinar_tecnicamente.cliente_azure_devops import ClienteAzureDevOps

    spec = tmp_path / "spec.md"
    spec.write_text("# Spec\n", encoding="utf-8")
    backlog = tmp_path / "backlog.md"
    backlog.write_text("# Backlog\n", encoding="utf-8")

    anexados: list[tuple[int, str, bytes]] = []

    def _anexar_espiao(self, work_item_id, nome_arquivo, conteudo):  # type: ignore[no-untyped-def]
        anexados.append((work_item_id, nome_arquivo, conteudo))

    monkeypatch.setattr(ClienteAzureDevOps, "anexar_arquivo", _anexar_espiao)
    monkeypatch.setattr(ClienteAzureDevOps, "gravar_campo", lambda *_a, **_kw: None)
    codigo = executar(
        [
            "gravar-spec-tecnica",
            "--demanda",
            "13959",
            "--spec",
            str(spec),
            "--backlog",
            str(backlog),
        ],
        env=_ENV,
        entrada=lambda _prompt: "AUTORIZAR GRAVAÇÃO SPEC TÉCNICA #13959",
    )
    assert codigo == 0
    assert (13959, "backlog.md", b"# Backlog\n") in anexados


def test_gravar_spec_tecnica_com_backlog_inexistente_devolve_codigo_de_erro(
    tmp_path: Path, capsys: object
) -> None:
    spec = tmp_path / "spec.md"
    spec.write_text("# Spec\n", encoding="utf-8")

    def _entrada_nao_deveria_ser_chamada(_prompt: str) -> str:
        raise AssertionError("entrada() não deveria ser chamada quando o backlog não existe")

    codigo = executar(
        [
            "gravar-spec-tecnica",
            "--demanda",
            "13959",
            "--spec",
            str(spec),
            "--backlog",
            "/caminho/que/nao/existe.md",
        ],
        env=_ENV,
        entrada=_entrada_nao_deveria_ser_chamada,
    )
    saida = capsys.readouterr().out  # type: ignore[attr-defined]
    assert codigo != 0
    assert "/caminho/que/nao/existe.md" in saida


def test_gravar_spec_tecnica_com_falha_no_anexo_apos_campo_gravado_pede_verificacao_manual(
    tmp_path: Path, capsys: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Achado 2 da revisão whole-branch: gravar_campo tem sucesso, mas anexar_arquivo (para
    spec.md) falha. A mensagem precisa deixar claro que o campo já foi gravado no Azure
    Boards, para quem lê não repetir a operação achando que nada aconteceu."""
    from refinar_tecnicamente.cliente_azure_devops import (
        ClienteAzureDevOps,
        ErroFalhaTransitoria,
    )

    spec = tmp_path / "spec.md"
    spec.write_text("# Spec\n", encoding="utf-8")

    def _anexar_falha(self, work_item_id, nome_arquivo, conteudo):  # type: ignore[no-untyped-def]
        raise ErroFalhaTransitoria(f"falha simulada ao anexar {nome_arquivo}")

    monkeypatch.setattr(ClienteAzureDevOps, "gravar_campo", lambda *_a, **_kw: None)
    monkeypatch.setattr(ClienteAzureDevOps, "anexar_arquivo", _anexar_falha)
    codigo = executar(
        ["gravar-spec-tecnica", "--demanda", "13959", "--spec", str(spec)],
        env=_ENV,
        entrada=lambda _prompt: "AUTORIZAR GRAVAÇÃO SPEC TÉCNICA #13959",
    )
    saida = capsys.readouterr().out  # type: ignore[attr-defined]
    assert codigo == 1
    assert "já foi gravado" in saida
    assert "verifi" in saida.lower()  # "verifique"/"verificação" manual
    assert "Traceback" not in saida


def test_resolver_spec_com_pasta_local_imprime_o_caminho(
    tmp_path: Path, capsys: object
) -> None:
    pasta = tmp_path / "docs" / "specs" / "DN-13959-slug"
    pasta.mkdir(parents=True)
    codigo = executar(
        ["resolver-spec", "--demanda", "13959", "--raiz", str(tmp_path)], env=_ENV
    )
    saida = capsys.readouterr().out  # type: ignore[attr-defined]
    assert codigo == 0
    assert str(pasta.resolve()) in saida


def test_resolver_spec_sem_pasta_local_baixa_e_usa_convencao_de_pasta(
    tmp_path: Path, capsys: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    from refinar_tecnicamente.cliente_azure_devops import ClienteAzureDevOps

    monkeypatch.setattr(
        ClienteAzureDevOps,
        "baixar_anexo",
        lambda _self, _id, nome: b"# Spec\n" if nome == "spec.md" else None,
    )
    monkeypatch.setattr(
        ClienteAzureDevOps,
        "ler_work_item",
        lambda _self, id_demanda: {
            "id": id_demanda, "fields": {"System.Title": "Emissao de Convites"}
        },
    )
    codigo = executar(
        ["resolver-spec", "--demanda", "13959", "--raiz", str(tmp_path)], env=_ENV
    )
    saida = capsys.readouterr().out  # type: ignore[attr-defined]
    esperado = tmp_path / "docs" / "specs" / "DN-13959-emissao-de-convites"
    assert codigo == 0
    assert str(esperado.resolve()) in saida
    assert (esperado / "spec.md").read_text(encoding="utf-8") == "# Spec\n"


def test_sugerir_story_points_imprime_a_sugestao(
    capsys: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    import refinar_tecnicamente.cli as cli_modulo
    from refinar_tecnicamente.ancoragem_story_points import SugestaoPontuacao

    capturado: dict[str, object] = {}

    def _sugerir_falso(cliente, *, projeto, area_path, tipos):  # type: ignore[no-untyped-def]
        capturado["projeto"] = projeto
        capturado["area_path"] = area_path
        capturado["tipos"] = tipos
        return SugestaoPontuacao(pontos=5.0, baseado_em=(1, 2, 3))

    monkeypatch.setattr(cli_modulo, "sugerir_story_points", _sugerir_falso)
    codigo = executar(
        [
            "sugerir-story-points",
            "--area-path",
            "MeuProjeto\\Time",
            "--tipo",
            "User Story",
            "--tipo",
            "Bug",
        ],
        env=_ENV,
    )
    saida = capsys.readouterr().out  # type: ignore[attr-defined]
    resultado = json.loads(saida)
    assert codigo == 0
    assert resultado["pontos"] == 5.0
    assert resultado["baseado_em"] == [1, 2, 3]
    assert capturado["projeto"] == "meu-projeto"
    assert capturado["area_path"] == "MeuProjeto\\Time"
    assert capturado["tipos"] == ("User Story", "Bug")


def test_configuracao_invalida_devolve_mensagem_limpa(capsys: object) -> None:
    """Cobre o ramo `except ErroConfiguracao` de `executar`: qualquer subcomando que
    precise de configuração falha de forma limpa quando o ambiente está incompleto."""
    env_incompleto = {"AZURE_DEVOPS_PROJETO": "meu-projeto", "AZURE_DEVOPS_TOKEN": "token"}
    codigo = executar(
        ["sugerir-story-points", "--area-path", "MeuProjeto", "--tipo", "Bug"],
        env=env_incompleto,
    )
    saida = capsys.readouterr().out  # type: ignore[attr-defined]
    assert codigo == 2
    assert "Configuração inválida" in saida
    assert "Traceback" not in saida


def test_falha_ao_falar_com_azure_boards_devolve_mensagem_limpa(
    capsys: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Cobre o ramo `except (ErroDestinoInvalido, ErroFalhaTransitoria, ErroRespostaInvalida)`
    de `executar`, disparado quando o cliente do Azure Boards falha durante um subcomando."""
    import refinar_tecnicamente.cli as cli_modulo
    from refinar_tecnicamente.cliente_azure_devops import ErroFalhaTransitoria

    def _sugerir_com_falha(cliente, *, projeto, area_path, tipos):  # type: ignore[no-untyped-def]
        raise ErroFalhaTransitoria("falha simulada ao falar com o Azure Boards")

    monkeypatch.setattr(cli_modulo, "sugerir_story_points", _sugerir_com_falha)
    codigo = executar(
        ["sugerir-story-points", "--area-path", "MeuProjeto", "--tipo", "Bug"], env=_ENV
    )
    saida = capsys.readouterr().out  # type: ignore[attr-defined]
    assert codigo == 1
    assert "Falha ao falar com o Azure Boards" in saida
    assert "Traceback" not in saida


def test_comando_desconhecido_e_recusado_pelo_parser(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`_construir_parser` só registra subcomandos que `executar` sabe tratar, então o
    `parser.error("comando desconhecido")` no fim da cadeia de ifs é uma guarda defensiva
    inalcançável por argv real (argparse já recusaria um subcomando desconhecido antes).
    Simula um `args.comando` fora do conjunto conhecido para exercitar essa guarda."""
    import refinar_tecnicamente.cli as cli_modulo

    def _parse_args_com_comando_bogus(self, _argv=None, _namespace=None):  # type: ignore[no-untyped-def]
        return argparse.Namespace(comando="bogus")

    monkeypatch.setattr(
        argparse.ArgumentParser, "parse_args", _parse_args_com_comando_bogus
    )
    with pytest.raises(SystemExit) as excinfo:
        cli_modulo.executar(["ler-lacunas", "spec.md"], env=_ENV)
    assert excinfo.value.code == 2


def test_comando_desconhecido_sem_parser_error_sair_devolve_2(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mesmo cenário defensivo acima, mas também neutraliza `parser.error` (que na vida real
    sempre levanta `SystemExit` antes) para provar que a guarda tem um `return 2` de reserva
    logo depois — a última linha genuinamente morta em código real, só alcançável assim."""
    import refinar_tecnicamente.cli as cli_modulo

    def _parse_args_com_comando_bogus(self, _argv=None, _namespace=None):  # type: ignore[no-untyped-def]
        return argparse.Namespace(comando="bogus")

    def _error_sem_sair(self, _mensagem):  # type: ignore[no-untyped-def]
        return None

    monkeypatch.setattr(
        argparse.ArgumentParser, "parse_args", _parse_args_com_comando_bogus
    )
    monkeypatch.setattr(argparse.ArgumentParser, "error", _error_sem_sair)
    assert cli_modulo.executar(["ler-lacunas", "spec.md"], env=_ENV) == 2


def test_resolver_spec_sem_pasta_local_e_sem_anexo_devolve_codigo_de_erro(
    tmp_path: Path, capsys: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    from refinar_tecnicamente.cliente_azure_devops import ClienteAzureDevOps

    monkeypatch.setattr(
        ClienteAzureDevOps, "baixar_anexo", lambda *_a, **_kw: None
    )
    codigo = executar(
        ["resolver-spec", "--demanda", "13959", "--raiz", str(tmp_path)], env=_ENV
    )
    saida = capsys.readouterr().out  # type: ignore[attr-defined]
    assert codigo != 0
    assert "13959" in saida
