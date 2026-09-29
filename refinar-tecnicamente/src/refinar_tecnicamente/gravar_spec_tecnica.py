"""Grava `Custom.DemandaSpecTecnica` sob confirmação textual explícita — a única escrita desta
skill no Azure Boards.

O campo é Markdown nativo no Azure Boards (evidência de tela coletada na Demanda 14064: o editor
mostra "Markdown supported" e uma barra de ferramentas de Markdown), não um campo HTML rico — por
isso o Markdown de `spec.md` é gravado como está, sem nenhuma conversão."""

from __future__ import annotations

from typing import Protocol


class _ClienteEscrita(Protocol):
    def gravar_campo(self, work_item_id: int, campo: str, valor: str) -> None: ...
    def anexar_arquivo(self, work_item_id: int, nome_arquivo: str, conteudo: bytes) -> None: ...


class ErroConfirmacaoInvalida(ValueError):
    """A resposta do usuário não é exatamente a frase de autorização esperada."""


class ErroAnexoAposCampoGravado(RuntimeError):
    """`gravar_campo` teve sucesso, mas um `anexar_arquivo` (spec.md ou backlog.md) falhou.

    Guarda a exceção original em `causa`. Quem chama sabe, ao capturar esta exceção, que o
    campo já foi escrito no Azure Boards mesmo que o anexo não tenha sido — não é uma falha
    total, e repetir a operação sem verificar o estado atual da Demanda arrisca confundir
    quem lê.
    """

    def __init__(self, causa: BaseException) -> None:
        super().__init__(str(causa))
        self.causa = causa


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
    backlog_md: str | None = None,
) -> None:
    """Grava spec_md (Markdown, sem conversão) e reanexa spec.md/backlog.md, só após confirmação
    exata. `backlog_md`, quando informado, é anexado como `backlog.md` na mesma operação — mantém
    o anexo remoto tão atual quanto a spec técnica que acabou de ser gravada.
    """
    frase_esperada = montar_frase_autorizacao(id_demanda)
    if resposta_confirmacao.strip() != frase_esperada:
        raise ErroConfirmacaoInvalida(
            "Confirmação ausente, incorreta ou vinculada a outra Demanda; "
            "nenhuma gravação foi feita."
        )
    cliente.gravar_campo(id_demanda, campo, spec_md)
    try:
        cliente.anexar_arquivo(id_demanda, "spec.md", spec_md.encode("utf-8"))
        if backlog_md is not None:
            cliente.anexar_arquivo(id_demanda, "backlog.md", backlog_md.encode("utf-8"))
    except Exception as erro:
        raise ErroAnexoAposCampoGravado(erro) from erro
