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
