import json

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


def test_resposta_json_que_nao_e_objeto_levanta_erro_resposta_invalida() -> None:
    handler = httpx.MockTransport(lambda _req: httpx.Response(200, json=[1, 2, 3]))
    with _cliente(handler) as cliente, pytest.raises(ErroRespostaInvalida):
        cliente.ler_work_item(1)


def test_erro_http_generico_no_get_levanta_erro_destino_invalido() -> None:
    """403 não é 404 nem um código retentável — deve virar ErroDestinoInvalido direto,
    passando pelo ramo genérico `>= 400` de `_verificar_e_decodificar`."""
    handler = httpx.MockTransport(lambda _req: httpx.Response(403, text="proibido"))
    with _cliente(handler) as cliente, pytest.raises(ErroDestinoInvalido):
        cliente.ler_work_item(1)


def test_erro_de_rede_em_chamada_retentavel_esgota_tentativas() -> None:
    chamadas = {"n": 0}

    def handler(_req: httpx.Request) -> httpx.Response:
        chamadas["n"] += 1
        raise httpx.RequestError("falha de rede simulada")

    with _cliente(httpx.MockTransport(handler)) as cliente, pytest.raises(ErroFalhaTransitoria):
        cliente.ler_work_item(1)
    assert chamadas["n"] == 3


def test_erro_de_rede_em_chamada_nao_retentavel_levanta_na_primeira_tentativa() -> None:
    chamadas = {"n": 0}

    def handler(_req: httpx.Request) -> httpx.Response:
        chamadas["n"] += 1
        raise httpx.RequestError("falha de rede simulada")

    with _cliente(httpx.MockTransport(handler)) as cliente, pytest.raises(ErroFalhaTransitoria):
        cliente.gravar_campo(5, "Custom.DemandaSpecTecnica", "<p>spec</p>")
    assert chamadas["n"] == 1


