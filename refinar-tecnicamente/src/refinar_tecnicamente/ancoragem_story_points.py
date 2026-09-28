"""Sugere Story Points a partir de itens fechados comparáveis; nunca inventa um número."""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from typing import Any

_ESTADOS_FECHADOS = ("Closed", "Done", "Resolved")
_CAMPO_STORY_POINTS = "Microsoft.VSTS.Scheduling.StoryPoints"


class _ClienteLeitura(Protocol):
    def consultar_wiql(self, wiql: str) -> list[int]: ...
    def ler_work_item(self, work_item_id: int) -> dict[str, Any]: ...


@dataclass(frozen=True)
class SugestaoPontuacao:
    """`pontos` é `None` quando não há item fechado comparável com Story Points preenchido."""

    pontos: float | None
    baseado_em: tuple[int, ...]


def sugerir_story_points(
    cliente: _ClienteLeitura,
    *,
    projeto: str,
    area_path: str,
    tipos: tuple[str, ...],
    limite: int = 20,
) -> SugestaoPontuacao:
    """Consulta itens fechados no mesmo Area Path e propõe a mediana dos que têm pontuação."""
    tipos_wiql = ", ".join(f"'{tipo}'" for tipo in tipos)
    estados_wiql = ", ".join(f"'{estado}'" for estado in _ESTADOS_FECHADOS)
    wiql = (
        "SELECT [System.Id] FROM WorkItems "
        f"WHERE [System.TeamProject] = '{projeto}' "
        f"AND [System.AreaPath] UNDER '{area_path}' "
        f"AND [System.WorkItemType] IN ({tipos_wiql}) "
        f"AND [System.State] IN ({estados_wiql}) "
        "ORDER BY [System.ChangedDate] DESC"
    )
    ids = cliente.consultar_wiql(wiql)[:limite]
    pontuados: list[tuple[int, float]] = []
    for work_item_id in ids:
        campos = cliente.ler_work_item(work_item_id).get("fields", {})
        pontos = campos.get(_CAMPO_STORY_POINTS)
        if isinstance(pontos, int | float):
            pontuados.append((work_item_id, float(pontos)))
    if not pontuados:
        return SugestaoPontuacao(pontos=None, baseado_em=())
    mediana = statistics.median(valor for _id, valor in pontuados)
    return SugestaoPontuacao(pontos=mediana, baseado_em=tuple(id_ for id_, _valor in pontuados))
