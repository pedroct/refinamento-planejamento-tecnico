# Refinamento e Planejamento Técnico Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir as três skills do repositório `refinamento-planejamento-tecnico` — `refinar-tecnicamente`, `decompor-tasks` e `preparar-implementacao` — que cobrem o refinamento técnico, o planejamento de capacidade por pessoa e a preparação do material de implementação, a partir de work items já publicados pelo `gerador-hu`.

**Architecture:** Três pacotes Python independentes, um por skill, cada um instalável isoladamente (padrão `npx skills`). Cada pacote vendoriza sua própria cópia de um cliente HTTP mínimo para o Azure Boards (GET, PATCH, POST, WIQL), seguindo o mesmo padrão de retentativa e classes de erro já usado em `publicar-backlog-demanda-azure-boards`, do repositório `gerador-hu`. Nenhum pacote importa de outro; cada SKILL.md guia o agente pelas partes de investigação e entrevista, enquanto os scripts Python cobrem chamadas de API, ancoragem de estimativa, autorização e manifesto.

**Tech Stack:** Python 3.12, `uv`, `httpx`, `pydantic` 2.x, `pydantic-settings`, `pytest`, `ruff`, `mypy` — mesmo conjunto do `gerador-hu`.

**Spec:** `docs/superpowers/specs/2026-09-28-refinamento-planejamento-tecnico-design.md`

## Global Constraints

- Nenhum tipo de work item é escrito por dois repositórios: este repositório nunca cria Epic, Feature, User Story ou Bug — só Task e o campo `Custom.DemandaSpecTecnica`.
- Story Points é lido da História/Bug como contexto de porte e **nunca** é copiado para nenhuma Task.
- Nenhuma estimativa (Story Points ou horas) é inventada sem ancoragem em item fechado comparável ou confirmação humana explícita.
- O PAT nunca é versionado; vem de variável de ambiente ou entrada interativa sem eco.
- Toda escrita (`PATCH` do campo customizado, `POST` de Task) exige confirmação textual explícita, apresentando o conteúdo exato antes da chamada.
- Timeout ou resposta ambígua numa escrita nunca autoriza repetir automaticamente — interrompe com estado bloqueado e exige reconciliação manual.
- `preparar-implementacao` não faz nenhuma chamada de escrita ao Azure Boards.

## Review Focus

- Confirmação textual com variação de caixa, espaço extra ou frase parecida (não idêntica) deve ser recusada, nunca aceita por semelhança.
- Reexecutar `decompor-tasks` sobre uma História com criação parcial (algumas Tasks já criadas antes de uma falha) deve retomar do manifesto sem duplicar Tasks.
- Campo `Custom.DemandaSpecTecnica` vazio ou ausente na Demanda não deve travar `preparar-implementacao` com erro genérico — o erro nomeia exatamente esse campo como faltante.
- Uma consulta WIQL sem nenhum item comparável (lista vazia) é tratada como "sem histórico" e cai no fluxo de pergunta ao humano, nunca como erro de execução.
- O HTML gerado a partir de `spec.md` para gravar em `Custom.DemandaSpecTecnica` é validado (bem formado) antes de ser apresentado para confirmação, nunca gravado a partir de uma conversão que falhou silenciosamente.

---

## Skill 1 — `refinar-tecnicamente`

### Task 1: Scaffold do pacote, configuração e cliente Azure DevOps (leitura)

**Files:**
- Create: `refinar-tecnicamente/pyproject.toml`
- Create: `refinar-tecnicamente/.env.example`
- Create: `refinar-tecnicamente/.gitignore`
- Create: `refinar-tecnicamente/src/refinar_tecnicamente/__init__.py`
- Create: `refinar-tecnicamente/src/refinar_tecnicamente/configuracao.py`
- Create: `refinar-tecnicamente/src/refinar_tecnicamente/cliente_azure_devops.py`
- Test: `refinar-tecnicamente/tests/test_configuracao.py`
- Test: `refinar-tecnicamente/tests/test_cliente_azure_devops.py`

**Interfaces:**
- Produces: `carregar_configuracao(env: Mapping[str, str] | None = None) -> ConfiguracaoRefinamento` (campos: `organizacao: str`, `projeto: str`, `token: SecretStr`, `campo_spec_tecnica: str = "Custom.DemandaSpecTecnica"`)
- Produces: `class ClienteAzureDevOps` com `ler_work_item(id: int) -> dict[str, Any]`, `consultar_wiql(wiql: str) -> list[int]`, `gravar_campo(id: int, campo: str, valor: str) -> None`, `usuario_autenticado() -> dict[str, Any]`
- Produces: `ErroDestinoInvalido`, `ErroFalhaTransitoria`, `ErroRespostaInvalida` (classes de exceção)

- [ ] **Step 1: Escrever o pyproject.toml e os arquivos de apoio**

```toml
[build-system]
requires = ["hatchling==1.29.0"]
build-backend = "hatchling.build"

[project]
name = "refinar-tecnicamente"
version = "0.1.0"
description = "Refinamento técnico de uma Demanda já publicada no Azure Boards"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
  "httpx==0.28.1",
  "markdown-it-py==4.2.0",
  "pydantic==2.13.5",
  "pydantic-settings==2.15.0",
]

[project.scripts]
refinar-tecnicamente = "refinar_tecnicamente:main"

[dependency-groups]
dev = [
  "mypy==2.1.0",
  "pytest==9.0.3",
  "ruff==0.15.14",
]

[tool.hatch.build.targets.wheel]
packages = ["src/refinar_tecnicamente"]

[tool.ruff]
line-length = 100
target-version = "py312"
exclude = [".venv/", ".git/"]

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "S"]

[tool.ruff.lint.per-file-ignores]
"**/tests/**/*.py" = ["S101"]

[tool.mypy]
python_version = "3.12"
strict = true
warn_unused_ignores = true

[tool.pytest.ini_options]
testpaths = ["tests"]
```

```text
# refinar-tecnicamente/.env.example
AZURE_DEVOPS_ORGANIZACAO=
AZURE_DEVOPS_PROJETO=
AZURE_DEVOPS_TOKEN=
AZURE_DEVOPS_CAMPO_SPEC_TECNICA=Custom.DemandaSpecTecnica
```

```text
# refinar-tecnicamente/.gitignore
.venv/
__pycache__/
*.pyc
.env
.mypy_cache/
.pytest_cache/
.ruff_cache/
uv.lock
```

```python
# refinar-tecnicamente/src/refinar_tecnicamente/__init__.py
"""Skill de refinamento técnico: fecha lacunas técnicas, registra abordagem e Story Points."""

from __future__ import annotations


def main() -> None:
    """Ponto de entrada da CLI; implementado na Task 5."""
    raise SystemExit("CLI ainda não implementada — veja o Task 5 do plano.")
```

- [ ] **Step 2: Escrever o teste de configuração**

```python
# refinar-tecnicamente/tests/test_configuracao.py
import pytest

from refinar_tecnicamente.configuracao import ErroConfiguracao, carregar_configuracao


def test_carrega_configuracao_completa() -> None:
    env = {
        "AZURE_DEVOPS_ORGANIZACAO": "minha-org",
        "AZURE_DEVOPS_PROJETO": "meu-projeto",
        "AZURE_DEVOPS_TOKEN": "token-secreto",
    }
    config = carregar_configuracao(env)
    assert config.organizacao == "minha-org"
    assert config.projeto == "meu-projeto"
    assert config.token.get_secret_value() == "token-secreto"
    assert config.campo_spec_tecnica == "Custom.DemandaSpecTecnica"


def test_recusa_configuracao_sem_organizacao() -> None:
    env = {"AZURE_DEVOPS_PROJETO": "meu-projeto", "AZURE_DEVOPS_TOKEN": "x"}
    with pytest.raises(ErroConfiguracao):
        carregar_configuracao(env)


def test_recusa_token_vazio() -> None:
    env = {
        "AZURE_DEVOPS_ORGANIZACAO": "minha-org",
        "AZURE_DEVOPS_PROJETO": "meu-projeto",
        "AZURE_DEVOPS_TOKEN": "   ",
    }
    with pytest.raises(ErroConfiguracao):
        carregar_configuracao(env)


def test_aceita_nome_de_campo_customizado() -> None:
    env = {
        "AZURE_DEVOPS_ORGANIZACAO": "minha-org",
        "AZURE_DEVOPS_PROJETO": "meu-projeto",
        "AZURE_DEVOPS_TOKEN": "x",
        "AZURE_DEVOPS_CAMPO_SPEC_TECNICA": "Custom.OutroCampo",
    }
    config = carregar_configuracao(env)
    assert config.campo_spec_tecnica == "Custom.OutroCampo"
```

- [ ] **Step 3: Rodar os testes e confirmar que falham**

Run: `cd refinar-tecnicamente && uv run pytest tests/test_configuracao.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'refinar_tecnicamente.configuracao'`

- [ ] **Step 4: Implementar `configuracao.py`**

```python
# refinar-tecnicamente/src/refinar_tecnicamente/configuracao.py
"""Carrega a configuração local sem expor o token em representações textuais."""

from __future__ import annotations

from collections.abc import Mapping

from pydantic import BaseModel, ConfigDict, SecretStr, ValidationError, field_validator


class ErroConfiguracao(ValueError):
    """Indica que não foi possível obter uma configuração completa e segura."""


class ConfiguracaoRefinamento(BaseModel):
    """Agrupa organização, projeto, credencial e o nome do campo de spec técnica."""

    model_config = ConfigDict(frozen=True)

    organizacao: str
    projeto: str
    token: SecretStr
    campo_spec_tecnica: str = "Custom.DemandaSpecTecnica"

    @field_validator("organizacao", "projeto", "campo_spec_tecnica")
    @classmethod
    def _validar_texto_obrigatorio(cls, valor: str) -> str:
        texto = valor.strip()
        if not texto:
            raise ValueError("deve ser informado")
        return texto

    @field_validator("token")
    @classmethod
    def _validar_token(cls, valor: SecretStr) -> SecretStr:
        if not valor.get_secret_value().strip():
            raise ValueError("deve ser informado")
        return valor


def carregar_configuracao(env: Mapping[str, str]) -> ConfiguracaoRefinamento:
    """Lê a configuração a partir de um mapa de variáveis de ambiente já resolvido."""
    try:
        return ConfiguracaoRefinamento(
            organizacao=env.get("AZURE_DEVOPS_ORGANIZACAO", ""),
            projeto=env.get("AZURE_DEVOPS_PROJETO", ""),
            token=env.get("AZURE_DEVOPS_TOKEN", ""),
            campo_spec_tecnica=env.get(
                "AZURE_DEVOPS_CAMPO_SPEC_TECNICA", "Custom.DemandaSpecTecnica"
            ),
        )
    except ValidationError as erro:
        raise ErroConfiguracao(f"Configuração incompleta ou inválida: {erro}") from erro
```

- [ ] **Step 5: Rodar os testes de configuração e confirmar que passam**

Run: `cd refinar-tecnicamente && uv run pytest tests/test_configuracao.py -v`
Expected: PASS (4 testes)

- [ ] **Step 6: Escrever o teste do cliente Azure DevOps**

```python
# refinar-tecnicamente/tests/test_cliente_azure_devops.py
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


def test_usuario_autenticado_devolve_perfil() -> None:
    handler = httpx.MockTransport(
        lambda _req: httpx.Response(200, json={"displayName": "Pedro", "emailAddress": "p@x"})
    )
    with _cliente(handler) as cliente:
        perfil = cliente.usuario_autenticado()
    assert perfil["emailAddress"] == "p@x"
```

- [ ] **Step 7: Rodar os testes do cliente e confirmar que falham**

Run: `cd refinar-tecnicamente && uv run pytest tests/test_cliente_azure_devops.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'refinar_tecnicamente.cliente_azure_devops'`

- [ ] **Step 8: Implementar `cliente_azure_devops.py`**

```python
# refinar-tecnicamente/src/refinar_tecnicamente/cliente_azure_devops.py
"""Cliente HTTP mínimo para leitura e escrita no Azure Boards via REST.

Cópia vendorizada, no mesmo padrão de `publicar-backlog-demanda-azure-boards`: cada skill
se instala de forma independente, então este arquivo duplica em vez de importar de outro
pacote. Ressincronize manualmente se o padrão de retentativa mudar em algum dos irmãos
(`decompor-tasks`, `preparar-implementacao`).
"""

from __future__ import annotations

import base64
import time
from typing import Any

import httpx

_VERSAO_API = "7.2-preview.3"
_VERSAO_WIQL = "7.2-preview.2"
_ERROS_RETENTAVEIS = frozenset({408, 429, 500, 502, 503, 504})
_MAX_TENTATIVAS = 3


class ErroDestinoInvalido(ValueError):
    """O work item, campo ou consulta solicitados não existem ou são inválidos."""


class ErroFalhaTransitoria(RuntimeError):
    """A chamada falhou por rede ou por erro remoto retentável, mesmo após tentativas."""


class ErroRespostaInvalida(RuntimeError):
    """A resposta remota não é JSON consumível ou não tem o formato esperado."""


class ClienteAzureDevOps:
    """Encapsula autenticação básica por PAT e o padrão de retentativa com backoff."""

    def __init__(
        self,
        organizacao: str,
        projeto: str,
        token: str,
        *,
        transport: httpx.BaseTransport | None = None,
        timeout: float = 10.0,
        espera_inicial: float = 0.2,
    ) -> None:
        self._organizacao = organizacao
        self._projeto = projeto
        self._espera_inicial = espera_inicial
        credencial = base64.b64encode(f":{token}".encode()).decode()
        self._cliente = httpx.Client(
            headers={"Authorization": f"Basic {credencial}"},
            timeout=httpx.Timeout(timeout),
            transport=transport,
        )

    def __enter__(self) -> ClienteAzureDevOps:
        return self

    def __exit__(self, *_exc: object) -> None:
        self._cliente.close()

    def ler_work_item(self, work_item_id: int) -> dict[str, Any]:
        """Busca um work item por GET, com campos e relações expandidos."""
        url = (
            f"https://dev.azure.com/{self._organizacao}/{self._projeto}"
            f"/_apis/wit/workitems/{work_item_id}?$expand=All&api-version={_VERSAO_API}"
        )
        resposta = self._executar("GET", url)
        return self._verificar_e_decodificar(resposta, work_item_id)

    def consultar_wiql(self, wiql: str) -> list[int]:
        """Executa uma consulta WIQL e devolve os IDs encontrados, na ordem devolvida."""
        url = (
            f"https://dev.azure.com/{self._organizacao}/{self._projeto}"
            f"/_apis/wit/wiql?api-version={_VERSAO_WIQL}"
        )
        resposta = self._executar("POST", url, corpo={"query": wiql})
        payload = self._verificar_e_decodificar(resposta, None)
        itens = payload.get("workItems")
        if not isinstance(itens, list):
            raise ErroRespostaInvalida("A consulta WIQL não devolveu uma lista de work items.")
        ids: list[int] = []
        for item in itens:
            if not isinstance(item, dict) or not isinstance(item.get("id"), int):
                raise ErroRespostaInvalida("Um item da consulta WIQL não trouxe um ID inteiro.")
            ids.append(item["id"])
        return ids

    def gravar_campo(self, work_item_id: int, campo: str, valor: str) -> None:
        """Grava um único campo por PATCH, usando JSON Patch (`replace`)."""
        url = (
            f"https://dev.azure.com/{self._organizacao}/{self._projeto}"
            f"/_apis/wit/workitems/{work_item_id}?api-version={_VERSAO_API}"
        )
        payload = [{"op": "replace", "path": f"/fields/{campo}", "value": valor}]
        resposta = self._executar(
            "PATCH", url, corpo=payload, content_type="application/json-patch+json"
        )
        self._verificar_e_decodificar(resposta, work_item_id)

    def usuario_autenticado(self) -> dict[str, Any]:
        """Devolve o perfil do titular do PAT (`displayName`, `emailAddress`)."""
        url = (
            f"https://vssps.dev.azure.com/{self._organizacao}"
            "/_apis/profile/profiles/me?api-version=7.1"
        )
        resposta = self._executar("GET", url)
        return self._verificar_e_decodificar(resposta, None)

    def _executar(
        self,
        metodo: str,
        url: str,
        *,
        corpo: Any = None,
        content_type: str | None = None,
    ) -> httpx.Response:
        headers = {"Content-Type": content_type} if content_type else None
        for tentativa in range(_MAX_TENTATIVAS):
            try:
                resposta = self._cliente.request(metodo, url, json=corpo, headers=headers)
            except httpx.RequestError as erro:
                if tentativa == _MAX_TENTATIVAS - 1:
                    raise ErroFalhaTransitoria(
                        f"A chamada {metodo} {url} falhou por erro de rede."
                    ) from erro
            else:
                if resposta.status_code not in _ERROS_RETENTAVEIS:
                    return resposta
                if tentativa == _MAX_TENTATIVAS - 1:
                    raise ErroFalhaTransitoria(
                        f"A chamada {metodo} {url} não se completou "
                        f"(HTTP {resposta.status_code}) após {_MAX_TENTATIVAS} tentativas."
                    )
            time.sleep(self._espera_inicial * (2**tentativa))
        raise ErroFalhaTransitoria(f"A chamada {metodo} {url} não se completou.")

    def _verificar_e_decodificar(
        self, resposta: httpx.Response, work_item_id: int | None
    ) -> dict[str, Any]:
        if resposta.status_code == 404:
            alvo = f"work item {work_item_id}" if work_item_id else "o recurso solicitado"
            raise ErroDestinoInvalido(f"Não foi possível encontrar {alvo}.")
        if resposta.status_code >= 400:
            raise ErroDestinoInvalido(
                f"A chamada devolveu HTTP {resposta.status_code}: {resposta.text[:300]}"
            )
        try:
            corpo_json = resposta.json()
        except ValueError as erro:
            raise ErroRespostaInvalida("A resposta não é JSON consumível.") from erro
        if not isinstance(corpo_json, dict):
            raise ErroRespostaInvalida("A resposta não é um objeto JSON.")
        return corpo_json
```

