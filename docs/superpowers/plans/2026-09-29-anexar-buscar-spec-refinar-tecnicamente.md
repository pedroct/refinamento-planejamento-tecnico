# Anexar e buscar spec.md/backlog.md via Demanda (refinar-tecnicamente) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fazer `refinar-tecnicamente` resolver `spec.md`/`backlog.md` de uma Demanda só pelo ID, anexando-os à Demanda a cada gravação confirmada e baixando o anexo mais recente quando a pasta local `docs/specs/DN-<id>-<slug>/` não existir.

**Architecture:** Duas capacidades novas em `ClienteAzureDevOps` (`anexar_arquivo`, `baixar_anexo`), reaproveitando o padrão de retry existente (retentável para leitura, sem retry para escrita). `gravar_spec_tecnica` passa a anexar como parte da mesma operação já confirmada. Um módulo novo e puro (`resolver_spec.py`) decide entre pasta local e anexo remoto, consumido por um subcomando novo da CLI. O `SKILL.md` passa a apontar para esse subcomando no passo 1, em vez de perguntar caminho manualmente ou sugerir `gerador-hu`.

**Tech Stack:** Python 3.12, `httpx` (já em uso), `pytest`, `argparse` — nenhuma dependência nova.

**Spec:** `/Volumes/DOCK/Projetos/pessoal/refinamento-planejamento-tecnico/docs/superpowers/specs/2026-09-29-anexar-spec-demanda-azure-boards-design.md`

## Global Constraints

- Escrita no Azure Boards (`anexar_arquivo`) é sempre uma única tentativa, sem retry automático — mesmo raciocínio já documentado em `gravar_campo`: um 5xx após o `POST`/`PATCH` já ter sido aceito pelo servidor é ambíguo.
- Leitura (`baixar_anexo`, listagem de `relations` via `ler_work_item`) usa o retry com backoff já existente.
- Nome do anexo é sempre `spec.md` ou `backlog.md`, nunca outro vocabulário.
- `resolver-spec` nunca pede caminho manualmente nem sugere rodar `gerador-hu`; só devolve o caminho resolvido ou recusa com mensagem clara.
- `decompor-tasks` e `preparar-implementacao` não são tocados por este plano — confirmado que não dependem de arquivo local.
- Nenhuma dependência nova (`httpx` já é usada pelo pacote).

## Review Focus

- **PATCH de vínculo falha depois do POST de upload ter sido aceito** — o blob fica no Azure Boards sem estar vinculado ao work item; a chamada deve reportar isso como falha, nunca reexecutar sozinha nem fingir sucesso.
- **Duas ou mais rodadas de refinamento acumulam vários anexos `spec.md`** — `baixar_anexo` deve sempre servir o mais recente (último da lista `relations`, já que o Azure Boards sempre acrescenta ao final), nunca o primeiro.
- **`--raiz` aponta para um diretório sem `docs/specs/`** — `localizar_pasta_local` deve tratar como "não encontrado", nunca lançar uma exceção de arquivo/diretório inexistente.
- **Duas pastas locais colidem no mesmo ID de Demanda** (`DN-13959-slug-antigo/` e `DN-13959-slug-novo/` coexistindo) — deve recusar com `ErroPastaAmbigua`, nunca escolher uma silenciosamente.
- **Nem pasta local nem anexo existem** (Demanda nunca teve spec gerada, ou ID errado) — `resolver_spec` deve levantar `ErroSpecNaoEncontrada` com mensagem que nomeia a Demanda e onde procurou, nunca um erro genérico de atributo/tipo.

---

### Task 1: `anexar_arquivo` no cliente Azure DevOps

**Files:**
- Modify: `refinar-tecnicamente/src/refinar_tecnicamente/cliente_azure_devops.py:9-20` (imports), depois de `gravar_campo` (linha 111), e a área dos métodos privados (linha 134-136)
- Test: `refinar-tecnicamente/tests/test_cliente_azure_devops.py`

**Interfaces:**
- Consumes: nada de tasks anteriores.
- Produces: `ClienteAzureDevOps.anexar_arquivo(work_item_id: int, nome_arquivo: str, conteudo: bytes) -> None` — upload (POST binário) + vínculo (PATCH de `relations`), uma única tentativa em cada chamada, sem retry.

- [ ] **Step 1: Escrever o teste que falha**

```python
def test_anexar_arquivo_faz_upload_e_vincula_ao_work_item() -> None:
    chamadas: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        chamadas.append((request.method, str(request.url)))
        if request.method == "POST":
            assert "attachments" in str(request.url)
            assert "fileName=spec.md" in str(request.url)
            assert request.headers["content-type"] == "application/octet-stream"
            assert request.read() == b"# Spec\n"
            return httpx.Response(
                200, json={"id": "abc", "url": "https://dev.azure.com/anexo/abc"}
            )
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
```

Adicione `import json` no topo de `tests/test_cliente_azure_devops.py`.

- [ ] **Step 2: Rodar o teste e confirmar que falha**

Run: `cd refinar-tecnicamente && uv run pytest tests/test_cliente_azure_devops.py::test_anexar_arquivo_faz_upload_e_vincula_ao_work_item -v`
Expected: FAIL — `AttributeError: 'ClienteAzureDevOps' object has no attribute 'anexar_arquivo'`

- [ ] **Step 3: Implementar**

Em `cliente_azure_devops.py`, adicione o import (linha 15, junto de `httpx`):

```python
from urllib.parse import quote
```

Depois de `gravar_campo` (após a linha 111, antes de `usuario_autenticado`):

