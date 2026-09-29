import argparse
from pathlib import Path

import pytest

from decompor_tasks import cli
from decompor_tasks.ancoragem_horas import SugestaoHoras
from decompor_tasks.cli import executar
from decompor_tasks.cliente_azure_devops import ErroFalhaTransitoria
from decompor_tasks.manifesto import Manifesto

_ENV = {
    "AZURE_DEVOPS_ORGANIZACAO": "minha-org",
    "AZURE_DEVOPS_PROJETO": "meu-projeto",
    "AZURE_DEVOPS_TOKEN": "token",
}


class _ClienteFalso:
    """Substitui `ClienteAzureDevOps` nos testes que exercitam `_sugerir_horas`/`_criar` sem
    rede: nenhum desses testes precisa de fato falar HTTP, só do protocolo de context manager
    que `cli.py` usa (`with ClienteAzureDevOps(...) as cliente`)."""

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        pass

    def __enter__(self) -> "_ClienteFalso":
        return self

    def __exit__(self, *_exc: object) -> None:
        return None


class _ParserComComandoDesconhecido:
    """Simula um parser cujo `parse_args` devolveu um `comando` fora dos subcomandos
    registrados e cujo `.error()` não interrompe a execução (ao contrário do `argparse` real,
    que sempre sai do processo) — só assim é possível exercitar o `return 2` de segurança que
    vem depois do `parser.error(...)` em `executar`, um ramo defensivo inalcançável via
    `argparse` real porque `subs.add_parser(..., required=True)` já garante que `args.comando`
    só pode ser "sugerir-horas" ou "criar"."""

    def parse_args(self, _argv: list[str]) -> argparse.Namespace:
        return argparse.Namespace(comando="outro-comando")

    def error(self, _mensagem: str) -> None:
        return None


def test_decompor_sem_confirmacao_exata_nao_chama_rede(tmp_path: Path, capsys: object) -> None:
    plano_json = tmp_path / "plano.json"
    plano_json.write_text(
        '{"historia_id": 100, "tasks": ['
        '{"titulo": "Task A", "original_estimate": 4.0, "remaining": 4.0, '
        '"assigned_to": "dev@x"}]}',
        encoding="utf-8",
    )
    codigo = executar(
        ["criar", str(plano_json), "--manifesto", str(tmp_path / "manifesto.json")],
        env=_ENV,
        entrada=lambda _prompt: "resposta errada",
    )
    saida = capsys.readouterr().out  # type: ignore[attr-defined]
    assert codigo != 0
    assert "100" in saida


def test_confirmacao_mostra_o_conteudo_exato_do_plano_antes_da_frase(
    tmp_path: Path, capsys: object
) -> None:
    plano_json = tmp_path / "plano.json"
    plano_json.write_text(
        '{"historia_id": 100, "tasks": ['
        '{"titulo": "Task A", "original_estimate": 4.0, "remaining": 4.0, '
        '"assigned_to": "dev@x"}]}',
        encoding="utf-8",
    )
    codigo = executar(
        ["criar", str(plano_json), "--manifesto", str(tmp_path / "manifesto.json")],
        env=_ENV,
        entrada=lambda _prompt: "resposta errada",
    )
    saida = capsys.readouterr().out  # type: ignore[attr-defined]
    assert codigo != 0
    # O conteúdo exato do plano precisa aparecer antes da frase de autorização, para que a
    # confirmação seja sobre o que de fato será criado — nunca só uma contagem.
    assert "Task A" in saida
    assert "4.0" in saida
    assert "dev@x" in saida


def test_criar_com_plano_inexistente_devolve_mensagem_limpa(
    tmp_path: Path, capsys: object
) -> None:
    codigo = executar(
        [
            "criar",
            str(tmp_path / "nao-existe.json"),
            "--manifesto",
            str(tmp_path / "manifesto.json"),
        ],
        env=_ENV,
        entrada=lambda _prompt: "não deveria ser chamado",
    )
    saida = capsys.readouterr().out  # type: ignore[attr-defined]
    assert codigo == 1
    assert "Traceback" not in saida
    assert "nao-existe.json" in saida


def test_criar_com_plano_malformado_devolve_mensagem_limpa(
    tmp_path: Path, capsys: object
) -> None:
    plano_json = tmp_path / "plano.json"
    plano_json.write_text('{"historia_id": 100}', encoding="utf-8")  # falta "tasks"
    codigo = executar(
        ["criar", str(plano_json), "--manifesto", str(tmp_path / "manifesto.json")],
        env=_ENV,
        entrada=lambda _prompt: "não deveria ser chamado",
    )
    saida = capsys.readouterr().out  # type: ignore[attr-defined]
    assert codigo == 1
    assert "Traceback" not in saida


