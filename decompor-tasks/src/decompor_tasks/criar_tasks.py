"""Cria as Tasks pendentes de um plano, sob confirmação textual exata, atualizando o
manifesto após cada criação para permitir retomada segura."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol

from decompor_tasks.manifesto import (
    Manifesto,
    PlanoTasks,
    TaskProposta,
    calcular_hash_plano,
    gravar_manifesto,
    montar_frase_autorizacao,
    tasks_pendentes,
)


class _ClienteEscrita(Protocol):
    def criar_work_item(self, tipo: str, operacoes: list[dict[str, Any]]) -> dict[str, Any]: ...


class ErroConfirmacaoInvalida(ValueError):
    """A resposta do usuário não é exatamente a frase de autorização esperada."""


def montar_operacoes_criacao(
    *, historia_id: int, organizacao: str, projeto: str, task: TaskProposta
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
            task=task,
        )
        # Grava a marca de "em andamento" ANTES da chamada de criação: se a chamada falhar
        # depois que o Azure Boards já tiver criado a Task (resposta ambígua perdida por
        # timeout ou 5xx), a marca persiste e uma reexecução exige reconciliação manual em
        # vez de recriar a Task silenciosamente.
        manifesto = Manifesto(
            historia_id=plano.historia_id,
            hash_plano=hash_atual,
            criadas=criadas,
            em_andamento=frozenset({task.titulo}),
        )
        gravar_manifesto(caminho_manifesto, manifesto)
        resultado = cliente.criar_work_item(tipo_task, operacoes)
        criadas[task.titulo] = resultado["id"]
        manifesto = Manifesto(historia_id=plano.historia_id, hash_plano=hash_atual, criadas=criadas)
        gravar_manifesto(caminho_manifesto, manifesto)
    return manifesto
