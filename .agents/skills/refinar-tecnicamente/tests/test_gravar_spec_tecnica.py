import pytest

from refinar_tecnicamente.gravar_spec_tecnica import (
    ErroAnexoAposCampoGravado,
    ErroConfirmacaoInvalida,
    gravar_spec_tecnica,
    montar_frase_autorizacao,
)


class ClienteFalso:
    def __init__(self) -> None:
        self.chamadas: list[tuple[int, str, str]] = []
        self.anexos: list[tuple[int, str, bytes]] = []
        self.falha_anexo: Exception | None = None

    def gravar_campo(self, work_item_id: int, campo: str, valor: str) -> None:
        self.chamadas.append((work_item_id, campo, valor))

    def anexar_arquivo(self, work_item_id: int, nome_arquivo: str, conteudo: bytes) -> None:
        if self.falha_anexo is not None:
            raise self.falha_anexo
        self.anexos.append((work_item_id, nome_arquivo, conteudo))


_SPEC_COM_TABELA = (
    "# Spec: Acesso dos Gestores\n\n"
    "## Tabela de hierarquia\n\n"
    "| Código | Sigla | Descrição |\n"
    "|---|---|---|\n"
    "| 1.0 | SECEX | Secretaria da Receita |\n"
)


def test_frase_de_autorizacao_nomeia_a_demanda() -> None:
    frase = montar_frase_autorizacao(13959)
    assert "13959" in frase
    assert frase.startswith("AUTORIZAR GRAVAÇÃO SPEC TÉCNICA")


def test_grava_o_markdown_original_sem_nenhuma_conversao() -> None:
    """O campo Custom.DemandaSpecTecnica é Markdown nativo no Azure Boards (confirmado por
    evidência de tela na Demanda 14064) — gravar HTML produzia tags cruas e tabelas Markdown
    não renderizadas dentro do campo. O valor gravado precisa ser idêntico, byte a byte, ao
    conteúdo de spec.md, inclusive a tabela."""
    cliente = ClienteFalso()
    frase = montar_frase_autorizacao(13959)
    gravar_spec_tecnica(
        cliente,
        id_demanda=13959,
        campo="Custom.DemandaSpecTecnica",
        spec_md=_SPEC_COM_TABELA,
        resposta_confirmacao=frase,
    )
    assert cliente.chamadas == [(13959, "Custom.DemandaSpecTecnica", _SPEC_COM_TABELA)]


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
    assert cliente.anexos == []


def test_confirmacao_com_espaco_extra_ao_final_ainda_e_aceita() -> None:
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


def test_falha_no_anexo_apos_campo_gravado_levanta_erro_nomeado() -> None:
    cliente = ClienteFalso()
    cliente.falha_anexo = RuntimeError("falha simulada")
    frase = montar_frase_autorizacao(13959)
    with pytest.raises(ErroAnexoAposCampoGravado):
        gravar_spec_tecnica(
            cliente,
            id_demanda=13959,
            campo="Custom.DemandaSpecTecnica",
            spec_md="# Spec\n",
            resposta_confirmacao=frase,
        )
    assert cliente.chamadas == [(13959, "Custom.DemandaSpecTecnica", "# Spec\n")]