```python
    def anexar_arquivo(self, work_item_id: int, nome_arquivo: str, conteudo: bytes) -> None:
        """Anexa um arquivo ao work item: upload (POST) seguido de vínculo (PATCH).

        Duas chamadas, cada uma numa única tentativa sem retry automático — mesmo raciocínio
        de `gravar_campo`: depois que o POST de upload é aceito pelo servidor, um 5xx no PATCH
        de vínculo deixa um blob órfão (aceito, mas não vinculado ao work item); repetir
        sozinho arriscaria mascarar essa ambiguidade ou duplicar o upload.
        """
        url_upload = (
            f"https://dev.azure.com/{self._organizacao}/{self._projeto}"
            f"/_apis/wit/attachments?fileName={quote(nome_arquivo, safe='')}"
            f"&api-version={_VERSAO_API}"
        )
        resposta_upload = self._executar_binario_sem_retry("POST", url_upload, conteudo)
        payload_upload = self._verificar_e_decodificar(resposta_upload, work_item_id)
        url_anexo = payload_upload.get("url")
        if not isinstance(url_anexo, str) or not url_anexo:
            raise ErroRespostaInvalida("O upload do anexo não devolveu uma URL válida.")
        url_vinculo = (
            f"https://dev.azure.com/{self._organizacao}/{self._projeto}"
            f"/_apis/wit/workitems/{work_item_id}?api-version={_VERSAO_API}"
        )
        payload_vinculo = [
            {
                "op": "add",
                "path": "/relations/-",
                "value": {
                    "rel": "AttachedFile",
                    "url": url_anexo,
                    "attributes": {"comment": nome_arquivo},
                },
            }
        ]
        resposta_vinculo = self._executar(
            "PATCH",
            url_vinculo,
            corpo=payload_vinculo,
            content_type="application/json-patch+json",
            retentavel=False,
        )
        self._verificar_e_decodificar(resposta_vinculo, work_item_id)
```

Na área dos métodos privados (depois de `_executar`, linha 134, antes de `_executar_sem_retry`):

```python
    def _executar_binario_sem_retry(
        self, metodo: str, url: str, conteudo: bytes
    ) -> httpx.Response:
        """Uma única tentativa sem retry, para upload de conteúdo binário (anexos)."""
        headers = {"Content-Type": "application/octet-stream"}
        try:
            resposta = self._cliente.request(metodo, url, content=conteudo, headers=headers)
        except httpx.RequestError as erro:
            raise ErroFalhaTransitoria(
                f"A chamada {metodo} {url} falhou por erro de rede."
            ) from erro
        if resposta.status_code in _ERROS_RETENTAVEIS:
            raise ErroFalhaTransitoria(
                f"A chamada {metodo} {url} não se completou (HTTP {resposta.status_code})."
            )
        return resposta
```

- [ ] **Step 4: Rodar o teste e confirmar que passa**

Run: `cd refinar-tecnicamente && uv run pytest tests/test_cliente_azure_devops.py -v`
Expected: PASS (todos, incluindo os já existentes)

- [ ] **Step 5: Teste de não-retry em falha transitória do upload**

```python
def test_anexar_arquivo_nao_retenta_upload_em_falha_transitoria() -> None:
    chamadas = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        chamadas["n"] += 1
        return httpx.Response(503, json={})

    with _cliente(httpx.MockTransport(handler)) as cliente, pytest.raises(ErroFalhaTransitoria):
        cliente.anexar_arquivo(5, "spec.md", b"conteudo")
    assert chamadas["n"] == 1
```

Run: `cd refinar-tecnicamente && uv run pytest tests/test_cliente_azure_devops.py::test_anexar_arquivo_nao_retenta_upload_em_falha_transitoria -v`
Expected: PASS

- [ ] **Step 6: Teste — upload aceito, mas o vínculo falha**

```python
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
```

Run: `cd refinar-tecnicamente && uv run pytest tests/test_cliente_azure_devops.py -v`
Expected: PASS (todos)

- [ ] **Step 7: Commit**

```bash
cd refinar-tecnicamente
git add src/refinar_tecnicamente/cliente_azure_devops.py tests/test_cliente_azure_devops.py
git commit -m "feat(refinar-tecnicamente): anexar arquivo ao work item via upload + vinculo"
```

---

### Task 2: `baixar_anexo` no cliente Azure DevOps

**Files:**
- Modify: `refinar-tecnicamente/src/refinar_tecnicamente/cliente_azure_devops.py` (depois de `anexar_arquivo`, criado na Task 1)
- Test: `refinar-tecnicamente/tests/test_cliente_azure_devops.py`

**Interfaces:**
- Consumes: `ler_work_item` já existente (relations vêm de `$expand=All`).
- Produces: `ClienteAzureDevOps.baixar_anexo(work_item_id: int, nome_arquivo: str) -> bytes | None` — `None` quando não há nenhum anexo com esse nome; senão, o conteúdo do **mais recente** (último da lista `relations` com `rel == "AttachedFile"` e `attributes.comment == nome_arquivo`).

- [ ] **Step 1: Escrever o teste que falha — nenhum anexo devolve `None`**

```python
def test_baixar_anexo_sem_nenhum_anexo_devolve_none() -> None:
    handler = httpx.MockTransport(
        lambda _req: httpx.Response(200, json={"id": 5, "fields": {}, "relations": []})
    )
    with _cliente(handler) as cliente:
        assert cliente.baixar_anexo(5, "spec.md") is None
```

- [ ] **Step 2: Rodar o teste e confirmar que falha**