def test_sugerir_horas_sem_configuracao_devolve_erro(capsys: object) -> None:
    codigo = executar(
        ["sugerir-horas", "--area-path", "proj\\Time A", "--titulo", "Criar endpoint"],
        env={},
    )
    saida = capsys.readouterr().out  # type: ignore[attr-defined]
    assert codigo == 2
    assert "Configuração inválida" in saida


def test_sugerir_horas_com_sucesso_imprime_a_sugestao_em_json(
    capsys: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cli, "ClienteAzureDevOps", _ClienteFalso)
    monkeypatch.setattr(
        cli,
        "sugerir_horas",
        lambda *_a, **_k: SugestaoHoras(horas=8.0, baseado_em=(1, 2)),
    )
    codigo = executar(
        ["sugerir-horas", "--area-path", "proj\\Time A", "--titulo", "Criar endpoint"],
        env=_ENV,
    )
    saida = capsys.readouterr().out  # type: ignore[attr-defined]
    assert codigo == 0
    assert '"horas": 8.0' in saida
    assert '"baseado_em"' in saida


def test_sugerir_horas_com_falha_do_azure_boards_devolve_mensagem_limpa(
    capsys: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cli, "ClienteAzureDevOps", _ClienteFalso)

    def _sugerir_horas_falsa(*_a: object, **_k: object) -> SugestaoHoras:
        raise ErroFalhaTransitoria("timeout simulado")

    monkeypatch.setattr(cli, "sugerir_horas", _sugerir_horas_falsa)
    codigo = executar(
        ["sugerir-horas", "--area-path", "proj\\Time A", "--titulo", "Criar endpoint"],
        env=_ENV,
    )
    saida = capsys.readouterr().out  # type: ignore[attr-defined]
    assert codigo == 1
    assert "Falha ao falar com o Azure Boards" in saida


def test_criar_com_manifesto_em_andamento_exige_reconciliacao(
    tmp_path: Path, capsys: object
) -> None:
    """`ErroReconciliacaoNecessaria` é levantado dentro de `criar_tasks_pendentes` (via
    `tasks_pendentes`) e propaga até o `try/except` de `executar`, sem passar pelo `except
    ErroConfirmacaoInvalida` local de `_criar`."""
    plano_json = tmp_path / "plano.json"
    plano_json.write_text(
        '{"historia_id": 100, "tasks": ['
        '{"titulo": "Task A", "original_estimate": 4.0, "remaining": 4.0, '
        '"assigned_to": "dev@x"}]}',
        encoding="utf-8",
    )
    manifesto_json = tmp_path / "manifesto.json"
    manifesto_json.write_text(
        '{"historia_id": 100, "hash_plano": "qualquer", "criadas": {}, '
        '"em_andamento": ["Task A"]}',
        encoding="utf-8",
    )
    codigo = executar(
        ["criar", str(plano_json), "--manifesto", str(manifesto_json)],
        env=_ENV,
        entrada=lambda _prompt: "AUTORIZAR TASKS #100",
    )
    saida = capsys.readouterr().out  # type: ignore[attr-defined]
    assert codigo == 1
    assert "Task A" in saida
    assert "verifique manualmente" in saida


def test_criar_com_confirmacao_correta_cria_tasks_e_imprime_sucesso(
    tmp_path: Path, capsys: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    plano_json = tmp_path / "plano.json"
    plano_json.write_text(
        '{"historia_id": 100, "tasks": ['
        '{"titulo": "Task A", "original_estimate": 4.0, "remaining": 4.0, '
        '"assigned_to": "dev@x"}]}',
        encoding="utf-8",
    )
    monkeypatch.setattr(cli, "ClienteAzureDevOps", _ClienteFalso)
    monkeypatch.setattr(
        cli,
        "criar_tasks_pendentes",
        lambda *_a, **_k: Manifesto(historia_id=100, hash_plano="hash", criadas={"Task A": 1}),
    )
    codigo = executar(
        ["criar", str(plano_json), "--manifesto", str(tmp_path / "manifesto.json")],
        env=_ENV,
        entrada=lambda _prompt: "AUTORIZAR TASKS #100",
    )
    saida = capsys.readouterr().out  # type: ignore[attr-defined]
    assert codigo == 0
    assert "Tasks pendentes criadas." in saida


def test_comando_desconhecido_apos_parser_devolve_codigo_2(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ramo defensivo: `_construir_parser` real nunca devolve `args.comando` fora de
    "sugerir-horas"/"criar" (subparsers com `required=True`), e o `argparse` real já sai do
    processo dentro de `parser.error(...)`. Um parser falso é o único jeito de alcançar o
    `parser.error(...)` seguido de `return 2` em `executar`."""
    monkeypatch.setattr(cli, "_construir_parser", lambda: _ParserComComandoDesconhecido())
    codigo = executar(["nao-importa"], env=_ENV)
    assert codigo == 2
