# Especificação: separar lacunas técnicas e Abordagem Técnica por perfil (Fullstack vs. Mobile)

## Contexto

`refinar-tecnicamente` conduz uma única sessão de entrevista técnica cobrindo todas as lacunas
`Técnico` de `spec.md`, e grava uma única seção `## Abordagem técnica` em `Custom.DemandaSpecTecnica`.
Na prática, quem refina API/Web e quem refina Mobile são profissionais distintos, em sessões
separadas — hoje não há como um deles ver só as perguntas do seu escopo, e a segunda sessão a rodar
sobrescreveria inteiramente o trabalho da primeira (`gravar_campo` faz `op: replace` no campo inteiro).

Achado ao vivo na Demanda 14064 (mesma sessão que motivou esta spec): o app mobile está **fora** do
escopo desta Demanda específica ("O app mobile fica fora" — decisão já registrada em `## Abordagem
técnica`), então esta Demanda não serve de exemplo real de lacuna mobile. A spec continua útil como
referência de formato, mas o comportamento por perfil só será observado numa Demanda futura que
realmente misture lacunas de API/Web e de Mobile.

## Objetivo

`refinar-tecnicamente` passa a permitir rodar a sessão de entrevista técnica **por perfil**
(`fullstack` ou `mobile`), mostrando só as lacunas Técnicas relevantes para esse perfil, e a estrutura
de `## Abordagem técnica` passa a ter uma subseção por perfil, escrita/atualizada de forma que a
sessão de um perfil nunca apague o trabalho já registrado pelo outro.

## Fora de escopo

- Geração de work items (Epic/Feature/User Story) por perfil — isso é responsabilidade de
  `publicar-backlog-demanda-azure-boards` (repositório `gerador-hu`), uma skill diferente, com seu
  próprio fluxo de confirmação antes de publicar. Decidido em conversa: não mexer aqui.
- `decompor-tasks` gravar `Description` em cada Task criada — pedido de melhoria relacionado, mas
  tratado como frente separada (não é sobre perfil).
- Marcar o perfil na origem da lacuna (mudar o formato que `spec.md` usa para `T· Técnico`) — exigiria
  mudar a skill que escreve `spec.md` no repositório `gerador-hu` e quebraria compatibilidade com
  specs já existentes no formato atual (a própria Demanda 14064, por exemplo). A classificação é só
  por inferência, no lado de `refinar-tecnicamente`.
- Perguntar perfil lacuna a lacuna durante a entrevista — descartado a favor de perguntar uma vez, no
  início da sessão, e filtrar automaticamente.
- Qualquer merge automático em Python do conteúdo de `spec.md`/do campo — a "mesclagem" entre os dois
  perfis é resolvida como disciplina de workflow (buscar a versão mais recente antes de escrever, só
  tocar na própria subseção), não como lógica de código.

## Restrições globais

- Conteúdo criado em português brasileiro.
- Cada arquivo de código alterado tem seu teste equivalente atualizado
  ([[cobertura-de-teste-por-arquivo]]).
- Sem `--perfil`, o comportamento de `ler-lacunas` continua exatamente como hoje (mostra todas as
  lacunas Técnicas e as sem rótulo) — mudança aditiva, não quebra uso existente.
- A heurística de classificação é só uma inferência local (regex sobre texto), sem rede, sem consulta
  a nenhum cadastro de repositórios.

## Decisões de arquitetura

### Classificação por evidência citada, não por rótulo na origem

`leitor_lacunas.py` ganha:

```python
Perfil = Literal["fullstack", "mobile", "ambos"]

def perfil_da_lacuna(lacuna: Lacuna) -> Perfil:
    """Classifica pela(s) referência(s) de caminho citadas entre crases na pergunta e/ou na
    evidência da lacuna. Um caminho é 'mobile' quando algum segmento do nome do repositório (a
    primeira parte antes de '/') contém 'mobile', case-insensitive — convenção observada nos
    repositórios reais (`diligencia-mobile`). Sem caminho nenhum citado, ou caminhos dos dois
    tipos ao mesmo tempo, o resultado é 'ambos' — nunca esconde uma pergunta por excesso de
    precisão da heurística.
    """
```

A função varre com regex os trechos entre crases (`` `...` ``) tanto em `lacuna.pergunta` quanto em
`lacuna.evidencia` (quando presente — o campo estruturado vindo do comentário `<!-- evidência: -->`,
ver `leitor_lacunas.py:11`), extrai o primeiro segmento de cada caminho encontrado e classifica cada
um como mobile/não-mobile. Nota registrada aqui por transparência: nos exemplos reais de lacunas já
vistos nesta sessão (Demanda 14064), nenhuma citava caminho de repositório na pergunta — eram
perguntas de escopo/negócio. Isso é esperado e não invalida o desenho: quando não há caminho citado,
`"ambos"` é o resultado seguro, e a heurística só entra em ação quando a lacuna já cita evidência de
código (prática já estabelecida no resto da spec, fora da seção de lacunas).