Run: `cd refinar-tecnicamente && uv run pytest tests/test_cliente_azure_devops.py::test_baixar_anexo_sem_nenhum_anexo_devolve_none -v`
Expected: FAIL — `AttributeError: 'ClienteAzureDevOps' object has no attribute 'baixar_anexo'`

- [ ] **Step 3: Implementar**

Depois de `anexar_arquivo`:

```python
    def baixar_anexo(self, work_item_id: int, nome_arquivo: str) -> bytes | None:
        """Baixa o conteúdo do anexo mais recente com esse nome, ou `None` se não houver nenhum.

        "Mais recente" é o último elemento de `relations` com `rel == "AttachedFile"` e
        `attributes.comment == nome_arquivo` — o Azure Boards sempre acrescenta ao final da
        lista (`path: "/relations/-"`), então a ordem da lista já reflete a ordem de anexo.
        """
        work_item = self.ler_work_item(work_item_id)
        relations = work_item.get("relations")
        url_mais_recente: str | None = None
        if isinstance(relations, list):
            for relacao in relations:
                if not isinstance(relacao, dict) or relacao.get("rel") != "AttachedFile":
                    continue
                atributos = relacao.get("attributes")
                if not isinstance(atributos, dict) or atributos.get("comment") != nome_arquivo:
                    continue
                url = relacao.get("url")
                if isinstance(url, str) and url:
                    url_mais_recente = url
        if url_mais_recente is None:
            return None
        resposta = self._executar("GET", url_mais_recente)
        if resposta.status_code == 404:
            raise ErroDestinoInvalido(f"Não foi possível encontrar o anexo {nome_arquivo}.")
        if resposta.status_code >= 400:
            raise ErroDestinoInvalido(
                f"O download do anexo devolveu HTTP {resposta.status_code}."
            )
        return resposta.content
```

- [ ] **Step 4: Rodar o teste e confirmar que passa**

Run: `cd refinar-tecnicamente && uv run pytest tests/test_cliente_azure_devops.py -v`
Expected: PASS

- [ ] **Step 5: Teste — anexo único é baixado**

```python
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
```

- [ ] **Step 6: Teste — múltiplos anexos com o mesmo nome, pega o último**

```python
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
```

Run: `cd refinar-tecnicamente && uv run pytest tests/test_cliente_azure_devops.py -v`
Expected: PASS (todos)

- [ ] **Step 7: Commit**

```bash
cd refinar-tecnicamente
git add src/refinar_tecnicamente/cliente_azure_devops.py tests/test_cliente_azure_devops.py
git commit -m "feat(refinar-tecnicamente): baixar o anexo mais recente por nome"
```

---

### Task 3: `gravar_spec_tecnica` também anexa `spec.md`/`backlog.md`

**Files:**
- Modify: `refinar-tecnicamente/src/refinar_tecnicamente/gravar_spec_tecnica.py:14-16,74-97`
- Test: `refinar-tecnicamente/tests/test_gravar_spec_tecnica.py`

**Interfaces:**
- Consumes: `ClienteAzureDevOps.anexar_arquivo` (Task 1).
- Produces: `gravar_spec_tecnica(cliente, *, id_demanda, campo, spec_md, resposta_confirmacao, html=None, backlog_md=None) -> None` — parâmetro novo `backlog_md: str | None = None`. Sempre anexa `spec.md`; anexa `backlog.md` só quando `backlog_md` não for `None`.

- [ ] **Step 1: Escrever o teste que falha**

```python
class ClienteFalso:
    def __init__(self) -> None:
        self.chamadas: list[tuple[int, str, str]] = []
        self.anexos: list[tuple[int, str, bytes]] = []

    def gravar_campo(self, work_item_id: int, campo: str, valor: str) -> None:
        self.chamadas.append((work_item_id, campo, valor))

    def anexar_arquivo(self, work_item_id: int, nome_arquivo: str, conteudo: bytes) -> None:
        self.anexos.append((work_item_id, nome_arquivo, conteudo))
```

(Substitui a `ClienteFalso` existente no topo do arquivo — mantém `gravar_campo`, acrescenta `anexar_arquivo`.)

```python
def test_grava_tambem_anexa_spec_md() -> None:
    cliente = ClienteFalso()
    frase = montar_frase_autorizacao(13959)
    gravar_spec_tecnica(
        cliente,
        id_demanda=13959,
        campo="Custom.DemandaSpecTecnica",
        spec_md="# Spec\n",
        resposta_confirmacao=frase,
    )
    assert (13959, "spec.md", b"# Spec\n") in cliente.anexos
    assert not any(nome == "backlog.md" for _, nome, _ in cliente.anexos)


def test_grava_com_backlog_tambem_anexa_backlog_md() -> None:
    cliente = ClienteFalso()
    frase = montar_frase_autorizacao(13959)
    gravar_spec_tecnica(
        cliente,
        id_demanda=13959,
        campo="Custom.DemandaSpecTecnica",
        spec_md="# Spec\n",
        resposta_confirmacao=frase,
        backlog_md="# Backlog\n",
    )
    assert (13959, "backlog.md", b"# Backlog\n") in cliente.anexos


def test_confirmacao_invalida_nao_anexa_nada() -> None:
    cliente = ClienteFalso()
    with pytest.raises(ErroConfirmacaoInvalida):
        gravar_spec_tecnica(
            cliente,
            id_demanda=13959,
            campo="Custom.DemandaSpecTecnica",
            spec_md="# Spec\n",
            resposta_confirmacao="resposta errada",
        )
    assert cliente.anexos == []
    assert cliente.chamadas == []
```

