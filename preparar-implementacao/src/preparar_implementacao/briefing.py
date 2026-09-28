"""Monta o briefing Markdown consolidado, para o desenvolvedor levar ao Superpowers."""

from __future__ import annotations

from typing import Any


def montar_briefing(
    *,
    work_item: dict[str, Any],
    spec_tecnica: str,
    spec_negocios: str | None,
    tasks: list[dict[str, Any]],
) -> str:
    """Consolida work item, abordagem técnica, contexto de negócio e Tasks num único documento."""
    campos = work_item["fields"]
    titulo = campos.get("System.Title", "")
    tipo = campos.get("System.WorkItemType", "")
    criterios = campos.get("Microsoft.VSTS.Common.AcceptanceCriteria", "")
    descricao = campos.get("System.Description") or campos.get(
        "Microsoft.VSTS.TCM.ReproSteps", ""
    )

    partes = [
        f"# Briefing de implementação — {tipo} #{work_item.get('id')}: {titulo}",
        "",
        "## Descrição",
        "",
        descricao,
        "",
        "## Critérios de aceitação",
        "",
        criterios,
        "",
        "## Abordagem técnica",
        "",
        spec_tecnica,
        "",
    ]
    if spec_negocios:
        partes += ["## Contexto de negócio", "", spec_negocios, ""]

    partes += ["## Tasks e estimativas", ""]
    if not tasks:
        partes.append("Nenhuma Task filha encontrada.")
    for task in tasks:
        campos_task = task["fields"]
        estimativa_original = campos_task.get("Microsoft.VSTS.Scheduling.OriginalEstimate")
        estimativa_restante = campos_task.get("Microsoft.VSTS.Scheduling.RemainingWork")
        partes.append(
            f"- **{campos_task.get('System.Title')}** — "
            f"Original Estimate: {estimativa_original} h, "
            f"Remaining: {estimativa_restante} h"
        )
    return "\n".join(partes)
