from pathlib import Path

import pytest

from decompor_tasks.manifesto import (
    ErroReconciliacaoNecessaria,
    Manifesto,
    PlanoTasks,
    TaskProposta,
    calcular_hash_plano,
    gravar_manifesto,
    ler_manifesto,
    montar_frase_autorizacao,
    tasks_pendentes,
)

_TASK_A = TaskProposta(titulo="Task A", original_estimate=4.0, remaining=4.0, assigned_to="dev@x")
_TASK_B = TaskProposta(titulo="Task B", original_estimate=2.0, remaining=2.0, assigned_to="dev@x")


def test_hash_e_estavel_para_o_mesmo_plano() -> None:
    plano = PlanoTasks(historia_id=100, tasks=(_TASK_A, _TASK_B))
    assert calcular_hash_plano(plano) == calcular_hash_plano(plano)


def test_hash_muda_quando_o_plano_muda() -> None:
    plano1 = PlanoTasks(historia_id=100, tasks=(_TASK_A,))
    plano2 = PlanoTasks(historia_id=100, tasks=(_TASK_A, _TASK_B))
    assert calcular_hash_plano(plano1) != calcular_hash_plano(plano2)


def test_sem_manifesto_todas_as_tasks_estao_pendentes() -> None:
    plano = PlanoTasks(historia_id=100, tasks=(_TASK_A, _TASK_B))
    assert tasks_pendentes(plano, None) == (_TASK_A, _TASK_B)


def test_com_manifesto_do_mesmo_hash_so_falta_o_que_nao_foi_criado() -> None:
    plano = PlanoTasks(historia_id=100, tasks=(_TASK_A, _TASK_B))
    manifesto = Manifesto(
        historia_id=100, hash_plano=calcular_hash_plano(plano), criadas={"Task A": 501}
    )
    assert tasks_pendentes(plano, manifesto) == (_TASK_B,)


def test_hash_diferente_sem_criadas_reinicia_do_zero() -> None:
    plano = PlanoTasks(historia_id=100, tasks=(_TASK_A, _TASK_B))
    manifesto = Manifesto(historia_id=100, hash_plano="hash-antigo", criadas={})
    assert tasks_pendentes(plano, manifesto) == (_TASK_A, _TASK_B)


def test_hash_diferente_com_criadas_exige_reconciliacao() -> None:
    plano = PlanoTasks(historia_id=100, tasks=(_TASK_A, _TASK_B))
    manifesto = Manifesto(historia_id=100, hash_plano="hash-antigo", criadas={"Task A": 501})
    with pytest.raises(ErroReconciliacaoNecessaria):
        tasks_pendentes(plano, manifesto)


def test_gravar_e_ler_manifesto_preserva_conteudo(tmp_path: Path) -> None:
    caminho = tmp_path / "historia-100.json"
    manifesto = Manifesto(historia_id=100, hash_plano="abc", criadas={"Task A": 501})
    gravar_manifesto(caminho, manifesto)
    lido = ler_manifesto(caminho)
    assert lido == manifesto


def test_gravar_e_ler_manifesto_preserva_em_andamento(tmp_path: Path) -> None:
    caminho = tmp_path / "historia-100.json"
    manifesto = Manifesto(
        historia_id=100,
        hash_plano="abc",
        criadas={"Task A": 501},
        em_andamento=frozenset({"Task B"}),
    )
    gravar_manifesto(caminho, manifesto)
    lido = ler_manifesto(caminho)
    assert lido == manifesto


def test_manifesto_com_task_em_andamento_exige_reconciliacao_e_nomeia_a_task() -> None:
    plano = PlanoTasks(historia_id=100, tasks=(_TASK_A, _TASK_B))
    manifesto = Manifesto(
        historia_id=100,
        hash_plano=calcular_hash_plano(plano),
        criadas={"Task A": 501},
        em_andamento=frozenset({"Task B"}),
    )
    with pytest.raises(ErroReconciliacaoNecessaria, match="Task B"):
        tasks_pendentes(plano, manifesto)


def test_ler_manifesto_inexistente_devolve_none(tmp_path: Path) -> None:
    assert ler_manifesto(tmp_path / "nao-existe.json") is None


def test_frase_de_autorizacao_nomeia_a_historia() -> None:
    frase = montar_frase_autorizacao(100)
    assert "100" in frase
    assert frase.startswith("AUTORIZAR TASKS")
