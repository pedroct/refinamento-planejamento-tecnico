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
PerfilFiltro = Literal["fullstack", "mobile"]

_CAMINHO_ENTRE_CRASES = re.compile(r"`([^`]+)`")


def _repositorio_do_caminho(token: str) -> str | None:
    """Devolve o nome do repositório se o token tem forma de caminho `repo/arquivo[:linha]`;
    senão `None`. Só conta como caminho um token que contém '/', não é URL (sem '://') e cujo
    primeiro segmento — o nome do repositório — contém '-' (ex.: `diligencia-api`,
    `diligencia-mobile`). Identificadores (`PENDENTE`, `Custom.Campo`, `Arquivo.java:75`),
    prosa como "API/Web" e "n/a"/"e/ou" não têm essa forma e não contribuem."""
    token = token.strip().rstrip(".,;:!?)")
    if "/" not in token or "://" in token or token.lower() in ("n/a", "e/ou"):
        return None
    repositorio = token.split("/", 1)[0]
    return repositorio if "-" in repositorio else None


def _tokens_de_texto_livre(texto: str) -> list[str]:
    """Separa por espaço, vírgula e ponto-e-vírgula o texto de uma evidência sem crases."""
    return [token for token in re.split(r"[\s,;]+", texto.strip()) if token]


def _e_repositorio_mobile(repositorio: str) -> bool:
    """'mobile' como substring do nome do repositório, case-insensitive, é a convenção
    observada nos repositórios reais (`diligencia-mobile`). Limitação conhecida e aceita: um
    repositório cujo nome contenha 'mobile' sem ser o app mobile também classificaria como
    mobile."""
    return "mobile" in repositorio.lower()


def perfil_da_lacuna(lacuna: Lacuna) -> Perfil:
    """Classifica pelos caminhos `repo/arquivo` citados na pergunta e na evidência, juntos:
    tokens entre crases e, quando a evidência não tem crases, seus tokens em texto livre.
    Só um token com '/', sem '://' e com '-' no primeiro segmento conta como caminho (ver
    `_repositorio_do_caminho`); o resto não contribui.
    Sem caminho nenhum, ou caminhos dos dois tipos ao mesmo tempo (mesmo campo ou campos
    diferentes), o resultado é 'ambos' — a heurística só pode errar nessa direção, nunca
    esconde uma pergunta por excesso de precisão."""
    texto = lacuna.pergunta + " " + (lacuna.evidencia or "")
    candidatos = _CAMINHO_ENTRE_CRASES.findall(texto)
    if lacuna.evidencia and not _CAMINHO_ENTRE_CRASES.search(lacuna.evidencia):
        candidatos.extend(_tokens_de_texto_livre(lacuna.evidencia))

    repositorios = [
        repositorio
        for candidato in candidatos
        if (repositorio := _repositorio_do_caminho(candidato)) is not None
    ]
    if not repositorios:
        return "ambos"
    classificacoes = {_e_repositorio_mobile(repositorio) for repositorio in repositorios}
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


def filtrar_tecnicas(lacunas: list[Lacuna], perfil: PerfilFiltro | None = None) -> list[Lacuna]:
    """Devolve as lacunas Técnico e as sem rótulo, preservando a ordem original. Quando `perfil`
    é informado, descarta também as que `perfil_da_lacuna` classifica para o outro perfil —
    lacunas 'ambos' sempre passam, em qualquer perfil."""
    tecnicas = [lacuna for lacuna in lacunas if lacuna.audiencia in (None, "Técnico")]
    if perfil is None:
        return tecnicas
    return [lacuna for lacuna in tecnicas if perfil_da_lacuna(lacuna) in (perfil, "ambos")]
