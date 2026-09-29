# Especificação: gravar Custom.DemandaSpecTecnica como Markdown, não HTML

## Contexto

`refinar-tecnicamente/gravar_spec_tecnica.py` convertia a spec (`spec.md`) para HTML via
`MarkdownIt("commonmark", {"html": False})` e gravava esse HTML em `Custom.DemandaSpecTecnica`
através de `gravar_campo` (PATCH). Essa conversão partiu do pressuposto de que o campo era um campo
HTML rico — o mesmo padrão de `System.Description`/`Acceptance Criteria`, tratado pela spec irmã
`2026-09-29-whitelist-html-azure-boards-design.md` (`gerador-hu`).

Investigação real na Demanda de Negócio 14064 revelou uma causa mais específica do que "HTML errado":
**campos multilinha do Azure Boards (`Description`, `Repro Steps`, `Acceptance Criteria` e campos
customizados de texto longo) têm um formato por gravação — HTML ou Markdown — controlado por uma
propriedade separada do JSON Patch, `multilineFieldsFormat`, e não pelo conteúdo em si.** Quando o
PATCH não inclui essa propriedade, **o Azure DevOps assume HTML por padrão**, mesmo que o valor
enviado seja texto/Markdown puro sem nenhuma tag. Fonte:
[Markdown Support Arrives for Work Items](https://devblogs.microsoft.com/devops/markdown-support-arrives-for-work-items/)
(Azure DevOps Blog) — *"The default format is `HTML`"*; para gravar em Markdown, o PATCH precisa de
duas operações:

```json
[
  { "op": "add", "path": "/fields/Custom.DemandaSpecTecnica", "value": "# seu texto em markdown" },
  { "op": "add", "path": "/multilineFieldsFormat/Custom.DemandaSpecTecnica", "value": "Markdown" }
]
```

Isso explica, em ordem, os três estados observados na Demanda 14064:

1. **Gravação original** (`converter_para_html`, antes de qualquer correção): enviava HTML puro sem
   `multilineFieldsFormat`. Como o padrão do Azure já é HTML, o conteúdo foi interpretado corretamente
   como HTML — blocos (`<h1>`, `<p>`, `<blockquote>`) renderizaram como blocos de verdade. O único
   defeito real dessa gravação era **tabela**: `MarkdownIt("commonmark", ...)` não produz `<table>`
   (tabelas GFM não fazem parte do CommonMark puro), então cada tabela da spec virou texto cru com
   pipes dentro de um `<p>`.
2. **Primeira correção desta spec** (gravar `spec_md` cru, sem conversão, também sem
   `multilineFieldsFormat`): o Azure continuou assumindo HTML por padrão — só que agora o valor
   gravado era Markdown puro, sem nenhuma tag. Texto sem marcação, interpretado como HTML, tem toda
   quebra de linha (`\n` ou `\r\n`) colapsada pelas regras normais de renderização HTML (espaço em
   branco não-`<pre>` colapsa para um espaço). Resultado: o documento inteiro virou uma única linha
   corrida — comprovado por um teste mínimo isolado (string de 3 linhas com `\r\n`, gravada e lida de
   volta achatada em uma linha só, print em mão).
3. **Consequência visível na UI**: o editor do campo alternou de um "modo Markdown" (barra simples,
   aviso "Markdown supported", Preview) — herdado de uma gravação Markdown anterior de outra sessão —
   para o editor rich-text clássico (B/I/U, cor, emoji, indentação) com o aviso "We support markdown,
   you can convert this field", confirmando que a gravação sem `multilineFieldsFormat` fez o campo
   voltar a HTML.

## Objetivo

`gravar_spec_tecnica` grava o Markdown original (`spec_md`) em `Custom.DemandaSpecTecnica`, **e**
declara explicitamente o formato Markdown no mesmo PATCH via `multilineFieldsFormat`, para que o
Azure Boards trate o valor como Markdown de verdade (preservando quebras de linha, tabelas — Azure
Boards Markdown suporta tabela GFM nativamente — headers etc.) em vez de aplicar o padrão HTML.

## Fora de escopo

- `System.Description`/`Acceptance Criteria` de Bug e User Story — mesma ressalva da versão anterior
  desta spec: fica para confirmação e frente separada.
- Reverter o campo de volta para HTML: a documentação da Microsoft é explícita — *"Once a work item is
  saved with Markdown, it cannot be reverted back to HTML"* — e não há necessidade de reverter, já que
  Markdown é o formato pretendido.
- Qualquer sanitização própria de Markdown/HTML malicioso: fora de escopo, como já registrado na
  versão anterior.

## Restrições globais

- Conteúdo criado em português brasileiro.
- Cada arquivo de código alterado tem seu teste equivalente atualizado
  ([[cobertura-de-teste-por-arquivo]]).
- Nenhuma mudança na frase de confirmação, no fluxo de anexo (`spec.md`/`backlog.md`) ou na
  ambiguidade tratada por `ErroAnexoAposCampoGravado`.

## Decisões de arquitetura

### `gravar_campo` passa a enviar as duas operações do JSON Patch

`ClienteAzureDevOps.gravar_campo` (único ponto que grava campos de work item nesta skill) monta o
PATCH com duas entradas, na ordem documentada pela Microsoft (valor primeiro, formato depois):

```python
payload = [
    {"op": "replace", "path": f"/fields/{campo}", "value": valor},
    {"op": "add", "path": f"/multilineFieldsFormat/{campo}", "value": "Markdown"},
]
```

Usar `add` para `multilineFieldsFormat` segue literalmente o exemplo documentado pela Microsoft — é o
`op` usado mesmo quando o campo já tem um formato definido de uma gravação anterior (comportamento de
upsert do lado do Azure, não um `add` estrito de RFC 6902 puro).

Essa mudança fica em `gravar_campo` (não em `gravar_spec_tecnica`), porque `gravar_campo` é o único
método de escrita de campo desta skill — hoje só é chamado para `Custom.DemandaSpecTecnica`, e
declarar Markdown ali é correto para o único uso existente. Se uma futura skill desta base de código
precisar gravar campo em HTML, esse método precisa ganhar um parâmetro explícito de formato — não
existe hoje, não é necessário até existir esse segundo uso.

## Fluxo esperado

```text
spec.md (Markdown)
  → lido do disco
  → mostrado ao usuário como prévia
  → frase de confirmação exata
  → PATCH: [{"op":"replace","path":"/fields/<campo>","value":spec_md},
            {"op":"add","path":"/multilineFieldsFormat/<campo>","value":"Markdown"}]
  → anexar_arquivo(spec.md) [+ backlog.md, quando informado]
```

## Testes de aceitação

- `gravar_campo` envia um PATCH com **duas** operações: a primeira grava o valor em
  `/fields/<campo>`, a segunda declara `/multilineFieldsFormat/<campo>` = `"Markdown"`.
- O teste decodifica o corpo da requisição capturada (JSON completo, não só `in bytes`) e confere as
  duas operações, na ordem.
- Os testes já existentes de `gravar_spec_tecnica` (gravação verbatim, confirmação exata, anexo,
  `ErroAnexoAposCampoGravado`) continuam passando sem alteração de comportamento — a mudança é só no
  formato do PATCH enviado por `gravar_campo`.

### Qualidade

- Suíte de `refinar-tecnicamente` passa por completo.
- Antes de regravar a spec completa da Demanda 14064 em produção, um teste mínimo (string curta,
  poucas linhas) confirma no Azure Boards real que a quebra de linha é preservada com o PATCH de duas
  operações.

## Critério de conclusão

Uma gravação de teste mínima em `Custom.DemandaSpecTecnica`, com `multilineFieldsFormat` declarado
como Markdown, preserva quebras de linha no Azure Boards real — confirmado por evidência de tela — e
só então a spec completa da Demanda 14064 é regravada.