- [ ] **Step 9: Rodar todos os testes do Task 1 e confirmar que passam**

Run: `cd refinar-tecnicamente && uv run pytest tests/ -v`
Expected: PASS (12 testes)

- [ ] **Step 10: Commit**

```bash
cd refinar-tecnicamente
git add pyproject.toml .env.example .gitignore src/ tests/
git commit -m "feat(refinar-tecnicamente): scaffold, configuração e cliente Azure DevOps

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

### Task 2: Leitor de lacunas técnicas de `spec.md`

O cálculo de fronteira e a condução da entrevista são trabalho do agente, guiado pelo SKILL.md
(Task 5) — igual ao `entrevistar-lacunas-requisito`, que também não tem essa lógica em código. Este
módulo só faz o parsing determinístico da seção `## Lacunas e perguntas abertas`.

**Files:**
- Create: `refinar-tecnicamente/src/refinar_tecnicamente/leitor_lacunas.py`
- Test: `refinar-tecnicamente/tests/test_leitor_lacunas.py`

**Interfaces:**
- Produces: `@dataclass(frozen=True) class Lacuna` (campos: `id: str | None`, `audiencia: str | None`, `pergunta: str`, `evidencia: str | None`)
- Produces: `ler_lacunas(spec_md: str) -> list[Lacuna]`
- Produces: `filtrar_tecnicas(lacunas: list[Lacuna]) -> list[Lacuna]` — devolve as rotuladas `Técnico` e as sem rótulo, na mesma ordem; nunca as rotuladas `Negócio`

- [ ] **Step 1: Escrever os testes**

```python
# refinar-tecnicamente/tests/test_leitor_lacunas.py
from refinar_tecnicamente.leitor_lacunas import Lacuna, filtrar_tecnicas, ler_lacunas

SPEC_COM_ROTULOS = """# Spec

## Comportamento esperado

...

## Lacunas e perguntas abertas

- **N3 · Negócio** — A data que o usuário vê deve ser a mesma que expira?
  <!-- evidência: MinhaDiligenciaDTO.java:76-78 -->
- **T2 · Técnico** — `PENDENTE` vira enum persistido ou é rótulo de exibição?
  <!-- evidência: DiligenciaService.java:120 -->
- **T5 · Técnico** — Onde persistir o prazo vigente?
"""

SPEC_SEM_ROTULOS = """# Spec

## Lacunas e perguntas abertas

- Qual o prazo padrão de expiração?
- Quem pode renovar uma diligência?
"""


def test_le_lacunas_rotuladas() -> None:
    lacunas = ler_lacunas(SPEC_COM_ROTULOS)
    assert len(lacunas) == 3
    assert lacunas[0] == Lacuna(
        id="N3",
        audiencia="Negócio",
        pergunta="A data que o usuário vê deve ser a mesma que expira?",
        evidencia="MinhaDiligenciaDTO.java:76-78",
    )
    assert lacunas[1].id == "T2"
    assert lacunas[1].audiencia == "Técnico"
    assert lacunas[2].evidencia is None


def test_le_lacunas_sem_rotulo() -> None:
    lacunas = ler_lacunas(SPEC_SEM_ROTULOS)
    assert len(lacunas) == 2
    assert lacunas[0].id is None
    assert lacunas[0].audiencia is None
    assert lacunas[0].pergunta == "Qual o prazo padrão de expiração?"


def test_spec_sem_secao_devolve_lista_vazia() -> None:
    assert ler_lacunas("# Spec\n\n## Comportamento esperado\n\nTexto.\n") == []


def test_filtrar_tecnicas_exclui_negocio_rotulado() -> None:
    lacunas = ler_lacunas(SPEC_COM_ROTULOS)
    tecnicas = filtrar_tecnicas(lacunas)
    assert [l.id for l in tecnicas] == ["T2", "T5"]


def test_filtrar_tecnicas_inclui_sem_rotulo() -> None:
    lacunas = ler_lacunas(SPEC_SEM_ROTULOS)
    tecnicas = filtrar_tecnicas(lacunas)
    assert len(tecnicas) == 2
```

- [ ] **Step 2: Rodar os testes e confirmar que falham**

Run: `cd refinar-tecnicamente && uv run pytest tests/test_leitor_lacunas.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'refinar_tecnicamente.leitor_lacunas'`

- [ ] **Step 3: Implementar `leitor_lacunas.py`**

```python
# refinar-tecnicamente/src/refinar_tecnicamente/leitor_lacunas.py
"""Lê, sem interpretar, a seção `## Lacunas e perguntas abertas` de uma spec."""

from __future__ import annotations

import re
from dataclasses import dataclass

_SECAO = re.compile(
    r"^## Lacunas e perguntas abertas\s*\n(?P<corpo>.*?)(?=\n## |\Z)",
    re.MULTILINE | re.DOTALL,
)
_ITEM_ROTULADO = re.compile(
    r"^- \*\*(?P<id>\w+) · (?P<audiencia>Negócio|Técnico)\*\* — (?P<pergunta>.+)$"
)
_ITEM_SIMPLES = re.compile(r"^- (?P<pergunta>.+)$")
_EVIDENCIA = re.compile(r"^\s*<!--\s*evidência:\s*(?P<evidencia>.+?)\s*-->\s*$")


@dataclass(frozen=True)
class Lacuna:
    """Um item de `## Lacunas e perguntas abertas`, sem interpretação de conteúdo."""

    id: str | None
    audiencia: str | None
    pergunta: str
    evidencia: str | None


def ler_lacunas(spec_md: str) -> list[Lacuna]:
    """Extrai cada lacuna da seção, na ordem em que aparece no documento."""
    secao = _SECAO.search(spec_md)
    if secao is None:
        return []
    linhas = secao.group("corpo").splitlines()
    lacunas: list[Lacuna] = []
    pendente: dict[str, str | None] | None = None
    for linha in linhas:
        rotulado = _ITEM_ROTULADO.match(linha)
        if rotulado:
            if pendente is not None:
                lacunas.append(Lacuna(**pendente))  # type: ignore[arg-type]
            pendente = {
                "id": rotulado.group("id"),
                "audiencia": rotulado.group("audiencia"),
                "pergunta": rotulado.group("pergunta").strip(),
                "evidencia": None,
            }
            continue
        evidencia = _EVIDENCIA.match(linha)
        if evidencia and pendente is not None:
            pendente["evidencia"] = evidencia.group("evidencia")
            continue
        simples = _ITEM_SIMPLES.match(linha)
        if simples:
            if pendente is not None:
                lacunas.append(Lacuna(**pendente))  # type: ignore[arg-type]
                pendente = None
            pendente = {
                "id": None,
                "audiencia": None,
                "pergunta": simples.group("pergunta").strip(),
                "evidencia": None,
            }
    if pendente is not None:
        lacunas.append(Lacuna(**pendente))  # type: ignore[arg-type]
    return lacunas


def filtrar_tecnicas(lacunas: list[Lacuna]) -> list[Lacuna]:
    """Devolve as lacunas `Técnico` e as sem rótulo, preservando a ordem original."""
    return [l for l in lacunas if l.audiencia in (None, "Técnico")]
```

- [ ] **Step 4: Rodar os testes e confirmar que passam**

Run: `cd refinar-tecnicamente && uv run pytest tests/test_leitor_lacunas.py -v`
Expected: PASS (6 testes)

- [ ] **Step 5: Commit**

```bash
cd refinar-tecnicamente
git add src/refinar_tecnicamente/leitor_lacunas.py tests/test_leitor_lacunas.py
git commit -m "feat(refinar-tecnicamente): leitor de lacunas técnicas de spec.md

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

### Task 3: Ancoragem de Story Points em itens fechados comparáveis

**Files:**
- Create: `refinar-tecnicamente/src/refinar_tecnicamente/ancoragem_story_points.py`
- Test: `refinar-tecnicamente/tests/test_ancoragem_story_points.py`

**Interfaces:**
- Consumes: `ClienteAzureDevOps.consultar_wiql(wiql: str) -> list[int]`, `ClienteAzureDevOps.ler_work_item(id: int) -> dict[str, Any]` (Task 1)
- Produces: `@dataclass(frozen=True) class SugestaoPontuacao` (campos: `pontos: float | None`, `baseado_em: tuple[int, ...]`)
- Produces: `sugerir_story_points(cliente, *, projeto: str, area_path: str, tipos: tuple[str, ...], limite: int = 20) -> SugestaoPontuacao`

- [ ] **Step 1: Escrever os testes**

```python
# refinar-tecnicamente/tests/test_ancoragem_story_points.py
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
    assert "User Story" in cliente.wiql_recebido and "Bug" in cliente.wiql_recebido
    assert "Closed" in cliente.wiql_recebido


def test_respeita_o_limite_de_itens_consultados() -> None:
    ids = list(range(1, 31))
    itens = {i: _item(float(i)) for i in ids}
    cliente = ClienteFalso(ids, itens)
    sugestao = sugerir_story_points(
        cliente, projeto="proj", area_path="proj\\Time A", tipos=("User Story",), limite=5
    )
    assert len(sugestao.baseado_em) == 5
```

- [ ] **Step 2: Rodar os testes e confirmar que falham**

Run: `cd refinar-tecnicamente && uv run pytest tests/test_ancoragem_story_points.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'refinar_tecnicamente.ancoragem_story_points'`

- [ ] **Step 3: Implementar `ancoragem_story_points.py`**

```python
# refinar-tecnicamente/src/refinar_tecnicamente/ancoragem_story_points.py
"""Sugere Story Points a partir de itens fechados comparáveis; nunca inventa um número."""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from typing import Any

_ESTADOS_FECHADOS = ("Closed", "Done", "Resolved")
_CAMPO_STORY_POINTS = "Microsoft.VSTS.Scheduling.StoryPoints"


class _ClienteLeitura(Protocol):
    def consultar_wiql(self, wiql: str) -> list[int]: ...
    def ler_work_item(self, work_item_id: int) -> dict[str, Any]: ...


@dataclass(frozen=True)
class SugestaoPontuacao:
    """`pontos` é `None` quando não há item fechado comparável com Story Points preenchido."""

    pontos: float | None
    baseado_em: tuple[int, ...]


def sugerir_story_points(
    cliente: _ClienteLeitura,
    *,
    projeto: str,
    area_path: str,
    tipos: tuple[str, ...],
    limite: int = 20,
) -> SugestaoPontuacao:
    """Consulta itens fechados no mesmo Area Path e propõe a mediana dos que têm pontuação."""
    tipos_wiql = ", ".join(f"'{tipo}'" for tipo in tipos)
    estados_wiql = ", ".join(f"'{estado}'" for estado in _ESTADOS_FECHADOS)
    wiql = (
        "SELECT [System.Id] FROM WorkItems "
        f"WHERE [System.TeamProject] = '{projeto}' "
        f"AND [System.AreaPath] UNDER '{area_path}' "
        f"AND [System.WorkItemType] IN ({tipos_wiql}) "
        f"AND [System.State] IN ({estados_wiql}) "
        "ORDER BY [System.ChangedDate] DESC"
    )
    ids = cliente.consultar_wiql(wiql)[:limite]
    pontuados: list[tuple[int, float]] = []
    for work_item_id in ids:
        campos = cliente.ler_work_item(work_item_id).get("fields", {})
        pontos = campos.get(_CAMPO_STORY_POINTS)
        if isinstance(pontos, int | float):
            pontuados.append((work_item_id, float(pontos)))
    if not pontuados:
        return SugestaoPontuacao(pontos=None, baseado_em=())
    mediana = statistics.median(valor for _id, valor in pontuados)
    return SugestaoPontuacao(pontos=mediana, baseado_em=tuple(id_ for id_, _valor in pontuados))
```

- [ ] **Step 4: Rodar os testes e confirmar que passam**

Run: `cd refinar-tecnicamente && uv run pytest tests/test_ancoragem_story_points.py -v`
Expected: PASS (6 testes)

- [ ] **Step 5: Commit**

```bash
cd refinar-tecnicamente
git add src/refinar_tecnicamente/ancoragem_story_points.py tests/test_ancoragem_story_points.py
git commit -m "feat(refinar-tecnicamente): ancoragem de Story Points em itens comparáveis

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

### Task 4: Conversão para HTML e gravação de `Custom.DemandaSpecTecnica` sob confirmação

**Files:**
- Create: `refinar-tecnicamente/src/refinar_tecnicamente/gravar_spec_tecnica.py`
- Test: `refinar-tecnicamente/tests/test_gravar_spec_tecnica.py`

**Interfaces:**
- Consumes: `ClienteAzureDevOps.gravar_campo(id, campo, valor)` (Task 1)
- Produces: `ErroConfirmacaoInvalida`, `ErroHtmlInvalido` (classes de exceção)
- Produces: `montar_frase_autorizacao(id_demanda: int) -> str`
- Produces: `converter_para_html(spec_md: str) -> str`
- Produces: `gravar_spec_tecnica(cliente, *, id_demanda: int, campo: str, spec_md: str, resposta_confirmacao: str) -> None`

- [ ] **Step 1: Escrever os testes**

```python
# refinar-tecnicamente/tests/test_gravar_spec_tecnica.py
from typing import Any

import pytest

from refinar_tecnicamente.gravar_spec_tecnica import (
    ErroConfirmacaoInvalida,
    ErroHtmlInvalido,
    converter_para_html,
    gravar_spec_tecnica,
    montar_frase_autorizacao,
)


class ClienteFalso:
    def __init__(self) -> None:
        self.chamadas: list[tuple[int, str, str]] = []

    def gravar_campo(self, work_item_id: int, campo: str, valor: str) -> None:
        self.chamadas.append((work_item_id, campo, valor))


def test_converte_markdown_simples() -> None:
    html = converter_para_html("# Título\n\nParágrafo com **negrito**.\n")
    assert "<h1>" in html and "</h1>" in html
    assert "<strong>negrito</strong>" in html


def test_recusa_html_malformado(monkeypatch: pytest.MonkeyPatch) -> None:
    import refinar_tecnicamente.gravar_spec_tecnica as modulo

    monkeypatch.setattr(modulo, "_renderizar_markdown", lambda _md: "<p>sem fechar")
    with pytest.raises(ErroHtmlInvalido):
        converter_para_html("qualquer coisa")


def test_frase_de_autorizacao_nomeia_a_demanda() -> None:
    frase = montar_frase_autorizacao(13959)
    assert "13959" in frase
    assert frase.startswith("AUTORIZAR GRAVAÇÃO SPEC TÉCNICA")


def test_grava_quando_confirmacao_e_exata() -> None:
    cliente = ClienteFalso()
    frase = montar_frase_autorizacao(13959)
    gravar_spec_tecnica(
        cliente,
        id_demanda=13959,
        campo="Custom.DemandaSpecTecnica",
        spec_md="# Spec\n",
        resposta_confirmacao=frase,
    )
    assert len(cliente.chamadas) == 1
    assert cliente.chamadas[0][0] == 13959
    assert cliente.chamadas[0][1] == "Custom.DemandaSpecTecnica"


@pytest.mark.parametrize(
    "resposta",
    [
        "autorizar gravação spec técnica #13959",  # caixa diferente
        "AUTORIZAR GRAVAÇÃO SPEC TÉCNICA #13959 ",  # espaço extra ao final não é o problema real
        "AUTORIZAR GRAVACAO SPEC TECNICA #13959",  # sem acentuação
        "AUTORIZAR GRAVAÇÃO SPEC TÉCNICA #99999",  # Demanda errada
        "sim",
    ],
)
def test_recusa_confirmacao_nao_exata(resposta: str) -> None:
    cliente = ClienteFalso()
    with pytest.raises(ErroConfirmacaoInvalida):
        gravar_spec_tecnica(
            cliente,
            id_demanda=13959,
            campo="Custom.DemandaSpecTecnica",
            spec_md="# Spec\n",
            resposta_confirmacao=resposta,
        )
    assert cliente.chamadas == []


def test_confirmacao_com_espaco_extra_ao_final_ainda_e_aceita() -> None:
    """Só o conteúdo importa; espaço à volta da resposta do usuário é ruído de digitação,
    não uma variação da frase em si — diferente do caso 'espaço extra' dentro da frase."""
    cliente = ClienteFalso()
    frase = montar_frase_autorizacao(13959)
    gravar_spec_tecnica(
        cliente,
        id_demanda=13959,
        campo="Custom.DemandaSpecTecnica",
        spec_md="# Spec\n",
        resposta_confirmacao=f"  {frase}  \n",
    )
    assert len(cliente.chamadas) == 1
```

- [ ] **Step 2: Rodar os testes e confirmar que falham**

Run: `cd refinar-tecnicamente && uv run pytest tests/test_gravar_spec_tecnica.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'refinar_tecnicamente.gravar_spec_tecnica'`

- [ ] **Step 3: Implementar `gravar_spec_tecnica.py`**

```python
# refinar-tecnicamente/src/refinar_tecnicamente/gravar_spec_tecnica.py
"""Converte a spec técnica para HTML e grava `Custom.DemandaSpecTecnica` sob confirmação
textual explícita — a única escrita desta skill no Azure Boards."""

