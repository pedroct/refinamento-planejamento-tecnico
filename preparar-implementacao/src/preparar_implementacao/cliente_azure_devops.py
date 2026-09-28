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
