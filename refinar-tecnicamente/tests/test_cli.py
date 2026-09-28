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