from __future__ import annotations

from html.parser import HTMLParser
from typing import TYPE_CHECKING, Protocol

from markdown_it import MarkdownIt

if TYPE_CHECKING:
    pass

_TAGS_SEM_FECHAMENTO = frozenset({"br", "hr", "img", "input", "meta", "col", "wbr"})


class _ClienteEscrita(Protocol):
    def gravar_campo(self, work_item_id: int, campo: str, valor: str) -> None: ...


class ErroConfirmacaoInvalida(ValueError):
    """A resposta do usuário não é exatamente a frase de autorização esperada."""


class ErroHtmlInvalido(ValueError):
    """O HTML gerado a partir da spec não está bem formado; a gravação é recusada."""


class _ValidadorDeAninhamento(HTMLParser):
    """Levanta erro na primeira tag de fechamento que não corresponde à mais recente aberta."""

    def __init__(self) -> None:
        super().__init__()
        self._pilha: list[str] = []

    def handle_starttag(self, tag: str, _attrs: list[tuple[str, str | None]]) -> None:
        if tag not in _TAGS_SEM_FECHAMENTO:
            self._pilha.append(tag)

    def handle_endtag(self, tag: str) -> None:
        if not self._pilha or self._pilha[-1] != tag:
            raise ErroHtmlInvalido(
                f"Tag de fechamento </{tag}> não corresponde à tag aberta mais recente."
            )
        self._pilha.pop()

    def verificar_tudo_fechado(self) -> None:
        if self._pilha:
            raise ErroHtmlInvalido(f"Tags não fechadas: {', '.join(self._pilha)}.")


def _renderizar_markdown(spec_md: str) -> str:
    return MarkdownIt("commonmark").render(spec_md)


def converter_para_html(spec_md: str) -> str:
    """Converte Markdown para HTML e recusa gravar se o resultado não estiver bem formado."""
    html = _renderizar_markdown(spec_md)
    validador = _ValidadorDeAninhamento()
    validador.feed(html)
    validador.verificar_tudo_fechado()
    return html


def montar_frase_autorizacao(id_demanda: int) -> str:
    """Frase que a pessoa precisa digitar exatamente; nomeia a Demanda de propósito."""
    return f"AUTORIZAR GRAVAÇÃO SPEC TÉCNICA #{id_demanda}"


def gravar_spec_tecnica(
    cliente: _ClienteEscrita,
    *,
    id_demanda: int,
    campo: str,
    spec_md: str,
    resposta_confirmacao: str,
) -> None:
    """Grava a spec técnica convertida, só após confirmação textual exata."""
    frase_esperada = montar_frase_autorizacao(id_demanda)
    if resposta_confirmacao.strip() != frase_esperada:
        raise ErroConfirmacaoInvalida(
            "Confirmação ausente, incorreta ou vinculada a outra Demanda; nenhuma gravação foi feita."
        )
    html = converter_para_html(spec_md)
    cliente.gravar_campo(id_demanda, campo, html)
```

- [ ] **Step 4: Rodar os testes e confirmar que passam**

Run: `cd refinar-tecnicamente && uv run pytest tests/test_gravar_spec_tecnica.py -v`
Expected: PASS (9 testes, incluindo os 5 casos parametrizados)

- [ ] **Step 5: Commit**

```bash
cd refinar-tecnicamente
git add src/refinar_tecnicamente/gravar_spec_tecnica.py tests/test_gravar_spec_tecnica.py
git commit -m "feat(refinar-tecnicamente): conversão para HTML e gravação sob confirmação

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

### Task 5: CLI, SKILL.md e teste de integração da skill 1

**Files:**
- Create: `refinar-tecnicamente/src/refinar_tecnicamente/cli.py`
- Modify: `refinar-tecnicamente/src/refinar_tecnicamente/__init__.py`
- Create: `refinar-tecnicamente/SKILL.md`
- Create: `refinar-tecnicamente/README.md`
- Test: `refinar-tecnicamente/tests/test_cli.py`

**Interfaces:**
- Consumes: `carregar_configuracao` (Task 1), `ClienteAzureDevOps` (Task 1), `ler_lacunas`/`filtrar_tecnicas` (Task 2), `sugerir_story_points` (Task 3), `montar_frase_autorizacao`/`gravar_spec_tecnica` (Task 4)
- Produces: `executar(argv: list[str], *, env: Mapping[str, str], entrada: Callable[[str], str] = input) -> int`

- [ ] **Step 1: Escrever os testes**

```python
# refinar-tecnicamente/tests/test_cli.py
import json
from pathlib import Path

from refinar_tecnicamente.cli import executar

_ENV = {
    "AZURE_DEVOPS_ORGANIZACAO": "minha-org",
    "AZURE_DEVOPS_PROJETO": "meu-projeto",
    "AZURE_DEVOPS_TOKEN": "token",
}

_SPEC = """# Spec

## Lacunas e perguntas abertas

- **N3 · Negócio** — Pergunta de negócio?
- **T2 · Técnico** — Pergunta técnica?
"""


def test_ler_lacunas_imprime_so_as_tecnicas(tmp_path: Path, capsys: object) -> None:
    spec = tmp_path / "spec.md"
    spec.write_text(_SPEC, encoding="utf-8")
    codigo = executar(["ler-lacunas", str(spec)], env=_ENV)
    saida = capsys.readouterr().out  # type: ignore[attr-defined]
    lacunas = json.loads(saida)
    assert codigo == 0
    assert len(lacunas) == 1
    assert lacunas[0]["id"] == "T2"


def test_ler_lacunas_com_arquivo_inexistente_devolve_codigo_de_erro(capsys: object) -> None:
    codigo = executar(["ler-lacunas", "/caminho/que/nao/existe.md"], env=_ENV)
    assert codigo != 0


def test_gravar_spec_tecnica_sem_confirmacao_exata_nao_chama_rede(
    tmp_path: Path, capsys: object
) -> None:
    spec = tmp_path / "spec.md"
    spec.write_text("# Spec\n", encoding="utf-8")
    codigo = executar(
        [
            "gravar-spec-tecnica",
            "--demanda",
            "13959",
            "--spec",
            str(spec),
        ],
        env=_ENV,
        entrada=lambda _prompt: "resposta errada",
    )
    saida = capsys.readouterr().out  # type: ignore[attr-defined]
    assert codigo != 0
    assert "13959" in saida  # a frase esperada foi mostrada, nomeando a Demanda
```

- [ ] **Step 2: Rodar os testes e confirmar que falham**

Run: `cd refinar-tecnicamente && uv run pytest tests/test_cli.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'refinar_tecnicamente.cli'`

- [ ] **Step 3: Implementar `cli.py`**

```python
# refinar-tecnicamente/src/refinar_tecnicamente/cli.py
"""CLI de apoio à skill: cada subcomando cobre um passo do SKILL.md que precisa de rede
ou de parsing determinístico. A condução da entrevista e a investigação de código
continuam sendo trabalho do agente, fora deste arquivo."""

from __future__ import annotations

import argparse
import dataclasses
import json
from collections.abc import Callable, Mapping
from pathlib import Path

from refinar_tecnicamente.ancoragem_story_points import sugerir_story_points
from refinar_tecnicamente.cliente_azure_devops import ClienteAzureDevOps
from refinar_tecnicamente.configuracao import ErroConfiguracao, carregar_configuracao
from refinar_tecnicamente.gravar_spec_tecnica import (
    ErroConfirmacaoInvalida,
    gravar_spec_tecnica,
    montar_frase_autorizacao,
)
from refinar_tecnicamente.leitor_lacunas import filtrar_tecnicas, ler_lacunas


def executar(
    argv: list[str], *, env: Mapping[str, str], entrada: Callable[[str], str] = input
) -> int:
    parser = _construir_parser()
    args = parser.parse_args(argv)
    try:
        if args.comando == "ler-lacunas":
            return _ler_lacunas(args.spec)
        if args.comando == "sugerir-story-points":
            return _sugerir_story_points(args, env)
        if args.comando == "gravar-spec-tecnica":
            return _gravar_spec_tecnica(args, env, entrada)
    except ErroConfiguracao as erro:
        print(f"Configuração inválida: {erro}")
        return 2
    parser.error("comando desconhecido")
    return 2


def _construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="refinar-tecnicamente")
    subs = parser.add_subparsers(dest="comando", required=True)

    ler = subs.add_parser("ler-lacunas")
    ler.add_argument("spec")

    sugerir = subs.add_parser("sugerir-story-points")
    sugerir.add_argument("--area-path", required=True)
    sugerir.add_argument("--tipo", action="append", dest="tipos", required=True)

    gravar = subs.add_parser("gravar-spec-tecnica")
    gravar.add_argument("--demanda", type=int, required=True)
    gravar.add_argument("--spec", required=True)
    gravar.add_argument("--campo", default="Custom.DemandaSpecTecnica")

    return parser


def _ler_lacunas(caminho_spec: str) -> int:
    caminho = Path(caminho_spec)
    if not caminho.is_file():
        print(f"Spec não encontrada: {caminho_spec}")
        return 1
    lacunas = filtrar_tecnicas(ler_lacunas(caminho.read_text(encoding="utf-8")))
    print(json.dumps([dataclasses.asdict(l) for l in lacunas], ensure_ascii=False, indent=2))
    return 0


def _sugerir_story_points(args: argparse.Namespace, env: Mapping[str, str]) -> int:
    config = carregar_configuracao(env)
    with ClienteAzureDevOps(
        config.organizacao, config.projeto, config.token.get_secret_value()
    ) as cliente:
        sugestao = sugerir_story_points(
            cliente, projeto=config.projeto, area_path=args.area_path, tipos=tuple(args.tipos)
        )
    print(json.dumps(dataclasses.asdict(sugestao), ensure_ascii=False, indent=2))
    return 0


def _gravar_spec_tecnica(
    args: argparse.Namespace, env: Mapping[str, str], entrada: Callable[[str], str]
) -> int:
    config = carregar_configuracao(env)
    spec_md = Path(args.spec).read_text(encoding="utf-8")
    frase = montar_frase_autorizacao(args.demanda)
    print(f"Digite exatamente a frase abaixo para confirmar a gravação em {args.campo}:")
    print(frase)
    resposta = entrada("> ")
    try:
        with ClienteAzureDevOps(
            config.organizacao, config.projeto, config.token.get_secret_value()
        ) as cliente:
            gravar_spec_tecnica(
                cliente,
                id_demanda=args.demanda,
                campo=args.campo,
                spec_md=spec_md,
                resposta_confirmacao=resposta,
            )
    except ErroConfirmacaoInvalida as erro:
        print(str(erro))
        return 1
    print("Spec técnica gravada.")
    return 0
```

```python
# refinar-tecnicamente/src/refinar_tecnicamente/__init__.py
"""Skill de refinamento técnico: fecha lacunas técnicas, registra abordagem e Story Points."""

from __future__ import annotations

import os
import sys


def main() -> None:
    from refinar_tecnicamente.cli import executar

    raise SystemExit(executar(sys.argv[1:], env=os.environ))
```

- [ ] **Step 4: Rodar os testes e confirmar que passam**

Run: `cd refinar-tecnicamente && uv run pytest tests/ -v`
Expected: PASS (todos os testes do pacote, inclusive os 3 novos de CLI)

- [ ] **Step 5: Escrever o SKILL.md**

```markdown
---
name: refinar-tecnicamente
description: Use na reunião técnica de refinamento, sobre a spec.md de uma Demanda já publicada no Azure Boards, para fechar as lacunas técnicas, registrar a abordagem e estimar Story Points.
---

# Refinar tecnicamente uma Demanda já publicada

## Objetivo

Fechar as lacunas rotuladas `Técnico` de `spec.md`, investigar o código e registrar a abordagem
técnica como seção nova da spec, estimar Story Points de cada História/Bug do backlog associado —
ancorado em itens fechados comparáveis, nunca inventado — e prender a spec atualizada à Demanda de
Negócio via `Custom.DemandaSpecTecnica`.

## Fluxo obrigatório

1. Receba o caminho da pasta `DN-<id>-<slug>/` (ou o ID da Demanda, resolvendo a pasta pela
   convenção de nomes do `gerador-hu`) e o ID da Demanda no Azure Boards.
2. Rode `ler-lacunas spec.md` para isolar as lacunas técnicas (e as sem rótulo, que entram em toda
   rodada). Conduza a entrevista em rodadas, no mesmo mecanismo de fronteira do
   `entrevistar-lacunas-requisito`: pergunte os itens que não dependem de resposta ainda em aberto,
   aceite adiamento explícito, nunca feche uma lacuna por inferência silenciosa.
3. Com as lacunas técnicas fechadas, investigue o código-fonte e escreva a seção
   `## Abordagem técnica` em `spec.md`: camadas tocadas, migração quando houver, estratégia de teste.
   Cite `caminho:linha` para cada afirmação, na mesma disciplina do resto da spec.
4. Para cada História/Bug do `backlog.md` associado, rode `sugerir-story-points --area-path <Area
   Path da Demanda> --tipo "User Story" --tipo Bug`. Quando a sugestão vier com `pontos: null`, não
   prossiga sozinho — pergunte a pontuação a quem está na reunião e registre a resposta no backlog;
   ela se torna histórico para a próxima execução.
5. Grave os Story Points sugeridos ou confirmados em `backlog.md`, um por História/Bug.
6. Rode `gravar-spec-tecnica --demanda <id> --spec spec.md`. Mostre a `spec.md` completa antes de
   confirmar. A CLI pede a frase de autorização; ela só grava (`PATCH`) se a resposta for
   **exatamente** igual — variação de caixa, acentuação ou Demanda errada é recusada sem chamada
   alguma ao Azure Boards.

## O que esta skill nunca faz

- Não cria Épico, Feature, História ou Bug — isso é exclusivo de
  `publicar-backlog-demanda-azure-boards`, no `gerador-hu`.
- Não decompõe em Tasks nem estima horas — isso é `decompor-tasks`, no momento do planning, pelo
  desenvolvedor que vai executar.
- Não inventa Story Points sem ancoragem em histórico ou confirmação humana explícita.
```

- [ ] **Step 6: Escrever o README.md**

```markdown
# refinar-tecnicamente

