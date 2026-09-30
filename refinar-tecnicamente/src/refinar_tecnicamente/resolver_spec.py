"""Resolve spec.md/backlog.md de uma Demanda: pasta local primeiro, anexo remoto como
fallback — nunca pede caminho manualmente nem sugere gerar a spec de novo. Quando precisa
baixar, materializa na mesma convenção de pasta que redigir-spec-demanda-azure-boards usa."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any, Protocol

_SUFIXO_REMOTO = ".remoto"


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
    """Procura `docs/specs/DN-<id>-*/` (ou `DN-<id>/`) sob `raiz`, ignorando as pastas
    `.remoto` de `resolver_spec_remoto`.

    Devolve `None` quando `docs/specs/` não existe ou nenhuma pasta corresponde — nunca
    levanta erro de arquivo/diretório inexistente, isso é uma ausência normal, não uma falha.
    """
    base = raiz / "docs" / "specs"
    if not base.is_dir():
        return None
    candidatos = sorted(
        {
            p
            for p in base.glob(f"DN-{id_demanda}-*")
            if p.is_dir() and not p.name.endswith(_SUFIXO_REMOTO)
        }
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
    return _baixar_e_materializar(cliente, raiz=raiz, id_demanda=id_demanda, sufixo="")


def resolver_spec_remoto(cliente: _ClienteLeitura, *, raiz: Path, id_demanda: int) -> Path:
    """Baixa o anexo mais recente da Demanda para uma pasta IRMÃ da local
    (`docs/specs/DN-<id>-<slug>.remoto/`), ignorando a pasta local existente. Serve para ler o
    que outra sessão (outro perfil) publicou sem sobrescrever o trabalho local. A pasta remota
    é regravada a cada chamada; a local nunca é tocada.

    Quando a pasta local existe, a `.remoto` herda o nome dela (`<nome local>.remoto`), para as
    duas ficarem sempre pareadas mesmo que o título da Demanda tenha mudado desde que a local
    foi criada. Sem pasta local, o nome sai do título atual, como em `resolver_spec`."""
    local = localizar_pasta_local(raiz, id_demanda)
    return _baixar_e_materializar(
        cliente,
        raiz=raiz,
        id_demanda=id_demanda,
        sufixo=_SUFIXO_REMOTO,
        nome_base=local.name if local is not None else None,
    )


def _baixar_e_materializar(
    cliente: _ClienteLeitura,
    *,
    raiz: Path,
    id_demanda: int,
    sufixo: str,
    nome_base: str | None = None,
) -> Path:
    spec_bytes = cliente.baixar_anexo(id_demanda, "spec.md")
    if spec_bytes is None:
        raise ErroSpecNaoEncontrada(
            f"Demanda {id_demanda}: nenhuma pasta local em {raiz / 'docs' / 'specs'} e "
            "nenhum anexo spec.md nessa Demanda. A spec ainda não foi publicada."
            if not sufixo
            else f"Demanda {id_demanda}: nenhum anexo spec.md nessa Demanda no Azure Boards. "
            "Não há versão remota para comparar."
        )
    # backlog.md é opcional, mas se o download dele falhar (exceção do cliente), nada pode
    # já ter sido gravado em disco — senão a próxima execução acharia uma pasta local
    # incompleta (só com spec.md) e a devolveria como resultado válido, sem nunca baixar o
    # backlog nem avisar ninguém. Por isso todos os downloads acontecem antes de criar a
    # pasta ou gravar qualquer arquivo.
    backlog_bytes = cliente.baixar_anexo(id_demanda, "backlog.md")
    if nome_base is None:
        work_item = cliente.ler_work_item(id_demanda)
        campos = work_item.get("fields")
        titulo = campos.get("System.Title", "") if isinstance(campos, dict) else ""
        nome_base = montar_nome_pasta(id_demanda, titulo if isinstance(titulo, str) else "")
    nome_pasta = nome_base
    destino = raiz / "docs" / "specs" / f"{nome_pasta}{sufixo}"
    destino.mkdir(parents=True, exist_ok=True)
    (destino / "spec.md").write_bytes(spec_bytes)
    if backlog_bytes is not None:
        (destino / "backlog.md").write_bytes(backlog_bytes)
    else:
        # Uma pasta `.remoto` reaproveitada não pode manter o backlog de um download anterior.
        (destino / "backlog.md").unlink(missing_ok=True)
    return destino
