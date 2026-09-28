from preparar_implementacao.cli import executar

_ENV = {
    "AZURE_DEVOPS_ORGANIZACAO": "minha-org",
    "AZURE_DEVOPS_PROJETO": "meu-projeto",
    "AZURE_DEVOPS_TOKEN": "token",
}


def test_montar_sem_configuracao_devolve_erro(capsys: object) -> None:
    codigo = executar(["montar", "1"], env={})
    saida = capsys.readouterr().out  # type: ignore[attr-defined]
    assert codigo == 2
    assert "Configuração inválida" in saida