Skill de refinamento técnico: fecha as lacunas técnicas de uma spec já produzida pelo
[`gerador-hu`](https://github.com/pedroct/gerador-de-hu), registra a abordagem técnica e estima
Story Points ancorados em itens fechados comparáveis, gravando o resultado em
`Custom.DemandaSpecTecnica` na Demanda de Negócio.

## Instalação

```bash
npx skills add pedroct/refinamento-planejamento-tecnico --skill refinar-tecnicamente -a claude-code
```

## Configuração

Copie `.env.example` para `.env` e preencha organização, projeto e token do Azure DevOps. O token
nunca deve ser versionado.
```

- [ ] **Step 7: Commit**

```bash
cd refinar-tecnicamente
git add src/refinar_tecnicamente/cli.py src/refinar_tecnicamente/__init__.py SKILL.md README.md tests/test_cli.py
git commit -m "feat(refinar-tecnicamente): CLI, SKILL.md e testes de integração

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

## Skill 2 — `decompor-tasks`

### Task 6: Scaffold do pacote, configuração e cliente Azure DevOps (leitura + escrita)

**Files:**
- Create: `decompor-tasks/pyproject.toml`
- Create: `decompor-tasks/.env.example`
- Create: `decompor-tasks/.gitignore`
- Create: `decompor-tasks/src/decompor_tasks/__init__.py`
- Create: `decompor-tasks/src/decompor_tasks/configuracao.py`
- Create: `decompor-tasks/src/decompor_tasks/cliente_azure_devops.py`
- Test: `decompor-tasks/tests/test_configuracao.py`
- Test: `decompor-tasks/tests/test_cliente_azure_devops.py`

**Interfaces:**
- Produces: `carregar_configuracao(env) -> ConfiguracaoDecomposicao` (campos: `organizacao: str`, `projeto: str`, `token: SecretStr`, `tipo_task: str = "Task"`)
- Produces: `class ClienteAzureDevOps` com `ler_work_item(id) -> dict`, `consultar_wiql(wiql) -> list[int]`, `criar_work_item(tipo, operacoes) -> dict`, `usuario_autenticado() -> dict`
- Produces: `ErroDestinoInvalido`, `ErroFalhaTransitoria`, `ErroRespostaInvalida`

Idêntico em estrutura ao Task 1 de `refinar-tecnicamente`, com duas diferenças: o cliente troca
`gravar_campo` por `criar_work_item` (esta skill cria Task, não grava campo), e `configuracao.py`
troca `campo_spec_tecnica` por `tipo_task`.

- [ ] **Step 1: Escrever pyproject.toml, .env.example e .gitignore**

```toml
[build-system]
requires = ["hatchling==1.29.0"]
build-backend = "hatchling.build"

[project]
name = "decompor-tasks"
version = "0.1.0"
description = "Decomposição de uma História/Bug em Tasks estimadas em horas, no planning"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
  "httpx==0.28.1",
  "pydantic==2.13.5",
  "pydantic-settings==2.15.0",
]

[project.scripts]
decompor-tasks = "decompor_tasks:main"

[dependency-groups]
dev = [
  "mypy==2.1.0",
  "pytest==9.0.3",
  "ruff==0.15.14",
]

[tool.hatch.build.targets.wheel]
packages = ["src/decompor_tasks"]

[tool.ruff]
line-length = 100
target-version = "py312"
exclude = [".venv/", ".git/"]

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "S"]

[tool.ruff.lint.per-file-ignores]
"**/tests/**/*.py" = ["S101"]

[tool.mypy]
python_version = "3.12"
strict = true
warn_unused_ignores = true

[tool.pytest.ini_options]
testpaths = ["tests"]
```

```text
# decompor-tasks/.env.example
AZURE_DEVOPS_ORGANIZACAO=
AZURE_DEVOPS_PROJETO=
AZURE_DEVOPS_TOKEN=
AZURE_DEVOPS_TIPO_TASK=Task
```

```text
# decompor-tasks/.gitignore
.venv/
__pycache__/
*.pyc
.env
.mypy_cache/
.pytest_cache/
.ruff_cache/
uv.lock
.manifestos/
```

```python
# decompor-tasks/src/decompor_tasks/__init__.py
"""Skill de planejamento: decompõe uma História/Bug em Tasks estimadas em horas."""

from __future__ import annotations
```

- [ ] **Step 2: Escrever o teste de configuração**

```python
# decompor-tasks/tests/test_configuracao.py
import pytest

from decompor_tasks.configuracao import ErroConfiguracao, carregar_configuracao


def test_carrega_configuracao_completa() -> None:
    env = {
        "AZURE_DEVOPS_ORGANIZACAO": "minha-org",
        "AZURE_DEVOPS_PROJETO": "meu-projeto",
        "AZURE_DEVOPS_TOKEN": "token-secreto",
    }
    config = carregar_configuracao(env)
    assert config.organizacao == "minha-org"
    assert config.tipo_task == "Task"


def test_recusa_configuracao_sem_projeto() -> None:
    env = {"AZURE_DEVOPS_ORGANIZACAO": "minha-org", "AZURE_DEVOPS_TOKEN": "x"}
    with pytest.raises(ErroConfiguracao):
        carregar_configuracao(env)


def test_aceita_tipo_task_customizado() -> None:
    env = {
        "AZURE_DEVOPS_ORGANIZACAO": "minha-org",
        "AZURE_DEVOPS_PROJETO": "meu-projeto",
        "AZURE_DEVOPS_TOKEN": "x",
        "AZURE_DEVOPS_TIPO_TASK": "Tarefa",
    }
    assert carregar_configuracao(env).tipo_task == "Tarefa"
```

- [ ] **Step 3: Rodar os testes e confirmar que falham**

Run: `cd decompor-tasks && uv run pytest tests/test_configuracao.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'decompor_tasks.configuracao'`

- [ ] **Step 4: Implementar `configuracao.py`**

```python
# decompor-tasks/src/decompor_tasks/configuracao.py
"""Carrega a configuração local sem expor o token em representações textuais."""

from __future__ import annotations

from collections.abc import Mapping

from pydantic import BaseModel, ConfigDict, SecretStr, ValidationError, field_validator


class ErroConfiguracao(ValueError):
    """Indica que não foi possível obter uma configuração completa e segura."""


class ConfiguracaoDecomposicao(BaseModel):
    """Agrupa organização, projeto, credencial e o nome remoto do tipo Task."""

    model_config = ConfigDict(frozen=True)

    organizacao: str
    projeto: str
    token: SecretStr
    tipo_task: str = "Task"

    @field_validator("organizacao", "projeto", "tipo_task")
    @classmethod
    def _validar_texto_obrigatorio(cls, valor: str) -> str:
        texto = valor.strip()
        if not texto:
            raise ValueError("deve ser informado")
        return texto

    @field_validator("token")
    @classmethod
    def _validar_token(cls, valor: SecretStr) -> SecretStr:
        if not valor.get_secret_value().strip():
            raise ValueError("deve ser informado")
        return valor


def carregar_configuracao(env: Mapping[str, str]) -> ConfiguracaoDecomposicao:
    """Lê a configuração a partir de um mapa de variáveis de ambiente já resolvido."""
    try:
        return ConfiguracaoDecomposicao(
            organizacao=env.get("AZURE_DEVOPS_ORGANIZACAO", ""),
            projeto=env.get("AZURE_DEVOPS_PROJETO", ""),
            token=env.get("AZURE_DEVOPS_TOKEN", ""),
            tipo_task=env.get("AZURE_DEVOPS_TIPO_TASK", "Task"),
        )
    except ValidationError as erro:
        raise ErroConfiguracao(f"Configuração incompleta ou inválida: {erro}") from erro
```

- [ ] **Step 5: Rodar os testes de configuração e confirmar que passam**

Run: `cd decompor-tasks && uv run pytest tests/test_configuracao.py -v`
Expected: PASS (3 testes)

- [ ] **Step 6: Escrever o teste do cliente Azure DevOps**

```python
# decompor-tasks/tests/test_cliente_azure_devops.py
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
```

- [ ] **Step 7: Rodar os testes do cliente e confirmar que falham**

Run: `cd decompor-tasks && uv run pytest tests/test_cliente_azure_devops.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'decompor_tasks.cliente_azure_devops'`

- [ ] **Step 8: Implementar `cliente_azure_devops.py`**

```python
# decompor-tasks/src/decompor_tasks/cliente_azure_devops.py
"""Cliente HTTP mínimo para leitura e criação de work items no Azure Boards via REST.

Cópia vendorizada do mesmo padrão usado em `refinar-tecnicamente` e em
`publicar-backlog-demanda-azure-boards` (repositório `gerador-hu`). Ressincronize manualmente
se o padrão de retentativa mudar em algum dos irmãos.
"""

from __future__ import annotations

import base64
import time
from typing import Any

import httpx

_VERSAO_API = "7.2-preview.3"
_VERSAO_WIQL = "7.2-preview.2"
_ERROS_RETENTAVEIS = frozenset({408, 429, 500, 502, 503, 504})
_MAX_TENTATIVAS = 3


class ErroDestinoInvalido(ValueError):
    """O work item, tipo ou consulta solicitados não existem ou são inválidos."""


class ErroFalhaTransitoria(RuntimeError):
    """A chamada falhou por rede ou por erro remoto retentável, mesmo após tentativas."""


class ErroRespostaInvalida(RuntimeError):
    """A resposta remota não é JSON consumível ou não tem o formato esperado."""


class ClienteAzureDevOps:
    """Encapsula autenticação básica por PAT e o padrão de retentativa com backoff."""

    def __init__(
        self,
        organizacao: str,
        projeto: str,
        token: str,
        *,
        transport: httpx.BaseTransport | None = None,
        timeout: float = 10.0,
        espera_inicial: float = 0.2,
    ) -> None:
        self._organizacao = organizacao
        self._projeto = projeto
        self._espera_inicial = espera_inicial
        credencial = base64.b64encode(f":{token}".encode()).decode()
        self._cliente = httpx.Client(
            headers={"Authorization": f"Basic {credencial}"},
            timeout=httpx.Timeout(timeout),
            transport=transport,
        )

    def __enter__(self) -> ClienteAzureDevOps:
        return self

    def __exit__(self, *_exc: object) -> None:
        self._cliente.close()

    def ler_work_item(self, work_item_id: int) -> dict[str, Any]:
        url = (
            f"https://dev.azure.com/{self._organizacao}/{self._projeto}"
            f"/_apis/wit/workitems/{work_item_id}?$expand=All&api-version={_VERSAO_API}"
        )
        resposta = self._executar("GET", url)
        return self._verificar_e_decodificar(resposta, work_item_id)

    def consultar_wiql(self, wiql: str) -> list[int]:
        url = (
            f"https://dev.azure.com/{self._organizacao}/{self._projeto}"
            f"/_apis/wit/wiql?api-version={_VERSAO_WIQL}"
        )
        resposta = self._executar("POST", url, corpo={"query": wiql})
        payload = self._verificar_e_decodificar(resposta, None)
        itens = payload.get("workItems")
        if not isinstance(itens, list):
            raise ErroRespostaInvalida("A consulta WIQL não devolveu uma lista de work items.")
        ids: list[int] = []
        for item in itens:
            if not isinstance(item, dict) or not isinstance(item.get("id"), int):
                raise ErroRespostaInvalida("Um item da consulta WIQL não trouxe um ID inteiro.")
            ids.append(item["id"])
        return ids

    def criar_work_item(self, tipo: str, operacoes: list[dict[str, Any]]) -> dict[str, Any]:
        """Cria um work item do tipo informado, com a lista de operações JSON Patch dada."""
        url = (
            f"https://dev.azure.com/{self._organizacao}/{self._projeto}"
            f"/_apis/wit/workitems/${tipo}?api-version={_VERSAO_API}"
        )
        resposta = self._executar(
            "POST", url, corpo=operacoes, content_type="application/json-patch+json"
        )
        return self._verificar_e_decodificar(resposta, None)

    def usuario_autenticado(self) -> dict[str, Any]:
        url = (
            f"https://vssps.dev.azure.com/{self._organizacao}"
            "/_apis/profile/profiles/me?api-version=7.1"
        )
        resposta = self._executar("GET", url)
        return self._verificar_e_decodificar(resposta, None)

    def _executar(
        self,
        metodo: str,
        url: str,
        *,
        corpo: Any = None,
        content_type: str | None = None,
    ) -> httpx.Response:
        headers = {"Content-Type": content_type} if content_type else None
        for tentativa in range(_MAX_TENTATIVAS):
            try:
                resposta = self._cliente.request(metodo, url, json=corpo, headers=headers)
            except httpx.RequestError as erro:
                if tentativa == _MAX_TENTATIVAS - 1:
                    raise ErroFalhaTransitoria(
                        f"A chamada {metodo} {url} falhou por erro de rede."
                    ) from erro
            else:
                if resposta.status_code not in _ERROS_RETENTAVEIS:
                    return resposta
                if tentativa == _MAX_TENTATIVAS - 1:
                    raise ErroFalhaTransitoria(
                        f"A chamada {metodo} {url} não se completou "
                        f"(HTTP {resposta.status_code}) após {_MAX_TENTATIVAS} tentativas."
                    )
            time.sleep(self._espera_inicial * (2**tentativa))
        raise ErroFalhaTransitoria(f"A chamada {metodo} {url} não se completou.")

    def _verificar_e_decodificar(
        self, resposta: httpx.Response, work_item_id: int | None
    ) -> dict[str, Any]:
        if resposta.status_code == 404:
            alvo = f"work item {work_item_id}" if work_item_id else "o recurso solicitado"
            raise ErroDestinoInvalido(f"Não foi possível encontrar {alvo}.")
        if resposta.status_code >= 400:
            raise ErroDestinoInvalido(
                f"A chamada devolveu HTTP {resposta.status_code}: {resposta.text[:300]}"
            )
        try:
            corpo_json = resposta.json()
        except ValueError as erro:
            raise ErroRespostaInvalida("A resposta não é JSON consumível.") from erro
        if not isinstance(corpo_json, dict):
            raise ErroRespostaInvalida("A resposta não é um objeto JSON.")
        return corpo_json
```

- [ ] **Step 9: Rodar todos os testes do Task 6 e confirmar que passam**

Run: `cd decompor-tasks && uv run pytest tests/ -v`
Expected: PASS (9 testes)

- [ ] **Step 10: Commit**

```bash
cd decompor-tasks
git add pyproject.toml .env.example .gitignore src/ tests/
git commit -m "feat(decompor-tasks): scaffold, configuração e cliente Azure DevOps

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

### Task 7: Ancoragem de horas em Tasks fechadas comparáveis

**Files:**
- Create: `decompor-tasks/src/decompor_tasks/ancoragem_horas.py`
- Test: `decompor-tasks/tests/test_ancoragem_horas.py`

**Interfaces:**
- Consumes: `ClienteAzureDevOps.consultar_wiql`, `ClienteAzureDevOps.ler_work_item` (Task 6)
- Produces: `@dataclass(frozen=True) class SugestaoHoras` (campos: `horas: float | None`, `baseado_em: tuple[int, ...]`)
- Produces: `sugerir_horas(cliente, *, projeto: str, area_path: str, tipo_task: str, titulo_aproximado: str, limite: int = 20) -> SugestaoHoras`

A busca por comparável usa duas condições: mesmo Area Path e `System.Title` contendo pelo menos uma
palavra significativa (4+ caracteres) do título da Task proposta — um filtro simples de similaridade
lexical, suficiente para reduzir o ruído de Tasks fechadas sem relação nenhuma com a proposta.

- [ ] **Step 1: Escrever os testes**

```python
# decompor-tasks/tests/test_ancoragem_horas.py
from typing import Any

from decompor_tasks.ancoragem_horas import sugerir_horas


class ClienteFalso:
    def __init__(self, ids: list[int], itens: dict[int, dict[str, Any]]) -> None:
        self._ids = ids
        self._itens = itens
        self.wiql_recebido: str | None = None

    def consultar_wiql(self, wiql: str) -> list[int]:
        self.wiql_recebido = wiql
        return self._ids

    def ler_work_item(self, work_item_id: int) -> dict[str, Any]:
        return self._itens[work_item_id]


def _task(titulo: str, completed_work: float | None) -> dict[str, Any]:
    fields: dict[str, Any] = {"System.Title": titulo}
    if completed_work is not None:
        fields["Microsoft.VSTS.Scheduling.CompletedWork"] = completed_work
    return {"fields": fields}


def test_sugere_mediana_de_tasks_com_titulo_parecido() -> None:
    itens = {
        1: _task("Criar endpoint de renovação de diligência", 4.0),
        2: _task("Ajustar endpoint de renovação de convite", 6.0),
        3: _task("Corrigir layout do menu lateral", 2.0),  # sem relação lexical
    }
    cliente = ClienteFalso([1, 2, 3], itens)
    sugestao = sugerir_horas(
        cliente,
        projeto="proj",
        area_path="proj\\Time A",
        tipo_task="Task",
        titulo_aproximado="Criar endpoint de renovação de convite",
    )
    assert sugestao.horas == 5.0
    assert sugestao.baseado_em == (1, 2)


def test_ignora_tasks_sem_completed_work() -> None:
    itens = {1: _task("Criar endpoint de renovação", 4.0), 2: _task("Renovação de teste", None)}
    cliente = ClienteFalso([1, 2], itens)
    sugestao = sugerir_horas(
        cliente,
        projeto="proj",
        area_path="proj\\Time A",
        tipo_task="Task",
        titulo_aproximado="Renovação de diligência",
    )
    assert sugestao.horas == 4.0
    assert sugestao.baseado_em == (1,)


def test_sem_titulo_parecido_devolve_none() -> None:
    itens = {1: _task("Corrigir cor do botão", 1.0)}
    cliente = ClienteFalso([1], itens)
    sugestao = sugerir_horas(
        cliente,
        projeto="proj",
        area_path="proj\\Time A",
        tipo_task="Task",
        titulo_aproximado="Criar endpoint de renovação",
    )
    assert sugestao.horas is None
    assert sugestao.baseado_em == ()


def test_sem_nenhum_item_devolve_none() -> None:
    cliente = ClienteFalso([], {})
    sugestao = sugerir_horas(
        cliente,
        projeto="proj",
        area_path="proj\\Time A",
        tipo_task="Task",
        titulo_aproximado="Qualquer coisa",
    )
    assert sugestao.horas is None


def test_consulta_filtra_projeto_area_e_tipo_task() -> None:
    cliente = ClienteFalso([], {})
    sugerir_horas(
        cliente,
        projeto="proj",
        area_path="proj\\Time A",
        tipo_task="Task",
        titulo_aproximado="Qualquer coisa",
    )
    assert cliente.wiql_recebido is not None
    assert "proj\\Time A" in cliente.wiql_recebido
    assert "'Task'" in cliente.wiql_recebido
    assert "Closed" in cliente.wiql_recebido
```

- [ ] **Step 2: Rodar os testes e confirmar que falham**

Run: `cd decompor-tasks && uv run pytest tests/test_ancoragem_horas.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'decompor_tasks.ancoragem_horas'`

- [ ] **Step 3: Implementar `ancoragem_horas.py`**

```python
# decompor-tasks/src/decompor_tasks/ancoragem_horas.py
"""Sugere horas (Original Estimate/Remaining) a partir de Tasks fechadas comparáveis."""

from __future__ import annotations

import re
import statistics
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from typing import Any

_ESTADOS_FECHADOS = ("Closed", "Done", "Resolved")
_CAMPO_COMPLETED_WORK = "Microsoft.VSTS.Scheduling.CompletedWork"
_TAMANHO_MINIMO_PALAVRA = 4


class _ClienteLeitura(Protocol):
    def consultar_wiql(self, wiql: str) -> list[int]: ...
    def ler_work_item(self, work_item_id: int) -> dict[str, Any]: ...


@dataclass(frozen=True)
class SugestaoHoras:
    """`horas` é `None` quando não há Task fechada comparável com Completed Work preenchido."""

    horas: float | None
    baseado_em: tuple[int, ...]


def _palavras_significativas(titulo: str) -> set[str]:
    palavras = re.findall(r"\w+", titulo.lower())
    return {p for p in palavras if len(p) >= _TAMANHO_MINIMO_PALAVRA}


def sugerir_horas(
    cliente: _ClienteLeitura,
    *,
    projeto: str,
    area_path: str,
    tipo_task: str,
    titulo_aproximado: str,
    limite: int = 20,
) -> SugestaoHoras:
    """Consulta Tasks fechadas no mesmo Area Path, filtra por semelhança de título e
    propõe a mediana do Completed Work das que sobrarem."""
    estados_wiql = ", ".join(f"'{estado}'" for estado in _ESTADOS_FECHADOS)
    wiql = (
        "SELECT [System.Id] FROM WorkItems "
        f"WHERE [System.TeamProject] = '{projeto}' "
        f"AND [System.AreaPath] UNDER '{area_path}' "
        f"AND [System.WorkItemType] = '{tipo_task}' "
        f"AND [System.State] IN ({estados_wiql}) "
        "ORDER BY [System.ChangedDate] DESC"
    )
    ids = cliente.consultar_wiql(wiql)[:limite]
    palavras_alvo = _palavras_significativas(titulo_aproximado)
    pontuados: list[tuple[int, float]] = []
    for work_item_id in ids:
        campos = cliente.ler_work_item(work_item_id).get("fields", {})
        titulo = campos.get("System.Title", "")
        if not palavras_alvo & _palavras_significativas(titulo):
            continue
        horas = campos.get(_CAMPO_COMPLETED_WORK)
        if isinstance(horas, int | float):
            pontuados.append((work_item_id, float(horas)))
    if not pontuados:
        return SugestaoHoras(horas=None, baseado_em=())
    mediana = statistics.median(valor for _id, valor in pontuados)
    return SugestaoHoras(horas=mediana, baseado_em=tuple(id_ for id_, _valor in pontuados))
```

- [ ] **Step 4: Rodar os testes e confirmar que passam**

Run: `cd decompor-tasks && uv run pytest tests/test_ancoragem_horas.py -v`
Expected: PASS (5 testes)

- [ ] **Step 5: Commit**

```bash
cd decompor-tasks
git add src/decompor_tasks/ancoragem_horas.py tests/test_ancoragem_horas.py
git commit -m "feat(decompor-tasks): ancoragem de horas em Tasks fechadas comparáveis

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

### Task 8: Plano, manifesto de retomada e frase de autorização

**Files:**
- Create: `decompor-tasks/src/decompor_tasks/manifesto.py`
- Test: `decompor-tasks/tests/test_manifesto.py`

**Interfaces:**
- Produces: `@dataclass(frozen=True) class TaskProposta` (campos: `titulo: str`, `original_estimate: float`, `remaining: float`, `assigned_to: str`)
- Produces: `@dataclass(frozen=True) class PlanoTasks` (campos: `historia_id: int`, `tasks: tuple[TaskProposta, ...]`)
- Produces: `@dataclass(frozen=True) class Manifesto` (campos: `historia_id: int`, `hash_plano: str`, `criadas: dict[str, int]`)
- Produces: `calcular_hash_plano(plano: PlanoTasks) -> str`
- Produces: `ler_manifesto(caminho: Path) -> Manifesto | None`
- Produces: `gravar_manifesto(caminho: Path, manifesto: Manifesto) -> None`
- Produces: `tasks_pendentes(plano: PlanoTasks, manifesto: Manifesto | None) -> tuple[TaskProposta, ...]`
- Produces: `ErroReconciliacaoNecessaria`
- Produces: `montar_frase_autorizacao(historia_id: int) -> str`

- [ ] **Step 1: Escrever os testes**

```python
# decompor-tasks/tests/test_manifesto.py
from pathlib import Path

import pytest

from decompor_tasks.manifesto import (
    ErroReconciliacaoNecessaria,
    Manifesto,
    PlanoTasks,
    TaskProposta,
    calcular_hash_plano,
    gravar_manifesto,
    ler_manifesto,
    montar_frase_autorizacao,
    tasks_pendentes,
)

_TASK_A = TaskProposta(titulo="Task A", original_estimate=4.0, remaining=4.0, assigned_to="dev@x")
_TASK_B = TaskProposta(titulo="Task B", original_estimate=2.0, remaining=2.0, assigned_to="dev@x")


def test_hash_e_estavel_para_o_mesmo_plano() -> None:
    plano = PlanoTasks(historia_id=100, tasks=(_TASK_A, _TASK_B))
    assert calcular_hash_plano(plano) == calcular_hash_plano(plano)


def test_hash_muda_quando_o_plano_muda() -> None:
    plano1 = PlanoTasks(historia_id=100, tasks=(_TASK_A,))
    plano2 = PlanoTasks(historia_id=100, tasks=(_TASK_A, _TASK_B))
    assert calcular_hash_plano(plano1) != calcular_hash_plano(plano2)


def test_sem_manifesto_todas_as_tasks_estao_pendentes() -> None:
    plano = PlanoTasks(historia_id=100, tasks=(_TASK_A, _TASK_B))
    assert tasks_pendentes(plano, None) == (_TASK_A, _TASK_B)


def test_com_manifesto_do_mesmo_hash_so_falta_o_que_nao_foi_criado() -> None:
    plano = PlanoTasks(historia_id=100, tasks=(_TASK_A, _TASK_B))
    manifesto = Manifesto(
        historia_id=100, hash_plano=calcular_hash_plano(plano), criadas={"Task A": 501}
    )
    assert tasks_pendentes(plano, manifesto) == (_TASK_B,)


def test_hash_diferente_sem_criadas_reinicia_do_zero() -> None:
    plano = PlanoTasks(historia_id=100, tasks=(_TASK_A, _TASK_B))
    manifesto = Manifesto(historia_id=100, hash_plano="hash-antigo", criadas={})
    assert tasks_pendentes(plano, manifesto) == (_TASK_A, _TASK_B)


def test_hash_diferente_com_criadas_exige_reconciliacao() -> None:
    plano = PlanoTasks(historia_id=100, tasks=(_TASK_A, _TASK_B))
    manifesto = Manifesto(historia_id=100, hash_plano="hash-antigo", criadas={"Task A": 501})
    with pytest.raises(ErroReconciliacaoNecessaria):
        tasks_pendentes(plano, manifesto)


def test_gravar_e_ler_manifesto_preserva_conteudo(tmp_path: Path) -> None:
    caminho = tmp_path / "historia-100.json"
    manifesto = Manifesto(historia_id=100, hash_plano="abc", criadas={"Task A": 501})
    gravar_manifesto(caminho, manifesto)
    lido = ler_manifesto(caminho)
    assert lido == manifesto


def test_ler_manifesto_inexistente_devolve_none(tmp_path: Path) -> None:
    assert ler_manifesto(tmp_path / "nao-existe.json") is None


def test_frase_de_autorizacao_nomeia_a_historia() -> None:
    frase = montar_frase_autorizacao(100)
    assert "100" in frase
    assert frase.startswith("AUTORIZAR TASKS")
```

- [ ] **Step 2: Rodar os testes e confirmar que falham**

Run: `cd decompor-tasks && uv run pytest tests/test_manifesto.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'decompor_tasks.manifesto'`

- [ ] **Step 3: Implementar `manifesto.py`**

```python
# decompor-tasks/src/decompor_tasks/manifesto.py
"""Plano, manifesto de retomada e frase de autorização para a criação de Tasks.

O manifesto garante que uma reexecução após falha parcial retome sem duplicar Tasks: uma
mudança no hash do plano com criações já registradas bloqueia nova escrita até reconciliação
manual, no mesmo espírito de `publicar-backlog-demanda-azure-boards`.
"""

from __future__ import annotations

import hashlib
import json
import tempfile
from dataclasses import dataclass, field
from pathlib import Path


class ErroReconciliacaoNecessaria(RuntimeError):
    """O plano mudou depois que algumas Tasks já foram criadas sob o hash anterior."""


@dataclass(frozen=True)
class TaskProposta:
    """Uma Task ainda não criada, com a estimativa e o responsável já decididos."""

    titulo: str
    original_estimate: float
    remaining: float
    assigned_to: str


@dataclass(frozen=True)
class PlanoTasks:
    """A decomposição completa de uma História/Bug em Tasks propostas."""

    historia_id: int
    tasks: tuple[TaskProposta, ...]


@dataclass(frozen=True)
class Manifesto:
    """Registra o hash do plano confirmado e as Tasks já criadas (`título -> ID`)."""

    historia_id: int
    hash_plano: str
    criadas: dict[str, int] = field(default_factory=dict)


def calcular_hash_plano(plano: PlanoTasks) -> str:
    """Hash estável do plano; qualquer mudança de conteúdo produz outro hash."""
    canonico = json.dumps(
        {
            "historia_id": plano.historia_id,
            "tasks": [
                {
                    "titulo": t.titulo,
                    "original_estimate": t.original_estimate,
                    "remaining": t.remaining,
                    "assigned_to": t.assigned_to,
                }
                for t in plano.tasks
            ],
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(canonico.encode("utf-8")).hexdigest()


def ler_manifesto(caminho: Path) -> Manifesto | None:
    """Devolve `None` quando o manifesto ainda não existe — primeira execução para a História."""
    if not caminho.is_file():
        return None
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    return Manifesto(
        historia_id=dados["historia_id"], hash_plano=dados["hash_plano"], criadas=dados["criadas"]
    )


def gravar_manifesto(caminho: Path, manifesto: Manifesto) -> None:
    """Grava atomicamente, para nunca deixar o manifesto num estado parcialmente escrito."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    dados = {
        "historia_id": manifesto.historia_id,
        "hash_plano": manifesto.hash_plano,
        "criadas": manifesto.criadas,
    }
    descritor, nome_temporario = tempfile.mkstemp(dir=caminho.parent)
    try:
        with open(descritor, "w", encoding="utf-8") as arquivo:
            json.dump(dados, arquivo, ensure_ascii=False, indent=2)
        Path(nome_temporario).replace(caminho)
    finally:
        Path(nome_temporario).unlink(missing_ok=True)


def tasks_pendentes(plano: PlanoTasks, manifesto: Manifesto | None) -> tuple[TaskProposta, ...]:
    """Devolve as Tasks do plano que ainda não foram criadas, bloqueando reconciliação pendente."""
    if manifesto is None:
        return plano.tasks
    hash_atual = calcular_hash_plano(plano)
    if manifesto.hash_plano != hash_atual:
        if manifesto.criadas:
            raise ErroReconciliacaoNecessaria(
                "O plano mudou depois de Tasks já criadas sob o hash anterior; "
                "reconcilie manualmente no Azure Boards antes de prosseguir."
            )
        return plano.tasks
    return tuple(t for t in plano.tasks if t.titulo not in manifesto.criadas)


def montar_frase_autorizacao(historia_id: int) -> str:
    """Frase que a pessoa precisa digitar exatamente; nomeia a História/Bug de propósito."""
    return f"AUTORIZAR TASKS #{historia_id}"
```

- [ ] **Step 4: Rodar os testes e confirmar que passam**

Run: `cd decompor-tasks && uv run pytest tests/test_manifesto.py -v`
Expected: PASS (9 testes)

- [ ] **Step 5: Commit**

```bash
cd decompor-tasks
git add src/decompor_tasks/manifesto.py tests/test_manifesto.py
git commit -m "feat(decompor-tasks): plano, manifesto de retomada e frase de autorização

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

### Task 9: Criação das Tasks, CLI, SKILL.md e testes de integração

**Files:**
- Create: `decompor-tasks/src/decompor_tasks/criar_tasks.py`
- Create: `decompor-tasks/src/decompor_tasks/cli.py`
- Modify: `decompor-tasks/src/decompor_tasks/__init__.py`
- Create: `decompor-tasks/SKILL.md`
- Create: `decompor-tasks/README.md`
- Test: `decompor-tasks/tests/test_criar_tasks.py`
- Test: `decompor-tasks/tests/test_cli.py`

**Interfaces:**
- Consumes: `ClienteAzureDevOps.criar_work_item` (Task 6), `PlanoTasks`/`TaskProposta`/`Manifesto`/`tasks_pendentes`/`ler_manifesto`/`gravar_manifesto`/`montar_frase_autorizacao` (Task 8)
- Produces: `montar_operacoes_criacao(*, historia_id, organizacao, projeto, tipo_task, task: TaskProposta) -> list[dict]`
- Produces: `ErroConfirmacaoInvalida`
- Produces: `criar_tasks_pendentes(cliente, *, organizacao, projeto, tipo_task, plano, manifesto_atual, caminho_manifesto, resposta_confirmacao) -> Manifesto`

- [ ] **Step 1: Escrever os testes de `criar_tasks.py`**

```python
# decompor-tasks/tests/test_criar_tasks.py
from pathlib import Path
from typing import Any

import pytest

from decompor_tasks.criar_tasks import (
    ErroConfirmacaoInvalida,
    criar_tasks_pendentes,
    montar_operacoes_criacao,
)
from decompor_tasks.manifesto import Manifesto, PlanoTasks, TaskProposta, ler_manifesto

_TASK_A = TaskProposta(titulo="Task A", original_estimate=4.0, remaining=4.0, assigned_to="dev@x")
_TASK_B = TaskProposta(titulo="Task B", original_estimate=2.0, remaining=2.0, assigned_to="dev@x")


class ClienteFalso:
    def __init__(self, ids_por_ordem: list[int]) -> None:
        self._ids = iter(ids_por_ordem)
        self.chamadas: list[tuple[str, list[dict[str, Any]]]] = []

    def criar_work_item(self, tipo: str, operacoes: list[dict[str, Any]]) -> dict[str, Any]:
        self.chamadas.append((tipo, operacoes))
        return {"id": next(self._ids)}


def test_operacoes_nunca_incluem_story_points() -> None:
    operacoes = montar_operacoes_criacao(
        historia_id=100, organizacao="org", projeto="proj", tipo_task="Task", task=_TASK_A
    )
    caminhos = [op["path"] for op in operacoes]
    assert "/fields/Microsoft.VSTS.Scheduling.StoryPoints" not in caminhos
    assert "/fields/Microsoft.VSTS.Scheduling.OriginalEstimate" in caminhos
    assert "/fields/Microsoft.VSTS.Scheduling.RemainingWork" in caminhos
    assert "/fields/System.AssignedTo" in caminhos


def test_operacoes_incluem_relacao_com_a_historia() -> None:
    operacoes = montar_operacoes_criacao(
        historia_id=100, organizacao="org", projeto="proj", tipo_task="Task", task=_TASK_A
    )
    relacao = next(op for op in operacoes if op["path"] == "/relations/-")
    assert relacao["value"]["rel"] == "System.LinkTypes.Hierarchy-Reverse"
    assert "workItems/100" in relacao["value"]["url"]


@pytest.mark.parametrize(
    "resposta",
    ["autorizar tasks #100", "AUTORIZAR TASKS #999", "sim", ""],
)
def test_recusa_confirmacao_nao_exata_e_nao_cria_nada(tmp_path: Path, resposta: str) -> None:
    plano = PlanoTasks(historia_id=100, tasks=(_TASK_A, _TASK_B))
    cliente = ClienteFalso([1, 2])
    with pytest.raises(ErroConfirmacaoInvalida):
        criar_tasks_pendentes(
            cliente,
            organizacao="org",
            projeto="proj",
            tipo_task="Task",
            plano=plano,
            manifesto_atual=None,
            caminho_manifesto=tmp_path / "manifesto.json",
            resposta_confirmacao=resposta,
        )
    assert cliente.chamadas == []


def test_cria_so_as_tasks_pendentes_e_atualiza_manifesto_apos_cada_uma(tmp_path: Path) -> None:
    plano = PlanoTasks(historia_id=100, tasks=(_TASK_A, _TASK_B))
    manifesto_existente = Manifesto(historia_id=100, hash_plano="", criadas={})
    from decompor_tasks.manifesto import calcular_hash_plano

    manifesto_existente = Manifesto(
        historia_id=100, hash_plano=calcular_hash_plano(plano), criadas={"Task A": 501}
    )
    caminho = tmp_path / "manifesto.json"
    cliente = ClienteFalso([502])
    resultado = criar_tasks_pendentes(
        cliente,
        organizacao="org",
        projeto="proj",
        tipo_task="Task",
        plano=plano,
        manifesto_atual=manifesto_existente,
        caminho_manifesto=caminho,
        resposta_confirmacao="AUTORIZAR TASKS #100",
    )
    assert len(cliente.chamadas) == 1  # só a Task B, que ainda não existia
    assert resultado.criadas == {"Task A": 501, "Task B": 502}
    assert ler_manifesto(caminho) == resultado
```

- [ ] **Step 2: Rodar os testes e confirmar que falham**

Run: `cd decompor-tasks && uv run pytest tests/test_criar_tasks.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'decompor_tasks.criar_tasks'`

- [ ] **Step 3: Implementar `criar_tasks.py`**

```python
# decompor-tasks/src/decompor_tasks/criar_tasks.py
"""Cria as Tasks pendentes de um plano, sob confirmação textual exata, atualizando o
manifesto após cada criação para permitir retomada segura."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

from decompor_tasks.manifesto import (
    Manifesto,
    PlanoTasks,
    TaskProposta,
    calcular_hash_plano,
    gravar_manifesto,
    montar_frase_autorizacao,
    tasks_pendentes,
)

if TYPE_CHECKING:
    pass


class _ClienteEscrita(Protocol):
    def criar_work_item(self, tipo: str, operacoes: list[dict[str, Any]]) -> dict[str, Any]: ...


class ErroConfirmacaoInvalida(ValueError):
    """A resposta do usuário não é exatamente a frase de autorização esperada."""


def montar_operacoes_criacao(
    *, historia_id: int, organizacao: str, projeto: str, tipo_task: str, task: TaskProposta
) -> list[dict[str, Any]]:
    """JSON Patch de criação: título, horas, responsável e o vínculo com a História/Bug pai.
    Nunca inclui Story Points — esse campo não existe em Task no processo Agile."""
    url_pai = f"https://dev.azure.com/{organizacao}/{projeto}/_apis/wit/workItems/{historia_id}"
    return [
        {"op": "add", "path": "/fields/System.Title", "value": task.titulo},
        {
            "op": "add",
            "path": "/fields/Microsoft.VSTS.Scheduling.OriginalEstimate",
            "value": task.original_estimate,
        },
        {
            "op": "add",
            "path": "/fields/Microsoft.VSTS.Scheduling.RemainingWork",
            "value": task.remaining,
        },
        {"op": "add", "path": "/fields/System.AssignedTo", "value": task.assigned_to},
        {
            "op": "add",
            "path": "/relations/-",
            "value": {"rel": "System.LinkTypes.Hierarchy-Reverse", "url": url_pai},
        },
    ]


def criar_tasks_pendentes(
    cliente: _ClienteEscrita,
    *,
    organizacao: str,
    projeto: str,
    tipo_task: str,
    plano: PlanoTasks,
    manifesto_atual: Manifesto | None,
    caminho_manifesto: Path,
    resposta_confirmacao: str,
) -> Manifesto:
    """Cria as Tasks ainda ausentes do manifesto, uma por vez, persistindo o progresso."""
    frase_esperada = montar_frase_autorizacao(plano.historia_id)
    if resposta_confirmacao.strip() != frase_esperada:
        raise ErroConfirmacaoInvalida(
            "Confirmação ausente, incorreta ou vinculada a outra História/Bug; "
            "nenhuma Task foi criada."
        )
    pendentes = tasks_pendentes(plano, manifesto_atual)  # pode levantar ErroReconciliacaoNecessaria
    criadas = dict(manifesto_atual.criadas) if manifesto_atual else {}
    hash_atual = calcular_hash_plano(plano)
    manifesto = Manifesto(historia_id=plano.historia_id, hash_plano=hash_atual, criadas=criadas)
    for task in pendentes:
        operacoes = montar_operacoes_criacao(
            historia_id=plano.historia_id,
            organizacao=organizacao,
            projeto=projeto,
            tipo_task=tipo_task,
            task=task,
        )
        resultado = cliente.criar_work_item(tipo_task, operacoes)
        criadas[task.titulo] = resultado["id"]
        manifesto = Manifesto(historia_id=plano.historia_id, hash_plano=hash_atual, criadas=criadas)
        gravar_manifesto(caminho_manifesto, manifesto)
    return manifesto
```

- [ ] **Step 4: Rodar os testes de `criar_tasks.py` e confirmar que passam**

Run: `cd decompor-tasks && uv run pytest tests/test_criar_tasks.py -v`
Expected: PASS (6 testes, incluindo os 4 parametrizados de confirmação)

- [ ] **Step 5: Escrever o teste da CLI**

```python
# decompor-tasks/tests/test_cli.py
from pathlib import Path

from decompor_tasks.cli import executar

_ENV = {
    "AZURE_DEVOPS_ORGANIZACAO": "minha-org",
    "AZURE_DEVOPS_PROJETO": "meu-projeto",
    "AZURE_DEVOPS_TOKEN": "token",
}


def test_decompor_sem_confirmacao_exata_nao_chama_rede(tmp_path: Path, capsys: object) -> None:
    plano_json = tmp_path / "plano.json"
    plano_json.write_text(
        '{"historia_id": 100, "tasks": ['
        '{"titulo": "Task A", "original_estimate": 4.0, "remaining": 4.0, '
        '"assigned_to": "dev@x"}]}',
        encoding="utf-8",
    )
    codigo = executar(
        ["criar", str(plano_json), "--manifesto", str(tmp_path / "manifesto.json")],
        env=_ENV,
        entrada=lambda _prompt: "resposta errada",
    )
    saida = capsys.readouterr().out  # type: ignore[attr-defined]
    assert codigo != 0
    assert "100" in saida


def test_sugerir_horas_sem_configuracao_devolve_erro(capsys: object) -> None:
    codigo = executar(
        ["sugerir-horas", "--area-path", "proj\\Time A", "--titulo", "Criar endpoint"],
        env={},
    )
    saida = capsys.readouterr().out  # type: ignore[attr-defined]
    assert codigo == 2
    assert "Configuração inválida" in saida
```

- [ ] **Step 6: Rodar o teste da CLI e confirmar que falha**

Run: `cd decompor-tasks && uv run pytest tests/test_cli.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'decompor_tasks.cli'`

- [ ] **Step 7: Implementar `cli.py` e atualizar `__init__.py`**

```python
# decompor-tasks/src/decompor_tasks/cli.py
"""CLI de apoio à skill: a decomposição em si (quais Tasks, a partir de qual abordagem
técnica) é trabalho do agente, guiado pelo SKILL.md; este arquivo cobre rede, ancoragem
de estimativa e a criação sob confirmação."""

from __future__ import annotations

import argparse
import dataclasses
import json
from collections.abc import Callable, Mapping
from pathlib import Path

from decompor_tasks.ancoragem_horas import sugerir_horas
from decompor_tasks.cliente_azure_devops import ClienteAzureDevOps
from decompor_tasks.configuracao import ErroConfiguracao, carregar_configuracao
from decompor_tasks.criar_tasks import ErroConfirmacaoInvalida, criar_tasks_pendentes
from decompor_tasks.manifesto import (
    PlanoTasks,
    TaskProposta,
    ler_manifesto,
    montar_frase_autorizacao,
)


def executar(
    argv: list[str], *, env: Mapping[str, str], entrada: Callable[[str], str] = input
) -> int:
    parser = _construir_parser()
    args = parser.parse_args(argv)
    try:
        if args.comando == "sugerir-horas":
            return _sugerir_horas(args, env)
        if args.comando == "criar":
            return _criar(args, env, entrada)
    except ErroConfiguracao as erro:
        print(f"Configuração inválida: {erro}")
        return 2
    parser.error("comando desconhecido")
    return 2


def _construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="decompor-tasks")
    subs = parser.add_subparsers(dest="comando", required=True)

    sugerir = subs.add_parser("sugerir-horas")
    sugerir.add_argument("--area-path", required=True)
    sugerir.add_argument("--tipo-task", default="Task")
    sugerir.add_argument("--titulo", required=True, dest="titulo_aproximado")

    criar = subs.add_parser("criar")
    criar.add_argument("plano", help="Caminho de um JSON com historia_id e a lista de tasks")
    criar.add_argument("--manifesto", required=True)

    return parser


def _sugerir_horas(args: argparse.Namespace, env: Mapping[str, str]) -> int:
    config = carregar_configuracao(env)
    with ClienteAzureDevOps(
        config.organizacao, config.projeto, config.token.get_secret_value()
    ) as cliente:
        sugestao = sugerir_horas(
            cliente,
            projeto=config.projeto,
            area_path=args.area_path,
            tipo_task=args.tipo_task,
            titulo_aproximado=args.titulo_aproximado,
        )
    print(json.dumps(dataclasses.asdict(sugestao), ensure_ascii=False, indent=2))
    return 0


def _carregar_plano(caminho: str) -> PlanoTasks:
    dados = json.loads(Path(caminho).read_text(encoding="utf-8"))
    tasks = tuple(TaskProposta(**t) for t in dados["tasks"])
    return PlanoTasks(historia_id=dados["historia_id"], tasks=tasks)


def _criar(args: argparse.Namespace, env: Mapping[str, str], entrada: Callable[[str], str]) -> int:
    config = carregar_configuracao(env)
    plano = _carregar_plano(args.plano)
    caminho_manifesto = Path(args.manifesto)
    manifesto_atual = ler_manifesto(caminho_manifesto)
    frase = montar_frase_autorizacao(plano.historia_id)
    print(f"{len(plano.tasks)} Task(s) no plano. Digite exatamente a frase para confirmar:")
    print(frase)
    resposta = entrada("> ")
    try:
        with ClienteAzureDevOps(
            config.organizacao, config.projeto, config.token.get_secret_value()
        ) as cliente:
            criar_tasks_pendentes(
                cliente,
                organizacao=config.organizacao,
                projeto=config.projeto,
                tipo_task=config.tipo_task,
                plano=plano,
                manifesto_atual=manifesto_atual,
                caminho_manifesto=caminho_manifesto,
                resposta_confirmacao=resposta,
            )
    except ErroConfirmacaoInvalida as erro:
        print(str(erro))
        return 1
    print("Tasks pendentes criadas.")
    return 0
```

```python
# decompor-tasks/src/decompor_tasks/__init__.py
"""Skill de planejamento: decompõe uma História/Bug em Tasks estimadas em horas."""

from __future__ import annotations

import os
import sys


def main() -> None:
    from decompor_tasks.cli import executar

    raise SystemExit(executar(sys.argv[1:], env=os.environ))
```

- [ ] **Step 8: Rodar todos os testes do pacote e confirmar que passam**

Run: `cd decompor-tasks && uv run pytest tests/ -v`
Expected: PASS (todos os testes do pacote, inclusive o novo de CLI)

- [ ] **Step 9: Escrever o SKILL.md**

```markdown
---
name: decompor-tasks
description: Use no planning, por item, pelo desenvolvedor que vai executá-lo, para decompor uma História/Bug já publicada em Tasks estimadas em horas e atribuídas a ele.
---

# Decompor uma História/Bug em Tasks

## Objetivo

Decompor uma História/Bug já publicada no Azure Boards em Tasks, a partir da abordagem técnica já
registrada em `Custom.DemandaSpecTecnica`, estimar cada Task em horas ancoradas em Tasks fechadas
comparáveis, atribuí-las a quem vai executar e criá-las sob autorização textual explícita.

## Fluxo obrigatório

1. Receba o ID da História/Bug — nunca de uma Task, que ainda não existe neste momento.
2. Leia a História/Bug e suba até a Demanda para ler `Custom.DemandaSpecTecnica`. Use o Story Points
   da História só como contexto de porte; nunca o copie para nenhuma Task.
3. Proponha a decomposição em Tasks a partir da abordagem técnica já registrada — não reabra desenho
   técnico.
4. Para cada Task proposta, rode `decompor-tasks sugerir-horas --area-path <Area Path da História>
   --tipo-task Task --titulo "<título da Task proposta>"`. Quando a sugestão vier sem base
   (`horas: null`), pergunte a estimativa ao desenvolvedor — a resposta se torna histórico para a
   próxima Task comparável.
5. Monte o plano (`historia_id` e a lista de Tasks com título, `original_estimate`, `remaining` e
   `assigned_to` = usuário do PAT) e grave num arquivo JSON temporário.
6. Rode `decompor-tasks criar <plano.json> --manifesto <caminho>`. A CLI mostra o plano completo e
   pede a frase de autorização; só cria (`POST`) as Tasks que a resposta exata autorizar. Uma
   reexecução após falha parcial retoma do manifesto sem duplicar.

## O que esta skill nunca faz

- Não cria Épico, Feature, História ou Bug.
- Não grava nem lê `Custom.DemandaSpecTecnica` — só o `refinar-tecnicamente` escreve; esta skill lê.
- Não copia Story Points para Task — esse campo não existe em Task no processo Agile.
- Não inventa horas sem ancoragem em histórico ou confirmação humana explícita.
```

- [ ] **Step 10: Escrever o README.md**

```markdown
# decompor-tasks

Skill de planejamento: decompõe uma História/Bug já publicada no Azure Boards em Tasks estimadas
em horas, atribuídas a quem vai executar, ancoradas em Tasks fechadas comparáveis.

## Instalação

```bash
npx skills add pedroct/refinamento-planejamento-tecnico --skill decompor-tasks -a claude-code
```

## Configuração

Copie `.env.example` para `.env` e preencha organização, projeto e token do Azure DevOps. O token
nunca deve ser versionado.
```

- [ ] **Step 11: Commit**

```bash
cd decompor-tasks
git add src/decompor_tasks/criar_tasks.py src/decompor_tasks/cli.py src/decompor_tasks/__init__.py \
  SKILL.md README.md tests/test_criar_tasks.py tests/test_cli.py
git commit -m "feat(decompor-tasks): criação de Tasks, CLI, SKILL.md e testes de integração

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

## Skill 3 — `preparar-implementacao`

### Task 10: Scaffold do pacote, configuração, cliente de leitura e subida de hierarquia

**Files:**
- Create: `preparar-implementacao/pyproject.toml`
- Create: `preparar-implementacao/.env.example`
- Create: `preparar-implementacao/.gitignore`
- Create: `preparar-implementacao/src/preparar_implementacao/__init__.py`
- Create: `preparar-implementacao/src/preparar_implementacao/configuracao.py`
- Create: `preparar-implementacao/src/preparar_implementacao/cliente_azure_devops.py`
- Create: `preparar-implementacao/src/preparar_implementacao/hierarquia.py`
- Test: `preparar-implementacao/tests/test_configuracao.py`
- Test: `preparar-implementacao/tests/test_cliente_azure_devops.py`
- Test: `preparar-implementacao/tests/test_hierarquia.py`

**Interfaces:**
- Produces: `carregar_configuracao(env) -> ConfiguracaoPreparacao` (campos: `organizacao: str`, `projeto: str`, `token: SecretStr`, `tipo_demanda: str = "Demanda de Negócio"`, `campo_spec_tecnica: str = "Custom.DemandaSpecTecnica"`, `campo_spec_negocios: str = "Custom.DemandaSpecNegocios"`)
- Produces: `class ClienteAzureDevOps` — só leitura: `ler_work_item(id) -> dict`, `consultar_wiql(wiql) -> list[int]`
- Produces: `ErroDestinoInvalido`, `ErroFalhaTransitoria`, `ErroRespostaInvalida`
- Produces: `subir_ate_demanda(cliente, work_item_id: int, tipo_demanda: str) -> list[dict[str, Any]]`

Cliente sem `gravar_campo` nem `criar_work_item` de propósito — esta skill nunca escreve no Azure
Boards.

- [ ] **Step 1: Escrever pyproject.toml, .env.example e .gitignore**

```toml
[build-system]
requires = ["hatchling==1.29.0"]
build-backend = "hatchling.build"

[project]
name = "preparar-implementacao"
version = "0.1.0"
description = "Briefing de implementação a partir de um work item já publicado e refinado"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
  "httpx==0.28.1",
  "pydantic==2.13.5",
  "pydantic-settings==2.15.0",
]

[project.scripts]
preparar-implementacao = "preparar_implementacao:main"

[dependency-groups]
dev = [
  "mypy==2.1.0",
  "pytest==9.0.3",
  "ruff==0.15.14",
]

[tool.hatch.build.targets.wheel]
packages = ["src/preparar_implementacao"]

[tool.ruff]
line-length = 100
target-version = "py312"
exclude = [".venv/", ".git/"]

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "S"]

[tool.ruff.lint.per-file-ignores]
"**/tests/**/*.py" = ["S101"]

[tool.mypy]
python_version = "3.12"
strict = true
warn_unused_ignores = true

[tool.pytest.ini_options]
testpaths = ["tests"]
```

```text
# preparar-implementacao/.env.example
AZURE_DEVOPS_ORGANIZACAO=
AZURE_DEVOPS_PROJETO=
AZURE_DEVOPS_TOKEN=
AZURE_DEVOPS_TIPO_DEMANDA=Demanda de Negócio
AZURE_DEVOPS_CAMPO_SPEC_TECNICA=Custom.DemandaSpecTecnica
AZURE_DEVOPS_CAMPO_SPEC_NEGOCIOS=Custom.DemandaSpecNegocios
```

```text
# preparar-implementacao/.gitignore
.venv/
__pycache__/
*.pyc
.env
.mypy_cache/
.pytest_cache/
.ruff_cache/
uv.lock
```

```python
# preparar-implementacao/src/preparar_implementacao/__init__.py
"""Skill de implementação: monta o briefing consolidado a partir de um work item refinado."""

from __future__ import annotations
```

- [ ] **Step 2: Escrever o teste de configuração**

```python
# preparar-implementacao/tests/test_configuracao.py
import pytest

from preparar_implementacao.configuracao import ErroConfiguracao, carregar_configuracao


def test_carrega_configuracao_com_padroes() -> None:
    env = {
        "AZURE_DEVOPS_ORGANIZACAO": "minha-org",
        "AZURE_DEVOPS_PROJETO": "meu-projeto",
        "AZURE_DEVOPS_TOKEN": "token",
    }
    config = carregar_configuracao(env)
    assert config.tipo_demanda == "Demanda de Negócio"
    assert config.campo_spec_tecnica == "Custom.DemandaSpecTecnica"
    assert config.campo_spec_negocios == "Custom.DemandaSpecNegocios"


def test_recusa_configuracao_sem_token() -> None:
    env = {"AZURE_DEVOPS_ORGANIZACAO": "minha-org", "AZURE_DEVOPS_PROJETO": "meu-projeto"}
    with pytest.raises(ErroConfiguracao):
        carregar_configuracao(env)
```

- [ ] **Step 3: Rodar os testes e confirmar que falham**

Run: `cd preparar-implementacao && uv run pytest tests/test_configuracao.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'preparar_implementacao.configuracao'`

- [ ] **Step 4: Implementar `configuracao.py`**

```python
# preparar-implementacao/src/preparar_implementacao/configuracao.py
"""Carrega a configuração local sem expor o token em representações textuais."""

from __future__ import annotations

from collections.abc import Mapping

from pydantic import BaseModel, ConfigDict, SecretStr, ValidationError, field_validator


class ErroConfiguracao(ValueError):
    """Indica que não foi possível obter uma configuração completa e segura."""


class ConfiguracaoPreparacao(BaseModel):
    """Agrupa organização, projeto, credencial e os nomes remotos que a skill lê."""

    model_config = ConfigDict(frozen=True)

    organizacao: str
    projeto: str
    token: SecretStr
    tipo_demanda: str = "Demanda de Negócio"
    campo_spec_tecnica: str = "Custom.DemandaSpecTecnica"
    campo_spec_negocios: str = "Custom.DemandaSpecNegocios"

    @field_validator(
        "organizacao", "projeto", "tipo_demanda", "campo_spec_tecnica", "campo_spec_negocios"
    )
    @classmethod
    def _validar_texto_obrigatorio(cls, valor: str) -> str:
        texto = valor.strip()
        if not texto:
            raise ValueError("deve ser informado")
        return texto

    @field_validator("token")
    @classmethod
    def _validar_token(cls, valor: SecretStr) -> SecretStr:
        if not valor.get_secret_value().strip():
            raise ValueError("deve ser informado")
        return valor


def carregar_configuracao(env: Mapping[str, str]) -> ConfiguracaoPreparacao:
    """Lê a configuração a partir de um mapa de variáveis de ambiente já resolvido."""
    try:
        return ConfiguracaoPreparacao(
            organizacao=env.get("AZURE_DEVOPS_ORGANIZACAO", ""),
            projeto=env.get("AZURE_DEVOPS_PROJETO", ""),
            token=env.get("AZURE_DEVOPS_TOKEN", ""),
            tipo_demanda=env.get("AZURE_DEVOPS_TIPO_DEMANDA", "Demanda de Negócio"),
            campo_spec_tecnica=env.get(
                "AZURE_DEVOPS_CAMPO_SPEC_TECNICA", "Custom.DemandaSpecTecnica"
            ),
            campo_spec_negocios=env.get(
                "AZURE_DEVOPS_CAMPO_SPEC_NEGOCIOS", "Custom.DemandaSpecNegocios"
            ),
        )
    except ValidationError as erro:
        raise ErroConfiguracao(f"Configuração incompleta ou inválida: {erro}") from erro
```

- [ ] **Step 5: Rodar os testes de configuração e confirmar que passam**

Run: `cd preparar-implementacao && uv run pytest tests/test_configuracao.py -v`
Expected: PASS (2 testes)

- [ ] **Step 6: Escrever o teste do cliente Azure DevOps**

```python
# preparar-implementacao/tests/test_cliente_azure_devops.py
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
```

- [ ] **Step 7: Rodar os testes do cliente e confirmar que falham**

Run: `cd preparar-implementacao && uv run pytest tests/test_cliente_azure_devops.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'preparar_implementacao.cliente_azure_devops'`

- [ ] **Step 8: Implementar `cliente_azure_devops.py`**

```python
# preparar-implementacao/src/preparar_implementacao/cliente_azure_devops.py
"""Cliente HTTP de **só leitura** para o Azure Boards via REST — sem `gravar_campo` nem
`criar_work_item` de propósito, porque esta skill nunca escreve no Azure Boards.

Cópia vendorizada do mesmo padrão usado em `refinar-tecnicamente` e `decompor-tasks`.
Ressincronize manualmente se o padrão de retentativa mudar em algum dos irmãos.
"""

from __future__ import annotations

import base64
import time
from typing import Any

import httpx

_VERSAO_API = "7.2-preview.3"
_VERSAO_WIQL = "7.2-preview.2"
_ERROS_RETENTAVEIS = frozenset({408, 429, 500, 502, 503, 504})
_MAX_TENTATIVAS = 3


class ErroDestinoInvalido(ValueError):
    """O work item ou consulta solicitados não existem ou são inválidos."""


class ErroFalhaTransitoria(RuntimeError):
    """A chamada falhou por rede ou por erro remoto retentável, mesmo após tentativas."""


class ErroRespostaInvalida(RuntimeError):
    """A resposta remota não é JSON consumível ou não tem o formato esperado."""


class ClienteAzureDevOps:
    """Encapsula autenticação básica por PAT e o padrão de retentativa com backoff."""

    def __init__(
        self,
        organizacao: str,
        projeto: str,
        token: str,
        *,
        transport: httpx.BaseTransport | None = None,
        timeout: float = 10.0,
        espera_inicial: float = 0.2,
    ) -> None:
        self._organizacao = organizacao
        self._projeto = projeto
        self._espera_inicial = espera_inicial
        credencial = base64.b64encode(f":{token}".encode()).decode()
        self._cliente = httpx.Client(
            headers={"Authorization": f"Basic {credencial}"},
            timeout=httpx.Timeout(timeout),
            transport=transport,
        )

    def __enter__(self) -> ClienteAzureDevOps:
        return self

    def __exit__(self, *_exc: object) -> None:
        self._cliente.close()

    def ler_work_item(self, work_item_id: int) -> dict[str, Any]:
        url = (
            f"https://dev.azure.com/{self._organizacao}/{self._projeto}"
            f"/_apis/wit/workitems/{work_item_id}?$expand=All&api-version={_VERSAO_API}"
        )
        resposta = self._executar("GET", url)
        return self._verificar_e_decodificar(resposta, work_item_id)

    def consultar_wiql(self, wiql: str) -> list[int]:
        url = (
            f"https://dev.azure.com/{self._organizacao}/{self._projeto}"
            f"/_apis/wit/wiql?api-version={_VERSAO_WIQL}"
        )
        resposta = self._executar("POST", url, corpo={"query": wiql})
        payload = self._verificar_e_decodificar(resposta, None)
        itens = payload.get("workItems")
        if not isinstance(itens, list):
            raise ErroRespostaInvalida("A consulta WIQL não devolveu uma lista de work items.")
        ids: list[int] = []
        for item in itens:
            if not isinstance(item, dict) or not isinstance(item.get("id"), int):
                raise ErroRespostaInvalida("Um item da consulta WIQL não trouxe um ID inteiro.")
            ids.append(item["id"])
        return ids

    def _executar(self, metodo: str, url: str, *, corpo: Any = None) -> httpx.Response:
        for tentativa in range(_MAX_TENTATIVAS):
            try:
                resposta = self._cliente.request(metodo, url, json=corpo)
            except httpx.RequestError as erro:
                if tentativa == _MAX_TENTATIVAS - 1:
                    raise ErroFalhaTransitoria(
                        f"A chamada {metodo} {url} falhou por erro de rede."
                    ) from erro
            else:
                if resposta.status_code not in _ERROS_RETENTAVEIS:
                    return resposta
                if tentativa == _MAX_TENTATIVAS - 1:
                    raise ErroFalhaTransitoria(
                        f"A chamada {metodo} {url} não se completou "
                        f"(HTTP {resposta.status_code}) após {_MAX_TENTATIVAS} tentativas."
                    )
            time.sleep(self._espera_inicial * (2**tentativa))
        raise ErroFalhaTransitoria(f"A chamada {metodo} {url} não se completou.")

    def _verificar_e_decodificar(
        self, resposta: httpx.Response, work_item_id: int | None
    ) -> dict[str, Any]:
        if resposta.status_code == 404:
            alvo = f"work item {work_item_id}" if work_item_id else "o recurso solicitado"
            raise ErroDestinoInvalido(f"Não foi possível encontrar {alvo}.")
        if resposta.status_code >= 400:
            raise ErroDestinoInvalido(
                f"A chamada devolveu HTTP {resposta.status_code}: {resposta.text[:300]}"
            )
        try:
            corpo_json = resposta.json()
        except ValueError as erro:
            raise ErroRespostaInvalida("A resposta não é JSON consumível.") from erro
        if not isinstance(corpo_json, dict):
            raise ErroRespostaInvalida("A resposta não é um objeto JSON.")
        return corpo_json
```

- [ ] **Step 9: Rodar os testes do cliente e confirmar que passam**

Run: `cd preparar-implementacao && uv run pytest tests/test_cliente_azure_devops.py -v`
Expected: PASS (5 testes)

- [ ] **Step 10: Escrever o teste de subida de hierarquia**

```python
# preparar-implementacao/tests/test_hierarquia.py
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
```

- [ ] **Step 11: Rodar os testes de hierarquia e confirmar que falham**

Run: `cd preparar-implementacao && uv run pytest tests/test_hierarquia.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'preparar_implementacao.hierarquia'`

- [ ] **Step 12: Implementar `hierarquia.py`**

```python
# preparar-implementacao/src/preparar_implementacao/hierarquia.py
"""Sobe a cadeia de work items pais até encontrar a Demanda de Negócio."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    pass

_REL_PAI = "System.LinkTypes.Hierarchy-Reverse"
_LIMITE_SALTOS = 8


class _ClienteLeitura(Protocol):
    def ler_work_item(self, work_item_id: int) -> dict[str, Any]: ...


class ErroHierarquiaIncompleta(RuntimeError):
    """A cadeia de pais terminou antes de alcançar um item do tipo da Demanda."""


def _id_do_pai(item: dict[str, Any]) -> int | None:
    for relacao in item.get("relations", []):
        if relacao.get("rel") == _REL_PAI:
            url = relacao.get("url", "")
            return int(url.rsplit("/", 1)[-1])
    return None


def subir_ate_demanda(
    cliente: _ClienteLeitura, work_item_id: int, tipo_demanda: str
) -> list[dict[str, Any]]:
    """Devolve a cadeia do item de folha até a Demanda, inclusive, na ordem folha → raiz."""
    cadeia: list[dict[str, Any]] = []
    atual = cliente.ler_work_item(work_item_id)
    for _ in range(_LIMITE_SALTOS):
        cadeia.append(atual)
        if atual["fields"].get("System.WorkItemType") == tipo_demanda:
            return cadeia
        id_pai = _id_do_pai(atual)
        if id_pai is None:
            break
        atual = cliente.ler_work_item(id_pai)
    raise ErroHierarquiaIncompleta(
        f"A cadeia de pais do work item {work_item_id} não alcançou um item do tipo "
        f"{tipo_demanda!r} em até {_LIMITE_SALTOS} saltos."
    )
```

- [ ] **Step 13: Rodar todos os testes do Task 10 e confirmar que passam**

Run: `cd preparar-implementacao && uv run pytest tests/ -v`
Expected: PASS (10 testes)

- [ ] **Step 14: Commit**

```bash
cd preparar-implementacao
git add pyproject.toml .env.example .gitignore src/ tests/
git commit -m "feat(preparar-implementacao): scaffold, configuração, cliente de leitura e hierarquia

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

### Task 11: Contexto (specs, Tasks irmãs) e verificador de suficiência

**Files:**
- Create: `preparar-implementacao/src/preparar_implementacao/contexto.py`
- Create: `preparar-implementacao/src/preparar_implementacao/suficiencia.py`
- Test: `preparar-implementacao/tests/test_contexto.py`
- Test: `preparar-implementacao/tests/test_suficiencia.py`

**Interfaces:**
- Consumes: `subir_ate_demanda` (Task 10), `ClienteAzureDevOps.ler_work_item` (Task 10)
- Produces: `extrair_campo_demanda(cadeia: list[dict[str, Any]], tipo_demanda: str, campo: str) -> str | None`
- Produces: `ids_tasks_filhas(historia: dict[str, Any]) -> list[int]`
- Produces: `ler_tasks(cliente, ids: list[int]) -> list[dict[str, Any]]`
- Produces: `ErroSuficienciaInsuficiente`
- Produces: `verificar_suficiencia(*, spec_tecnica: str | None, criterios_aceitacao: str | None, tasks: list[dict[str, Any]]) -> None`

- [ ] **Step 1: Escrever os testes de `contexto.py`**

```python
# preparar-implementacao/tests/test_contexto.py
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
```

- [ ] **Step 2: Rodar os testes de `contexto.py` e confirmar que falham**

Run: `cd preparar-implementacao && uv run pytest tests/test_contexto.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'preparar_implementacao.contexto'`

- [ ] **Step 3: Implementar `contexto.py`**

```python
# preparar-implementacao/src/preparar_implementacao/contexto.py
"""Extrai o contexto de implementação já registrado: campos da Demanda e Tasks irmãs."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    pass

_REL_FILHO = "System.LinkTypes.Hierarchy-Forward"


class _ClienteLeitura(Protocol):
    def ler_work_item(self, work_item_id: int) -> dict[str, Any]: ...


def extrair_campo_demanda(
    cadeia: list[dict[str, Any]], tipo_demanda: str, campo: str
) -> str | None:
    """Procura, na cadeia devolvida por `subir_ate_demanda`, o item da Demanda e lê `campo`."""
    for item in cadeia:
        if item["fields"].get("System.WorkItemType") == tipo_demanda:
            valor = item["fields"].get(campo)
            return valor if isinstance(valor, str) and valor.strip() else None
    return None


def ids_tasks_filhas(historia: dict[str, Any]) -> list[int]:
    """Lê os IDs de Task filhas a partir das relações de hierarquia para frente."""
    ids: list[int] = []
    for relacao in historia.get("relations", []):
        if relacao.get("rel") == _REL_FILHO:
            ids.append(int(relacao["url"].rsplit("/", 1)[-1]))
    return ids


def ler_tasks(cliente: _ClienteLeitura, ids: list[int]) -> list[dict[str, Any]]:
    """Busca cada Task por ID, na ordem recebida."""
    return [cliente.ler_work_item(id_) for id_ in ids]
```

- [ ] **Step 4: Rodar os testes de `contexto.py` e confirmar que passam**

Run: `cd preparar-implementacao && uv run pytest tests/test_contexto.py -v`
Expected: PASS (6 testes)

- [ ] **Step 5: Escrever os testes de `suficiencia.py`**

```python
# preparar-implementacao/tests/test_suficiencia.py
from typing import Any

import pytest

from preparar_implementacao.suficiencia import ErroSuficienciaInsuficiente, verificar_suficiencia


def _task_estimada(titulo: str) -> dict[str, Any]:
    return {
        "fields": {
            "System.Title": titulo,
            "Microsoft.VSTS.Scheduling.OriginalEstimate": 4.0,
            "Microsoft.VSTS.Scheduling.RemainingWork": 4.0,
        }
    }


def _task_sem_estimativa(titulo: str) -> dict[str, Any]:
    return {"fields": {"System.Title": titulo}}


def test_tudo_presente_nao_levanta_erro() -> None:
    verificar_suficiencia(
        spec_tecnica="<p>abordagem</p>",
        criterios_aceitacao="<p>critérios</p>",
        tasks=[_task_estimada("Task A")],
    )


def test_sem_spec_tecnica_nomeia_a_lacuna() -> None:
    with pytest.raises(ErroSuficienciaInsuficiente, match="spec técnica"):
        verificar_suficiencia(
            spec_tecnica=None, criterios_aceitacao="<p>x</p>", tasks=[_task_estimada("Task A")]
        )


def test_sem_criterios_de_aceitacao_nomeia_a_lacuna() -> None:
    with pytest.raises(ErroSuficienciaInsuficiente, match="critério de aceitação"):
        verificar_suficiencia(
            spec_tecnica="<p>x</p>", criterios_aceitacao=None, tasks=[_task_estimada("Task A")]
        )


def test_sem_nenhuma_task_nomeia_a_lacuna() -> None:
    with pytest.raises(ErroSuficienciaInsuficiente, match="Task"):
        verificar_suficiencia(spec_tecnica="<p>x</p>", criterios_aceitacao="<p>x</p>", tasks=[])


def test_task_sem_estimativa_nomeia_o_titulo_dela() -> None:
    with pytest.raises(ErroSuficienciaInsuficiente, match="Task B"):
        verificar_suficiencia(
            spec_tecnica="<p>x</p>",
            criterios_aceitacao="<p>x</p>",
            tasks=[_task_estimada("Task A"), _task_sem_estimativa("Task B")],
        )


def test_multiplas_lacunas_aparecem_todas_na_mesma_mensagem() -> None:
    with pytest.raises(ErroSuficienciaInsuficiente) as excecao:
        verificar_suficiencia(spec_tecnica=None, criterios_aceitacao=None, tasks=[])
    mensagem = str(excecao.value)
    assert "spec técnica" in mensagem
    assert "critério de aceitação" in mensagem
    assert "Task" in mensagem
```

- [ ] **Step 6: Rodar os testes de `suficiencia.py` e confirmar que falham**

Run: `cd preparar-implementacao && uv run pytest tests/test_suficiencia.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'preparar_implementacao.suficiencia'`

- [ ] **Step 7: Implementar `suficiencia.py`**

```python
# preparar-implementacao/src/preparar_implementacao/suficiencia.py
"""Verifica se há o mínimo para montar o briefing; nunca inventa o que falta."""

from __future__ import annotations

from typing import Any


class ErroSuficienciaInsuficiente(RuntimeError):
    """A hierarquia não tem o mínimo necessário; a mensagem nomeia cada lacuna encontrada."""


def verificar_suficiencia(
    *,
    spec_tecnica: str | None,
    criterios_aceitacao: str | None,
    tasks: list[dict[str, Any]],
) -> None:
    """Levanta uma única exceção nomeando todas as lacunas bloqueantes encontradas."""
    lacunas: list[str] = []
    if not spec_tecnica:
        lacunas.append("a Demanda não tem spec técnica registrada em Custom.DemandaSpecTecnica")
    if not criterios_aceitacao:
        lacunas.append("a História/Bug não tem critério de aceitação preenchido")
    if not tasks:
        lacunas.append("não há nenhuma Task filha")
    else:
        for task in tasks:
            campos = task["fields"]
            tem_estimativa = (
                campos.get("Microsoft.VSTS.Scheduling.OriginalEstimate") is not None
                and campos.get("Microsoft.VSTS.Scheduling.RemainingWork") is not None
            )
            if not tem_estimativa:
                titulo = campos.get("System.Title", f"Task {task.get('id')}")
                lacunas.append(f"a Task {titulo!r} não tem Original Estimate/Remaining")
    if lacunas:
        raise ErroSuficienciaInsuficiente(
            "Faltam itens para montar o briefing: " + "; ".join(lacunas) + "."
        )
```

- [ ] **Step 8: Rodar os testes de `suficiencia.py` e confirmar que passam**

Run: `cd preparar-implementacao && uv run pytest tests/test_suficiencia.py -v`
Expected: PASS (6 testes)

- [ ] **Step 9: Commit**

```bash
cd preparar-implementacao
git add src/preparar_implementacao/contexto.py src/preparar_implementacao/suficiencia.py \
  tests/test_contexto.py tests/test_suficiencia.py
git commit -m "feat(preparar-implementacao): contexto da Demanda, Tasks irmãs e verificador de suficiência

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

### Task 12: Montagem do briefing, CLI, SKILL.md e testes de integração

**Files:**
- Create: `preparar-implementacao/src/preparar_implementacao/briefing.py`
- Create: `preparar-implementacao/src/preparar_implementacao/cli.py`
- Modify: `preparar-implementacao/src/preparar_implementacao/__init__.py`
- Create: `preparar-implementacao/SKILL.md`
- Create: `preparar-implementacao/README.md`
- Test: `preparar-implementacao/tests/test_briefing.py`
- Test: `preparar-implementacao/tests/test_cli.py`

**Interfaces:**
- Consumes: `subir_ate_demanda` (Task 10), `extrair_campo_demanda`/`ids_tasks_filhas`/`ler_tasks` (Task 11), `verificar_suficiencia`/`ErroSuficienciaInsuficiente` (Task 11)
- Produces: `montar_briefing(*, work_item: dict[str, Any], spec_tecnica: str, spec_negocios: str | None, tasks: list[dict[str, Any]]) -> str`

- [ ] **Step 1: Escrever os testes de `briefing.py`**

```python
# preparar-implementacao/tests/test_briefing.py
from typing import Any

from preparar_implementacao.briefing import montar_briefing


def _work_item(tipo: str) -> dict[str, Any]:
    return {
        "id": 1,
        "fields": {
            "System.Title": "Renovar diligência automaticamente",
            "System.WorkItemType": tipo,
            "System.Description": "<p>Como usuário, quero...</p>",
            "Microsoft.VSTS.Common.AcceptanceCriteria": "<p>Dado que...</p>",
        },
    }


def _task(titulo: str, estimativa: float) -> dict[str, Any]:
    return {
        "id": 10,
        "fields": {
            "System.Title": titulo,
            "Microsoft.VSTS.Scheduling.OriginalEstimate": estimativa,
            "Microsoft.VSTS.Scheduling.RemainingWork": estimativa,
        },
    }


def test_briefing_inclui_titulo_e_criterios() -> None:
    briefing = montar_briefing(
        work_item=_work_item("User Story"),
        spec_tecnica="<p>abordagem técnica</p>",
        spec_negocios="<p>contexto de negócio</p>",
        tasks=[_task("Task A", 4.0)],
    )
    assert "Renovar diligência automaticamente" in briefing
    assert "abordagem técnica" in briefing
    assert "contexto de negócio" in briefing
    assert "Dado que" in briefing
    assert "Task A" in briefing
    assert "4.0" in briefing


def test_briefing_sem_spec_negocios_nao_quebra() -> None:
    briefing = montar_briefing(
        work_item=_work_item("Bug"),
        spec_tecnica="<p>abordagem</p>",
        spec_negocios=None,
        tasks=[],
    )
    assert "Renovar diligência automaticamente" in briefing
```

- [ ] **Step 2: Rodar os testes de `briefing.py` e confirmar que falham**

Run: `cd preparar-implementacao && uv run pytest tests/test_briefing.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'preparar_implementacao.briefing'`

- [ ] **Step 3: Implementar `briefing.py`**

```python
# preparar-implementacao/src/preparar_implementacao/briefing.py
"""Monta o briefing Markdown consolidado, para o desenvolvedor levar ao Superpowers."""

from __future__ import annotations

from typing import Any


def montar_briefing(
    *,
    work_item: dict[str, Any],
    spec_tecnica: str,
    spec_negocios: str | None,
    tasks: list[dict[str, Any]],
) -> str:
    """Consolida work item, abordagem técnica, contexto de negócio e Tasks num único documento."""
    campos = work_item["fields"]
    titulo = campos.get("System.Title", "")
    tipo = campos.get("System.WorkItemType", "")
    criterios = campos.get("Microsoft.VSTS.Common.AcceptanceCriteria", "")
    descricao = campos.get("System.Description") or campos.get(
        "Microsoft.VSTS.TCM.ReproSteps", ""
    )

    partes = [
        f"# Briefing de implementação — {tipo} #{work_item.get('id')}: {titulo}",
        "",
        "## Descrição",
        "",
        descricao,
        "",
        "## Critérios de aceitação",
        "",
        criterios,
        "",
        "## Abordagem técnica",
        "",
        spec_tecnica,
        "",
    ]
    if spec_negocios:
        partes += ["## Contexto de negócio", "", spec_negocios, ""]

    partes += ["## Tasks e estimativas", ""]
    if not tasks:
        partes.append("Nenhuma Task filha encontrada.")
    for task in tasks:
        campos_task = task["fields"]
        partes.append(
            f"- **{campos_task.get('System.Title')}** — "
            f"Original Estimate: {campos_task.get('Microsoft.VSTS.Scheduling.OriginalEstimate')} h, "
            f"Remaining: {campos_task.get('Microsoft.VSTS.Scheduling.RemainingWork')} h"
        )
    return "\n".join(partes)
```

- [ ] **Step 4: Rodar os testes de `briefing.py` e confirmar que passam**

Run: `cd preparar-implementacao && uv run pytest tests/test_briefing.py -v`
Expected: PASS (2 testes)

- [ ] **Step 5: Escrever o teste da CLI**

```python
# preparar-implementacao/tests/test_cli.py
from preparar_implementacao.cli import executar

_ENV = {
    "AZURE_DEVOPS_ORGANIZACAO": "minha-org",
    "AZURE_DEVOPS_PROJETO": "meu-projeto",
    "AZURE_DEVOPS_TOKEN": "token",
}


def test_montar_sem_configuracao_devolve_erro(capsys: object) -> None:
    codigo = executar(["montar", "1"], env={})
    saida = capsys.readouterr().out  # type: ignore[attr-defined]
    assert codigo == 2
    assert "Configuração inválida" in saida
```

- [ ] **Step 6: Rodar o teste da CLI e confirmar que falha**

Run: `cd preparar-implementacao && uv run pytest tests/test_cli.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'preparar_implementacao.cli'`

- [ ] **Step 7: Implementar `cli.py` e atualizar `__init__.py`**

```python
# preparar-implementacao/src/preparar_implementacao/cli.py
"""CLI de apoio à skill: leitura, verificação de suficiência e montagem do briefing.
Nenhum comando escreve no Azure Boards."""

from __future__ import annotations

import argparse
from collections.abc import Mapping

from preparar_implementacao.briefing import montar_briefing
from preparar_implementacao.cliente_azure_devops import ClienteAzureDevOps
from preparar_implementacao.configuracao import ErroConfiguracao, carregar_configuracao
from preparar_implementacao.contexto import extrair_campo_demanda, ids_tasks_filhas, ler_tasks
from preparar_implementacao.hierarquia import subir_ate_demanda
from preparar_implementacao.suficiencia import ErroSuficienciaInsuficiente, verificar_suficiencia


def executar(argv: list[str], *, env: Mapping[str, str]) -> int:
    parser = _construir_parser()
    args = parser.parse_args(argv)
    try:
        config = carregar_configuracao(env)
    except ErroConfiguracao as erro:
        print(f"Configuração inválida: {erro}")
        return 2
    if args.comando != "montar":
        parser.error("comando desconhecido")
        return 2
    try:
        with ClienteAzureDevOps(
            config.organizacao, config.projeto, config.token.get_secret_value()
        ) as cliente:
            work_item = cliente.ler_work_item(args.work_item_id)
            cadeia = subir_ate_demanda(cliente, args.work_item_id, config.tipo_demanda)
            spec_tecnica = extrair_campo_demanda(
                cadeia, config.tipo_demanda, config.campo_spec_tecnica
            )
            spec_negocios = extrair_campo_demanda(
                cadeia, config.tipo_demanda, config.campo_spec_negocios
            )
            tasks = ler_tasks(cliente, ids_tasks_filhas(work_item))
            criterios = work_item["fields"].get("Microsoft.VSTS.Common.AcceptanceCriteria")
            verificar_suficiencia(
                spec_tecnica=spec_tecnica, criterios_aceitacao=criterios, tasks=tasks
            )
    except ErroSuficienciaInsuficiente as erro:
        print(str(erro))
        return 1
    briefing = montar_briefing(
        work_item=work_item,
        spec_tecnica=spec_tecnica or "",
        spec_negocios=spec_negocios,
        tasks=tasks,
    )
    print(briefing)
    return 0


def _construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="preparar-implementacao")
    subs = parser.add_subparsers(dest="comando", required=True)
    montar = subs.add_parser("montar")
    montar.add_argument("work_item_id", type=int)
    return parser