def test_retry_sem_nenhuma_tentativa_disponivel_levanta_erro_generico(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Guarda de robustez: se `_MAX_TENTATIVAS` fosse 0 (não é, é uma constante fixa em 3),
    o laço de retry nem chegaria a rodar uma vez, caindo no `raise` de fallback ao final de
    `_executar_com_retry`. Cobre essa linha defensiva sem depender de rede real."""
    import refinar_tecnicamente.cliente_azure_devops as modulo

    monkeypatch.setattr(modulo, "_MAX_TENTATIVAS", 0)
    handler = httpx.MockTransport(lambda _req: httpx.Response(200, json={"id": 1}))
    with _cliente(handler) as cliente, pytest.raises(ErroFalhaTransitoria) as excinfo:
        cliente.ler_work_item(1)
    assert "não se completou." in str(excinfo.value)


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


def test_consultar_wiql_sem_lista_workitems_levanta_erro_resposta_invalida() -> None:
    handler = httpx.MockTransport(lambda _req: httpx.Response(200, json={"workItems": "x"}))
    with _cliente(handler) as cliente, pytest.raises(ErroRespostaInvalida):
        cliente.consultar_wiql("SELECT [System.Id] FROM WorkItems")


def test_consultar_wiql_com_item_sem_id_inteiro_levanta_erro_resposta_invalida() -> None:
    handler = httpx.MockTransport(
        lambda _req: httpx.Response(200, json={"workItems": [{"id": "não é inteiro"}]})
    )
    with _cliente(handler) as cliente, pytest.raises(ErroRespostaInvalida):
        cliente.consultar_wiql("SELECT [System.Id] FROM WorkItems")


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


def test_gravar_campo_declara_multilineFieldsFormat_markdown() -> None:
    """Sem essa segunda operação no PATCH, o Azure DevOps assume HTML por padrão (documentado
    em https://devblogs.microsoft.com/devops/markdown-support-arrives-for-work-items/) — texto
    Markdown puro gravado sem essa declaração tem toda quebra de linha colapsada, porque é
    interpretado como HTML sem tags de bloco. Comprovado ao vivo na Demanda 14064: uma gravação
    de teste sem essa propriedade achatou um texto de 3 linhas em uma linha só."""
    capturado: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        capturado["corpo"] = json.loads(request.read())
        return httpx.Response(200, json={"id": 5})

    with _cliente(httpx.MockTransport(handler)) as cliente:
        cliente.gravar_campo(5, "Custom.DemandaSpecTecnica", "linha um\n\nlinha dois")

    corpo = capturado["corpo"]
    assert corpo == [
        {
            "op": "replace",
            "path": "/fields/Custom.DemandaSpecTecnica",
            "value": "linha um\n\nlinha dois",
        },
        {
            "op": "add",
            "path": "/multilineFieldsFormat/Custom.DemandaSpecTecnica",
            "value": "Markdown",
        },
    ]


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


def test_anexar_arquivo_faz_upload_e_vincula_ao_work_item() -> None:
    chamadas: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        chamadas.append((request.method, str(request.url)))
        if request.method == "POST":
            assert "attachments" in str(request.url)
            assert "fileName=spec.md" in str(request.url)
            assert request.headers["content-type"] == "application/octet-stream"
            assert request.read() == b"# Spec\n"
            return httpx.Response(200, json={"id": "abc", "url": "https://dev.azure.com/anexo/abc"})
        assert request.method == "PATCH"
        corpo = json.loads(request.read())
        assert corpo[0]["op"] == "add"
        assert corpo[0]["path"] == "/relations/-"
        assert corpo[0]["value"]["rel"] == "AttachedFile"
        assert corpo[0]["value"]["url"] == "https://dev.azure.com/anexo/abc"
        assert corpo[0]["value"]["attributes"]["comment"] == "spec.md"
        return httpx.Response(200, json={"id": 5})

    with _cliente(httpx.MockTransport(handler)) as cliente:
        cliente.anexar_arquivo(5, "spec.md", b"# Spec\n")
    assert [m for m, _ in chamadas] == ["POST", "PATCH"]


def test_anexar_arquivo_com_upload_sem_url_levanta_erro_resposta_invalida() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST":
            return httpx.Response(200, json={"id": "abc"})  # sem "url"
        raise AssertionError("PATCH não deveria ser chamado sem URL de anexo válida")

    with _cliente(httpx.MockTransport(handler)) as cliente, pytest.raises(ErroRespostaInvalida):
        cliente.anexar_arquivo(5, "spec.md", b"# Spec\n")


def test_anexar_arquivo_com_erro_de_rede_no_upload_levanta_erro_falha_transitoria() -> None:
    def handler(_req: httpx.Request) -> httpx.Response:
        raise httpx.RequestError("falha de rede simulada")

    with _cliente(httpx.MockTransport(handler)) as cliente, pytest.raises(ErroFalhaTransitoria):
        cliente.anexar_arquivo(5, "spec.md", b"conteudo")


def test_anexar_arquivo_nao_retenta_upload_em_falha_transitoria() -> None:
    chamadas = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        chamadas["n"] += 1
        return httpx.Response(503, json={})

    with _cliente(httpx.MockTransport(handler)) as cliente, pytest.raises(ErroFalhaTransitoria):
        cliente.anexar_arquivo(5, "spec.md", b"conteudo")
    assert chamadas["n"] == 1


def test_anexar_arquivo_com_upload_ok_e_vinculo_falho_nao_retenta_nenhum_dos_dois() -> None:
    """O POST já foi aceito quando o PATCH de vínculo falha — o blob fica órfão no Azure
    Boards. A chamada deve relatar isso e parar, nunca repetir o POST nem o PATCH sozinha."""
    chamadas: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        chamadas.append(request.method)
        if request.method == "POST":
            return httpx.Response(200, json={"url": "https://dev.azure.com/anexo/abc"})
        return httpx.Response(503, json={})

    with _cliente(httpx.MockTransport(handler)) as cliente, pytest.raises(ErroFalhaTransitoria):
        cliente.anexar_arquivo(5, "spec.md", b"conteudo")
    assert chamadas == ["POST", "PATCH"]


def test_baixar_anexo_sem_nenhum_anexo_devolve_none() -> None:
    handler = httpx.MockTransport(
        lambda _req: httpx.Response(200, json={"id": 5, "fields": {}, "relations": []})
    )
    with _cliente(handler) as cliente:
        assert cliente.baixar_anexo(5, "spec.md") is None


def test_baixar_anexo_com_relations_ausente_devolve_none() -> None:
    """`relations` nem sempre vem no payload (work item sem nenhuma relação) — o campo
    ausente vira `None`, que não é uma lista; não deve ser tratado como anexo encontrado."""
    handler = httpx.MockTransport(lambda _req: httpx.Response(200, json={"id": 5, "fields": {}}))
    with _cliente(handler) as cliente:
        assert cliente.baixar_anexo(5, "spec.md") is None


def test_baixar_anexo_ignora_relacoes_de_outro_tipo_e_de_outro_arquivo() -> None:
    handler = httpx.MockTransport(
        lambda _req: httpx.Response(
            200,
            json={
                "id": 5,
                "fields": {},
                "relations": [
                    {"rel": "Related", "url": "https://dev.azure.com/x", "attributes": {}},
                    {
                        "rel": "AttachedFile",
                        "url": "https://dev.azure.com/anexo/attachments/outro",
                        "attributes": {"comment": "backlog.md"},
                    },
                    {"rel": "AttachedFile", "url": "https://dev.azure.com/sem-atributos"},
                ],
            },
        )
    )
    with _cliente(handler) as cliente:
        assert cliente.baixar_anexo(5, "spec.md") is None


def test_baixar_anexo_inexistente_levanta_erro_destino_invalido_em_404() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if "attachments/abc" in str(request.url):
            return httpx.Response(404, json={})
        return httpx.Response(
            200,
            json={
                "id": 5,
                "fields": {},
                "relations": [
                    {
                        "rel": "AttachedFile",
                        "url": "https://dev.azure.com/anexo/attachments/abc",
                        "attributes": {"comment": "spec.md"},
                    }
                ],
            },
        )

    with _cliente(httpx.MockTransport(handler)) as cliente, pytest.raises(ErroDestinoInvalido):
        cliente.baixar_anexo(5, "spec.md")


def test_baixar_anexo_com_erro_http_generico_levanta_erro_destino_invalido() -> None:
    """403 não está entre os códigos retentáveis (408/429/500/502/503/504) — deve virar
    ErroDestinoInvalido de imediato, sem esgotar as 3 tentativas de retry."""

    def handler(request: httpx.Request) -> httpx.Response:
        if "attachments/abc" in str(request.url):
            return httpx.Response(403, json={})
        return httpx.Response(
            200,
            json={
                "id": 5,
                "fields": {},
                "relations": [
                    {
                        "rel": "AttachedFile",
                        "url": "https://dev.azure.com/anexo/attachments/abc",
                        "attributes": {"comment": "spec.md"},
                    }
                ],
            },
        )

    with _cliente(httpx.MockTransport(handler)) as cliente, pytest.raises(ErroDestinoInvalido):
        cliente.baixar_anexo(5, "spec.md")


def test_baixar_anexo_devolve_conteudo_do_anexo_existente() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if "attachments/abc" in str(request.url):
            return httpx.Response(200, content=b"# Spec\n")
        return httpx.Response(
            200,
            json={
                "id": 5,
                "fields": {},
                "relations": [
                    {
                        "rel": "AttachedFile",
                        "url": "https://dev.azure.com/anexo/attachments/abc",
                        "attributes": {"comment": "spec.md"},
                    }
                ],
            },
        )

    with _cliente(httpx.MockTransport(handler)) as cliente:
        conteudo = cliente.baixar_anexo(5, "spec.md")
    assert conteudo == b"# Spec\n"


def test_baixar_anexo_com_varios_do_mesmo_nome_pega_o_ultimo() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if "attachments/novo" in str(request.url):
            return httpx.Response(200, content=b"versao nova")
        if "attachments/velho" in str(request.url):
            return httpx.Response(200, content=b"versao velha")
        return httpx.Response(
            200,
            json={
                "id": 5,
                "fields": {},
                "relations": [
                    {
                        "rel": "AttachedFile",
                        "url": "https://dev.azure.com/anexo/attachments/velho",
                        "attributes": {"comment": "spec.md"},
                    },
                    {
                        "rel": "AttachedFile",
                        "url": "https://dev.azure.com/anexo/attachments/novo",
                        "attributes": {"comment": "spec.md"},
                    },
                ],
            },
        )

    with _cliente(httpx.MockTransport(handler)) as cliente:
        conteudo = cliente.baixar_anexo(5, "spec.md")
    assert conteudo == b"versao nova"
