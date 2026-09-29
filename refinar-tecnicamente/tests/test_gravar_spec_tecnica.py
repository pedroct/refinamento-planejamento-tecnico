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


def test_recusa_html_com_tag_de_fechamento_nao_correspondente(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """HTML cru embutido na spec (`<p></div>`) — cobre o ramo de `handle_endtag` que compara
    a tag de fechamento com o topo da pilha, diferente de `test_recusa_html_malformado`
    (que testa tag nunca fechada, via `verificar_tudo_fechado`). Com `html: False` no
    renderizador, HTML digitado como Markdown é escapado (vira texto, não tag real), então
    simulamos a saída hostil do renderizador via monkeypatch em vez de HTML cru na fonte."""
    import refinar_tecnicamente.gravar_spec_tecnica as modulo

    monkeypatch.setattr(modulo, "_renderizar_markdown", lambda _spec_md: "<p></div>")
    with pytest.raises(ErroHtmlInvalido):
        converter_para_html("qualquer coisa")


def test_aceita_tag_autofechada_nao_vazia(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tag com sintaxe de auto-fechamento (`<tag/>`) que não está entre as tags void
    conhecidas (br, hr, img, ...) — rara, mas o parser precisa tratá-la como abertura e
    fechamento imediatos, sem sobrar nada na pilha. Usa <code/> (tag permitida) em vez de
    <minhatag/> para respeitar a whitelist. Com `html: False`, `<code/>` digitado como
    Markdown seria escapado, então simulamos a saída do renderizador via monkeypatch."""
    import refinar_tecnicamente.gravar_spec_tecnica as modulo

    monkeypatch.setattr(modulo, "_renderizar_markdown", lambda _spec_md: "<code/>\n")
    html = converter_para_html("qualquer coisa")
    assert "code" in html


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


def test_recusa_script_embutido_na_spec_tecnica(monkeypatch: pytest.MonkeyPatch) -> None:
    """Com `html: False`, HTML cru na fonte Markdown é escapado, então um `<script>` não
    chega mais como tag real ao converter passando pela fonte Markdown. Simulamos a saída
    hostil do renderizador via monkeypatch para continuar exercitando a whitelist
    isoladamente (mesmo padrão usado nos pacotes irmãos deste plano)."""
    import refinar_tecnicamente.gravar_spec_tecnica as modulo

    monkeypatch.setattr(
        modulo, "_renderizar_markdown", lambda _spec_md: "<script>alert(1)</script>"
    )
    with pytest.raises(ErroHtmlInvalido, match="script"):
        converter_para_html("qualquer coisa")


def test_recusa_iframe_embutido_na_spec_tecnica(monkeypatch: pytest.MonkeyPatch) -> None:
    """docs/documentacao_markdown_azure.md é explícito: Azure DevOps não suporta iframes.
    Com `html: False`, HTML cru na fonte é escapado, então simulamos a saída hostil do
    renderizador via monkeypatch para exercitar a whitelist isoladamente."""
    import refinar_tecnicamente.gravar_spec_tecnica as modulo

    monkeypatch.setattr(
        modulo,
        "_renderizar_markdown",
        lambda _spec_md: '<iframe src="https://exemplo.invalido"></iframe>',
    )
    with pytest.raises(ErroHtmlInvalido, match="iframe"):
        converter_para_html("qualquer coisa")


def test_recusa_tag_fora_da_whitelist_em_caixa_alta(monkeypatch: pytest.MonkeyPatch) -> None:
    """HTMLParser normaliza para minúsculas; confirma que <SCRIPT> não escapa da whitelist
    por variação de maiúsculas/minúsculas. Com `html: False`, HTML cru na fonte é escapado,
    então simulamos a saída hostil do renderizador via monkeypatch."""
    import refinar_tecnicamente.gravar_spec_tecnica as modulo

    monkeypatch.setattr(
        modulo, "_renderizar_markdown", lambda _spec_md: "<SCRIPT>alert(1)</SCRIPT>"
    )
    with pytest.raises(ErroHtmlInvalido, match="script"):
        converter_para_html("qualquer coisa")


def test_recusa_gravar_quando_spec_tem_tag_fora_da_whitelist(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Integração via `gravar_spec_tecnica`: nenhuma escrita deve acontecer quando a spec
    renderiza para uma tag fora da whitelist. Com `html: False`, HTML cru na fonte é
    escapado, então simulamos a saída hostil do renderizador via monkeypatch."""
    import refinar_tecnicamente.gravar_spec_tecnica as modulo

    monkeypatch.setattr(
        modulo, "_renderizar_markdown", lambda _spec_md: "<script>alert(1)</script>"
    )
    cliente = ClienteFalso()
    frase = montar_frase_autorizacao(13959)
    with pytest.raises(ErroHtmlInvalido):
        gravar_spec_tecnica(
            cliente,
            id_demanda=13959,
            campo="Custom.DemandaSpecTecnica",
            spec_md="<script>alert(1)</script>\n",
            resposta_confirmacao=frase,
        )
    assert cliente.chamadas == []
    assert cliente.anexos == []


def test_html_cru_com_comentario_nao_libera_script_embutido() -> None:
    """Antes desta correção, um <script> disfarçado de comentário/CDATA HTML passava direto
    pelos dois validadores porque MarkdownIt repassava HTML cru sem escapar. Com
    {"html": False}, o texto inteiro vira texto literal escapado — nenhuma tag real chega
    aos validadores."""
    html = converter_para_html("<!--><script>alert(1)</script>-->\n")
    assert "<script" not in html


def test_aceita_markdown_com_quebra_de_linha_forcada() -> None:
    """Regressão: quebra de linha forçada (dois espaços ao final da linha) é Markdown comum,
    recomendado pela doc de referência do Azure DevOps, e o CommonMark renderiza como
    `<br />` — precisa estar na whitelist."""
    html = converter_para_html("linha um  \nlinha dois\n")
    assert "<br" in html