```

```python
# preparar-implementacao/src/preparar_implementacao/__init__.py
"""Skill de implementação: monta o briefing consolidado a partir de um work item refinado."""

from __future__ import annotations

import os
import sys


def main() -> None:
    from preparar_implementacao.cli import executar

    raise SystemExit(executar(sys.argv[1:], env=os.environ))
```

- [ ] **Step 8: Rodar todos os testes do pacote e confirmar que passam**

Run: `cd preparar-implementacao && uv run pytest tests/ -v`
Expected: PASS (todos os testes do pacote, inclusive o novo de CLI)

- [ ] **Step 9: Escrever o SKILL.md**

```markdown
---
name: preparar-implementacao
description: Use ao começar a codar uma História/Bug já refinada e decomposta, para montar o briefing que você leva ao superpowers:brainstorming e superpowers:writing-plans.
---

# Preparar o material de implementação

## Objetivo

Ler o work item, subir até a Demanda, reunir a abordagem técnica (`Custom.DemandaSpecTecnica`), o
contexto de negócio (`Custom.DemandaSpecNegocios`) e as Tasks já estimadas, verificar se há o mínimo
necessário e montar um briefing único em Markdown. Esta skill nunca escreve no Azure Boards e nunca
invoca `brainstorming` nem `writing-plans` — você leva o briefing a eles, na sua própria sessão.

