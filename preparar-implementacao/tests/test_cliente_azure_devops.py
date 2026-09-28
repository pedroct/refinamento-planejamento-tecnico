import httpx
import pytest

from preparar_implementacao.cliente_azure_devops import (
    ClienteAzureDevOps,
    ErroDestinoInvalido,
    ErroFalhaTransitoria,
)


def _cliente(handler: httpx.MockTransport) -> ClienteAzureDevOps:
    return ClienteAzureDevOps(
        "minha-org", "meu-projeto", "token", transport=handler, espera_inicial=0.0
    )


def test_ler_work_item_devolve_campos() -> None:
    handler = httpx.MockTransport(
        lambda _req: httpx.Response(200, json={"id": 1, "fields": {"System.Title": "H1"}})
    )
    with _cliente(handler) as cliente:
        assert cliente.ler_work_item(1)["fields"]["System.Title"] == "H1"


def test_ler_work_item_inexistente_levanta_erro_destino() -> None:
    handler = httpx.MockTransport(lambda _req: httpx.Response(404, json={}))
    with _cliente(handler) as cliente, pytest.raises(ErroDestinoInvalido):
        cliente.ler_work_item(999)


def test_falha_transitoria_esgota_tentativas() -> None:
    handler = httpx.MockTransport(lambda _req: httpx.Response(503, json={}))
    with _cliente(handler) as cliente, pytest.raises(ErroFalhaTransitoria):
        cliente.ler_work_item(1)


def test_consultar_wiql_devolve_ids() -> None:
    handler = httpx.MockTransport(
        lambda _req: httpx.Response(200, json={"workItems": [{"id": 3}]})
    )
    with _cliente(handler) as cliente:
        assert cliente.consultar_wiql("SELECT [System.Id] FROM WorkItems") == [3]


def test_cliente_nao_tem_metodo_de_escrita() -> None:
    """Garante em teste a intenção do design: esta skill nunca escreve no Azure Boards."""
    with _cliente(httpx.MockTransport(lambda _req: httpx.Response(200, json={}))) as cliente:
        assert not hasattr(cliente, "gravar_campo")
        assert not hasattr(cliente, "criar_work_item")
