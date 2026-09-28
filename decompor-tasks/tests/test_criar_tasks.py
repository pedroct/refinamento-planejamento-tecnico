from pathlib import Path
from typing import Any

import pytest

from decompor_tasks.criar_tasks import (
    ErroConfirmacaoInvalida,
    criar_tasks_pendentes,
    montar_operacoes_criacao,
)
from decompor_tasks.manifesto import Manifesto, PlanoTasks, TaskProposta, ler_manifesto

_TASK_A = TaskProposta(titulo="Task A", original_estimate=4.0, remaining=4.0, assigned_to="dev@x")
_TASK_B = TaskProposta(titulo="Task B", original_estimate=2.0, remaining=2.0, assigned_to="dev@x")


class ClienteFalso:
    def __init__(self, ids_por_ordem: list[int]) -> None:
        self._ids = iter(ids_por_ordem)
        self.chamadas: list[tuple[str, list[dict[str, Any]]]] = []

    def criar_work_item(self, tipo: str, operacoes: list[dict[str, Any]]) -> dict[str, Any]:
        self.chamadas.append((tipo, operacoes))
        return {"id": next(self._ids)}


def test_operacoes_nunca_incluem_story_points() -> None:
    operacoes = montar_operacoes_criacao(
        historia_id=100, organizacao="org", projeto="proj", tipo_task="Task", task=_TASK_A
    )
    caminhos = [op["path"] for op in operacoes]
    assert "/fields/Microsoft.VSTS.Scheduling.StoryPoints" not in caminhos
    assert "/fields/Microsoft.VSTS.Scheduling.OriginalEstimate" in caminhos
    assert "/fields/Microsoft.VSTS.Scheduling.RemainingWork" in caminhos
    assert "/fields/System.AssignedTo" in caminhos


def test_operacoes_incluem_relacao_com_a_historia() -> None:
    operacoes = montar_operacoes_criacao(
        historia_id=100, organizacao="org", projeto="proj", tipo_task="Task", task=_TASK_A
    )
    relacao = next(op for op in operacoes if op["path"] == "/relations/-")
    assert relacao["value"]["rel"] == "System.LinkTypes.Hierarchy-Reverse"
    assert "workItems/100" in relacao["value"]["url"]


@pytest.mark.parametrize(
    "resposta",
    ["autorizar tasks #100", "AUTORIZAR TASKS #999", "sim", ""],
)
def test_recusa_confirmacao_nao_exata_e_nao_cria_nada(tmp_path: Path, resposta: str) -> None:
    plano = PlanoTasks(historia_id=100, tasks=(_TASK_A, _TASK_B))
    cliente = ClienteFalso([1, 2])
    with pytest.raises(ErroConfirmacaoInvalida):
        criar_tasks_pendentes(
            cliente,
            organizacao="org",
            projeto="proj",
            tipo_task="Task",
            plano=plano,
            manifesto_atual=None,
            caminho_manifesto=tmp_path / "manifesto.json",
            resposta_confirmacao=resposta,
        )
    assert cliente.chamadas == []


def test_cria_so_as_tasks_pendentes_e_atualiza_manifesto_apos_cada_uma(tmp_path: Path) -> None:
    plano = PlanoTasks(historia_id=100, tasks=(_TASK_A, _TASK_B))
    manifesto_existente = Manifesto(historia_id=100, hash_plano="", criadas={})
    from decompor_tasks.manifesto import calcular_hash_plano

    manifesto_existente = Manifesto(
        historia_id=100, hash_plano=calcular_hash_plano(plano), criadas={"Task A": 501}
    )
    caminho = tmp_path / "manifesto.json"
    cliente = ClienteFalso([502])
    resultado = criar_tasks_pendentes(
        cliente,
        organizacao="org",
        projeto="proj",
        tipo_task="Task",
        plano=plano,
        manifesto_atual=manifesto_existente,
        caminho_manifesto=caminho,
        resposta_confirmacao="AUTORIZAR TASKS #100",
    )
    assert len(cliente.chamadas) == 1  # só a Task B, que ainda não existia
    assert resultado.criadas == {"Task A": 501, "Task B": 502}
    assert ler_manifesto(caminho) == resultado
