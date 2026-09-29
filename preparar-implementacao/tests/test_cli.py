import argparse
from typing import Any

import httpx
import pytest

from preparar_implementacao import cli
from preparar_implementacao.cli import executar
from preparar_implementacao.cliente_azure_devops import ClienteAzureDevOps

_ENV = {
    "AZURE_DEVOPS_ORGANIZACAO": "minha-org",
    "AZURE_DEVOPS_PROJETO": "meu-projeto",
    "AZURE_DEVOPS_TOKEN": "token",
}

_ID_HISTORIA = 100
_ID_DEMANDA = 50
_ID_TASK = 10


def test_montar_sem_configuracao_devolve_erro(capsys: pytest.CaptureFixture[str]) -> None:
    codigo = executar(["montar", "1"], env={})
    saida = capsys.readouterr().out
    assert codigo == 2
    assert "Configuração inválida" in saida


def _historia(*, com_criterios: bool) -> dict[str, Any]:
    campos = {
        "System.Title": "Renovar diligência automaticamente",
        "System.WorkItemType": "User Story",
        "System.Description": "<p>Como usuário, quero...</p>",
    }
    if com_criterios:
        campos["Microsoft.VSTS.Common.AcceptanceCriteria"] = "<p>Dado que...</p>"
    return {
        "id": _ID_HISTORIA,
        "fields": campos,
        "relations": [
            {
                "rel": "System.LinkTypes.Hierarchy-Reverse",
                "url": f"https://dev.azure.com/org/proj/_apis/wit/workItems/{_ID_DEMANDA}",
            },
            {
                "rel": "System.LinkTypes.Hierarchy-Forward",
                "url": f"https://dev.azure.com/org/proj/_apis/wit/workItems/{_ID_TASK}",
            },
        ],
    }


def _demanda(*, com_spec_tecnica: bool) -> dict[str, Any]:
    campos = {
        "System.Title": "Renovar diligências automaticamente",
        "System.WorkItemType": "Demanda de Negócio",
    }
    if com_spec_tecnica:
        campos["Custom.DemandaSpecTecnica"] = "<p>abordagem técnica</p>"
    return {"id": _ID_DEMANDA, "fields": campos, "relations": []}


def _task(*, com_estimativas: bool) -> dict[str, Any]:
    campos: dict[str, Any] = {"System.Title": "Task A"}
    if com_estimativas:
        campos["Microsoft.VSTS.Scheduling.OriginalEstimate"] = 4.0
        campos["Microsoft.VSTS.Scheduling.RemainingWork"] = 4.0
    return {"id": _ID_TASK, "fields": campos, "relations": []}


def _instalar_cliente_falso(
    monkeypatch: pytest.MonkeyPatch, itens: dict[int, dict[str, Any]]
) -> None:
    """Substitui `ClienteAzureDevOps` no módulo `cli` por uma fábrica que injeta um transporte
    HTTP falso, para exercitar o cliente real (retentativa, decodificação, etc.) sem rede."""

    def handler(request: httpx.Request) -> httpx.Response:
        id_ = int(request.url.path.rsplit("/", 1)[-1])
        return httpx.Response(200, json=itens[id_])

    def fabrica(organizacao: str, projeto: str, token: str) -> ClienteAzureDevOps:
        return ClienteAzureDevOps(
            organizacao, projeto, token, transport=httpx.MockTransport(handler)
        )

    monkeypatch.setattr(cli, "ClienteAzureDevOps", fabrica)


