import httpx
import pytest

from decompor_tasks.cliente_azure_devops import (
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


def test_criar_work_item_envia_post_com_operacoes() -> None:
    capturado: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        capturado["metodo"] = request.method
        capturado["url"] = str(request.url)
        return httpx.Response(200, json={"id": 42})

    with _cliente(httpx.MockTransport(handler)) as cliente:
        resultado = cliente.criar_work_item(
            "Task", [{"op": "add", "path": "/fields/System.Title", "value": "T1"}]
        )
    assert capturado["metodo"] == "POST"
    assert "$Task" in str(capturado["url"])
    assert resultado["id"] == 42


def test_falha_transitoria_esgota_tentativas() -> None:
    handler = httpx.MockTransport(lambda _req: httpx.Response(503, json={}))
    with _cliente(handler) as cliente, pytest.raises(ErroFalhaTransitoria):
        cliente.ler_work_item(1)


def test_consultar_wiql_devolve_ids() -> None:
    handler = httpx.MockTransport(
        lambda _req: httpx.Response(200, json={"workItems": [{"id": 7}]})
    )
    with _cliente(handler) as cliente:
        assert cliente.consultar_wiql("SELECT [System.Id] FROM WorkItems") == [7]


def test_usuario_autenticado_devolve_perfil() -> None:
    handler = httpx.MockTransport(
        lambda _req: httpx.Response(200, json={"emailAddress": "dev@time"})
    )
    with _cliente(handler) as cliente:
        assert cliente.usuario_autenticado()["emailAddress"] == "dev@time"


def test_criar_work_item_nao_retenta_em_falha_transitoria() -> None:
    """Escritas (criar_work_item) nunca devem retentar automaticamente.

    Se Azure DevOps retorna 503 após criar o item, não se sabe se foi realmente criado.
    Retentar causaria duplicação silenciosa. Deve falhar imediatamente após UMA tentativa.
    """
    chamadas = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        chamadas["count"] += 1
        return httpx.Response(503, json={})

    with _cliente(httpx.MockTransport(handler)) as cliente, pytest.raises(ErroFalhaTransitoria):
        cliente.criar_work_item(
            "Task", [{"op": "add", "path": "/fields/System.Title", "value": "T1"}]
        )
    # Deve ter feito exatamente 1 chamada, não 3 (como faria uma leitura retentável)
    assert chamadas["count"] == 1
