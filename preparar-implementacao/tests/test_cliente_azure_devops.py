import httpx
import pytest

from preparar_implementacao.cliente_azure_devops import (
    ClienteAzureDevOps,
    ErroDestinoInvalido,
    ErroFalhaTransitoria,
    ErroRespostaInvalida,
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


def test_consultar_wiql_com_payload_sem_lista_de_work_items_levanta_erro_resposta() -> None:
    handler = httpx.MockTransport(lambda _req: httpx.Response(200, json={"workItems": "nada"}))
    with _cliente(handler) as cliente, pytest.raises(ErroRespostaInvalida):
        cliente.consultar_wiql("SELECT [System.Id] FROM WorkItems")


def test_consultar_wiql_com_item_sem_id_inteiro_levanta_erro_resposta() -> None:
    handler = httpx.MockTransport(
        lambda _req: httpx.Response(200, json={"workItems": [{"id": "não é inteiro"}]})
    )
    with _cliente(handler) as cliente, pytest.raises(ErroRespostaInvalida):
        cliente.consultar_wiql("SELECT [System.Id] FROM WorkItems")


def test_falha_de_rede_esgota_tentativas_e_levanta_erro_transitorio() -> None:
    def handler(_req: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("rede indisponível")

    with (
        _cliente(httpx.MockTransport(handler)) as cliente,
        pytest.raises(ErroFalhaTransitoria),
    ):
        cliente.ler_work_item(1)


def test_http_erro_generico_nao_retentavel_levanta_erro_destino() -> None:
    handler = httpx.MockTransport(lambda _req: httpx.Response(403, text="acesso negado"))
    with _cliente(handler) as cliente, pytest.raises(ErroDestinoInvalido):
        cliente.ler_work_item(1)


def test_resposta_nao_json_levanta_erro_resposta_invalida() -> None:
    handler = httpx.MockTransport(lambda _req: httpx.Response(200, text="isto não é JSON"))
    with _cliente(handler) as cliente, pytest.raises(ErroRespostaInvalida):
        cliente.ler_work_item(1)


def test_resposta_json_que_nao_e_objeto_levanta_erro_resposta_invalida() -> None:
    handler = httpx.MockTransport(lambda _req: httpx.Response(200, json=[1, 2, 3]))
    with _cliente(handler) as cliente, pytest.raises(ErroRespostaInvalida):
        cliente.ler_work_item(1)
