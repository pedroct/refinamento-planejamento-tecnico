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

## Instalação e atualização

As skills seguem o formato aberto (`SKILL.md` por pasta) suportado pelo [`npx skills`](https://skills.sh), que instala diretamente a partir deste repositório do GitHub — não é necessário publicar em nenhum registro.

```bash
# listar as skills disponíveis
npx skills add pedroct/refinamento-planejamento-tecnico --list

# instalar todas, no projeto atual, para Claude Code
npx skills add pedroct/refinamento-planejamento-tecnico --all -a claude-code

# instalar só uma
npx skills add pedroct/refinamento-planejamento-tecnico --skill decompor-tasks -a claude-code
```

A instalação pode ser por projeto (padrão) ou global:

| Escopo | Flag | Onde fica |
|---|---|---|
| Projeto | *(nenhuma)* | `./<agente>/skills/` — versionado com o projeto, compartilhado com o time |
| Global | `-g` | `~/<agente>/skills/` — disponível em qualquer projeto da máquina |

```bash
# instalar globalmente, disponível em todos os projetos
npx skills add pedroct/refinamento-planejamento-tecnico --all -a claude-code -g
```

### Atualização

```bash
# atualizar todas as skills instaladas neste projeto
npx skills update -y

# atualizar só uma
npx skills update refinar-tecnicamente -y

# escopo explícito, quando houver instalação nos dois lugares
npx skills update -p -y   # só as do projeto
npx skills update -g -y   # só as globais

# ver o que está instalado e de onde veio
npx skills ls
```

O `add` grava um `skills-lock.json` na raiz do projeto, com a origem e um hash de cada skill. É
esse arquivo que o `update` lê para saber de onde re-buscar cada skill — por isso o comando não
repete o nome do repositório. Ele também **não** aceita `-a/--agent`: descobre sozinho para quais
agentes a skill está instalada e atualiza todos.

Uma ressalva: o `update` informa `✓ Updated` mesmo quando não havia nada novo a trazer. A mensagem
confirma que a skill foi ressincronizada com a origem, não que o conteúdo mudou. Para saber se algo
de fato mudou, compare o `computedHash` no `skills-lock.json` antes e depois.

### `update` não traz skills novas

**O `update` só ressincroniza o que já está no `skills-lock.json`.** Uma skill nova neste
repositório não é instalada nem mencionada: o comando termina com `✓ Updated N skill(s)` e o
projeto continua sem ela. Não há aviso.

O comando que traz skills novas é o `add` com curinga:

```bash
npx skills add pedroct/refinamento-planejamento-tecnico --skill '*' -a '*' -y
```

Ele é idempotente: repõe o que falta, preserva o que já está instalado e mantém o layout canônico.
Use-o como sincronização periódica, não o `update`.

Duas armadilhas que motivam a forma exata acima:

| Erro | O que acontece |
|---|---|
| `--skill nome1,nome2` | nomes separados por vírgula **não instalam nada**; o comando apenas lista as skills disponíveis |
| `-a claude-code` em vez de `-a '*'` | instala como **cópia** dentro de `.claude/skills/`, em vez do diretório canônico `.agents/skills/` com symlinks por agente. A cópia fica invisível para os outros agentes e não acompanha as atualizações |

Para desenvolver num pacote isoladamente:

```bash
cd decompor-tasks
uv sync
uv run pytest
```

## Configuração

Cada skill é um pacote isolado e lê suas próprias variáveis de ambiente — não existe configuração
compartilhada na raiz do projeto (o `.env` da raiz é só para `SONAR_TOKEN`, usado pelo scan local,
ver [Qualidade de código](#qualidade-de-código)).

### 1. Gerar o PAT do Azure DevOps

Em `https://dev.azure.com/<sua-organização>/_usage/token`, crie um Personal Access Token com escopo
**Work Items → Read & Write**. É o mesmo PAT que pode ser reaproveitado nas três skills, desde que
tenha acesso ao projeto usado por todas.

### 2. Preencher o `.env` de cada skill

Copie o `.env.example` de cada skill para `.env` na mesma pasta e preencha:

```bash
cp refinar-tecnicamente/.env.example refinar-tecnicamente/.env
cp decompor-tasks/.env.example decompor-tasks/.env
cp preparar-implementacao/.env.example preparar-implementacao/.env
```

| Variável | `refinar-tecnicamente` | `decompor-tasks` | `preparar-implementacao` |
|---|---|---|---|
| `AZURE_DEVOPS_ORGANIZACAO` | ✅ | ✅ | ✅ |
| `AZURE_DEVOPS_PROJETO` | ✅ | ✅ | ✅ |
| `AZURE_DEVOPS_TOKEN` | ✅ | ✅ | ✅ |
| `AZURE_DEVOPS_CAMPO_SPEC_TECNICA` | ✅ (`Custom.DemandaSpecTecnica`) | — | ✅ (`Custom.DemandaSpecTecnica`) |
| `AZURE_DEVOPS_CAMPO_SPEC_NEGOCIOS` | — | — | ✅ (`Custom.DemandaSpecNegocios`) |
| `AZURE_DEVOPS_TIPO_TASK` | — | ✅ (`Task`) | — |
| `AZURE_DEVOPS_TIPO_DEMANDA` | — | — | ✅ (`Demanda de Negócio`) |

O `.env.example` já vem com os valores padrão preenchidos para os campos e tipos — normalmente só
`ORGANIZACAO`, `PROJETO` e `TOKEN` ficam em branco para você completar. O `.env` nunca deve ser
versionado (já está no `.gitignore`).

### 3. Exportar as variáveis antes de rodar os comandos

**Nenhuma das skills lê o `.env` automaticamente.** O `.env` é só um lugar para guardar os valores —
quem os coloca no ambiente é você, antes de chamar o comando:

```bash
cd refinar-tecnicamente
uv sync   # só na primeira vez, ou após atualizar dependências
export $(grep -v '^#' .env | xargs)
uv run refinar-tecnicamente sugerir-story-points --area-path "Projeto\Time A" --tipo "User Story"
```

Isso vale para as três skills, sempre a partir da pasta da skill correspondente (cada uma tem seu
próprio `.env`, então exportar o de uma não configura as outras).

## Qualidade de código

Cada pacote tem sua própria suíte, isolada: `uv run --directory <pacote> pytest`, mais `mypy` e
`ruff` (strict, configurados no `pyproject.toml` de cada skill). Não há teste combinado na raiz —
os três pacotes não compartilham ambiente nem `sys.path`.

O scan local do SonarQube cobre as três skills numa única análise:

```bash
cp .env.example .env   # preencha SONAR_TOKEN, uma vez
bash scripts/run-sonar-local.sh
```

O script gera o `coverage.xml` de cada pacote separadamente (`uv run --directory <pacote> pytest
--cov`) antes de rodar o `pysonar` — rodar tudo num único `pytest` combinado esconderia a cobertura
real de cada skill, já que cada uma tem seu próprio ambiente. `cliente_azure_devops.py` é vendorizado
à parte em cada skill (nenhuma importa módulo de skill irmã, de propósito — ver o docstring do
próprio arquivo), então essa duplicação entre elas é excluída do CPD (`sonar.cpd.exclusions` em
`sonar-project.properties`): é arquitetural, não um defeito a corrigir.

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
