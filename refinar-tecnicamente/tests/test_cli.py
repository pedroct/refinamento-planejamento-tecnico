import json
from pathlib import Path

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


def test_gravar_spec_tecnica_mostra_o_html_antes_da_frase_de_confirmacao(
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
    indice_html = saida.index("<h1>Título</h1>")
    indice_frase = saida.index("AUTORIZAR GRAVAÇÃO SPEC TÉCNICA #13959")
    assert indice_html < indice_frase  # o HTML real aparece antes da frase de confirmação


def test_gravar_spec_tecnica_com_html_invalido_recusa_sem_pedir_confirmacao(
    tmp_path: Path, capsys: object
) -> None:
    spec = tmp_path / "spec.md"
    # Markdown cujo HTML renderizado tem uma tag não fechada, via HTML embutido cru.
    spec.write_text("<div><span>sem fechar\n", encoding="utf-8")

    def _entrada_nao_deveria_ser_chamada(_prompt: str) -> str:
        raise AssertionError("entrada() não deveria ser chamada quando o HTML é inválido")

    codigo = executar(
        ["gravar-spec-tecnica", "--demanda", "13959", "--spec", str(spec)],
        env=_ENV,
        entrada=_entrada_nao_deveria_ser_chamada,
    )
    saida = capsys.readouterr().out  # type: ignore[attr-defined]
    assert codigo == 1
    assert "Traceback" not in saida
    assert "inválido" in saida


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
    tmp_path: Path, capsys: object
) -> None:
    from refinar_tecnicamente.cliente_azure_devops import ClienteAzureDevOps

    spec = tmp_path / "spec.md"
    spec.write_text("# Spec\n", encoding="utf-8")
    backlog = tmp_path / "backlog.md"
    backlog.write_text("# Backlog\n", encoding="utf-8")

    anexados: list[tuple[int, str, bytes]] = []
    original = ClienteAzureDevOps.anexar_arquivo

    def _anexar_espiao(self, work_item_id, nome_arquivo, conteudo):  # type: ignore[no-untyped-def]
        anexados.append((work_item_id, nome_arquivo, conteudo))

    import pytest as _pytest

    monkeypatch = _pytest.MonkeyPatch()
    monkeypatch.setattr(ClienteAzureDevOps, "anexar_arquivo", _anexar_espiao)
    monkeypatch.setattr(ClienteAzureDevOps, "gravar_campo", lambda *_a, **_kw: None)
    try:
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
    finally:
        monkeypatch.undo()
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
    tmp_path: Path, capsys: object
) -> None:
    from refinar_tecnicamente.cliente_azure_devops import ClienteAzureDevOps

    import pytest as _pytest

    monkeypatch = _pytest.MonkeyPatch()
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
    try:
        codigo = executar(
            ["resolver-spec", "--demanda", "13959", "--raiz", str(tmp_path)], env=_ENV
        )
    finally:
        monkeypatch.undo()
    saida = capsys.readouterr().out  # type: ignore[attr-defined]
    esperado = tmp_path / "docs" / "specs" / "DN-13959-emissao-de-convites"
    assert codigo == 0
    assert str(esperado.resolve()) in saida
    assert (esperado / "spec.md").read_text(encoding="utf-8") == "# Spec\n"


def test_resolver_spec_sem_pasta_local_e_sem_anexo_devolve_codigo_de_erro(
    tmp_path: Path, capsys: object
) -> None:
    from refinar_tecnicamente.cliente_azure_devops import ClienteAzureDevOps

    import pytest as _pytest

    monkeypatch = _pytest.MonkeyPatch()
    monkeypatch.setattr(
        ClienteAzureDevOps, "baixar_anexo", lambda *_a, **_kw: None
    )
    try:
        codigo = executar(
            ["resolver-spec", "--demanda", "13959", "--raiz", str(tmp_path)], env=_ENV
        )
    finally:
        monkeypatch.undo()
    saida = capsys.readouterr().out  # type: ignore[attr-defined]
    assert codigo != 0
    assert "13959" in saida