- [ ] **Step 2: Rodar os testes e confirmar que falham**

Run: `cd refinar-tecnicamente && uv run pytest tests/test_gravar_spec_tecnica.py -v`
Expected: FAIL em `test_grava_tambem_anexa_spec_md` e `test_grava_com_backlog_tambem_anexa_backlog_md` — `AttributeError: 'ClienteFalso' object has no attribute 'anexos'` (antes de editar a implementação) ou `assert (...) in []` depois de editar só o teste.

- [ ] **Step 3: Implementar**

Em `gravar_spec_tecnica.py`, troque o `Protocol` (linhas 14-15):

```python
class _ClienteEscrita(Protocol):
    def gravar_campo(self, work_item_id: int, campo: str, valor: str) -> None: ...
    def anexar_arquivo(self, work_item_id: int, nome_arquivo: str, conteudo: bytes) -> None: ...
```

Troque a assinatura e o corpo de `gravar_spec_tecnica` (linhas 74-96):

```python
def gravar_spec_tecnica(
    cliente: _ClienteEscrita,
    *,
    id_demanda: int,
    campo: str,
    spec_md: str,
    resposta_confirmacao: str,
    html: str | None = None,
    backlog_md: str | None = None,
) -> None:
    """Grava a spec técnica convertida e reanexa spec.md/backlog.md, só após confirmação exata.

    `html` é o HTML já convertido e validado (a CLI converte antes de mostrar o conteúdo para
    confirmação). `backlog_md`, quando informado, é anexado como `backlog.md` na mesma operação
    — mantém o anexo remoto tão atual quanto a spec técnica que acabou de ser gravada.
    """
    frase_esperada = montar_frase_autorizacao(id_demanda)
    if resposta_confirmacao.strip() != frase_esperada:
        raise ErroConfirmacaoInvalida(
            "Confirmação ausente, incorreta ou vinculada a outra Demanda; nenhuma gravação foi feita."
        )
    html_final = html if html is not None else converter_para_html(spec_md)
    cliente.gravar_campo(id_demanda, campo, html_final)
    cliente.anexar_arquivo(id_demanda, "spec.md", spec_md.encode("utf-8"))
    if backlog_md is not None:
        cliente.anexar_arquivo(id_demanda, "backlog.md", backlog_md.encode("utf-8"))
```

- [ ] **Step 4: Rodar os testes e confirmar que passam**

Run: `cd refinar-tecnicamente && uv run pytest tests/test_gravar_spec_tecnica.py -v`
Expected: PASS (todos, incluindo os pré-existentes — nenhum usava `backlog_md`, então continuam válidos com o default `None`)

- [ ] **Step 5: Commit**

```bash
cd refinar-tecnicamente
git add src/refinar_tecnicamente/gravar_spec_tecnica.py tests/test_gravar_spec_tecnica.py
git commit -m "feat(refinar-tecnicamente): reanexar spec.md/backlog.md ao gravar a spec tecnica"
```

---

### Task 4: CLI — `--backlog` opcional em `gravar-spec-tecnica`

**Files:**
- Modify: `refinar-tecnicamente/src/refinar_tecnicamente/cli.py:67-75,102-139`
- Test: `refinar-tecnicamente/tests/test_cli.py`

**Interfaces:**
- Consumes: `gravar_spec_tecnica(..., backlog_md=...)` (Task 3).
- Produces: `gravar-spec-tecnica --demanda <id> --spec <caminho> [--backlog <caminho>]` — quando `--backlog` é informado e o arquivo não existe, falha com código de erro antes de pedir confirmação (mesmo padrão já usado para `--spec` inexistente).

- [ ] **Step 1: Escrever o teste que falha**

```python
def test_gravar_spec_tecnica_com_backlog_anexa_backlog_md(
    tmp_path: Path, capsys: object
) -> None:
    from refinar_tecnicamente.cliente_azure_devops import ClienteAzureDevOps

    spec = tmp_path / "spec.md"
    spec.write_text("# Spec\n", encoding="utf-8")
    backlog = tmp_path / "backlog.md"
    backlog.write_text("# Backlog\n", encoding="utf-8")

    anexados: list[tuple[int, str, bytes]] = []
    original = ClienteAzureDevOps.anexar_arquivo

    def _anexar_espiao(self, work_item_id, nome_arquivo, conteudo):  # type: ignore[no-untyped-def]
        anexados.append((work_item_id, nome_arquivo, conteudo))

    import pytest as _pytest

    monkeypatch = _pytest.MonkeyPatch()
    monkeypatch.setattr(ClienteAzureDevOps, "anexar_arquivo", _anexar_espiao)
    monkeypatch.setattr(ClienteAzureDevOps, "gravar_campo", lambda *_a, **_kw: None)
    try:
        codigo = executar(
            [
                "gravar-spec-tecnica",
                "--demanda",
                "13959",
                "--spec",
                str(spec),
                "--backlog",
                str(backlog),
            ],
            env=_ENV,
            entrada=lambda _prompt: "AUTORIZAR GRAVAÇÃO SPEC TÉCNICA #13959",
        )
    finally:
        monkeypatch.undo()
    assert codigo == 0
    assert (13959, "backlog.md", b"# Backlog\n") in anexados


def test_gravar_spec_tecnica_com_backlog_inexistente_devolve_codigo_de_erro(
    tmp_path: Path, capsys: object
) -> None:
    spec = tmp_path / "spec.md"
    spec.write_text("# Spec\n", encoding="utf-8")

    def _entrada_nao_deveria_ser_chamada(_prompt: str) -> str:
        raise AssertionError("entrada() não deveria ser chamada quando o backlog não existe")

    codigo = executar(
        [
            "gravar-spec-tecnica",
            "--demanda",
            "13959",
            "--spec",
            str(spec),
            "--backlog",
            "/caminho/que/nao/existe.md",
        ],
        env=_ENV,
        entrada=_entrada_nao_deveria_ser_chamada,
    )
    saida = capsys.readouterr().out  # type: ignore[attr-defined]
    assert codigo != 0
    assert "/caminho/que/nao/existe.md" in saida
```

