import pytest

from refinar_tecnicamente.configuracao import ErroConfiguracao, carregar_configuracao


def test_carrega_configuracao_completa() -> None:
    env = {
        "AZURE_DEVOPS_ORGANIZACAO": "minha-org",
        "AZURE_DEVOPS_PROJETO": "meu-projeto",
        "AZURE_DEVOPS_TOKEN": "token-secreto",
    }
    config = carregar_configuracao(env)
    assert config.organizacao == "minha-org"
    assert config.projeto == "meu-projeto"
    assert config.token.get_secret_value() == "token-secreto"
    assert config.campo_spec_tecnica == "Custom.DemandaSpecTecnica"


def test_recusa_configuracao_sem_organizacao() -> None:
    env = {"AZURE_DEVOPS_PROJETO": "meu-projeto", "AZURE_DEVOPS_TOKEN": "x"}
    with pytest.raises(ErroConfiguracao):
        carregar_configuracao(env)


def test_recusa_token_vazio() -> None:
    env = {
        "AZURE_DEVOPS_ORGANIZACAO": "minha-org",
        "AZURE_DEVOPS_PROJETO": "meu-projeto",
        "AZURE_DEVOPS_TOKEN": "   ",
    }
    with pytest.raises(ErroConfiguracao):
        carregar_configuracao(env)


def test_aceita_nome_de_campo_customizado() -> None:
    env = {
        "AZURE_DEVOPS_ORGANIZACAO": "minha-org",
        "AZURE_DEVOPS_PROJETO": "meu-projeto",
        "AZURE_DEVOPS_TOKEN": "x",
        "AZURE_DEVOPS_CAMPO_SPEC_TECNICA": "Custom.OutroCampo",
    }
    config = carregar_configuracao(env)
    assert config.campo_spec_tecnica == "Custom.OutroCampo"
