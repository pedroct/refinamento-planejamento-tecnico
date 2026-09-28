from typing import Any

from decompor_tasks.ancoragem_horas import sugerir_horas


class ClienteFalso:
    def __init__(self, ids: list[int], itens: dict[int, dict[str, Any]]) -> None:
        self._ids = ids
        self._itens = itens
        self.wiql_recebido: str | None = None

    def consultar_wiql(self, wiql: str) -> list[int]:
        self.wiql_recebido = wiql
        return self._ids

    def ler_work_item(self, work_item_id: int) -> dict[str, Any]:
        return self._itens[work_item_id]


def _task(titulo: str, completed_work: float | None) -> dict[str, Any]:
    fields: dict[str, Any] = {"System.Title": titulo}
    if completed_work is not None:
        fields["Microsoft.VSTS.Scheduling.CompletedWork"] = completed_work
    return {"fields": fields}


def test_sugere_mediana_de_tasks_com_titulo_parecido() -> None:
    itens = {
        1: _task("Criar endpoint de renovação de diligência", 4.0),
        2: _task("Ajustar endpoint de renovação de convite", 6.0),
        3: _task("Corrigir layout do menu lateral", 2.0),  # sem relação lexical
    }
    cliente = ClienteFalso([1, 2, 3], itens)
    sugestao = sugerir_horas(
        cliente,
        projeto="proj",
        area_path="proj\\Time A",
        tipo_task="Task",
        titulo_aproximado="Criar endpoint de renovação de convite",
    )
    assert sugestao.horas == 5.0
    assert sugestao.baseado_em == (1, 2)


def test_ignora_tasks_sem_completed_work() -> None:
    itens = {1: _task("Criar endpoint de renovação", 4.0), 2: _task("Renovação de teste", None)}
    cliente = ClienteFalso([1, 2], itens)
    sugestao = sugerir_horas(
        cliente,
        projeto="proj",
        area_path="proj\\Time A",
        tipo_task="Task",
        titulo_aproximado="Renovação de diligência",
    )
    assert sugestao.horas == 4.0
    assert sugestao.baseado_em == (1,)


def test_sem_titulo_parecido_devolve_none() -> None:
    itens = {1: _task("Corrigir cor do botão", 1.0)}
    cliente = ClienteFalso([1], itens)
    sugestao = sugerir_horas(
        cliente,
        projeto="proj",
        area_path="proj\\Time A",
        tipo_task="Task",
        titulo_aproximado="Criar endpoint de renovação",
    )
    assert sugestao.horas is None
    assert sugestao.baseado_em == ()


def test_sem_nenhum_item_devolve_none() -> None:
    cliente = ClienteFalso([], {})
    sugestao = sugerir_horas(
        cliente,
        projeto="proj",
        area_path="proj\\Time A",
        tipo_task="Task",
        titulo_aproximado="Qualquer coisa",
    )
    assert sugestao.horas is None


def test_consulta_filtra_projeto_area_e_tipo_task() -> None:
    cliente = ClienteFalso([], {})
    sugerir_horas(
        cliente,
        projeto="proj",
        area_path="proj\\Time A",
        tipo_task="Task",
        titulo_aproximado="Qualquer coisa",
    )
    assert cliente.wiql_recebido is not None
    assert "proj\\Time A" in cliente.wiql_recebido
    assert "'Task'" in cliente.wiql_recebido
    assert "Closed" in cliente.wiql_recebido