def test_montar_com_hierarquia_completa_monta_e_imprime_briefing(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    itens = {
        _ID_HISTORIA: _historia(com_criterios=True),
        _ID_DEMANDA: _demanda(com_spec_tecnica=True),
        _ID_TASK: _task(com_estimativas=True),
    }
    _instalar_cliente_falso(monkeypatch, itens)

    codigo = executar(["montar", str(_ID_HISTORIA)], env=_ENV)

    saida = capsys.readouterr().out
    assert codigo == 0
    assert "Renovar diligência automaticamente" in saida
    assert "abordagem técnica" in saida
    assert "Task A" in saida


def test_montar_sem_spec_tecnica_recusa_e_nomeia_a_lacuna(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    itens = {
        _ID_HISTORIA: _historia(com_criterios=True),
        _ID_DEMANDA: _demanda(com_spec_tecnica=False),
        _ID_TASK: _task(com_estimativas=True),
    }
    _instalar_cliente_falso(monkeypatch, itens)

    codigo = executar(["montar", str(_ID_HISTORIA)], env=_ENV)

    saida = capsys.readouterr().out
    assert codigo == 1
    assert "spec técnica" in saida
    assert "Custom.DemandaSpecTecnica" in saida
    assert "Traceback" not in saida


def test_montar_sem_spec_tecnica_nomeia_o_campo_configurado_quando_customizado(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    itens = {
        _ID_HISTORIA: _historia(com_criterios=True),
        _ID_DEMANDA: _demanda(com_spec_tecnica=False),
        _ID_TASK: _task(com_estimativas=True),
    }
    _instalar_cliente_falso(monkeypatch, itens)
    env = {**_ENV, "AZURE_DEVOPS_CAMPO_SPEC_TECNICA": "Custom.OutroCampo"}

    codigo = executar(["montar", str(_ID_HISTORIA)], env=env)

    saida = capsys.readouterr().out
    assert codigo == 1
    assert "Custom.OutroCampo" in saida


def test_montar_com_hierarquia_incompleta_devolve_mensagem_limpa(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # A História não tem relação de pai — a cadeia nunca alcança a Demanda de Negócio.
    historia_sem_pai = {
        "id": _ID_HISTORIA,
        "fields": {
            "System.Title": "Renovar diligência automaticamente",
            "System.WorkItemType": "User Story",
            "Microsoft.VSTS.Common.AcceptanceCriteria": "<p>Dado que...</p>",
        },
        "relations": [],
    }
    itens = {_ID_HISTORIA: historia_sem_pai}
    _instalar_cliente_falso(monkeypatch, itens)

    codigo = executar(["montar", str(_ID_HISTORIA)], env=_ENV)

    saida = capsys.readouterr().out
    assert codigo == 1
    assert "Traceback" not in saida


def test_montar_com_falha_ao_falar_com_azure_boards_devolve_mensagem_limpa(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """`args.comando` só admite "montar" hoje (único subparser registrado), então o único jeito
    real de exercitar o `except (ErroDestinoInvalido, ...)` é fazer o cliente HTTP (real, via
    MockTransport) devolver um 404 ao ler o work item inicial."""

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={})

    def fabrica(organizacao: str, projeto: str, token: str) -> ClienteAzureDevOps:
        return ClienteAzureDevOps(
            organizacao, projeto, token, transport=httpx.MockTransport(handler)
        )

    monkeypatch.setattr(cli, "ClienteAzureDevOps", fabrica)

    codigo = executar(["montar", str(_ID_HISTORIA)], env=_ENV)

    saida = capsys.readouterr().out
    assert codigo == 1
    assert "Falha ao falar com o Azure Boards" in saida
    assert "Traceback" not in saida


def test_montar_com_comando_desconhecido_devolve_codigo_2(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`_construir_parser` só registra o subcomando "montar", então `argparse` nunca deixa
    `args.comando` chegar a `executar` com outro valor — o `if args.comando != "montar"` é uma
    salvaguarda defensiva. Para cobri-la sem tocar em `src/`, trocamos o parser por um dublê que
    devolve um `Namespace` com outro comando e um `.error()` que não interrompe a execução (ao
    contrário do `argparse` real, que já sairia com `SystemExit` antes desta checagem)."""

    class _ParserFalso:
        def parse_args(self, _argv: list[str]) -> argparse.Namespace:
            return argparse.Namespace(comando="outro")

        def error(self, _mensagem: str) -> None:
            return None

    monkeypatch.setattr(cli, "_construir_parser", lambda: _ParserFalso())

    codigo = executar(["outro"], env=_ENV)

    assert codigo == 2
