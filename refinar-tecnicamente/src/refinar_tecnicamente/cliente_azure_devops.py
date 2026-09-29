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
from urllib.parse import quote

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
        """Grava um único campo por PATCH, usando JSON Patch (`replace`).

        Usa uma única tentativa sem retry automático: se o Azure DevOps retorna um código
        retentável (500/502/503) depois de já ter aplicado o PATCH, não se sabe se a escrita
        de fato aconteceu. Repetir automaticamente arrisca mascarar essa ambiguidade.
        Reconhecimento de ambiguidade e reconciliação ficam a cargo da camada chamadora.
        """
        url = (
            f"https://dev.azure.com/{self._organizacao}/{self._projeto}"
            f"/_apis/wit/workitems/{work_item_id}?api-version={_VERSAO_API}"
        )
        payload = [{"op": "replace", "path": f"/fields/{campo}", "value": valor}]
        resposta = self._executar(
            "PATCH",
            url,
            corpo=payload,
            content_type="application/json-patch+json",
            retentavel=False,
        )
        self._verificar_e_decodificar(resposta, work_item_id)

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
        retentavel: bool = True,
    ) -> httpx.Response:
        headers = {"Content-Type": content_type} if content_type else None
        if not retentavel:
            return self._executar_sem_retry(metodo, url, corpo, headers)
        return self._executar_com_retry(metodo, url, corpo, headers)

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

    def _executar_sem_retry(
        self, metodo: str, url: str, corpo: Any, headers: dict[str, str] | None
    ) -> httpx.Response:
        """Uma única tentativa sem retry automático, para operações não-retentáveis (escritas)."""
        try:
            resposta = self._cliente.request(metodo, url, json=corpo, headers=headers)
        except httpx.RequestError as erro:
            raise ErroFalhaTransitoria(
                f"A chamada {metodo} {url} falhou por erro de rede."
            ) from erro
        if resposta.status_code in _ERROS_RETENTAVEIS:
            raise ErroFalhaTransitoria(
                f"A chamada {metodo} {url} não se completou (HTTP {resposta.status_code})."
            )
        return resposta

    def _executar_com_retry(
        self, metodo: str, url: str, corpo: Any, headers: dict[str, str] | None
    ) -> httpx.Response:
        """Retry com backoff exponencial, para operações retentáveis (leituras)."""
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