## Fluxo obrigatório

1. Receba o ID da História/Bug (ou de uma Task específica, se você já souber qual).
2. Rode `preparar-implementacao montar <id>`.
3. Se faltar spec técnica, critério de aceitação ou alguma Task sem estimativa, a CLI recusa montar o
   briefing e nomeia exatamente o que falta — volte para `refinar-tecnicamente` ou `decompor-tasks`
   antes de prosseguir. Nunca preencha a lacuna você mesmo para contornar o aviso.
4. Com o briefing pronto, leve-o ao `superpowers:brainstorming` para desenhar a abordagem e depois ao
   `superpowers:writing-plans` para gerar o plano de implementação.

## O que esta skill nunca faz

- Não escreve em nenhum campo nem cria nenhum work item.
- Não invoca `brainstorming` nem `writing-plans` diretamente.
- Não preenche uma lacuna de suficiência com conteúdo inventado.
```

- [ ] **Step 10: Escrever o README.md**

```markdown
# preparar-implementacao

Skill de implementação: lê um work item já refinado e decomposto no Azure Boards, reúne a
abordagem técnica, o contexto de negócio e as Tasks estimadas, e monta um briefing único em
Markdown — sem nenhuma escrita no Azure Boards.

## Instalação

```bash
npx skills add pedroct/refinamento-planejamento-tecnico --skill preparar-implementacao -a claude-code
```