- [ ] **Step 2: Rodar os testes e confirmar que falham**

Run: `cd refinar-tecnicamente && uv run pytest tests/test_cli.py -k backlog -v`
Expected: FAIL — `error: unrecognized arguments: --backlog ...`

- [ ] **Step 3: Implementar**

No parser (`_construir_parser`, depois da linha 69 `gravar.add_argument("--spec", required=True)`):

```python
    gravar.add_argument("--backlog", default=None)
```

Em `_gravar_spec_tecnica` (substitui o corpo atual, linhas 102-139):

```python
def _gravar_spec_tecnica(
    args: argparse.Namespace, env: Mapping[str, str], entrada: Callable[[str], str]
) -> int:
    config = carregar_configuracao(env)
    campo = args.campo if args.campo is not None else config.campo_spec_tecnica
    caminho_spec = Path(args.spec)
    if not caminho_spec.is_file():
        print(f"Spec não encontrada: {args.spec}")
        return 1
    backlog_md: str | None = None
    if args.backlog is not None:
        caminho_backlog = Path(args.backlog)
        if not caminho_backlog.is_file():
            print(f"Backlog não encontrado: {args.backlog}")
            return 1
        backlog_md = caminho_backlog.read_text(encoding="utf-8")
    spec_md = caminho_spec.read_text(encoding="utf-8")
    try:
        html = converter_para_html(spec_md)
    except ErroHtmlInvalido as erro:
        print(f"HTML gerado a partir da spec é inválido, gravação recusada: {erro}")
        return 1
    frase = montar_frase_autorizacao(args.demanda)
    print(f"HTML que será gravado em {campo}:")
    print(html)
    print(f"Digite exatamente a frase abaixo para confirmar a gravação em {campo}:")
    print(frase)
    resposta = entrada("> ")
    try:
        with ClienteAzureDevOps(
            config.organizacao, config.projeto, config.token.get_secret_value()
        ) as cliente:
            gravar_spec_tecnica(
                cliente,
                id_demanda=args.demanda,
                campo=campo,
                spec_md=spec_md,
                resposta_confirmacao=resposta,
                html=html,
                backlog_md=backlog_md,
            )
    except ErroConfirmacaoInvalida as erro:
        print(str(erro))
        return 1
    print("Spec técnica gravada.")
    return 0
```

- [ ] **Step 4: Rodar os testes e confirmar que passam**

Run: `cd refinar-tecnicamente && uv run pytest tests/test_cli.py -v`
Expected: PASS (todos)

- [ ] **Step 5: Commit**

```bash
cd refinar-tecnicamente
git add src/refinar_tecnicamente/cli.py tests/test_cli.py
git commit -m "feat(refinar-tecnicamente): --backlog opcional em gravar-spec-tecnica"
```

---

### Task 5: módulo `resolver_spec.py` (localizar pasta local ou baixar anexo, na convenção de `gerador-hu`)

**Files:**
- Create: `refinar-tecnicamente/src/refinar_tecnicamente/resolver_spec.py`
- Test: `refinar-tecnicamente/tests/test_resolver_spec.py`

**Interfaces:**
- Consumes: um cliente com `baixar_anexo(work_item_id: int, nome_arquivo: str) -> bytes | None` (Task 2) e `ler_work_item(work_item_id: int) -> dict[str, Any]` (já existente) — protocolo próprio, satisfeito por `ClienteAzureDevOps`.
- Produces:
  - `localizar_pasta_local(raiz: Path, id_demanda: int) -> Path | None`
  - `montar_nome_pasta(id_demanda: int, titulo: str) -> str` — mesmo algoritmo de slug de `redigir-spec-demanda-azure-boards/SKILL.md` > **Pasta da Demanda**.
  - `resolver_spec(cliente, *, raiz: Path, id_demanda: int) -> Path` — **sem** parâmetro de destino; quando precisa baixar, calcula o nome da pasta a partir do `System.Title` da própria Demanda.
  - `class ErroPastaAmbigua(RuntimeError)`
  - `class ErroSpecNaoEncontrada(RuntimeError)`

**Por que mudou em relação a uma versão anterior deste plano:** a pasta reconstruída por download
precisa usar a mesma convenção `DN-<id>-<slug>/` que `redigir-spec-demanda-azure-boards` já usa —
nunca um nome inventado à parte (`DN-<id>-recuperado-do-azure-boards`, cogitado antes). Um nome
próprio criaria uma segunda pasta órfã se o desenvolvedor depois clonar o repositório de verdade
(GitLab Sefaz): o Git traria `DN-<id>-<slug-real>/`, diferente do que o fallback já tivesse criado.

- [ ] **Step 1: Escrever os testes que falham**

