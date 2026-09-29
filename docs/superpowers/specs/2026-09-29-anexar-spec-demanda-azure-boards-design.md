# Design: anexar `spec.md`/`backlog.md` na Demanda e buscá-los só pelo ID

## Contexto

`refinar-tecnicamente` assume, no passo 1 do seu `SKILL.md`, que quem conduz a reunião técnica tem
localmente a pasta `docs/specs/DN-<id>-<slug>/` (com `spec.md` e `backlog.md`) gerada por
`redigir-spec-demanda-azure-boards`, no repositório do próprio projeto. Na prática, quem roda
`refinar-tecnicamente` é o desenvolvedor da reunião — não necessariamente quem gerou a spec — e essa
pasta muitas vezes não existe na máquina dele: o projeto vive num repositório GitLab (Sefaz) separado
do GitHub onde as skills são distribuídas, e nada força um `git pull`/`clone` antes da reunião. O
resultado observado: a skill pergunta o caminho manualmente ou sugere rodar `gerador-hu` — nenhuma das
duas opções faz sentido para o papel de quem está executando.

Este design elimina a dependência de sistema de arquivos/git para essa leitura: a Demanda, por ser o
work item raiz de toda a hierarquia, passa a carregar `spec.md` (e, quando existir, `backlog.md`) como
**anexos** (Attachments API do Azure Boards) — recurso nativo do work item, sem precisar de repositório
novo nem de escopo de PAT adicional (`Work Items Read & Write`, já usado por todas as escritas
existentes nos dois repositórios, cobre anexos).

## Decisão de mecanismo (registrada)

| Opção | Descartada porque |
|---|---|
| `git pull`/`clone` orquestrado pela skill | O projeto vive em GitLab (Sefaz), separado do GitHub das skills; a equipe não quer a skill operando git contra um repositório de aplicação. |
| Ler `Custom.DemandaSpecNegocios` (`negocio.md`) | `negocio.md` é uma projeção deliberadamente incompleta: nunca inclui lacunas rotuladas `Técnico`, nunca inclui evidência `caminho:linha`, e não tem `backlog.md` — exatamente o que `refinar-tecnicamente` precisa. Confirmado em `redigir-spec-demanda-azure-boards/SKILL.md:245-289` (gerador-hu). |
| Repositório dedicado no Azure Repos | Ganha histórico de versão real, mas exige provisionar um repositório novo, escopo de PAT adicional (`Code Read & Write`) e uma convenção de caminho própria — carga operacional maior para o mesmo resultado que o anexo já entrega (buscar a versão mais recente pelo ID da Demanda). |
| **Attachments do work item da Demanda** | **Escolhida.** Sem repositório novo, sem escopo de PAT adicional, ligado nativamente ao work item que já é o ponto único da hierarquia. Contrapartida aceita: não há diff/histórico entre versões, só a mais recente por data de upload. |

## Quem anexa

1. **`redigir-spec-demanda-azure-boards` (`gerador-hu`)** — hoje só faz `GET` na Demanda, sob uma
   regra explícita e documentada na própria skill (seção **Limites de leitura e de decisão**): "não
   execute POST, não execute PATCH, não execute PUT e não execute DELETE" / "Não crie, atualize, mova,
   comente, relacione ou exclua work items". Anexar um arquivo via API do Azure Boards exige duas
   chamadas — `POST` (upload do conteúdo) e `PATCH` (vincula o anexo ao work item via `relations`) —
   então essa mudança **levanta essa trava deliberadamente, só para esse caso específico**: a seção
   passa a listar uma exceção única e nomeada ("anexar `spec.md`/`backlog.md` à própria Demanda, ao
   terminar o rascunho"), mantendo proibido tudo o resto que já estava proibido (`PATCH` em qualquer
   campo, `PUT`, `DELETE`, criar/atualizar/mover/comentar/excluir qualquer work item, relacionar com
   qualquer work item que não seja o anexo na própria Demanda). Passa a anexar `spec.md` ao terminar de
   escrevê-lo pela primeira vez (cold start: `backlog.md` ainda não existe nesse ponto do pipeline, só
   é gerado depois por `gerar-backlog-azure-boards`).
2. **`refinar-tecnicamente gravar-spec-tecnica` (`refinamento-planejamento-tecnico`)** — já escreve
   `Custom.DemandaSpecTecnica` sob confirmação textual exata. Passa a, na mesma operação já confirmada,
   também reanexar `spec.md` (atualizado com a `## Abordagem técnica`) e `backlog.md` (já com Story
   Points), garantindo que o anexo fique atual a cada refinamento técnico.
