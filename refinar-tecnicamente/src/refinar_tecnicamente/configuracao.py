"""Carrega a configuração local sem expor o token em representações textuais."""

from __future__ import annotations

from collections.abc import Mapping

from pydantic import BaseModel, ConfigDict, SecretStr, ValidationError, field_validator


class ErroConfiguracao(ValueError):
    """Indica que não foi possível obter uma configuração completa e segura."""


class ConfiguracaoRefinamento(BaseModel):
    """Agrupa organização, projeto, credencial e o nome do campo de spec técnica."""

    model_config = ConfigDict(frozen=True)

    organizacao: str
    projeto: str
    token: SecretStr
    campo_spec_tecnica: str = "Custom.DemandaSpecTecnica"

    @field_validator("organizacao", "projeto", "campo_spec_tecnica")
    @classmethod
    def _validar_texto_obrigatorio(cls, valor: str) -> str:
        texto = valor.strip()
        if not texto:
            raise ValueError("deve ser informado")
        return texto

    @field_validator("token")
    @classmethod
    def _validar_token(cls, valor: SecretStr) -> SecretStr:
        if not valor.get_secret_value().strip():
            raise ValueError("deve ser informado")
        return valor


def carregar_configuracao(env: Mapping[str, str]) -> ConfiguracaoRefinamento:
    """Lê a configuração a partir de um mapa de variáveis de ambiente já resolvido."""
    try:
        return ConfiguracaoRefinamento(
            organizacao=env.get("AZURE_DEVOPS_ORGANIZACAO", ""),
            projeto=env.get("AZURE_DEVOPS_PROJETO", ""),
            token=SecretStr(env.get("AZURE_DEVOPS_TOKEN", "")),
            campo_spec_tecnica=env.get(
                "AZURE_DEVOPS_CAMPO_SPEC_TECNICA", "Custom.DemandaSpecTecnica"
            ),
        )
    except ValidationError as erro:
        raise ErroConfiguracao(f"Configuração incompleta ou inválida: {erro}") from erro
