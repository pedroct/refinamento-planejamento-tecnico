"""Lê, sem interpretar, a seção `## Lacunas e perguntas abertas` de uma spec."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

_TITULO_SECAO = "## Lacunas e perguntas abertas"
_ITEM_ROTULADO = re.compile(
    r"^- \*\*(?P<id>\w+) · (?P<audiencia>Negócio|Técnico)\*\* — (?P<pergunta>.+)$"
)
_ITEM_SIMPLES = re.compile(r"^- (?P<pergunta>.+)$")
_EVIDENCIA = re.compile(r"^\s*<!--\s*evidência:(?P<evidencia>.+?)-->\s*$")
_ITEM_AMBIGUO = re.compile(r"^- \*\*[^*]*\*\*")


class ErroLacunaAmbigua(ValueError):
    """Levantado quando uma lacuna parece ser rotulada mas não segue o padrão exato."""

    pass


@dataclass(frozen=True)
class Lacuna:
    """Um item de `## Lacunas e perguntas abertas`, sem interpretação de conteúdo."""

    id: str | None
    audiencia: str | None
    pergunta: str
    evidencia: str | None


Perfil = Literal["fullstack", "mobile", "ambos"]

_CAMINHO_ENTRE_CRASES = re.compile(r"`([^`]+)`")


def _parece_caminho(texto: str) -> bool:
    """Verifica se o texto parece um caminho de repositório (ex.: 'repo/arquivo' ou
    'repo/arquivo:linha'). Exclui texto livre sem '/' para não classificar evidências
    como "Nenhuma referência" ou "Ver código" como caminhos."""
    return re.match(r"\S+/\S+", texto) is not None


def _e_caminho_mobile(caminho: str) -> bool:
    """O primeiro segmento do caminho (antes de '/') é o nome do repositório; 'mobile' como
    substring nele, case-insensitive, é a convenção observada nos repositórios reais
    (`diligencia-mobile`). Limitação conhecida e aceita: um repositório cujo nome contenha
    'mobile' sem ser o app mobile também classificaria como mobile."""
    repositorio = caminho.split("/", 1)[0]
    return "mobile" in repositorio.lower()


def perfil_da_lacuna(lacuna: Lacuna) -> Perfil:
    """Classifica pelos caminhos citados entre crases na pergunta e na evidência, juntos.
    A evidência sem crases é interpretada como caminho direto apenas se parecer um caminho
    (padrão \\S+/\\S+); texto livre sem "/" (ex.: "Nenhuma referência") não contribui.
    Sem caminho nenhum, ou caminhos dos dois tipos ao mesmo tempo (mesmo campo ou campos
    diferentes), o resultado é 'ambos' — nunca esconde uma pergunta por excesso de precisão."""
    texto = lacuna.pergunta + " " + (lacuna.evidencia or "")
    caminhos = _CAMINHO_ENTRE_CRASES.findall(texto)

    # Se a evidência não estiver vazia, não tiver caminhos entre crases e parecer um caminho,
    # interpretá-la como um caminho direto
    if (
        lacuna.evidencia
        and not _CAMINHO_ENTRE_CRASES.search(lacuna.evidencia)
        and _parece_caminho(lacuna.evidencia)
    ):
        caminhos.append(lacuna.evidencia)

    if not caminhos:
        return "ambos"
    classificacoes = {_e_caminho_mobile(caminho) for caminho in caminhos}
    if len(classificacoes) > 1:
        return "ambos"
    return "mobile" if classificacoes.pop() else "fullstack"


def _corpo_secao_lacunas(spec_md: str) -> str | None:
    """Isola o corpo de `## Lacunas e perguntas abertas`, até a próxima seção ou o fim.

    Escrito como varredura de linhas, não regex: um `.*?` reluctant seguido de um limite que
    também casa string vazia (fim de arquivo) dispara alertas de regex mal-comportada (Sonar
    python:S6019 e python:S8786) sem trazer nenhum ganho sobre a varredura direta.
    """
    linhas = spec_md.splitlines()
    inicio: int | None = None
    for indice, linha in enumerate(linhas):
        if linha.rstrip() == _TITULO_SECAO:
            inicio = indice + 1
            break
    if inicio is None:
        return None
    corpo: list[str] = []
    for linha in linhas[inicio:]:
        if linha.startswith("## "):
            break
        corpo.append(linha)
    return "\n".join(corpo)


def _fechar_pendente(lacunas: list[Lacuna], pendente: dict[str, str | None] | None) -> None:
    if pendente is not None:
        lacunas.append(Lacuna(**pendente))  # type: ignore[arg-type]


def ler_lacunas(spec_md: str) -> list[Lacuna]:
    """Extrai cada lacuna da seção, na ordem em que aparece no documento."""
    corpo = _corpo_secao_lacunas(spec_md)
    if corpo is None:
        return []
    lacunas: list[Lacuna] = []
    pendente: dict[str, str | None] | None = None
    for linha in corpo.splitlines():
        rotulado = _ITEM_ROTULADO.match(linha)
        if rotulado:
            _fechar_pendente(lacunas, pendente)
            pendente = {
                "id": rotulado.group("id"),
                "audiencia": rotulado.group("audiencia"),
                "pergunta": rotulado.group("pergunta").strip(),
                "evidencia": None,
            }
            continue
        if _ITEM_AMBIGUO.match(linha):
            raise ErroLacunaAmbigua(f"Lacuna parece rotulada mas não segue o padrão exato: {linha}")
        evidencia = _EVIDENCIA.match(linha)
        if evidencia and pendente is not None:
            pendente["evidencia"] = evidencia.group("evidencia").strip()
            continue
        simples = _ITEM_SIMPLES.match(linha)
        if simples:
            _fechar_pendente(lacunas, pendente)
            pendente = {
                "id": None,
                "audiencia": None,
                "pergunta": simples.group("pergunta").strip(),
                "evidencia": None,
            }
    _fechar_pendente(lacunas, pendente)
    return lacunas


def filtrar_tecnicas(lacunas: list[Lacuna], perfil: Perfil | None = None) -> list[Lacuna]:
    """Devolve as lacunas Técnico e as sem rótulo, preservando a ordem original. Quando `perfil`
    é informado, descarta também as que `perfil_da_lacuna` classifica para o outro perfil —
    lacunas 'ambos' sempre passam, em qualquer perfil."""
    tecnicas = [lacuna for lacuna in lacunas if lacuna.audiencia in (None, "Técnico")]
    if perfil is None:
        return tecnicas
    return [lacuna for lacuna in tecnicas if perfil_da_lacuna(lacuna) in (perfil, "ambos")]