3. **`entrevistar-lacunas-requisito` (`gerador-hu`)** — cobre a janela que sobrava entre o cold start
   e o próximo refinamento técnico: cada rodada de negócio grava decisões em `spec.md` (nunca em
   `negocio.md`, que é sempre regerado) e, até então, nada resincronizava nem a pasta local nem o
   anexo da Demanda. Ao encerrar qualquer rodada — negócio ou técnica — a skill passa a instruir a
   sincronização: regerar `negocio.md` (só na rodada de escopo negócio) e reanexar `spec.md` para
   **cada Demanda cujo `spec.md` foi editado na sessão**, cobrindo também o caso de impacto cruzado
   (uma rodada revela que a spec de **outra** Demanda também precisa mudar — ambas são
   sincronizadas, não só a que motivou a reunião). Isso levanta a invariante "skill-folha sem rede"
   dessa skill, documentada de propósito e **coberta por teste automatizado** que precisa ser
   atualizado (`entrevistar-lacunas-requisito/tests/test_skill_integration.py`, especialmente
   `test_interviewing_skill_does_not_call_other_skills` e
   `test_rodada_de_negocio_avisa_que_negocio_md_ficou_desatualizado`, que hoje trava no texto exato
   "Esta skill não regenera `negocio.md`").

**Decisão de escopo do repositório, motivada por esta mudança:** as skills deste fluxo (negócio +
técnica) deixam de precisar ser **instaláveis avulsas** entre si — a partir de agora, o time trabalha
com um fluxo definido (equipe de negócio conduzindo `entrevistar-lacunas-requisito`/
`redigir-spec-demanda-azure-boards`, equipe técnica conduzindo `refinar-tecnicamente`), não mais com
a garantia de que qualquer skill individual funciona sozinha, sem as demais instaladas. Por isso,
`entrevistar-lacunas-requisito` chama o script de `redigir-spec-demanda-azure-boards` diretamente
(caminho de pasta irmã), em vez de vendorizar uma cópia própria — o padrão de duplicação que as
demais skills deste repositório seguem (`cliente_azure_devops.py`, `cliente_jev.py`) não se aplica a
essa chamada nova. Essa decisão vale só para as skills deste fluxo, tocadas por este design; não
propõe (nem descarta) revisitar a vendorização já existente em nenhuma outra skill.

**`decompor-tasks` e `preparar-implementacao` não mudam** — decisão revisitada e confirmada, não só
uma constatação inicial. Cheguei a considerar migrá-las para ler `spec.md` (pasta local/anexo, como
`refinar-tecnicamente`), já que aparentemente seria "a mesma fonte de verdade" — mas isso pioraria o
desenho: hoje as duas fazem um único `GET` num campo já conhecido, sem tocar em sistema de
arquivos, sem Attachments API, sem cálculo de pasta — o caminho de leitura mais simples que existe.
Trocar isso por pasta-local-ou-anexo importaria pra dentro delas toda a máquina construída neste
design, sem ganho real: `Custom.DemandaSpecTecnica` **é**, por construção, `spec.md` convertido para
HTML (`gravar_spec_tecnica` faz exatamente essa conversão antes de gravar) — não é uma cópia que
diverge por acaso, é o mesmo conteúdo. Como nenhuma das duas **edita** o documento (só leem para dar
contexto ao agente que conduz a conversa), HTML serve tão bem quanto Markdown. O anexo em Markdown só
é indispensável para quem **edita e regrava** o documento — só `refinar-tecnicamente`. Confirmado
lendo os dois `SKILL.md`: nenhum dos dois depende de `spec.md`/`backlog.md` locais hoje, e este design
não muda isso.

**`Custom.DemandaSpecNegocios` sai de escopo.** Nunca teve escritor implementado em nenhum dos dois
repositórios (achado desta investigação) — não é um campo que ficaria redundante com o anexo, é um
campo **já órfão hoje**, independente deste design. A skill que o escreveria
(`publicar-spec-negocios-azure-boards`, desenhada em
`gerador-hu/docs/superpowers/specs/2026-09-28-publicar-spec-negocios-azure-boards-design.md`) **não
será construída** como parte deste trabalho — decisão explícita, não esquecimento. `negocio.md`
continua existindo só como material de leitura da reunião de negócio (ver **Quem anexa**, item 3);
nada além disso o consome.

## Quem busca

`refinar-tecnicamente`, passo 1 do fluxo: dado o ID da Demanda, procura
`docs/specs/DN-<id>-<slug>/` na raiz do repositório atualmente aberto. **Se não existir**, baixa o
anexo mais recente chamado `spec.md` (e `backlog.md`, se houver) da Demanda e reconstrói os arquivos
localmente — sem pedir o caminho manualmente nem sugerir rodar `gerador-hu`, que deixa de fazer
sentido como primeira pergunta.

