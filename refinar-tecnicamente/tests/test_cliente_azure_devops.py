import httpx
import pytest

from refinar_tecnicamente.cliente_azure_devops import (
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
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert "/workitems/123" in str(request.url)
        return httpx.Response(200, json={"id": 123, "fields": {"System.Title": "Item"}})

    with _cliente(httpx.MockTransport(handler)) as cliente:
        corpo = cliente.ler_work_item(123)
    assert corpo["fields"]["System.Title"] == "Item"


def test_ler_work_item_inexistente_levanta_erro_destino() -> None:
    handler = httpx.MockTransport(lambda _req: httpx.Response(404, json={}))
    with _cliente(handler) as cliente, pytest.raises(ErroDestinoInvalido):
        cliente.ler_work_item(999)


def test_falha_transitoria_esgota_tentativas() -> None:
    chamadas = {"n": 0}

    def handler(_req: httpx.Request) -> httpx.Response:
        chamadas["n"] += 1
        return httpx.Response(503, json={})

    with _cliente(httpx.MockTransport(handler)) as cliente, pytest.raises(ErroFalhaTransitoria):
        cliente.ler_work_item(1)
    assert chamadas["n"] == 3


def test_resposta_nao_json_levanta_erro_resposta_invalida() -> None:
    handler = httpx.MockTransport(lambda _req: httpx.Response(200, text="não é json"))
    with _cliente(handler) as cliente, pytest.raises(ErroRespostaInvalida):
        cliente.ler_work_item(1)


def test_consultar_wiql_devolve_ids_na_ordem() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert "wiql" in str(request.url)
        return httpx.Response(200, json={"workItems": [{"id": 10}, {"id": 20}]})

    with _cliente(httpx.MockTransport(handler)) as cliente:
        ids = cliente.consultar_wiql("SELECT [System.Id] FROM WorkItems")
    assert ids == [10, 20]


def test_consultar_wiql_sem_resultado_devolve_lista_vazia() -> None:
    handler = httpx.MockTransport(lambda _req: httpx.Response(200, json={"workItems": []}))
    with _cliente(handler) as cliente:
        assert cliente.consultar_wiql("SELECT [System.Id] FROM WorkItems") == []


def test_gravar_campo_envia_json_patch() -> None:
    capturado: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        capturado["metodo"] = request.method
        capturado["content_type"] = request.headers["content-type"]
        capturado["corpo"] = request.read()
        return httpx.Response(200, json={"id": 5})

    with _cliente(httpx.MockTransport(handler)) as cliente:
        cliente.gravar_campo(5, "Custom.DemandaSpecTecnica", "<p>spec</p>")
    assert capturado["metodo"] == "PATCH"
    assert capturado["content_type"] == "application/json-patch+json"
    assert b"Custom.DemandaSpecTecnica" in capturado["corpo"]  # type: ignore[operator]


def test_gravar_campo_nao_retenta_em_falha_transitoria() -> None:
    """Escritas (gravar_campo) nunca devem retentar automaticamente.

    Se o Azure DevOps retorna 503 após aplicar o PATCH, não se sabe se a escrita foi
    realmente aplicada. Retentar arriscaria mascarar essa ambiguidade. Deve falhar
    imediatamente após UMA tentativa.
    """
    chamadas = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        chamadas["count"] += 1
        return httpx.Response(503, json={})

    with _cliente(httpx.MockTransport(handler)) as cliente, pytest.raises(ErroFalhaTransitoria):
        cliente.gravar_campo(5, "Custom.DemandaSpecTecnica", "<p>spec</p>")
    # Deve ter feito exatamente 1 chamada, não 3 (como faria uma leitura retentável)
    assert chamadas["count"] == 1


def test_usuario_autenticado_devolve_perfil() -> None:
    handler = httpx.MockTransport(
        lambda _req: httpx.Response(200, json={"displayName": "Pedro", "emailAddress": "p@x"})
    )
    with _cliente(handler) as cliente:
        perfil = cliente.usuario_autenticado()
    assert perfil["emailAddress"] == "p@x"