```python
from pathlib import Path
from typing import Any

import pytest

from refinar_tecnicamente.resolver_spec import (
    ErroPastaAmbigua,
    ErroSpecNaoEncontrada,
    localizar_pasta_local,
    montar_nome_pasta,
    resolver_spec,
)


class ClienteFalso:
    def __init__(
        self, anexos: dict[str, bytes] | None = None, titulo: str = "Emissão de convites"
    ) -> None:
        self._anexos = anexos or {}
        self._titulo = titulo

    def baixar_anexo(self, work_item_id: int, nome_arquivo: str) -> bytes | None:
        return self._anexos.get(nome_arquivo)

    def ler_work_item(self, work_item_id: int) -> dict[str, Any]:
        return {"id": work_item_id, "fields": {"System.Title": self._titulo}}


def test_montar_nome_pasta_normaliza_titulo() -> None:
    assert montar_nome_pasta(14125, "Emissão de Convites!") == "DN-14125-emissao-de-convites"


def test_montar_nome_pasta_sem_caractere_aproveitavel_usa_so_o_id() -> None:
    assert montar_nome_pasta(14125, "!!!") == "DN-14125"


def test_montar_nome_pasta_trunca_em_60_sem_hifen_na_ponta() -> None:
    titulo_longo = "palavra " * 20
    nome = montar_nome_pasta(1, titulo_longo)
    assert len(nome) <= len("DN-1-") + 60
    assert not nome.endswith("-")


def test_localizar_pasta_local_sem_docs_specs_devolve_none(tmp_path: Path) -> None:
    assert localizar_pasta_local(tmp_path, 13959) is None


def test_localizar_pasta_local_encontra_pasta_com_slug(tmp_path: Path) -> None:
    pasta = tmp_path / "docs" / "specs" / "DN-13959-emissao-de-convites"
    pasta.mkdir(parents=True)
    assert localizar_pasta_local(tmp_path, 13959) == pasta


def test_localizar_pasta_local_com_duas_pastas_do_mesmo_id_recusa(tmp_path: Path) -> None:
    base = tmp_path / "docs" / "specs"
    (base / "DN-13959-slug-antigo").mkdir(parents=True)
    (base / "DN-13959-slug-novo").mkdir(parents=True)
    with pytest.raises(ErroPastaAmbigua):
        localizar_pasta_local(tmp_path, 13959)


def test_resolver_spec_prioriza_pasta_local(tmp_path: Path) -> None:
    pasta = tmp_path / "docs" / "specs" / "DN-13959-slug"
    pasta.mkdir(parents=True)
    cliente = ClienteFalso({"spec.md": b"nao deveria ser usado"})
    resultado = resolver_spec(cliente, raiz=tmp_path, id_demanda=13959)
    assert resultado == pasta


def test_resolver_spec_sem_pasta_local_baixa_anexos_na_convencao_de_pasta(
    tmp_path: Path,
) -> None:
    cliente = ClienteFalso(
        {"spec.md": b"# Spec\n", "backlog.md": b"# Backlog\n"}, titulo="Emissão de Convites"
    )
    resultado = resolver_spec(cliente, raiz=tmp_path, id_demanda=13959)
    esperado = tmp_path / "docs" / "specs" / "DN-13959-emissao-de-convites"
    assert resultado == esperado
    assert (esperado / "spec.md").read_bytes() == b"# Spec\n"
    assert (esperado / "backlog.md").read_bytes() == b"# Backlog\n"


def test_resolver_spec_sem_pasta_local_e_sem_backlog_anexado_nao_cria_backlog(
    tmp_path: Path,
) -> None:
    cliente = ClienteFalso({"spec.md": b"# Spec\n"})
    resolver_spec(cliente, raiz=tmp_path, id_demanda=13959)
    esperado = tmp_path / "docs" / "specs" / "DN-13959-emissao-de-convites"
    assert not (esperado / "backlog.md").exists()


def test_resolver_spec_sem_pasta_local_e_sem_anexo_recusa(tmp_path: Path) -> None:
    cliente = ClienteFalso({})
    with pytest.raises(ErroSpecNaoEncontrada):
        resolver_spec(cliente, raiz=tmp_path, id_demanda=13959)
```

- [ ] **Step 2: Rodar os testes e confirmar que falham**

Run: `cd refinar-tecnicamente && uv run pytest tests/test_resolver_spec.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'refinar_tecnicamente.resolver_spec'`

- [ ] **Step 3: Implementar**

