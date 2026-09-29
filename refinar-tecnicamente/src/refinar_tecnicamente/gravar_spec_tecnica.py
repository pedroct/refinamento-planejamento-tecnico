"""Converte a spec técnica para HTML e grava `Custom.DemandaSpecTecnica` sob confirmação
textual explícita — a única escrita desta skill no Azure Boards."""

from __future__ import annotations

from html.parser import HTMLParser
from typing import Protocol

from markdown_it import MarkdownIt

_TAGS_SEM_FECHAMENTO = frozenset({"br", "hr", "img", "input", "meta", "col", "wbr"})


class _ClienteEscrita(Protocol):
    def gravar_campo(self, work_item_id: int, campo: str, valor: str) -> None: ...
    def anexar_arquivo(self, work_item_id: int, nome_arquivo: str, conteudo: bytes) -> None: ...


class ErroConfirmacaoInvalida(ValueError):
    """A resposta do usuário não é exatamente a frase de autorização esperada."""


class ErroHtmlInvalido(ValueError):
    """O HTML gerado a partir da spec não está bem formado; a gravação é recusada."""


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


class _ValidadorDeAninhamento(HTMLParser):
    """Levanta erro na primeira tag de fechamento que não corresponde à mais recente aberta."""

    def __init__(self) -> None:
        super().__init__()
        self._pilha: list[str] = []

    def handle_starttag(self, tag: str, _attrs: list[tuple[str, str | None]]) -> None:
        if tag not in _TAGS_SEM_FECHAMENTO:
            self._pilha.append(tag)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag not in _TAGS_SEM_FECHAMENTO:
            # Não-nula tag com auto-fechamento (raro, mas possível)
            self.handle_starttag(tag, attrs)
            self.handle_endtag(tag)
        # Caso contrário (tag sem fechamento): ignorar, é auto-contida

    def handle_endtag(self, tag: str) -> None:
        if not self._pilha or self._pilha[-1] != tag:
            raise ErroHtmlInvalido(
                f"Tag de fechamento </{tag}> não corresponde à tag aberta mais recente."
            )
        self._pilha.pop()

    def verificar_tudo_fechado(self) -> None:
        if self._pilha:
            raise ErroHtmlInvalido(f"Tags não fechadas: {', '.join(self._pilha)}.")


def _renderizar_markdown(spec_md: str) -> str:
    return MarkdownIt("commonmark").render(spec_md)


def converter_para_html(spec_md: str) -> str:
    """Converte Markdown para HTML e recusa gravar se o resultado não estiver bem formado."""
    html = _renderizar_markdown(spec_md)
    validador = _ValidadorDeAninhamento()
    validador.feed(html)
    validador.verificar_tudo_fechado()
    return html


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
    html: str | None = None,
    backlog_md: str | None = None,
) -> None:
    """Grava a spec técnica convertida e reanexa spec.md/backlog.md, só após confirmação exata.

    `html` é o HTML já convertido e validado (a CLI converte antes de mostrar o conteúdo para
    confirmação). `backlog_md`, quando informado, é anexado como `backlog.md` na mesma operação
    — mantém o anexo remoto tão atual quanto a spec técnica que acabou de ser gravada.
    """
    frase_esperada = montar_frase_autorizacao(id_demanda)
    if resposta_confirmacao.strip() != frase_esperada:
        raise ErroConfirmacaoInvalida(
            "Confirmação ausente, incorreta ou vinculada a outra Demanda; nenhuma gravação foi feita."
        )
    html_final = html if html is not None else converter_para_html(spec_md)
    cliente.gravar_campo(id_demanda, campo, html_final)
    try:
        cliente.anexar_arquivo(id_demanda, "spec.md", spec_md.encode("utf-8"))
        if backlog_md is not None:
            cliente.anexar_arquivo(id_demanda, "backlog.md", backlog_md.encode("utf-8"))
    except Exception as erro:
        raise ErroAnexoAposCampoGravado(erro) from erro
