# Especificação: gravar Custom.DemandaSpecTecnica como Markdown, não HTML

## Contexto

`refinar-tecnicamente/gravar_spec_tecnica.py` converte a spec (`spec.md`) para HTML via
`MarkdownIt("commonmark", {"html": False})` e grava esse HTML em `Custom.DemandaSpecTecnica` através
de `gravar_campo` (PATCH). Essa conversão partiu do pressuposto de que o campo era um campo HTML rico
— o mesmo padrão de `System.Description`/`Acceptance Criteria`, tratado pela spec irmã
`2026-09-29-whitelist-html-azure-boards-design.md` (`gerador-hu`).

Esse pressuposto está errado. Evidência coletada diretamente na Demanda de Negócio 14064, após uma
gravação real feita pela skill:

- O editor do campo na tela do work item mostra o aviso **"Markdown supported"**, com barra de
  ferramentas de Markdown (negrito, itálico, link, código, listas) e um toggle **Preview** — a mesma UI
  usada pelo Azure Boards para campos `Text (multiple lines)` com formato **Markdown**, não HTML.
- O conteúdo efetivamente salvo no campo, em modo de edição, é a string HTML literal produzida pelo
  conversor: `<h1>Spec: ...</h1>`, `<p>...</p>`, `<blockquote>...</blockquote>`, tabelas Markdown
  (`| Código | Sigla | ... |` / `|---|---|...`) preservadas cruas dentro de um `<p>` — porque
  `MarkdownIt("commonmark", ...)` não interpreta tabelas GFM, então elas atravessam a conversão como
  texto comum.
- Quando o Azure renderiza essa string como Markdown (modo Preview), ele descarta/ignora as tags HTML
  desconhecidas para esse contexto e mantém só o texto interno — por isso o que a pessoa lê na tela é
  prosa "limpa" sem tags visíveis, mas com a sintaxe de tabela (`|---|---|`) sobrando crua, já que o
  parser Markdown não reconhece como tabela um bloco de texto que não começou como tal.

Ou seja: o defeito não é "tabela não suportada" (a causa originalmente suspeitada) — é que **a
conversão para HTML nunca deveria ter acontecido para este campo**. O campo já é Markdown nativo; a
skill deveria gravar `spec.md` como está.

Este é o mesmo tipo de campo (`Text (multiple lines)`) usado por `redigir-spec-demanda-azure-boards`
para `negocio.md`/`spec.md` — mas aquela skill só lê (`GET`), nunca grava campo; não é afetada.

## Objetivo

`gravar_spec_tecnica` passa a gravar o Markdown original (`spec_md`) em `Custom.DemandaSpecTecnica`,
sem nenhuma conversão para HTML. A confirmação textual (`montar_frase_autorizacao`) e o restante do
fluxo (upload/vínculo de `spec.md`/`backlog.md` como anexo) continuam exatamente como estão — a
mudança é só o valor gravado no campo.

## Fora de escopo

- `System.Description`/`Acceptance Criteria` de Bug e User Story
  (`publicar-backlog-azure-boards`/`publicar-backlog-demanda-azure-boards`, repositório `gerador-hu`):
  o usuário suspeita do mesmo problema, mas ainda não confirmou o formato configurado nesses campos.
  Frente separada, só depois de confirmação equivalente à desta spec.
- Corrigir manualmente o conteúdo já gravado na Demanda 14064 no Azure Boards — é uma escrita real
  em produção; fica a critério do usuário repetir `gravar-spec-tecnica` depois que o conserto estiver
  implementado.
- Qualquer sanitização própria de HTML/Markdown malicioso digitado na spec: o Azure Boards já
  sanitiza o que renderiza no campo Markdown (evidenciado pelo próprio caso: as tags HTML gravadas
  foram descartadas na renderização, não executadas) — não é responsabilidade desta skill duplicar
  essa sanitização.

## Restrições globais

- Conteúdo criado em português brasileiro.
- Cada arquivo de código alterado tem seu teste equivalente atualizado (convenção do projeto —
  [[cobertura-de-teste-por-arquivo]]).
- Nenhuma mudança na frase de confirmação, no fluxo de anexo (`spec.md`/`backlog.md`) ou na
  ambiguidade tratada por `ErroAnexoAposCampoGravado`.

## Decisões de arquitetura

### Remover a conversão para HTML, não escondê-la atrás de uma flag

`gravar_spec_tecnica.py` perde `_renderizar_markdown`, `converter_para_html`,
`_ValidadorDeAninhamento`, `_ValidadorDeTagsPermitidas`, `ErroHtmlInvalido` e as constantes de
whitelist (`_TAGS_HTML_PERMITIDAS`, `_TAGS_SEM_FECHAMENTO`) — código morto depois da correção, não
mantido como opção alternativa. Não há cenário em que gravar HTML nesse campo seja o comportamento
certo.

`gravar_spec_tecnica(...)` perde o parâmetro `html`; passa a gravar `spec_md` diretamente:

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
    ...
    cliente.gravar_campo(id_demanda, campo, spec_md)
    ...
```

### CLI mostra o Markdown, não HTML, antes da confirmação

`cli.py::_gravar_spec_tecnica` para de chamar `converter_para_html`/tratar `ErroHtmlInvalido`. A
prévia mostrada ao usuário antes da frase de confirmação passa a ser o próprio conteúdo de `spec.md`
(rotulada como Markdown, não HTML), para que a pessoa continue vendo exatamente o que vai ser gravado.

## Fluxo esperado

```text
spec.md (Markdown)
  → lido do disco
  → mostrado ao usuário como prévia (rotulado "Markdown", não HTML)
  → frase de confirmação exata
  → gravar_campo(id_demanda, campo, spec_md)  # sem conversão
  → anexar_arquivo(spec.md) [+ backlog.md, quando informado]
```

## Testes de aceitação

- Uma spec com título, parágrafo, tabela Markdown e lista é gravada **verbatim** — o valor passado a
  `cliente.gravar_campo` é byte-a-byte igual ao conteúdo de `spec.md` (nenhuma tag `<h1>`/`<p>`/`<table>`
  aparece no valor gravado).
- A confirmação textual continua exigida e exata (`ErroConfirmacaoInvalida` nos mesmos casos de hoje).
- O anexo de `spec.md`/`backlog.md` continua acontecendo depois da gravação do campo, com o mesmo
  tratamento de `ErroAnexoAposCampoGravado` quando o anexo falha após o campo já ter sido gravado.
- A CLI mostra o conteúdo de `spec.md` (não HTML) antes de pedir a frase de confirmação.
- Os testes que hoje cobrem rejeição de HTML malformado/tag fora da whitelist/script embutido são
  removidos — deixam de fazer sentido, porque não há mais conversão nem validação de HTML neste
  caminho.

### Qualidade

- Suíte de `refinar-tecnicamente` passa por completo, sem a dependência de `markdown-it-py` neste
  módulo (a dependência pode continuar no `pyproject.toml` só se outro módulo da skill ainda a usar;
  confirmar antes de removê-la).
- Lint/format/type-check da skill continuam passando.

## Critério de conclusão

`Custom.DemandaSpecTecnica` passa a receber exatamente o conteúdo de `spec.md`, sem nenhuma tag HTML
nem perda de sintaxe (tabelas, headers) — comportamento comprovado por teste que compara o valor
gravado byte-a-byte com o arquivo de entrada.