**A pasta reconstruída usa a mesma convenção `DN-<id>-<slug>/` de `redigir-spec-demanda-azure-boards`
— nunca um nome inventado.** Um nome próprio (cogitado numa versão anterior deste design) criaria uma
segunda pasta órfã se o desenvolvedor depois clonar o repositório de verdade (GitLab Sefaz): o Git
traria `DN-<id>-<slug-real>/`, diferente do que o fallback já tivesse criado, e as duas coexistiriam
sem nenhuma delas saber da outra. Para computar o mesmo `<slug>`, o fallback busca `System.Title` da
Demanda (`GET`, já disponível via `ler_work_item`) e aplica o algoritmo já documentado em
`redigir-spec-demanda-azure-boards/SKILL.md` > **Pasta da Demanda**: minúsculas, acentos removidos,
espaços/pontuação viram hífen, hífens repetidos colapsam, truncado em 60 caracteres, sem hífen inicial
nem final; sem caractere aproveitável, usa só `DN-<id>`.

## Contrato dos anexos

- **Nome fixo:** `spec.md` e `backlog.md`, sempre esses nomes — é como o consumidor localiza o anexo
  certo sem heurística de conteúdo.
- **Sem versionamento real.** Cada upload cria um novo anexo com o mesmo nome; o Azure Boards não
  substitui o anterior. Quem lê pega **o último elemento de `relations` com esse nome** — o Azure
  Boards sempre acrescenta ao final (`path: "/relations/-"`), então a ordem da lista já reflete a
  ordem de anexo, sem depender de nenhum atributo de data. Anexos antigos não são apagados
  automaticamente — é ruído aceito, não um defeito a corrigir agora.
- **Sem retry em escrita.** Upload de anexo e vínculo ao work item seguem a mesma postura já
  estabelecida em `cliente_azure_devops.py`: uma tentativa, sem retry automático — um 5xx depois do
  `POST` é ambíguo (o blob pode ter sido criado sem o vínculo `AttachedFile` ter sido aplicado), e
  repetir sozinho arriscaria duplicar. Erro é reportado pedindo verificação manual, nunca reexecutado
  sozinho.

## API do Azure Boards usada

- **Upload do conteúdo:** `POST https://dev.azure.com/{organizacao}/{projeto}/_apis/wit/attachments
  ?fileName={nome}&api-version=7.2-preview.3`, corpo binário (`Content-Type: application/octet-stream`),
  devolve `{"id": "<guid>", "url": "<url>"}`.
- **Vincular ao work item:** `PATCH .../_apis/wit/workitems/{id}?api-version=7.2-preview.3`, JSON Patch
  `{"op": "add", "path": "/relations/-", "value": {"rel": "AttachedFile", "url": "<url do upload>",
  "attributes": {"comment": "spec.md" | "backlog.md"}}}`.
- **Listar anexos existentes:** já vem no `GET` de `ler_work_item` (`$expand=All` já inclui
  `relations`); filtrar `rel == "AttachedFile"` e `attributes.comment` igual ao nome procurado, e usar
  o **último** da lista filtrada (ver **Contrato dos anexos**).
- **Baixar conteúdo:** `GET {url do anexo}?fileName={nome}&download=true` (a mesma `url` guardada na
  relação).

## Módulos afetados

### `refinamento-planejamento-tecnico/refinar-tecnicamente`

- `cliente_azure_devops.py` — adicionar `anexar_arquivo(work_item_id, nome, conteudo: bytes) -> None`
  (upload sem retry + PATCH de vínculo) e `baixar_anexo(work_item_id, nome) -> bytes | None` (lê
  relações do `ler_work_item` já existente, filtra pelo nome, baixa o mais recente por data; devolve
  `None` se não houver nenhum anexo com aquele nome).
- `gravar_spec_tecnica.py` — `gravar_spec_tecnica(...)` passa a também anexar `spec.md` sempre, e
  `backlog.md` quando um caminho for informado (parâmetro novo, opcional). O `Protocol` de escrita
  (`_ClienteEscrita`) ganha `anexar_arquivo` na assinatura.
- `resolver_spec.py` (módulo novo) — `resolver_spec(cliente, *, raiz, id_demanda)` recebe só a raiz
  e o ID (**sem** parâmetro de destino): procura `docs/specs/DN-<id>-*/` sob a raiz e, se não achar,
  busca `System.Title` via `ler_work_item` (por isso o `Protocol` de leitura ganha esse método, além
  de `baixar_anexo`), calcula o mesmo `DN-<id>-<slug>/` que `redigir-spec-demanda-azure-boards`
  calcularia, baixa os anexos e materializa os arquivos lá — nunca num nome inventado (ver **Quem
  busca**).
