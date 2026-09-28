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
