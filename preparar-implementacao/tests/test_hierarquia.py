from typing import Any

import pytest

from preparar_implementacao.hierarquia import ErroHierarquiaIncompleta, subir_ate_demanda


class ClienteFalso:
    def __init__(self, itens: dict[int, dict[str, Any]]) -> None:
        self._itens = itens

    def ler_work_item(self, work_item_id: int) -> dict[str, Any]:
        return self._itens[work_item_id]


def _item(work_item_id: int, tipo: str, pai: int | None) -> dict[str, Any]:
    relations = []
    if pai is not None:
        relations.append(
            {
                "rel": "System.LinkTypes.Hierarchy-Reverse",
                "url": f"https://dev.azure.com/org/proj/_apis/wit/workItems/{pai}",
            }
        )
    return {
        "id": work_item_id,
        "fields": {"System.WorkItemType": tipo, "System.Title": f"Item {work_item_id}"},
        "relations": relations,
    }


def test_sobe_a_cadeia_ate_a_demanda() -> None:
    itens = {
        1: _item(1, "User Story", pai=2),
        2: _item(2, "Feature", pai=3),
        3: _item(3, "Epic", pai=4),
        4: _item(4, "Demanda de Negócio", pai=None),
    }
    cliente = ClienteFalso(itens)
    cadeia = subir_ate_demanda(cliente, 1, "Demanda de Negócio")
    assert [item["id"] for item in cadeia] == [1, 2, 3, 4]


def test_cadeia_quebrada_antes_da_demanda_levanta_erro() -> None:
    itens = {1: _item(1, "User Story", pai=2), 2: _item(2, "Feature", pai=None)}
    cliente = ClienteFalso(itens)
    with pytest.raises(ErroHierarquiaIncompleta):
        subir_ate_demanda(cliente, 1, "Demanda de Negócio")


def test_item_ja_e_a_demanda() -> None:
    itens = {4: _item(4, "Demanda de Negócio", pai=None)}
    cliente = ClienteFalso(itens)
    cadeia = subir_ate_demanda(cliente, 4, "Demanda de Negócio")
    assert [item["id"] for item in cadeia] == [4]
