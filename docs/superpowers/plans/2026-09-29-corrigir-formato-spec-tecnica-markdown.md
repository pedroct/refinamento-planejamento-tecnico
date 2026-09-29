# Corrigir formato de Custom.DemandaSpecTecnica (Markdown, não HTML) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans para implementar este
> plano tarefa a tarefa. Passos usam checkbox (`- [ ]`).

**Goal:** `gravar_spec_tecnica` para de converter `spec.md` para HTML e passa a gravar o Markdown
original em `Custom.DemandaSpecTecnica` — o campo é nativamente Markdown no Azure Boards (confirmado
por evidência de tela na Demanda 14064), então a conversão produzia tags HTML cruas e tabelas
Markdown não renderizadas dentro do campo.

**Architecture:** Remoção de código, não adição — `_renderizar_markdown`, `converter_para_html` e os
dois validadores de HTML saem de `gravar_spec_tecnica.py`; `gravar_spec_tecnica()` grava `spec_md`
direto via `cliente.gravar_campo`. `cli.py` para de chamar `converter_para_html` e mostra `spec_md` na
prévia. Dependência `markdown-it-py` sai do `pyproject.toml` (não usada em mais nenhum lugar da
skill).

**Tech Stack:** Python 3.12, `pytest`.

**Spec:** `docs/superpowers/specs/2026-09-29-corrigir-formato-spec-tecnica-markdown-design.md`

## Global Constraints

- Nenhuma mudança na frase de confirmação (`montar_frase_autorizacao`) nem no fluxo de anexo
  (`anexar_arquivo` de `spec.md`/`backlog.md`, incluindo `ErroAnexoAposCampoGravado`).
- `gravar_campo` deve receber o conteúdo de `spec_md` byte-a-byte, sem nenhuma transformação.

## Review Focus

- **Regressão na confirmação** — qualquer teste de `ErroConfirmacaoInvalida` precisa continuar
  passando sem alteração de comportamento.
- **Valor gravado no campo** — o teste de aceitação central compara `cliente.gravar_campo` byte-a-byte
  com o `spec.md` de entrada, incluindo tabela Markdown e cabeçalhos, para provar que nada é reescrito.
- **Dependência órfã** — confirmar que nenhum outro módulo de `refinar-tecnicamente` importa
  `markdown_it` antes de remover do `pyproject.toml`.

---

### Task 1: Remover conversão HTML de `gravar_spec_tecnica.py` e `cli.py`

**Files:**
- Modify: `refinar-tecnicamente/src/refinar_tecnicamente/gravar_spec_tecnica.py`
- Modify: `refinar-tecnicamente/src/refinar_tecnicamente/cli.py`
- Modify: `refinar-tecnicamente/tests/test_gravar_spec_tecnica.py`
- Modify: `refinar-tecnicamente/tests/test_cli.py`
- Modify: `refinar-tecnicamente/pyproject.toml` (remover dependência `markdown-it-py`)
- Modify: `refinar-tecnicamente/README.md` (linha ~58: "converte a spec atualizada para HTML e grava"
  → "grava o Markdown da spec, sem conversão")

**Interfaces:**
- Produces: `gravar_spec_tecnica(cliente, *, id_demanda, campo, spec_md, resposta_confirmacao,
  backlog_md=None) -> None` (sem `html`).
- Remove: `converter_para_html`, `ErroHtmlInvalido`, `_renderizar_markdown`,
  `_ValidadorDeAninhamento`, `_ValidadorDeTagsPermitidas`, `_TAGS_HTML_PERMITIDAS`,
  `_TAGS_SEM_FECHAMENTO`.

- [ ] **Step 1: Escrever os testes que falham**

Reescreva `tests/test_gravar_spec_tecnica.py` por completo:

```python
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
```

E ajuste `tests/test_cli.py`:

- Substitua `test_gravar_spec_tecnica_mostra_o_html_antes_da_frase_de_confirmacao` por uma versão que
  verifica que o **Markdown** (não HTML) aparece antes da frase:

```python
def test_gravar_spec_tecnica_mostra_o_markdown_antes_da_frase_de_confirmacao(
    tmp_path: Path, capsys: object
) -> None:
    spec = tmp_path / "spec.md"
    spec.write_text("# Título\n\nParágrafo da spec.\n", encoding="utf-8")
    codigo = executar(
        ["gravar-spec-tecnica", "--demanda", "13959", "--spec", str(spec)],
        env=_ENV,
        entrada=lambda _prompt: "resposta errada",
    )
    saida = capsys.readouterr().out  # type: ignore[attr-defined]
    assert codigo != 0
    indice_markdown = saida.index("# Título\n\nParágrafo da spec.")
    indice_frase = saida.index("AUTORIZAR GRAVAÇÃO SPEC TÉCNICA #13959")
    assert indice_markdown < indice_frase
    assert "<h1>" not in saida
```