## Configuração

Copie `.env.example` para `.env` e preencha organização, projeto e token do Azure DevOps. O token
nunca deve ser versionado.
```

- [ ] **Step 11: Commit**

```bash
cd preparar-implementacao
git add src/preparar_implementacao/briefing.py src/preparar_implementacao/cli.py \
  src/preparar_implementacao/__init__.py SKILL.md README.md tests/test_briefing.py tests/test_cli.py
git commit -m "feat(preparar-implementacao): montagem do briefing, CLI, SKILL.md e testes

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

## Task 13: Documentação de topo do repositório

**Files:**
- Create: `README.md`
- Create: `CLAUDE.md`
- Create: `.gitignore` (raiz)

**Interfaces:**
- Nenhuma — documentação, sem código.

- [ ] **Step 1: Escrever o `README.md` da raiz**

```markdown
# Refinamento e Planejamento Técnico

Skills para a equipe técnica: refinamento técnico de uma Demanda já publicada pelo
[`gerador-hu`](https://github.com/pedroct/gerador-de-hu), planejamento de capacidade por pessoa e
preparação do material de implementação.

## O que o projeto faz

```text
gerador-hu (PO + negócio)
  Demanda → spec.md / negocio.md → backlog.md
                                     └─ publicar-backlog-demanda-azure-boards
                                        └─ Épico → Feature → História/Bug

