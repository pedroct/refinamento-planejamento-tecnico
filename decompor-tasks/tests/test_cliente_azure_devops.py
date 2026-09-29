import httpx
import pytest

from decompor_tasks import cliente_azure_devops
from decompor_tasks.cliente_azure_devops import (
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


def test_consultar_wiql_com_workitems_fora_do_formato_lista_levanta_erro_resposta() -> None:
    handler = httpx.MockTransport(
        lambda _req: httpx.Response(200, json={"workItems": "não é uma lista"})
    )
    with _cliente(handler) as cliente, pytest.raises(ErroRespostaInvalida):
        cliente.consultar_wiql("SELECT [System.Id] FROM WorkItems")


def test_consultar_wiql_com_item_sem_id_inteiro_levanta_erro_resposta() -> None:
    handler = httpx.MockTransport(
        lambda _req: httpx.Response(200, json={"workItems": [{"id": "não-é-inteiro"}]})
    )
    with _cliente(handler) as cliente, pytest.raises(ErroRespostaInvalida):
        cliente.consultar_wiql("SELECT [System.Id] FROM WorkItems")


def test_criar_work_item_com_erro_de_rede_levanta_falha_transitoria_sem_retry() -> None:
    """`criar_work_item` usa `_executar_sem_retry`: um `httpx.RequestError` (rede indisponível,
    DNS, etc.) deve virar `ErroFalhaTransitoria` numa única tentativa."""

    def handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("rede indisponível")

    with _cliente(httpx.MockTransport(handler)) as cliente, pytest.raises(ErroFalhaTransitoria):
        cliente.criar_work_item(
            "Task", [{"op": "add", "path": "/fields/System.Title", "value": "T1"}]
        )


def test_leitura_com_erro_de_rede_persistente_esgota_tentativas_e_levanta_falha_transitoria() -> (
    None
):
    """`ler_work_item` usa `_executar_com_retry`: um `httpx.RequestError` que se repete em
    todas as tentativas deve virar `ErroFalhaTransitoria` só depois da última."""
    chamadas = {"count": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        chamadas["count"] += 1
        raise httpx.ConnectError("rede indisponível")

    with _cliente(httpx.MockTransport(handler)) as cliente, pytest.raises(ErroFalhaTransitoria):
        cliente.ler_work_item(1)
    assert chamadas["count"] == 3


def test_leitura_com_erro_de_rede_transitorio_retenta_e_depois_funciona() -> None:
    """Falha de rede nas primeiras tentativas, sucesso na última: cobre o ramo do `except
    httpx.RequestError` em que a tentativa NÃO é a última (nenhuma exceção é levantada ali,
    só espera e tenta de novo)."""
    chamadas = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        chamadas["count"] += 1
        if chamadas["count"] < 2:
            raise httpx.ConnectError("rede indisponível")
        return httpx.Response(200, json={"id": 1, "fields": {}})

    with _cliente(httpx.MockTransport(handler)) as cliente:
        assert cliente.ler_work_item(1)["id"] == 1
    assert chamadas["count"] == 2


def test_com_max_tentativas_zero_levanta_erro_defensivo(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ramo defensivo: com o padrão de retentativa atual, o `for tentativa in
    range(_MAX_TENTATIVAS)` sempre termina em `return` (sucesso) ou `raise` (última tentativa
    falhou) dentro do laço — o `raise ErroFalhaTransitoria(...)` depois do `for` é
    inalcançável com `_MAX_TENTATIVAS >= 1`. Só forçando `_MAX_TENTATIVAS = 0` o laço não
    executa nenhuma vez e o código cai nesse `raise` final."""
    monkeypatch.setattr(cliente_azure_devops, "_MAX_TENTATIVAS", 0)
    handler = httpx.MockTransport(lambda _req: httpx.Response(200, json={}))
    with _cliente(handler) as cliente, pytest.raises(ErroFalhaTransitoria):
        cliente.ler_work_item(1)


def test_resposta_http_erro_generico_nao_404_levanta_erro_destino() -> None:
    handler = httpx.MockTransport(lambda _req: httpx.Response(401, text="não autorizado"))
    with _cliente(handler) as cliente, pytest.raises(ErroDestinoInvalido):
        cliente.usuario_autenticado()


def test_resposta_com_corpo_nao_json_levanta_erro_resposta_invalida() -> None:
    handler = httpx.MockTransport(
        lambda _req: httpx.Response(200, content=b"isto nao e json", headers={})
    )
    with _cliente(handler) as cliente, pytest.raises(ErroRespostaInvalida):
        cliente.usuario_autenticado()


def test_resposta_json_que_nao_e_objeto_levanta_erro_resposta_invalida() -> None:
    handler = httpx.MockTransport(lambda _req: httpx.Response(200, json=[1, 2, 3]))
    with _cliente(handler) as cliente, pytest.raises(ErroRespostaInvalida):
        cliente.usuario_autenticado()