- `cli.py` — `gravar-spec-tecnica` ganha `--backlog <caminho>` opcional; novo subcomando
  `resolver-spec --demanda <id> --raiz <diretorio>` (sem `--destino`: o caminho final é sempre
  calculado, nunca escolhido pelo usuário) que imprime o caminho final resolvido.
- `SKILL.md` — passo 1 reescrito: raiz de busca explícita (`docs/specs/` do repositório atual), e
  fallback de download em vez de perguntar caminho manual ou sugerir `gerador-hu`.

### `gerador-hu/redigir-spec-demanda-azure-boards`

- Esta skill **não tem cliente HTTP vendorizado nem `pyproject.toml`** — `consultar_demanda.py` usa só
  `urllib.request` da stdlib, convenção "sem dependência externa de propósito" do repositório. A função
  nova (`anexar_arquivo`, em `scripts/consultar_demanda.py` ou módulo irmão no mesmo estilo) segue o
  mesmo padrão: `urllib.request.Request` com `method="POST"`/`"PATCH"`, sem introduzir `httpx` nem
  nenhuma dependência nova — só a metade de escrita (upload + vínculo); esta skill não precisa baixar
  nada.
- `SKILL.md`, seção **Limites de leitura e de decisão**: reescrita para abrir a exceção nomeada (ver
  **Quem anexa**), sem afrouxar o restante da regra.
- Fluxo do `SKILL.md`: último passo (10) passa a anexar `spec.md` à Demanda, sem confirmação textual
  (não é gravação de campo visível, é só o arquivo-fonte ficando disponível para os passos seguintes do
  pipeline — mesmo raciocínio de "efeito colateral de baixo risco" já aceito para o anexo, distinto do
  `PATCH` de campo que sempre exige frase exata).

### `gerador-hu/entrevistar-lacunas-requisito`

- `SKILL.md`, passo 6 do "Fluxo": ao encerrar qualquer rodada, além do aviso já existente (para
  rodada de escopo negócio, que `negocio.md` ficou desatualizado), passa a instruir: regerar
  `negocio.md` conforme o **Template de negocio.md** documentado em
  `redigir-spec-demanda-azure-boards/SKILL.md` (referenciado, não reproduzido — ver decisão de escopo
  acima) e rodar, a partir da raiz desta skill,
  `uv run python ../redigir-spec-demanda-azure-boards/scripts/anexar_spec.py <id> <caminho completo
  de spec.md>` para **cada** Demanda cujo `spec.md` foi editado na sessão — não só a que motivou a
  reunião.
- `SKILL.md`, seção **Boundaries**: "Skill-folha: nunca invoque nenhuma outra skill deste
  repositório" ganha a mesma exceção nomeada e restrita já usada em
  `redigir-spec-demanda-azure-boards` — só a sincronização do passo 6, nada mais.
- `tests/test_skill_integration.py`: `test_rodada_de_negocio_avisa_que_negocio_md_ficou_desatualizado`
  precisa de novas asserções (a skill agora instrui a regeneração, não só avisa); e
  `test_interviewing_skill_does_not_call_other_skills` precisa admitir a chamada nomeada e restrita a
  `redigir-spec-demanda-azure-boards/scripts/anexar_spec.py`, sem enfraquecer a checagem para as
  demais skills da lista (`refinar-historias-3w`, `refinar-historias-3c`,
  `refinar-historias-gherkin`, `gerar-backlog-azure-boards`, `redigir-spec-pedido-negocio`).

## Fora de escopo

- Limpeza de anexos antigos/duplicados.
- `decompor-tasks`, `preparar-implementacao` — decisão revisitada e confirmada sem mudança (ver
  **Quem anexa**).
- `publicar-spec-negocios-azure-boards` — não será construída; `Custom.DemandaSpecNegocios`
  permanece sem escritor (ver **Quem anexa**).
- Revisitar a vendorização já existente em outras skills (`cliente_azure_devops.py` triplicado entre
  as três skills de `refinamento-planejamento-tecnico`, `cliente_jev.py`) — a decisão de não vendorizar
  vale só para a chamada nova de `entrevistar-lacunas-requisito`.
- Diff/histórico de versão entre anexos — aceito como limite do mecanismo escolhido (ver tabela de
  decisão).

## Limites da verificação

Testes cobrem `anexar_arquivo`/`baixar_anexo` com transporte HTTP injetável (mesmo padrão de
`httpx.BaseTransport` já usado nos dois repositórios), incluindo o caso de múltiplos anexos com o
mesmo nome (escolhe o mais recente) e nenhum anexo (devolve `None`). Nenhum teste prova que um anexo
real chega íntegro e legível pela UI do Azure Boards — isso exige verificação manual contra uma
Demanda de teste antes do primeiro uso real, como já é prática para as escritas existentes nos dois
repositórios.
