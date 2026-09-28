# Design: skills de refinamento e planejamento técnico

## Contexto

O repositório [`gerador-hu`](https://github.com/pedroct/gerador-de-hu) cobre o lado de negócio do
ciclo: de uma Demanda de Negócio até um backlog Markdown revisado, publicado no Azure Boards como
Épico → Feature → História/Bug (`publicar-backlog-demanda-azure-boards`). Ele para deliberadamente
aí — `gerar-backlog-azure-boards/SKILL.md` proíbe inventar Story Points, prioridade ou responsável, e
`publicar-backlog-demanda-azure-boards/SKILL.md` proíbe criar Task.

A partir de 24/09/2026 o refinamento de uma Demanda passa a acontecer em duas reuniões separadas —
uma de negócio, outra técnica — e a spec gerada por `redigir-spec-demanda-azure-boards` já reflete
essa fronteira: cada lacuna carrega um rótulo de audiência (`Negócio` ou `Técnico`), e `negocio.md` é
uma projeção de `spec.md` para quem não lê código.

Este repositório, `refinamento-planejamento-tecnico`, cobre o que vem depois da reunião de negócio:
o refinamento técnico propriamente dito, o planejamento de capacidade por pessoa, e a preparação do
material que o desenvolvedor leva ao Superpowers (`brainstorming` → `writing-plans`) para gerar a
spec e o plano de implementação de cada item, no momento de codar.

Este design nasceu de uma sessão de brainstorming com o usuário e incorpora três decisões dele que
corrigiram o desenho inicial:

1. **Tasks e horas são de quem executa, não de quem refina.** Nascer sem dono quebraria o cálculo de
   capacidade nativo do Azure Boards, que compara horas por pessoa contra `Remaining Work` das Tasks
   atribuídas a ela.
2. **Story Points e horas são grandezas diferentes, em momentos diferentes.** O refinamento técnico
   estima em Story Points, grandeza relativa, para o planning decidir o que cabe na sprint. O dev, ao
   puxar o item, converte em Tasks com horas reais.
3. **A spec técnica fica presa à Demanda por um campo customizado**, `Custom.DemandaSpecTecnica`,
   numa página "Spec" do processo do Azure DevOps — já criada pelo usuário antes deste desenho, junto
   com `Custom.DemandaSpecNegocios` (simétrico, mas fora do escopo deste repositório). Sem isso, quem
   só tem acesso ao board, e não ao repositório de specs, perde a abordagem técnica: ela não existe em
   nenhum nível publicado (Épico, Feature, História) porque nasce antes da publicação e descreve a
   Demanda inteira, não um item de folha.

## Objetivos

1. Fechar as lacunas técnicas de `spec.md` (rótulo `Técnico`) por entrevista, reaproveitando o
   mecanismo de rodada/fronteira já existente no `gerador-hu`.
2. Investigar o código e registrar a abordagem técnica — camadas tocadas, migração quando houver,
   estratégia de teste — como uma seção nova de `spec.md`, mantendo a fonte única já estabelecida.
3. Estimar em Story Points cada História/Bug, ancorado em itens fechados comparáveis, e publicar essa
   estimativa junto com o backlog enriquecido.
4. Prender a spec técnica atualizada à Demanda de Negócio, via `Custom.DemandaSpecTecnica`, para que
   ela sobreviva independente de acesso ao repositório de specs.
5. Decompor uma História/Bug já publicada em Tasks, no momento do planning, atribuídas a quem vai
   executar e estimadas em horas ancoradas em Tasks fechadas comparáveis.
6. Preparar, no momento de começar a codar, um briefing consolidado — work item, hierarquia acima
   dele, spec técnica e de negócio, Tasks e estimativas — para o desenvolvedor levar ao
   `superpowers:brainstorming` e `superpowers:writing-plans`.
7. Nunca inventar um número de estimativa (Story Points ou horas) sem ancoragem em histórico ou
   confirmação explícita de quem está na conversa.

## Fora de escopo

- **Cálculo de capacidade.** O Azure Boards já tem gráfico de capacidade nativo, alimentado por
  `Remaining Work` e atribuição — construir um cálculo próprio duplicaria a ferramenta. Este
  repositório só garante que os dados que o gráfico consome (horas, responsável) cheguem corretos.
- **Criação de Épico, Feature, História ou Bug.** Esses tipos são escritos exclusivamente pelo
  `gerador-hu` (`publicar-backlog-demanda-azure-boards`). Este repositório só complementa itens já
  publicados por ele — nunca cria um do zero.
- **Escrita em `Custom.DemandaSpecNegocios`.** É simétrico ao campo que este repositório escreve, mas
  pertence ao lado de negócio. Fica como acompanhamento para uma mudança futura em
  `redigir-spec-demanda-azure-boards` ou `entrevistar-lacunas-requisito`, no `gerador-hu` — fora do
  escopo desta spec.
- **Campo customizado para `telas-ux-ui.md` (`Custom.DemandaSpecUXUI` ou similar).** Considerado
  durante o desenho e adiado deliberadamente: ao contrário de `spec.md`/`negocio.md`, esse documento é
  condicional — só existe quando o requisito envolve tela nova ou fluxo alterado — e abri-lo agora
  levantaria a mesma pergunta para os outros documentos condicionais da pasta
  (`debitos-tecnicos.md`, `revisao-textos.md`), inflando o corte inicial antes de as três skills deste
  repositório estarem provadas em uso real. A skill 3 já não bloqueia por ausência de contexto
  opcional — só por ausência de abordagem técnica, critério de aceitação ou Task estimada — então essa
  leitura extra pode ser adicionada depois sem alterar o invariante de escrita.
- **A rodada de entrevista de negócio e a geração do backlog inicial.** Continuam no `gerador-hu`,
  sem alteração.
- **Execução do `brainstorming`/`writing-plans`.** Este repositório prepara o material; quem invoca o
  Superpowers é o desenvolvedor, na sessão dele. Nenhuma skill daqui chama outra skill de outro
  pacote.
- **Geração de código.** Nenhuma das três skills escreve código de produto.

## Invariante de escrita

**Nenhum tipo de work item é escrito por dois repositórios.** `gerador-hu` é o único que cria Epic,
Feature, User Story e Bug. Este repositório é o único que cria Task, e o único que escreve em
`Custom.DemandaSpecTecnica`. As duas superfícies de escrita daqui — criação de Task e `PATCH` do
campo customizado — nunca se sobrepõem ao que o `gerador-hu` publica.

## Arquitetura: três skills, três momentos

```text
gerador-hu (PO + negócio)
  Demanda → spec.md / negocio.md → backlog.md
                                     └→ publicar-backlog-demanda-azure-boards
                                        └→ Épico → Feature → História/Bug

refinamento-planejamento-tecnico — refinamento (reunião técnica, com o dev)
  refinar-tecnicamente
    ├─ fecha lacunas Técnico (entrevista em rodadas)
    ├─ investiga código, registra abordagem técnica em spec.md
    ├─ estima Story Points (ancorado em Histórias fechadas comparáveis)
    ├─ grava spec.md em Custom.DemandaSpecTecnica (PATCH, com confirmação)
    └─ backlog.md enriquecido com Story Points
       └→ publicar-backlog-demanda-azure-boards (do gerador-hu, sem alteração de fluxo)

refinamento-planejamento-tecnico — planning (o dev que vai executar, por item)
  decompor-tasks
    ├─ lê a História/Bug já publicada (Story Points como contexto de porte, não copiado)
    ├─ decompõe em Tasks a partir da abordagem técnica já registrada
    ├─ estima Original Estimate/Remaining (ancorado em Tasks fechadas comparáveis)
    ├─ atribui cada Task ao usuário do PAT
    └─ cria as Tasks, com autorização textual explícita e manifesto de retomada

refinamento-planejamento-tecnico — implementação (o mesmo dev, ao começar a codar)
  preparar-implementacao
    ├─ lê a História/Bug, sobe até Feature/Épico/Demanda
    ├─ lê Custom.DemandaSpecTecnica e Custom.DemandaSpecNegocios da Demanda
    ├─ lê as Tasks irmãs e suas estimativas
    ├─ verifica suficiência (aponta lacuna em vez de inventar)
    └─ produz um briefing único em Markdown — sem invocar Superpowers
```

## Skill 1 — `refinar-tecnicamente`

**Quando:** na reunião técnica, sobre a `spec.md` de uma pasta `DN-<id>-<slug>/` já produzida pelo
`gerador-hu`.

**Entrada:** caminho da pasta, ou ID da Demanda quando a pasta segue a convenção de nomes já
estabelecida (`docs/specs/DN-<id>-<slug>/`).

**Fluxo:**

1. Lê `spec.md` e isola as lacunas rotuladas `Técnico` (formato `- **N3 · Técnico** — <pergunta>`,
   já produzido por `redigir-spec-demanda-azure-boards`).
2. Fecha essas lacunas por entrevista em rodadas, reaproveitando o mecanismo de rodada/fronteira de
   `entrevistar-lacunas-requisito` — adaptado para **permitir** investigação de código durante a
   entrevista, ao contrário da skill original, que a proíbe. Adiamento explícito é sempre aceito;
   nenhuma lacuna é fechada por inferência silenciosa.
3. Com as lacunas técnicas fechadas, investiga o código e escreve a abordagem técnica como seção nova
   de `spec.md`: camadas tocadas, migração quando houver, estratégia de teste. Cada afirmação cita
   `caminho:linha`, na mesma disciplina de evidência já usada no resto da spec.
4. Para cada História/Bug do backlog associado, busca Histórias/Bugs fechados recentemente no mesmo
   `AreaPath`, compara complexidade pelo mesmo critério usado para classificar lacunas como técnicas
   (o que muda em camadas, arquivos e testes) e propõe uma pontuação em Story Points. Sem análogo
   comparável, pergunta a quem está na reunião — a resposta se torna histórico para a próxima
   execução.
5. Converte `spec.md` atualizada para HTML (reaproveitando o conversor já usado por
   `publicar-backlog-demanda-azure-boards`) e apresenta o conteúdo que vai gravar em
   `Custom.DemandaSpecTecnica`. Só grava (`PATCH`) após confirmação textual explícita — a única
   escrita desta skill no Azure Boards.
6. Produz ou atualiza `backlog.md` com Story Points nas Histórias/Bugs.

**Saída:** `spec.md` com lacunas técnicas fechadas e abordagem técnica registrada; `backlog.md` com
Story Points; `Custom.DemandaSpecTecnica` atualizado na Demanda. Nenhuma criação de work item — isso
continua exclusivo de `publicar-backlog-demanda-azure-boards`.

## Skill 2 — `decompor-tasks`

**Quando:** no planning, por item, executada pelo desenvolvedor que vai executar aquele item.

**Entrada:** ID da História/Bug já publicada no Azure Boards. **Nunca** o ID de uma Task — Tasks não
existem ainda neste momento.

**Fluxo:**

1. Lê a História/Bug por `GET`: título, `Description`, critérios de aceitação, Story Points e a
   abordagem técnica (lida de `Custom.DemandaSpecTecnica`, subindo até a Demanda). Story Points é
   contexto de porte para calibrar a decomposição — **nunca é copiado para nenhuma Task**, porque o
   tipo Task não expõe esse campo no processo Agile.
2. Propõe uma decomposição em Tasks a partir da abordagem técnica já registrada. Não reabre desenho
   técnico — usa o que a skill 1 já decidiu.
3. Para cada Task proposta, busca Tasks fechadas comparáveis (mesmo `AreaPath`, título
   semanticamente próximo) com `Microsoft.VSTS.Scheduling.CompletedWork` preenchido, e propõe
   `Original Estimate`/`Remaining` a partir delas. Sem análogo, pergunta ao desenvolvedor — a resposta
   se torna histórico para a próxima Task comparável.
4. Apresenta o plano completo — Tasks, horas, cada uma atribuída ao usuário do PAT configurado — e
   exige autorização textual explícita antes de qualquer `POST`, na mesma frase de segurança do
   publicador existente, adaptada ao contexto de Task.
5. Cria as Tasks como filhas da História/Bug, com manifesto de retomada equivalente ao de
   `publicar-backlog-demanda-azure-boards`: hash do plano, registro por item criado, reconciliação
   manual obrigatória após qualquer resposta ambígua.

**Saída:** Tasks criadas sob a História/Bug, com `Original Estimate`, `Remaining` e `AssignedTo`
preenchidos. Nenhum Story Points é tocado nesta skill.

## Skill 3 — `preparar-implementacao`

**Quando:** ao começar a codar, pelo mesmo desenvolvedor.

**Entrada:** ID da História/Bug (ou de uma Task específica, quando o dev já sabe qual).

**Fluxo:**

1. Lê o work item por `GET` e sobe a hierarquia até Feature, Épico e Demanda.
2. Lê `Custom.DemandaSpecTecnica` e `Custom.DemandaSpecNegocios` da Demanda — os dois, para que o
   briefing tenha tanto a abordagem técnica quanto o contexto de negócio que a originou.
3. Lê as Tasks irmãs da História/Bug e suas estimativas.
4. Verifica suficiência: se faltar abordagem técnica, critério de aceitação ou Task estimada, aponta
   a lacuna nomeando o que falta, em vez de inventar conteúdo para completar o briefing — mesmo
   princípio do gate de prontidão do 3C no `gerador-hu`.
5. Produz um briefing único em Markdown, consolidando tudo acima.

**Saída:** um documento Markdown. Nenhuma chamada de escrita ao Azure Boards. A skill não invoca
`brainstorming` nem `writing-plans` — o desenvolvedor leva o briefing a eles, na própria sessão.

## Tratamento de erro

Reaproveita as classes já estabelecidas em `publicar-backlog-demanda-azure-boards`
(`ErroDestinoInvalido`, `ErroFalhaTransitoria`, `ErroRespostaInvalida`), com uma classe nova:

- `ErroSuficienciaInsuficiente` — levantada pela skill 3 quando a hierarquia não tem o mínimo
  necessário para montar o briefing (sem abordagem técnica registrada, por exemplo). Nunca é
  contornada por invenção de conteúdo.

Chamadas de leitura seguem o mesmo padrão de retentativa com backoff exponencial já usado em
`leitor_demanda.py` (`_ERROS_RETENTAVEIS = {408, 429, 500, 502, 503, 504}`, três tentativas).
Timeout ou resposta ambígua numa chamada de escrita (`PATCH` do campo, `POST` de Task) nunca autoriza
repetir automaticamente — mesma regra do publicador: interrompe com o manifesto bloqueado e exige
reconciliação manual.

## Dependências e pré-requisitos

- **`Custom.DemandaSpecTecnica`** — campo HTML/multilinha, criado numa página "Spec" do processo do
  Azure DevOps. Já existe (ação do usuário, anterior a este design). O tamanho suportado pelo campo
  ainda não foi validado contra o volume real de uma spec com abordagem técnica completa; primeira
  execução real da skill 1 deve confirmar isso.
- **`Custom.DemandaSpecNegocios`** — já existe, simétrico, mas esta spec não o escreve; só o lê, na
  skill 3.
- **PAT do Azure DevOps** — mesmo mecanismo de configuração do `gerador-hu` (`.env`, nunca versionado,
  entrada interativa sem eco quando ausente). O usuário do PAT é quem recebe `AssignedTo` nas Tasks
  criadas pela skill 2.
- **Histórico de Tasks e Histórias fechadas** — ambas as estimativas (Story Points e horas) dependem
  de itens fechados comparáveis existirem no projeto. No início da adoção, sem histórico suficiente,
  as duas skills perguntam ao humano na conversa, e essa resposta constrói o histórico que as
  próximas execuções vão consultar.
- **`gerador-hu` publicado e acessível** — a spec técnica desta skill 1 assume que `spec.md` já existe
  na convenção de pastas `docs/specs/DN-<id>-<slug>/` estabelecida lá.

## Testes

Mesmo estilo do `publicar-backlog-demanda-azure-boards`: um módulo de teste por responsabilidade
(configuração, cliente Azure DevOps, leitura de work item, ancoragem de estimativa, manifesto,
autorização, CLI, integração de skill), cobrindo:

- Recusa de leitura quando o work item não existe, é de tipo errado, ou pertence a outro projeto.
- Ancoragem de estimativa: com análogo disponível, sem análogo (pergunta ao humano), com análogo cujo
  `CompletedWork`/Story Points está ausente (tratado como sem análogo).
- Confirmação ausente, vaga, incorreta ou vinculada a outro hash resulta em zero chamadas de escrita,
  tanto para o `PATCH` do campo quanto para o `POST` de Task.
- Manifesto: retomada só sob o mesmo hash; reconciliação pendente bloqueia nova escrita.
- Skill 3: `ErroSuficienciaInsuficiente` levantado e nomeando exatamente o que falta, para cada
  combinação de ausência (spec técnica, critério de aceitação, Task estimada).
- Skill 2: Story Points da História nunca aparece em nenhum payload de criação de Task.

## Alternativas consideradas

**Publicador próprio, sem depender de `gerador-hu`.** Rejeitada: duplicaria o cliente Azure DevOps, o
manifesto e a política de reconciliação já endurecidos e testados em
`publicar-backlog-demanda-azure-boards`, arriscando os dois divergirem em silêncio sobre o mesmo tipo
de work item. O invariante de escrita por tipo elimina esse risco sem duplicar código de publicação de
Épico/Feature/História.

**Estimativa (Story Points e horas) decidida só pelo LLM, sem ancoragem.** Rejeitada explicitamente
pelo usuário: um número sem base em histórico ou confirmação humana seria a mesma invenção que o
`gerador-hu` já proíbe para outros campos (Area Path, prioridade, responsável).

**Tasks e horas geradas no refinamento técnico, junto com Story Points.** Rejeitada: quebraria o
cálculo de capacidade nativo do Azure Boards, que depende de `Remaining Work` atribuído a uma pessoa
específica — Tasks nascidas no refinamento não têm executor definido ainda.

**Anexo de arquivo em vez de campo customizado para a spec técnica.** Considerada e descartada pelo
usuário em favor do campo customizado, apesar do anexo não exigir customização de processo nem ter
risco de limite de tamanho. O campo já foi criado antes deste desenho; a spec registra o risco de
tamanho como suposição a validar, não como razão para reverter a escolha.