- Remova `test_gravar_spec_tecnica_com_html_invalido_recusa_sem_pedir_confirmacao` — não há mais
  conversão nem validação de HTML nesse caminho.
- Os demais testes de `gravar-spec-tecnica` (`test_gravar_spec_tecnica_sem_confirmacao_exata_...`,
  `..._usa_campo_configurado_por_padrao`, `..._com_arquivo_inexistente_...`,
  `..._com_backlog_anexa_backlog_md`, `..._com_backlog_inexistente_...`,
  `..._com_falha_no_anexo_apos_campo_gravado_...`) continuam sem alteração — não dependem de HTML.

- [ ] **Step 2: Rodar os testes e confirmar que falham**

Run: `uv run pytest refinar-tecnicamente/tests/test_gravar_spec_tecnica.py refinar-tecnicamente/tests/test_cli.py -v`
Expected: FAIL nos testes novos/alterados (a implementação ainda converte para HTML)

- [ ] **Step 3: Implementar**

Em `gravar_spec_tecnica.py`: remova `_TAGS_SEM_FECHAMENTO`, `_TAGS_HTML_PERMITIDAS`,
`ErroHtmlInvalido`, `_ValidadorDeAninhamento`, `_ValidadorDeTagsPermitidas`, `_renderizar_markdown`,
`converter_para_html`, o import de `markdown_it` e o de `html.parser.HTMLParser`. Reescreva
`gravar_spec_tecnica`:

```python
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
    exata. Custom.DemandaSpecTecnica é um campo Markdown nativo do Azure Boards — gravar HTML aqui
    produzia tags cruas e tabelas não renderizadas dentro do campo."""
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
```

Mantenha `_ClienteEscrita`, `ErroConfirmacaoInvalida`, `ErroAnexoAposCampoGravado` e
`montar_frase_autorizacao` como estão.

Em `cli.py`: remova o import de `converter_para_html`/`ErroHtmlInvalido`. Em `_gravar_spec_tecnica`,
troque o bloco que converte e mostra HTML:

```python
    spec_md = caminho_spec.read_text(encoding="utf-8")
    frase = montar_frase_autorizacao(args.demanda)
    print(f"Markdown que será gravado em {campo}:")
    print(spec_md)
    print(f"Digite exatamente a frase abaixo para confirmar a gravação em {campo}:")
    print(frase)
    resposta = entrada("> ")
    try:
        with ClienteAzureDevOps(
            config.organizacao, config.projeto, config.token.get_secret_value()
        ) as cliente:
            gravar_spec_tecnica(
                cliente,
                id_demanda=args.demanda,
                campo=campo,
                spec_md=spec_md,
                resposta_confirmacao=resposta,
                backlog_md=backlog_md,
            )
```

(Remova o `try/except ErroHtmlInvalido` que existia antes desse trecho; o restante do `try/except`
para `ErroConfirmacaoInvalida`/`ErroAnexoAposCampoGravado` continua igual.)

Em `pyproject.toml`: remova a entrada de dependência `markdown-it-py` (conferir o nome exato usado
hoje antes de remover).

Em `README.md`: troque a frase "converte a spec atualizada para HTML e grava em
`Custom.DemandaSpecTecnica`" por "grava o Markdown da spec em `Custom.DemandaSpecTecnica`, sem
conversão — o campo já é Markdown nativo no Azure Boards".

- [ ] **Step 4: Rodar os testes e confirmar que passam**

Run: `uv run pytest refinar-tecnicamente/tests -v`
Expected: PASS (toda a suíte, sem os testes removidos)

- [ ] **Step 5: Conferir que `markdown_it` não é mais importado em lugar nenhum da skill**

Run: `grep -rn "markdown_it\|markdown-it" refinar-tecnicamente/src refinar-tecnicamente/pyproject.toml`
Expected: nenhuma ocorrência

- [ ] **Step 6: Rodar lint/format/type-check da skill**

Run: `cd refinar-tecnicamente && uv run ruff check . && uv run ruff format --check . && uv run mypy src`
Expected: sem erros

- [ ] **Step 7: Commit**

```bash
cd refinar-tecnicamente
git add src/refinar_tecnicamente/gravar_spec_tecnica.py src/refinar_tecnicamente/cli.py \
  tests/test_gravar_spec_tecnica.py tests/test_cli.py pyproject.toml README.md
git commit -m "fix(refinar-tecnicamente): gravar Spec Técnica como Markdown, não HTML"
```