```python
"""Resolve spec.md/backlog.md de uma Demanda: pasta local primeiro, anexo remoto como
fallback — nunca pede caminho manualmente nem sugere gerar a spec de novo. Quando precisa
baixar, materializa na mesma convenção de pasta que redigir-spec-demanda-azure-boards usa."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any, Protocol


class _ClienteLeitura(Protocol):
    def baixar_anexo(self, work_item_id: int, nome_arquivo: str) -> bytes | None: ...
    def ler_work_item(self, work_item_id: int) -> dict[str, Any]: ...


class ErroPastaAmbigua(RuntimeError):
    """Mais de uma pasta local corresponde ao ID da Demanda."""


class ErroSpecNaoEncontrada(RuntimeError):
    """Nem a pasta local nem nenhum anexo contêm spec.md para essa Demanda."""


def montar_nome_pasta(id_demanda: int, titulo: str) -> str:
    """`DN-<id>-<slug>`, no mesmo algoritmo de redigir-spec-demanda-azure-boards/SKILL.md >
    Pasta da Demanda: minúsculas, sem acento, espaço/pontuação vira hífen, hífens repetidos
    colapsam, truncado em 60 caracteres, sem hífen nas pontas. Sem caractere aproveitável no
    título, usa só `DN-<id>`."""
    sem_acento = unicodedata.normalize("NFKD", titulo).encode("ascii", "ignore").decode("ascii")
    hifenizado = re.sub(r"[^a-zA-Z0-9]+", "-", sem_acento.lower())
    slug = re.sub(r"-+", "-", hifenizado).strip("-")[:60].strip("-")
    return f"DN-{id_demanda}-{slug}" if slug else f"DN-{id_demanda}"


def localizar_pasta_local(raiz: Path, id_demanda: int) -> Path | None:
    """Procura `docs/specs/DN-<id>-*/` (ou `DN-<id>/`) sob `raiz`.

    Devolve `None` quando `docs/specs/` não existe ou nenhuma pasta corresponde — nunca
    levanta erro de arquivo/diretório inexistente, isso é uma ausência normal, não uma falha.
    """
    base = raiz / "docs" / "specs"
    if not base.is_dir():
        return None
    candidatos = sorted(
        {p for p in base.glob(f"DN-{id_demanda}-*") if p.is_dir()}
        | {p for p in base.glob(f"DN-{id_demanda}") if p.is_dir()}
    )
    if not candidatos:
        return None
    if len(candidatos) > 1:
        nomes = ", ".join(p.name for p in candidatos)
        raise ErroPastaAmbigua(
            f"Mais de uma pasta local corresponde à Demanda {id_demanda}: {nomes}. "
            "Resolva manualmente qual é a correta antes de continuar."
        )
    return candidatos[0]


def resolver_spec(cliente: _ClienteLeitura, *, raiz: Path, id_demanda: int) -> Path:
    """Devolve o diretório com `spec.md` (e `backlog.md`, se houver) pronto para uso.

    Prioriza a pasta local já existente. Na ausência dela, baixa o anexo mais recente da
    Demanda e materializa os arquivos em `docs/specs/DN-<id>-<slug>/`, calculando o mesmo
    `<slug>` que redigir-spec-demanda-azure-boards calcularia a partir do título da Demanda.
    """
    pasta_local = localizar_pasta_local(raiz, id_demanda)
    if pasta_local is not None:
        return pasta_local
    spec_bytes = cliente.baixar_anexo(id_demanda, "spec.md")
    if spec_bytes is None:
        raise ErroSpecNaoEncontrada(
            f"Demanda {id_demanda}: nenhuma pasta local em {raiz / 'docs' / 'specs'} e "
            "nenhum anexo spec.md nessa Demanda. A spec ainda não foi publicada."
        )
    work_item = cliente.ler_work_item(id_demanda)
    campos = work_item.get("fields")
    titulo = campos.get("System.Title", "") if isinstance(campos, dict) else ""
    nome_pasta = montar_nome_pasta(id_demanda, titulo if isinstance(titulo, str) else "")
    destino = raiz / "docs" / "specs" / nome_pasta
    destino.mkdir(parents=True, exist_ok=True)
    (destino / "spec.md").write_bytes(spec_bytes)
    backlog_bytes = cliente.baixar_anexo(id_demanda, "backlog.md")
    if backlog_bytes is not None:
        (destino / "backlog.md").write_bytes(backlog_bytes)
    return destino
```

- [ ] **Step 4: Rodar os testes e confirmar que passam**

Run: `cd refinar-tecnicamente && uv run pytest tests/test_resolver_spec.py -v`
Expected: PASS (todos)

- [ ] **Step 5: Commit**

```bash
cd refinar-tecnicamente
git add src/refinar_tecnicamente/resolver_spec.py tests/test_resolver_spec.py
git commit -m "feat(refinar-tecnicamente): resolver spec.md por pasta local ou anexo remoto"
```

---

### Task 6: CLI — subcomando `resolver-spec`

**Files:**
- Modify: `refinar-tecnicamente/src/refinar_tecnicamente/cli.py`
- Test: `refinar-tecnicamente/tests/test_cli.py`

**Interfaces:**
- Consumes: `resolver_spec`, `ErroPastaAmbigua`, `ErroSpecNaoEncontrada` (Task 5).
- Produces: `resolver-spec --demanda <id> --raiz <diretorio>` — imprime em `stdout` o caminho final (local ou reconstruído na convenção `DN-<id>-<slug>/`) e devolve 0; recusa com mensagem clara e código 1 quando não há nem pasta nem anexo. Sem `--destino`: o caminho final é sempre calculado, nunca escolhido por quem chama.

- [ ] **Step 1: Escrever os testes que falham**

