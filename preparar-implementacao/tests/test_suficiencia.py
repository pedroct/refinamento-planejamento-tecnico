from typing import Any

import pytest

from preparar_implementacao.suficiencia import ErroSuficienciaInsuficiente, verificar_suficiencia


def _task_estimada(titulo: str) -> dict[str, Any]:
    return {
        "fields": {
            "System.Title": titulo,
            "Microsoft.VSTS.Scheduling.OriginalEstimate": 4.0,
            "Microsoft.VSTS.Scheduling.RemainingWork": 4.0,
        }
    }


def _task_sem_estimativa(titulo: str) -> dict[str, Any]:
    return {"fields": {"System.Title": titulo}}


def _task_so_original_estimate(titulo: str) -> dict[str, Any]:
    return {
        "fields": {
            "System.Title": titulo,
            "Microsoft.VSTS.Scheduling.OriginalEstimate": 4.0,
        }
    }


def _task_so_remaining_work(titulo: str) -> dict[str, Any]:
    return {
        "fields": {
            "System.Title": titulo,
            "Microsoft.VSTS.Scheduling.RemainingWork": 4.0,
        }
    }


def test_tudo_presente_nao_levanta_erro() -> None:
    verificar_suficiencia(
        spec_tecnica="<p>abordagem</p>",
        criterios_aceitacao="<p>critérios</p>",
        tasks=[_task_estimada("Task A")],
    )


def test_sem_spec_tecnica_nomeia_a_lacuna() -> None:
    with pytest.raises(ErroSuficienciaInsuficiente, match="spec técnica"):
        verificar_suficiencia(
            spec_tecnica=None, criterios_aceitacao="<p>x</p>", tasks=[_task_estimada("Task A")]
        )


def test_sem_criterios_de_aceitacao_nomeia_a_lacuna() -> None:
    with pytest.raises(ErroSuficienciaInsuficiente, match="critério de aceitação"):
        verificar_suficiencia(
            spec_tecnica="<p>x</p>", criterios_aceitacao=None, tasks=[_task_estimada("Task A")]
        )


def test_sem_nenhuma_task_nomeia_a_lacuna() -> None:
    with pytest.raises(ErroSuficienciaInsuficiente, match="Task"):
        verificar_suficiencia(spec_tecnica="<p>x</p>", criterios_aceitacao="<p>x</p>", tasks=[])


def test_task_sem_estimativa_nomeia_o_titulo_dela() -> None:
    with pytest.raises(ErroSuficienciaInsuficiente, match="Task B"):
        verificar_suficiencia(
            spec_tecnica="<p>x</p>",
            criterios_aceitacao="<p>x</p>",
            tasks=[_task_estimada("Task A"), _task_sem_estimativa("Task B")],
        )


def test_multiplas_lacunas_aparecem_todas_na_mesma_mensagem() -> None:
    with pytest.raises(ErroSuficienciaInsuficiente) as excecao:
        verificar_suficiencia(spec_tecnica=None, criterios_aceitacao=None, tasks=[])
    mensagem = str(excecao.value)
    assert "spec técnica" in mensagem
    assert "critério de aceitação" in mensagem
    assert "Task" in mensagem


def test_task_com_so_original_estimate_nomeia_a_lacuna() -> None:
    with pytest.raises(ErroSuficienciaInsuficiente, match="Task C"):
        verificar_suficiencia(
            spec_tecnica="<p>x</p>",
            criterios_aceitacao="<p>x</p>",
            tasks=[_task_estimada("Task A"), _task_so_original_estimate("Task C")],
        )


def test_task_com_so_remaining_work_nomeia_a_lacuna() -> None:
    with pytest.raises(ErroSuficienciaInsuficiente, match="Task D"):
        verificar_suficiencia(
            spec_tecnica="<p>x</p>",
            criterios_aceitacao="<p>x</p>",
            tasks=[_task_estimada("Task A"), _task_so_remaining_work("Task D")],
        )
