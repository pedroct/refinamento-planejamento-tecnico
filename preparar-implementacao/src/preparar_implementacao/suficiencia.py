"""Verifica se há o mínimo para montar o briefing; nunca inventa o que falta."""

from __future__ import annotations

from typing import Any


class ErroSuficienciaInsuficiente(RuntimeError):
    """A hierarquia não tem o mínimo necessário; a mensagem nomeia cada lacuna encontrada."""


def verificar_suficiencia(
    *,
    spec_tecnica: str | None,
    criterios_aceitacao: str | None,
    tasks: list[dict[str, Any]],
) -> None:
    """Levanta uma única exceção nomeando todas as lacunas bloqueantes encontradas."""
    lacunas: list[str] = []
    if not spec_tecnica:
        lacunas.append("a Demanda não tem spec técnica registrada em Custom.DemandaSpecTecnica")
    if not criterios_aceitacao:
        lacunas.append("a História/Bug não tem critério de aceitação preenchido")
    if not tasks:
        lacunas.append("não há nenhuma Task filha")
    else:
        for task in tasks:
            campos = task["fields"]
            tem_estimativa = (
                campos.get("Microsoft.VSTS.Scheduling.OriginalEstimate") is not None
                and campos.get("Microsoft.VSTS.Scheduling.RemainingWork") is not None
            )
            if not tem_estimativa:
                titulo = campos.get("System.Title", f"Task {task.get('id')}")
                lacunas.append(f"a Task {titulo!r} não tem Original Estimate/Remaining")
    if lacunas:
        raise ErroSuficienciaInsuficiente(
            "Faltam itens para montar o briefing: " + "; ".join(lacunas) + "."
        )
