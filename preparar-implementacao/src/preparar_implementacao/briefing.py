"""Monta o briefing Markdown consolidado, para o desenvolvedor levar ao Superpowers."""

from __future__ import annotations

from typing import Any


def montar_briefing(
    *,
    work_item: dict[str, Any],
    spec_tecnica: str,
    tasks: list[dict[str, Any]],
    id_task_origem: int | None = None,
) -> str:
    """Consolida work item, abordagem técnica e Tasks num único documento.

    `work_item` é sempre a História/Bug, nunca uma Task — quando o ID recebido pelo comando
    era o de uma Task, `id_task_origem` carrega esse ID só para a nota de rastreabilidade;
    o restante do briefing (Tasks irmãs, critério de aceitação, título) já vem resolvido
    contra a História/Bug pai.
    """
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
    ]
    if id_task_origem is not None:
        partes += [
            f"> Recebido com o ID da Task #{id_task_origem} — este briefing foi montado a "
            f"partir da {tipo} pai #{work_item.get('id')}, de onde vêm as Tasks irmãs e o "
            "critério de aceitação.",
            "",
        ]
    partes += [
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
        "## Tasks e estimativas",
        "",
    ]
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
