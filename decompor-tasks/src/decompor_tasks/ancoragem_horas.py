"""Sugere horas (Original Estimate/Remaining) a partir de Tasks fechadas comparáveis."""

from __future__ import annotations

import re
import statistics
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from typing import Any

_ESTADOS_FECHADOS = ("Closed", "Done", "Resolved")
_CAMPO_COMPLETED_WORK = "Microsoft.VSTS.Scheduling.CompletedWork"
_TAMANHO_MINIMO_PALAVRA = 4


class _ClienteLeitura(Protocol):
    def consultar_wiql(self, wiql: str) -> list[int]: ...
    def ler_work_item(self, work_item_id: int) -> dict[str, Any]: ...


@dataclass(frozen=True)
class SugestaoHoras:
    """`horas` é `None` quando não há Task fechada comparável com Completed Work preenchido."""

    horas: float | None
    baseado_em: tuple[int, ...]


def _palavras_significativas(titulo: str) -> set[str]:
    palavras = re.findall(r"\w+", titulo.lower())
    return {p for p in palavras if len(p) >= _TAMANHO_MINIMO_PALAVRA}


def sugerir_horas(
    cliente: _ClienteLeitura,
    *,
    projeto: str,
    area_path: str,
    tipo_task: str,
    titulo_aproximado: str,
    limite: int = 20,
) -> SugestaoHoras:
    """Consulta Tasks fechadas no mesmo Area Path, filtra por semelhança de título e
    propõe a mediana do Completed Work das que sobrarem."""
    estados_wiql = ", ".join(f"'{estado}'" for estado in _ESTADOS_FECHADOS)
    wiql = (
        "SELECT [System.Id] FROM WorkItems "  # noqa: S608
        f"WHERE [System.TeamProject] = '{projeto}' "
        f"AND [System.AreaPath] UNDER '{area_path}' "
        f"AND [System.WorkItemType] = '{tipo_task}' "
        f"AND [System.State] IN ({estados_wiql}) "
        "ORDER BY [System.ChangedDate] DESC"
    )
    ids = cliente.consultar_wiql(wiql)[:limite]
    palavras_alvo = _palavras_significativas(titulo_aproximado)
    pontuados: list[tuple[int, float]] = []
    for work_item_id in ids:
        campos = cliente.ler_work_item(work_item_id).get("fields", {})
        titulo = campos.get("System.Title", "")
        if not palavras_alvo & _palavras_significativas(titulo):
            continue
        horas = campos.get(_CAMPO_COMPLETED_WORK)
        if isinstance(horas, int | float):
            pontuados.append((work_item_id, float(horas)))
    if not pontuados:
        return SugestaoHoras(horas=None, baseado_em=())
    mediana = statistics.median(valor for _id, valor in pontuados)
    return SugestaoHoras(horas=mediana, baseado_em=tuple(id_ for id_, _valor in pontuados))
