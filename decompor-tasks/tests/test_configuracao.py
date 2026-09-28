import pytest

from decompor_tasks.configuracao import ErroConfiguracao, carregar_configuracao


def test_carrega_configuracao_completa() -> None:
    env = {
        "AZURE_DEVOPS_ORGANIZACAO": "minha-org",
        "AZURE_DEVOPS_PROJETO": "meu-projeto",
        "AZURE_DEVOPS_TOKEN": "token-secreto",
    }
    config = carregar_configuracao(env)
    assert config.organizacao == "minha-org"
    assert config.tipo_task == "Task"


def test_recusa_configuracao_sem_projeto() -> None:
    env = {"AZURE_DEVOPS_ORGANIZACAO": "minha-org", "AZURE_DEVOPS_TOKEN": "x"}
    with pytest.raises(ErroConfiguracao):
        carregar_configuracao(env)


def test_aceita_tipo_task_customizado() -> None:
    env = {
        "AZURE_DEVOPS_ORGANIZACAO": "minha-org",
        "AZURE_DEVOPS_PROJETO": "meu-projeto",
        "AZURE_DEVOPS_TOKEN": "x",
        "AZURE_DEVOPS_TIPO_TASK": "Tarefa",
    }
    assert carregar_configuracao(env).tipo_task == "Tarefa"