```python
def test_resolver_spec_com_pasta_local_imprime_o_caminho(
    tmp_path: Path, capsys: object
) -> None:
    pasta = tmp_path / "docs" / "specs" / "DN-13959-slug"
    pasta.mkdir(parents=True)
    codigo = executar(
        ["resolver-spec", "--demanda", "13959", "--raiz", str(tmp_path)], env=_ENV
    )
    saida = capsys.readouterr().out  # type: ignore[attr-defined]
    assert codigo == 0
    assert str(pasta.resolve()) in saida


def test_resolver_spec_sem_pasta_local_baixa_e_usa_convencao_de_pasta(
    tmp_path: Path, capsys: object
) -> None:
    from refinar_tecnicamente.cliente_azure_devops import ClienteAzureDevOps

    import pytest as _pytest

    monkeypatch = _pytest.MonkeyPatch()
    monkeypatch.setattr(
        ClienteAzureDevOps,
        "baixar_anexo",
        lambda _self, _id, nome: b"# Spec\n" if nome == "spec.md" else None,
    )
    monkeypatch.setattr(
        ClienteAzureDevOps,
        "ler_work_item",
        lambda _self, id_demanda: {
            "id": id_demanda, "fields": {"System.Title": "Emissao de Convites"}
        },
    )
    try:
        codigo = executar(
            ["resolver-spec", "--demanda", "13959", "--raiz", str(tmp_path)], env=_ENV
        )
    finally:
        monkeypatch.undo()
    saida = capsys.readouterr().out  # type: ignore[attr-defined]
    esperado = tmp_path / "docs" / "specs" / "DN-13959-emissao-de-convites"
    assert codigo == 0
    assert str(esperado.resolve()) in saida
    assert (esperado / "spec.md").read_text(encoding="utf-8") == "# Spec\n"


def test_resolver_spec_sem_pasta_local_e_sem_anexo_devolve_codigo_de_erro(
    tmp_path: Path, capsys: object
) -> None:
    from refinar_tecnicamente.cliente_azure_devops import ClienteAzureDevOps

    import pytest as _pytest

    monkeypatch = _pytest.MonkeyPatch()
    monkeypatch.setattr(
        ClienteAzureDevOps, "baixar_anexo", lambda *_a, **_kw: None
    )
    try:
        codigo = executar(
            ["resolver-spec", "--demanda", "13959", "--raiz", str(tmp_path)], env=_ENV
        )
    finally:
        monkeypatch.undo()
    saida = capsys.readouterr().out  # type: ignore[attr-defined]
    assert codigo != 0
    assert "13959" in saida
```

- [ ] **Step 2: Rodar os testes e confirmar que falham**

Run: `cd refinar-tecnicamente && uv run pytest tests/test_cli.py -k resolver_spec -v`
Expected: FAIL — `error: argument comando: invalid choice: 'resolver-spec'`

- [ ] **Step 3: Implementar**

No topo de `cli.py`, junto dos outros imports do pacote:

```python
from refinar_tecnicamente.resolver_spec import (
    ErroPastaAmbigua,
    ErroSpecNaoEncontrada,
    resolver_spec,
)
```

Em `executar` (dentro do `try`, junto dos outros `if args.comando == ...`):

```python
        if args.comando == "resolver-spec":
            return _resolver_spec(args, env)
```

E no bloco `except`, junto de `ErroLacunaAmbigua`:

```python
    except (ErroPastaAmbigua, ErroSpecNaoEncontrada) as erro:
        print(str(erro))
        return 1
```

Em `_construir_parser`, junto dos outros subparsers:

```python
    resolver = subs.add_parser("resolver-spec")
    resolver.add_argument("--demanda", type=int, required=True)
    resolver.add_argument("--raiz", required=True)
```

Nova função, ao lado de `_gravar_spec_tecnica`:

```python
def _resolver_spec(args: argparse.Namespace, env: Mapping[str, str]) -> int:
    raiz = Path(args.raiz)
    config = carregar_configuracao(env)
    with ClienteAzureDevOps(
        config.organizacao, config.projeto, config.token.get_secret_value()
    ) as cliente:
        caminho = resolver_spec(cliente, raiz=raiz, id_demanda=args.demanda)
    print(str(caminho.resolve()))
    return 0
```

- [ ] **Step 4: Rodar os testes e confirmar que passam**

Run: `cd refinar-tecnicamente && uv run pytest tests/test_cli.py -v`
Expected: PASS (todos)

- [ ] **Step 5: Rodar a suíte completa do pacote**

Run: `cd refinar-tecnicamente && uv run pytest -v`
Expected: PASS (todos os testes do pacote, sem regressão)

- [ ] **Step 6: Commit**

```bash
cd refinar-tecnicamente
git add src/refinar_tecnicamente/cli.py tests/test_cli.py
git commit -m "feat(refinar-tecnicamente): subcomando resolver-spec"
```

---

### Task 7: `SKILL.md` — passo 1 aponta para `resolver-spec`

**Files:**
- Modify: `refinar-tecnicamente/SKILL.md` (passo 1 do "Fluxo obrigatório")

**Interfaces:**
- Consumes: `resolver-spec` (Task 6).
- Produces: instrução atualizada para o agente que conduz a reunião técnica.

- [ ] **Step 1: Reescrever o passo 1**

Troque:

```markdown
1. Receba o caminho da pasta `DN-<id>-<slug>/` (ou o ID da Demanda, resolvendo a pasta pela
   convenção de nomes do `gerador-hu`) e o ID da Demanda no Azure Boards.
```

Por:

```markdown
1. Receba o ID da Demanda no Azure Boards. Rode `resolver-spec --demanda <id> --raiz <raiz do
   repositório atualmente aberto>`: ele procura `docs/specs/DN-<id>-*/` sob essa raiz e, se não
   encontrar, baixa `spec.md`/`backlog.md` do anexo mais recente da própria Demanda e materializa
   uma pasta local a partir deles. Use o caminho impresso em `stdout` nos passos seguintes. Se a
   CLI recusar (nem pasta local, nem anexo), pare e informe que a Demanda ainda não tem spec
   publicada — não peça o caminho manualmente, nem sugira rodar `gerador-hu` você mesmo.
```

- [ ] **Step 2: Conferir que a mudança está no arquivo**

Run: `cd refinar-tecnicamente && grep -n "resolver-spec" SKILL.md`
Expected: mostra a linha do passo 1 reescrito

- [ ] **Step 3: Commit**

```bash
cd refinar-tecnicamente
git add SKILL.md
git commit -m "docs(refinar-tecnicamente): passo 1 usa resolver-spec em vez de pedir caminho manual"
```
