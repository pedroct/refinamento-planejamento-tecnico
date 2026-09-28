from typing import Any

from refinar_tecnicamente.ancoragem_story_points import sugerir_story_points


class ClienteFalso:
    """Substitui ClienteAzureDevOps nos testes: devolve o que os dicionários definem."""

    def __init__(self, ids: list[int], itens: dict[int, dict[str, Any]]) -> None:
        self._ids = ids
        self._itens = itens
        self.wiql_recebido: str | None = None

    def consultar_wiql(self, wiql: str) -> list[int]:
        self.wiql_recebido = wiql
        return self._ids

    def ler_work_item(self, work_item_id: int) -> dict[str, Any]:
        return self._itens[work_item_id]


def _item(story_points: float | None) -> dict[str, Any]:
    fields: dict[str, Any] = {"System.Title": "Item fechado"}
    if story_points is not None:
        fields["Microsoft.VSTS.Scheduling.StoryPoints"] = story_points
    return {"fields": fields}


def test_sugere_mediana_dos_itens_com_pontuacao() -> None:
    itens = {1: _item(3.0), 2: _item(5.0), 3: _item(8.0)}
    cliente = ClienteFalso([1, 2, 3], itens)
    sugestao = sugerir_story_points(
        cliente, projeto="proj", area_path="proj\\Time A", tipos=("User Story", "Bug")
    )
    assert sugestao.pontos == 5.0
    assert sugestao.baseado_em == (1, 2, 3)


def test_ignora_itens_sem_story_points() -> None:
    itens = {1: _item(3.0), 2: _item(None)}
    cliente = ClienteFalso([1, 2], itens)
    sugestao = sugerir_story_points(
        cliente, projeto="proj", area_path="proj\\Time A", tipos=("User Story",)
    )
    assert sugestao.pontos == 3.0
    assert sugestao.baseado_em == (1,)


def test_sem_nenhum_comparavel_devolve_none() -> None:
    cliente = ClienteFalso([], {})
    sugestao = sugerir_story_points(
        cliente, projeto="proj", area_path="proj\\Time A", tipos=("User Story",)
    )
    assert sugestao.pontos is None
    assert sugestao.baseado_em == ()


def test_todos_sem_pontuacao_e_tratado_como_sem_comparavel() -> None:
    itens = {1: _item(None), 2: _item(None)}
    cliente = ClienteFalso([1, 2], itens)
    sugestao = sugerir_story_points(
        cliente, projeto="proj", area_path="proj\\Time A", tipos=("User Story",)
    )
    assert sugestao.pontos is None
    assert sugestao.baseado_em == ()


def test_consulta_filtra_projeto_area_e_estados_fechados() -> None:
    cliente = ClienteFalso([], {})
    sugerir_story_points(
        cliente, projeto="proj", area_path="proj\\Time A", tipos=("User Story", "Bug")
    )
    assert cliente.wiql_recebido is not None
    assert "proj" in cliente.wiql_recebido
    assert "proj\\Time A" in cliente.wiql_recebido
    assert "User Story" in cliente.wiql_recebido
    assert "Bug" in cliente.wiql_recebido
    assert "Closed" in cliente.wiql_recebido


def test_respeita_o_limite_de_itens_consultados() -> None:
    ids = list(range(1, 31))
    itens = {i: _item(float(i)) for i in ids}
    cliente = ClienteFalso(ids, itens)
    sugestao = sugerir_story_points(
        cliente, projeto="proj", area_path="proj\\Time A", tipos=("User Story",), limite=5
    )
    assert len(sugestao.baseado_em) == 5


def test_ignora_item_com_story_points_nao_numerico() -> None:
    # Item 1 tem Story Points válido (3.0), item 2 tem string (deve ser ignorado),
    # item 3 tem Story Points válido (7.0). Mediana deve ser calculada apenas dos 2 válidos.
    itens = {
        1: _item(3.0),
        2: {"fields": {"System.Title": "Item com SP inválido", "Microsoft.VSTS.Scheduling.StoryPoints": "grande"}},
        3: _item(7.0),
    }
    cliente = ClienteFalso([1, 2, 3], itens)
    sugestao = sugerir_story_points(
        cliente, projeto="proj", area_path="proj\\Time A", tipos=("User Story",)
    )
    # Mediana de [3.0, 7.0] é 5.0; item 2 deve ser excluído
    assert sugestao.pontos == 5.0
    assert sugestao.baseado_em == (1, 3)
