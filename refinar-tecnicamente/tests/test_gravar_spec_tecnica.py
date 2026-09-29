import pytest

from refinar_tecnicamente.gravar_spec_tecnica import (
    ErroConfirmacaoInvalida,
    ErroHtmlInvalido,
    converter_para_html,
    gravar_spec_tecnica,
    montar_frase_autorizacao,
)


class ClienteFalso:
    def __init__(self) -> None:
        self.chamadas: list[tuple[int, str, str]] = []
        self.anexos: list[tuple[int, str, bytes]] = []

    def gravar_campo(self, work_item_id: int, campo: str, valor: str) -> None:
        self.chamadas.append((work_item_id, campo, valor))

    def anexar_arquivo(self, work_item_id: int, nome_arquivo: str, conteudo: bytes) -> None:
        self.anexos.append((work_item_id, nome_arquivo, conteudo))


def test_converte_markdown_simples() -> None:
    html = converter_para_html("# Título\n\nParágrafo com **negrito**.\n")
    assert "<h1>" in html
    assert "</h1>" in html
    assert "<strong>negrito</strong>" in html


def test_recusa_html_malformado(monkeypatch: pytest.MonkeyPatch) -> None:
    import refinar_tecnicamente.gravar_spec_tecnica as modulo

    monkeypatch.setattr(modulo, "_renderizar_markdown", lambda _md: "<p>sem fechar")
    with pytest.raises(ErroHtmlInvalido):
        converter_para_html("qualquer coisa")


def test_frase_de_autorizacao_nomeia_a_demanda() -> None:
    frase = montar_frase_autorizacao(13959)
    assert "13959" in frase
    assert frase.startswith("AUTORIZAR GRAVAÇÃO SPEC TÉCNICA")


def test_grava_quando_confirmacao_e_exata() -> None:
    cliente = ClienteFalso()
    frase = montar_frase_autorizacao(13959)
    gravar_spec_tecnica(
        cliente,
        id_demanda=13959,
        campo="Custom.DemandaSpecTecnica",
        spec_md="# Spec\n",
        resposta_confirmacao=frase,
    )
    assert len(cliente.chamadas) == 1
    assert cliente.chamadas[0][0] == 13959
    assert cliente.chamadas[0][1] == "Custom.DemandaSpecTecnica"


@pytest.mark.parametrize(
    "resposta",
    [
        "autorizar gravação spec técnica #13959",  # caixa diferente
        "AUTORIZAR GRAVACAO SPEC TECNICA #13959",  # sem acentuação
        "AUTORIZAR GRAVAÇÃO SPEC TÉCNICA #99999",  # Demanda errada
        "AUTORIZAR GRAVAÇÃO SPEC TÉCNICA #13959 com mais texto",  # conteúdo extra
        "sim",
    ],
)
def test_recusa_confirmacao_nao_exata(resposta: str) -> None:
    cliente = ClienteFalso()
    with pytest.raises(ErroConfirmacaoInvalida):
        gravar_spec_tecnica(
            cliente,
            id_demanda=13959,
            campo="Custom.DemandaSpecTecnica",
            spec_md="# Spec\n",
            resposta_confirmacao=resposta,
        )
    assert cliente.chamadas == []


def test_confirmacao_com_espaco_extra_ao_final_ainda_e_aceita() -> None:
    """Só o conteúdo importa; espaço à volta da resposta do usuário é ruído de digitação,
    não uma variação da frase em si — diferente do caso 'espaço extra' dentro da frase."""
    cliente = ClienteFalso()
    frase = montar_frase_autorizacao(13959)
    gravar_spec_tecnica(
        cliente,
        id_demanda=13959,
        campo="Custom.DemandaSpecTecnica",
        spec_md="# Spec\n",
        resposta_confirmacao=f"  {frase}  \n",
    )
    assert len(cliente.chamadas) == 1


def test_recusa_html_com_tag_de_fechamento_nao_correspondente() -> None:
    """HTML cru embutido na spec (`<p></div>`) — cobre o ramo de `handle_endtag` que compara
    a tag de fechamento com o topo da pilha, diferente de `test_recusa_html_malformado`
    (que testa tag nunca fechada, via `verificar_tudo_fechado`)."""
    with pytest.raises(ErroHtmlInvalido):
        converter_para_html("<p></div>\n")


def test_aceita_tag_autofechada_nao_vazia() -> None:
    """Tag com sintaxe de auto-fechamento (`<tag/>`) que não está entre as tags void
    conhecidas (br, hr, img, ...) — rara, mas o parser precisa tratá-la como abertura e
    fechamento imediatos, sem sobrar nada na pilha."""
    html = converter_para_html("<minhatag/>\n")
    assert "minhatag" in html


def test_aceita_markdown_com_imagem() -> None:
    """Regressão: markdown com imagem (void tag) não deve levantar ErroHtmlInvalido."""
    html = converter_para_html("![alt](x.png)\n")
    assert "<img" in html
    assert "alt=" in html or "alt =" in html


def test_aceita_markdown_com_linha_horizontal() -> None:
    """Regressão: markdown com linha horizontal (void tag hr) não deve levantar ErroHtmlInvalido."""
    html = converter_para_html("texto\n\n---\n\nmais texto\n")
    assert "<hr" in html
    assert "texto" in html
    assert "mais texto" in html


def test_grava_tambem_anexa_spec_md() -> None:
    cliente = ClienteFalso()
    frase = montar_frase_autorizacao(13959)
    gravar_spec_tecnica(
        cliente,
        id_demanda=13959,
        campo="Custom.DemandaSpecTecnica",
        spec_md="# Spec\n",
        resposta_confirmacao=frase,
    )
    assert (13959, "spec.md", b"# Spec\n") in cliente.anexos
    assert not any(nome == "backlog.md" for _, nome, _ in cliente.anexos)


def test_grava_com_backlog_tambem_anexa_backlog_md() -> None:
    cliente = ClienteFalso()
    frase = montar_frase_autorizacao(13959)
    gravar_spec_tecnica(
        cliente,
        id_demanda=13959,
        campo="Custom.DemandaSpecTecnica",
        spec_md="# Spec\n",
        resposta_confirmacao=frase,
        backlog_md="# Backlog\n",
    )
    assert (13959, "backlog.md", b"# Backlog\n") in cliente.anexos


def test_confirmacao_invalida_nao_anexa_nada() -> None:
    cliente = ClienteFalso()
    with pytest.raises(ErroConfirmacaoInvalida):
        gravar_spec_tecnica(
            cliente,
            id_demanda=13959,
            campo="Custom.DemandaSpecTecnica",
            spec_md="# Spec\n",
            resposta_confirmacao="resposta errada",
        )
    assert cliente.anexos == []
    assert cliente.chamadas == []
