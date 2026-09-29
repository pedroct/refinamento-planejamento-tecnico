from typing import Any

from preparar_implementacao.briefing import montar_briefing


def _work_item(tipo: str) -> dict[str, Any]:
    return {
        "id": 1,
        "fields": {
            "System.Title": "Renovar diligência automaticamente",
            "System.WorkItemType": tipo,
            "System.Description": "<p>Como usuário, quero...</p>",
            "Microsoft.VSTS.Common.AcceptanceCriteria": "<p>Dado que...</p>",
        },
    }


def _task(titulo: str, estimativa: float) -> dict[str, Any]:
    return {
        "id": 10,
        "fields": {
            "System.Title": titulo,
            "Microsoft.VSTS.Scheduling.OriginalEstimate": estimativa,
            "Microsoft.VSTS.Scheduling.RemainingWork": estimativa,
        },
    }


def test_briefing_inclui_titulo_e_criterios() -> None:
    briefing = montar_briefing(
        work_item=_work_item("User Story"),
        spec_tecnica="<p>abordagem técnica</p>",
        tasks=[_task("Task A", 4.0)],
    )
    assert "Renovar diligência automaticamente" in briefing
    assert "abordagem técnica" in briefing
    assert "Dado que" in briefing
    assert "Task A" in briefing
    assert "4.0" in briefing


def test_briefing_sem_tasks_avisa_que_nao_ha_task_filha() -> None:
    briefing = montar_briefing(
        work_item=_work_item("Bug"),
        spec_tecnica="<p>abordagem</p>",
        tasks=[],
    )
    assert "Renovar diligência automaticamente" in briefing
    assert "Nenhuma Task filha encontrada." in briefing


def test_briefing_com_id_task_origem_inclui_nota_de_rastreabilidade() -> None:
    briefing = montar_briefing(
        work_item=_work_item("User Story"),
        spec_tecnica="<p>abordagem</p>",
        tasks=[],
        id_task_origem=999,
    )
    assert "Recebido com o ID da Task #999" in briefing
    assert "User Story pai #1" in briefing


def test_briefing_sem_id_task_origem_nao_inclui_nota() -> None:
    briefing = montar_briefing(
        work_item=_work_item("User Story"),
        spec_tecnica="<p>abordagem</p>",
        tasks=[],
    )
    assert "Recebido com o ID da Task" not in briefing
