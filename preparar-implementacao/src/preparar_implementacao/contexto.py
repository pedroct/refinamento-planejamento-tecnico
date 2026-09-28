"""Extrai o contexto de implementação já registrado: campos da Demanda e Tasks irmãs."""

from __future__ import annotations

from typing import Any, Protocol

_REL_FILHO = "System.LinkTypes.Hierarchy-Forward"


class _ClienteLeitura(Protocol):
    def ler_work_item(self, work_item_id: int) -> dict[str, Any]: ...


def extrair_campo_demanda(
    cadeia: list[dict[str, Any]], tipo_demanda: str, campo: str
) -> str | None:
    """Procura, na cadeia devolvida por `subir_ate_demanda`, o item da Demanda e lê `campo`."""
    for item in cadeia:
        if item["fields"].get("System.WorkItemType") == tipo_demanda:
            valor = item["fields"].get(campo)
            return valor if isinstance(valor, str) and valor.strip() else None
    return None


def ids_tasks_filhas(historia: dict[str, Any]) -> list[int]:
    """Lê os IDs de Task filhas a partir das relações de hierarquia para frente."""
    ids: list[int] = []
    for relacao in historia.get("relations", []):
        if relacao.get("rel") == _REL_FILHO:
            ids.append(int(relacao["url"].rsplit("/", 1)[-1]))
    return ids


def ler_tasks(cliente: _ClienteLeitura, ids: list[int]) -> list[dict[str, Any]]:
    """Busca cada Task por ID, na ordem recebida."""
    return [cliente.ler_work_item(id_) for id_ in ids]
