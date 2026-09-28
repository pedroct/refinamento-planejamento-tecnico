"""Sobe a cadeia de work items pais até encontrar a Demanda de Negócio."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    pass

_REL_PAI = "System.LinkTypes.Hierarchy-Reverse"
_LIMITE_SALTOS = 8


class _ClienteLeitura(Protocol):
    def ler_work_item(self, work_item_id: int) -> dict[str, Any]: ...


class ErroHierarquiaIncompleta(RuntimeError):
    """A cadeia de pais terminou antes de alcançar um item do tipo da Demanda."""


def _id_do_pai(item: dict[str, Any]) -> int | None:
    for relacao in item.get("relations", []):
        if relacao.get("rel") == _REL_PAI:
            url = relacao.get("url", "")
            return int(url.rsplit("/", 1)[-1])
    return None


def subir_ate_demanda(
    cliente: _ClienteLeitura, work_item_id: int, tipo_demanda: str
) -> list[dict[str, Any]]:
    """Devolve a cadeia do item de folha até a Demanda, inclusive, na ordem folha → raiz."""
    cadeia: list[dict[str, Any]] = []
    atual = cliente.ler_work_item(work_item_id)
    for _ in range(_LIMITE_SALTOS):
        cadeia.append(atual)
        if atual["fields"].get("System.WorkItemType") == tipo_demanda:
            return cadeia
        id_pai = _id_do_pai(atual)
        if id_pai is None:
            break
        atual = cliente.ler_work_item(id_pai)
    raise ErroHierarquiaIncompleta(
        f"A cadeia de pais do work item {work_item_id} não alcançou um item do tipo "
        f"{tipo_demanda!r} em até {_LIMITE_SALTOS} saltos."
    )