### `filtrar_tecnicas` ganha um filtro aditivo por perfil

```python
def filtrar_tecnicas(lacunas: list[Lacuna], perfil: Perfil | None = None) -> list[Lacuna]:
    """Devolve as lacunas Técnico e as sem rótulo, preservando a ordem original. Quando `perfil`
    é informado, descarta também as que `perfil_da_lacuna` classifica para o outro perfil
    (lacunas 'ambos' sempre passam)."""
```

### CLI: `ler-lacunas --perfil {fullstack,mobile}`

`construir_parser` (`cli.py`) adiciona `--perfil` com `choices=["fullstack", "mobile"]`, opcional,
default `None`. `_ler_lacunas` repassa para `filtrar_tecnicas(lacunas, perfil=args.perfil)`.

### Template de `## Abordagem técnica`: duas subseções de propriedade exclusiva

O template documentado no `SKILL.md` (passo 3 do fluxo) passa a declarar:

```markdown
## Abordagem técnica

### Escopo Fullstack (API/Web)
<decisões e detalhamento de repositórios não-mobile>
<estratégia de teste da parte fullstack>

### Escopo Mobile
<decisões e detalhamento de repositórios mobile>
<estratégia de teste da parte mobile>
```

### Fluxo da entrevista por perfil (mudança em `SKILL.md`, não em código)

Passo novo, antes do passo 2 atual: perguntar o perfil de quem está conduzindo a sessão
(`fullstack` ou `mobile`). Passo 2 passa a rodar `ler-lacunas spec.md --perfil <perfil>`. Passo 3
(escrever `## Abordagem técnica`) ganha a instrução: antes de escrever, rodar `resolver-spec` de novo
para buscar a versão mais recente de `spec.md` (pode ter sido atualizada pela sessão do outro
perfil, publicada em paralelo); montar o novo conteúdo substituindo **só** a subseção do próprio
perfil (`### Escopo Fullstack (API/Web)` ou `### Escopo Mobile`) — se a subseção do outro perfil já
existir no arquivo buscado, ela entra intacta no `spec.md` final antes de gravar.

## Fluxo esperado

```text
Sessão de refinamento técnico (perfil = fullstack | mobile)
  → resolver-spec (pega a versão mais atual de spec.md)
  → ler-lacunas spec.md --perfil <perfil>
  → entrevista só das lacunas Técnicas do perfil (+ sem rótulo)
  → investigação de código, escreve só a subseção "### Escopo <Perfil>" de "## Abordagem técnica"
  → resolver-spec de novo (revalida se a versão mudou; preserva a subseção do outro perfil se existir)
  → sugerir-story-points, gravar backlog.md
  → gravar-spec-tecnica (spec.md completo, com as duas subseções que existirem até agora)
```

## Testes de aceitação

- `perfil_da_lacuna`: lacuna com só caminho(s) mobile → `"mobile"`; só caminho(s) não-mobile →
  `"fullstack"`; caminhos dos dois tipos → `"ambos"`; nenhum caminho citado (nem em `pergunta` nem em
  `evidencia`) → `"ambos"`.
- `filtrar_tecnicas(lacunas, perfil="fullstack")` e `perfil="mobile"`: cada um devolve só as lacunas do
  próprio perfil mais as `"ambos"`; nunca deixa passar lacuna `Negócio`; `perfil=None` (ou omitido)
  devolve exatamente o resultado de hoje — regressão coberta explicitamente.
- CLI: `ler-lacunas spec.md --perfil mobile` filtra a saída JSON; `--perfil` com valor fora de
  `{fullstack, mobile}` devolve erro de uso do `argparse` (código 2), sem tentar ler o arquivo.
- `test_skill_integration.py` (ou equivalente): confere que o `SKILL.md` menciona a pergunta de perfil
  no início do fluxo, o novo template com as duas subseções, e a instrução de buscar a versão mais
  recente antes de escrever a própria subseção.

### Qualidade

- Suíte de `refinar-tecnicamente` passa por completo, sem regressão nos testes de `ler-lacunas` sem
  `--perfil`.
- Lint/format/type-check da skill continuam passando.

## Critério de conclusão

Rodar `ler-lacunas spec.md --perfil mobile` numa spec com lacunas técnicas mistas mostra só as
lacunas cuja evidência aponta para repositório mobile (mais as sem evidência nenhuma); o mesmo com
`--perfil fullstack` mostra o complemento; sem a flag, o resultado é idêntico ao comportamento atual.
