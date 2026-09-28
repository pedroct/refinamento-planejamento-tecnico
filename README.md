# Refinamento e Planejamento Técnico

Três skills para a equipe técnica, usadas em momentos diferentes do ciclo de uma Demanda já publicada
no Azure Boards pelo [`gerador-hu`](https://github.com/pedroct/gerador-de-hu): refinamento técnico na
reunião com o time, decomposição em Tasks no planning, e preparação do material de implementação ao
começar a codar.

## O que o projeto faz

```text
gerador-hu (PO + negócio)
  Demanda → spec.md / negocio.md → backlog.md
                                     └─ publicar-backlog-demanda-azure-boards
                                        └─ Épico → Feature → História/Bug

refinamento-planejamento-tecnico
  refinar-tecnicamente        (reunião técnica)
    └─ fecha lacunas técnicas, registra abordagem, estima Story Points
       └─ grava Custom.DemandaSpecTecnica na Demanda

  decompor-tasks               (planning, por item, por quem executa)
    └─ decompõe em Tasks, estima horas, atribui a si, cria as Tasks

  preparar-implementacao       (ao começar a codar, mesmo dev)
    └─ monta o briefing → dev leva a superpowers:brainstorming e writing-plans
```

Cada skill é um pacote Python independente, instalável separadamente, que vendoriza sua própria cópia
de um cliente HTTP mínimo para o Azure Boards. Nenhuma importa da outra.

### `refinar-tecnicamente`

Na reunião técnica, sobre a `spec.md` de uma Demanda já publicada:

- fecha as lacunas rotuladas `Técnico` por entrevista, em rodadas;
- investiga o código e registra a abordagem técnica como seção nova de `spec.md`;
- estima Story Points de cada História/Bug, ancorado em itens fechados comparáveis no mesmo Area
  Path — sem análogo, pergunta a quem está na reunião;
- converte a spec atualizada para HTML e grava em `Custom.DemandaSpecTecnica`, só após confirmação
  textual exata.

```bash
refinar-tecnicamente ler-lacunas caminho/para/spec.md
refinar-tecnicamente sugerir-story-points --area-path "Projeto\\Time A" --tipo "User Story" --tipo Bug
refinar-tecnicamente gravar-spec-tecnica --demanda 13959 --spec caminho/para/spec.md
```

### `decompor-tasks`

No planning, por item, pelo desenvolvedor que vai executá-lo:

- decompõe a História/Bug em Tasks a partir da abordagem técnica já registrada — nunca reabre o
  desenho técnico, e nunca copia Story Points para a Task;
- estima horas (Original Estimate/Remaining) ancoradas em Tasks fechadas comparáveis;
- cria as Tasks como filhas da História/Bug, atribuídas ao usuário do PAT, sob confirmação textual
  exata e manifesto de retomada — uma reexecução após falha parcial nunca duplica Tasks.

```bash
decompor-tasks sugerir-horas --area-path "Projeto\\Time A" --tipo-task Task --titulo "Criar endpoint"
decompor-tasks criar plano.json --manifesto historia-100.json
```

### `preparar-implementacao`

Ao começar a codar, pelo mesmo desenvolvedor:

- lê a História/Bug e sobe a hierarquia até a Demanda;
- lê `Custom.DemandaSpecTecnica` e `Custom.DemandaSpecNegocios`, e as Tasks irmãs com suas estimativas;
- verifica suficiência — se faltar abordagem técnica, critério de aceitação ou alguma Task sem
  estimativa, recusa montar o briefing e nomeia exatamente o que falta;
- monta um briefing único em Markdown, sem nenhuma escrita no Azure Boards e sem invocar
  `brainstorming`/`writing-plans` — o desenvolvedor leva o briefing a eles, na própria sessão.

```bash
preparar-implementacao montar 100
```

## Invariantes

- **Nenhum tipo de work item é escrito por dois repositórios.** `gerador-hu` é o único que cria Epic,
  Feature, User Story e Bug. Este repositório é o único que cria Task e o único que escreve em
  `Custom.DemandaSpecTecnica`.
- **Story Points nunca é copiado para uma Task.** É lido da História/Bug só como contexto de porte —
  Task não expõe esse campo no processo Agile.
- **Nenhuma estimativa é inventada.** Sem item fechado comparável, a skill pergunta a quem está na
  conversa; a resposta se torna histórico para a próxima execução.
- **Toda escrita exige confirmação textual explícita** — variação de caixa, acentuação, espaço extra
  ou frase parecida (não idêntica) é recusada, sem nenhuma chamada ao Azure Boards.
- **Uma escrita nunca se repete sozinha.** Timeout ou resposta ambígua interrompe com estado bloqueado
  e exige reconciliação manual — nunca invenção nem repetição automática.

## Instalação

```bash
# listar as skills disponíveis
npx skills add pedroct/refinamento-planejamento-tecnico --list

# instalar todas, no projeto atual, para Claude Code
npx skills add pedroct/refinamento-planejamento-tecnico --all -a claude-code

# instalar só uma
npx skills add pedroct/refinamento-planejamento-tecnico --skill decompor-tasks -a claude-code
```

Cada skill tem seu próprio `.env.example` — copie para `.env` e preencha organização, projeto e
token do Azure DevOps antes de usar. O token nunca deve ser versionado.

Para desenvolver num pacote isoladamente:

```bash
cd decompor-tasks
uv sync
uv run pytest
```

## Pré-requisitos

- `gerador-hu` publicado e configurado, com uma spec (`spec.md`) já gerada para a Demanda.
- Os campos customizados `Custom.DemandaSpecTecnica` e `Custom.DemandaSpecNegocios`, criados no
  processo do Azure DevOps (página "Spec" da Demanda de Negócio).
- Um PAT do Azure DevOps com permissão de leitura e escrita em work items.

## Estado do projeto

As três skills estão implementadas e testadas (119 testes no total, um pacote por skill). Lacunas
conhecidas em relação à spec original, ainda não implementadas:

- `preparar-implementacao` só aceita ID de História/Bug — não aceita ID de Task diretamente.
- `decompor-tasks` não tem comando de CLI para subir até a Demanda nem para consultar o usuário
  autenticado do PAT (`usuario_autenticado()` existe no cliente, mas não é exposto).
- Nenhum pacote lê `.env` automaticamente nem pede o PAT interativamente sem eco — a configuração
  hoje depende de variáveis de ambiente já exportadas no shell.
- A sugestão de Story Points não compara item a item — devolve a mesma mediana do Area Path para
  toda História/Bug do backlog.
