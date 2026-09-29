import pytest

from preparar_implementacao.configuracao import ErroConfiguracao, carregar_configuracao


def test_carrega_configuracao_com_padroes() -> None:
    env = {
        "AZURE_DEVOPS_ORGANIZACAO": "minha-org",
        "AZURE_DEVOPS_PROJETO": "meu-projeto",
        "AZURE_DEVOPS_TOKEN": "token",
    }
    config = carregar_configuracao(env)
    assert config.tipo_demanda == "Demanda de Negócio"
    assert config.tipo_task == "Task"
    assert config.campo_spec_tecnica == "Custom.DemandaSpecTecnica"


def test_recusa_configuracao_sem_token() -> None:
    env = {"AZURE_DEVOPS_ORGANIZACAO": "minha-org", "AZURE_DEVOPS_PROJETO": "meu-projeto"}
    with pytest.raises(ErroConfiguracao):
        carregar_configuracao(env)
