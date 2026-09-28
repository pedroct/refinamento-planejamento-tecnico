from pathlib import Path

from decompor_tasks.cli import executar

_ENV = {
    "AZURE_DEVOPS_ORGANIZACAO": "minha-org",
    "AZURE_DEVOPS_PROJETO": "meu-projeto",
    "AZURE_DEVOPS_TOKEN": "token",
}


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


def test_sugerir_horas_sem_configuracao_devolve_erro(capsys: object) -> None:
    codigo = executar(
        ["sugerir-horas", "--area-path", "proj\\Time A", "--titulo", "Criar endpoint"],
        env={},
    )
    saida = capsys.readouterr().out  # type: ignore[attr-defined]
    assert codigo == 2
    assert "Configuração inválida" in saida