refinamento-planejamento-tecnico
  refinar-tecnicamente        (reunião técnica)
    └─ fecha lacunas técnicas, registra abordagem, estima Story Points
       └─ grava Custom.DemandaSpecTecnica na Demanda

  decompor-tasks               (planning, por item, por quem executa)
    └─ decompõe em Tasks, estima horas, atribui a si, cria as Tasks

  preparar-implementacao       (ao começar a codar, mesmo dev)
    └─ monta o briefing → dev leva a superpowers:brainstorming e writing-plans
```

- **Refinamento técnico:** fecha as lacunas técnicas de `spec.md`, investiga o código, registra a
  abordagem técnica e estima Story Points ancorados em Histórias/Bugs fechados comparáveis. Grava a
  spec atualizada em `Custom.DemandaSpecTecnica`, na Demanda de Negócio.
- **Decomposição em Tasks:** no planning, por item, pelo desenvolvedor que vai executá-lo. Decompõe
  a História/Bug em Tasks a partir da abordagem já registrada, estima horas ancoradas em Tasks
  fechadas comparáveis e cria as Tasks atribuídas a si.
- **Preparação da implementação:** ao começar a codar, monta um briefing único — work item,
  hierarquia, spec técnica e de negócio, Tasks e estimativas — para o desenvolvedor levar ao
  Superpowers (`brainstorming` → `writing-plans`).

## Invariante de escrita

Nenhum tipo de work item é escrito por dois repositórios. `gerador-hu` é o único que cria Epic,
Feature, User Story e Bug. Este repositório é o único que cria Task e o único que escreve em
`Custom.DemandaSpecTecnica`.

## Instalação

```bash
# listar as skills disponíveis
npx skills add pedroct/refinamento-planejamento-tecnico --list

# instalar todas, no projeto atual, para Claude Code
npx skills add pedroct/refinamento-planejamento-tecnico --all -a claude-code

# instalar só uma
npx skills add pedroct/refinamento-planejamento-tecnico --skill decompor-tasks -a claude-code
```

Cada skill tem seu próprio `.env.example` — copie para `.env` e preencha organização, projeto e
token do Azure DevOps antes de usar. O token nunca deve ser versionado.

## Pré-requisitos

- `gerador-hu` publicado e configurado, com uma spec (`spec.md`) já gerada para a Demanda.
- Os campos customizados `Custom.DemandaSpecTecnica` e `Custom.DemandaSpecNegocios`, criados no
  processo do Azure DevOps (página "Spec" da Demanda de Negócio).
- Um PAT do Azure DevOps com permissão de leitura e escrita em work items.
```

- [ ] **Step 2: Escrever o `CLAUDE.md` da raiz**

```markdown
# Convenções deste projeto

## Idioma

Todo o conteúdo criado neste projeto — `SKILL.md`, referências, specs de design, planos de
implementação, README, comentários e mensagens de commit quando fizer sentido — deve ser escrito em
**português brasileiro**, nunca em inglês.

## Invariante de escrita

Nenhum tipo de work item é escrito por dois repositórios. Este repositório nunca cria Epic, Feature,
User Story ou Bug — isso é exclusivo do `gerador-hu`. Este repositório é o único que cria Task e o
único que escreve em `Custom.DemandaSpecTecnica`.

## Estimativa

Nenhuma estimativa (Story Points ou horas) é inventada sem ancoragem em item fechado comparável ou
confirmação humana explícita registrada na conversa.
```

- [ ] **Step 3: Escrever o `.gitignore` da raiz**

```text
.venv/
__pycache__/
*.pyc
.env
.mypy_cache/
.pytest_cache/
.ruff_cache/
.DS_Store
```

- [ ] **Step 4: Commit**

```bash
git add README.md CLAUDE.md .gitignore
git commit -m "docs: README e convenções de topo do repositório

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```
