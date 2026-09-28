from typing import Any

from preparar_implementacao.contexto import extrair_campo_demanda, ids_tasks_filhas, ler_tasks


def _demanda(campos_extra: dict[str, Any]) -> dict[str, Any]:
    fields = {"System.WorkItemType": "Demanda de Negócio", **campos_extra}
    return {"id": 4, "fields": fields}


def test_extrai_campo_presente_na_demanda() -> None:
    cadeia = [
        {"id": 1, "fields": {"System.WorkItemType": "User Story"}},
        _demanda({"Custom.DemandaSpecTecnica": "<p>abordagem</p>"}),
    ]
    valor = extrair_campo_demanda(cadeia, "Demanda de Negócio", "Custom.DemandaSpecTecnica")
    assert valor == "<p>abordagem</p>"


def test_campo_ausente_devolve_none() -> None:
    cadeia = [_demanda({})]
    assert extrair_campo_demanda(cadeia, "Demanda de Negócio", "Custom.DemandaSpecTecnica") is None


def test_cadeia_sem_demanda_devolve_none() -> None:
    cadeia = [{"id": 1, "fields": {"System.WorkItemType": "User Story"}}]
    assert extrair_campo_demanda(cadeia, "Demanda de Negócio", "Custom.DemandaSpecTecnica") is None


def test_ids_tasks_filhas_le_relacoes_para_frente() -> None:
    historia = {
        "id": 1,
        "relations": [
            {
                "rel": "System.LinkTypes.Hierarchy-Forward",
                "url": "https://dev.azure.com/org/proj/_apis/wit/workItems/10",
            },
            {
                "rel": "System.LinkTypes.Hierarchy-Reverse",
                "url": "https://dev.azure.com/org/proj/_apis/wit/workItems/2",
            },
            {
                "rel": "System.LinkTypes.Hierarchy-Forward",
                "url": "https://dev.azure.com/org/proj/_apis/wit/workItems/11",
            },
        ],
    }
    assert ids_tasks_filhas(historia) == [10, 11]


def test_ids_tasks_filhas_sem_relacoes_devolve_lista_vazia() -> None:
    assert ids_tasks_filhas({"id": 1, "relations": []}) == []


def test_ler_tasks_busca_cada_id() -> None:
    class ClienteFalso:
        def ler_work_item(self, work_item_id: int) -> dict[str, Any]:
            return {"id": work_item_id, "fields": {"System.Title": f"Task {work_item_id}"}}

    tasks = ler_tasks(ClienteFalso(), [10, 11])
    assert [t["id"] for t in tasks] == [10, 11]
