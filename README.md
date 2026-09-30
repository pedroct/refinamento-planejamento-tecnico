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
    └─ resolve spec.md/backlog.md só pelo ID da Demanda (pasta local ou anexo remoto)
       └─ uma sessão por perfil (fullstack ou mobile): fecha só as lacunas do perfil
          e escreve só a subseção da abordagem técnica do perfil
          └─ estima Story Points
             └─ grava Custom.DemandaSpecTecnica e reanexa spec.md/backlog.md na Demanda

  decompor-tasks               (planning, por item, por quem executa)
    └─ decompõe em Tasks, estima horas, atribui a si, cria as Tasks

  preparar-implementacao       (ao começar a codar, mesmo dev)
    └─ monta o briefing → dev leva a superpowers:brainstorming e writing-plans
```

Cada skill é um pacote Python independente, instalável separadamente, que vendoriza sua própria cópia
de um cliente HTTP mínimo para o Azure Boards. Nenhuma importa da outra.

## Como usar na prática

Você não roda os comandos à mão: chama a skill no seu agente (Claude Code, Cursor ou Codex), passando
o **ID** do work item e, quando a skill pede, o **parâmetro**, e o agente conduz o resto — roda as
CLIs, faz as perguntas e só grava depois da sua confirmação. No Claude Code a chamada é
`/nome-da-skill <argumentos>`; nos outros agentes, escreva em linguagem natural ("use a skill
`decompor-tasks` na História 4321"). Informar o ID e o parâmetro já na chamada evita que o agente
pergunte de novo.

| Skill | Qual ID passar | Parâmetro | Chamada |
|---|---|---|---|
| `refinar-tecnicamente` | **Demanda de Negócio** | perfil: `fullstack` ou `mobile` | `/refinar-tecnicamente 13959 fullstack` |
| `decompor-tasks` | **História ou Bug** (nunca Task) | nenhum | `/decompor-tasks 4321` |
| `preparar-implementacao` | **História, Bug ou Task** | nenhum | `/preparar-implementacao 4321` |

Antes da primeira vez: instale as skills, preencha o `.env` de cada uma e rode `uv sync` (ver
[Instalação e atualização](#instalação-e-atualização) e [Configuração](#configuração)). O agente
exporta o `.env` da skill sozinho a cada sessão.

### `refinar-tecnicamente` — ID da Demanda + perfil

```text
/refinar-tecnicamente 13959 fullstack
/refinar-tecnicamente 13959 mobile
```

O que o agente faz, em ordem:

1. **Resolve a spec pelo ID.** Usa `docs/specs/DN-13959-*/` se existir no repositório aberto; senão
   baixa `spec.md` e `backlog.md` do anexo mais recente da Demanda. Se a Demanda não tem spec
   publicada, para e avisa — não pede caminho.
2. **Confirma o perfil.** Se você não escreveu `fullstack` ou `mobile` na chamada, pergunta. O perfil
   decide quais lacunas você vê e qual subseção da abordagem você escreve. Se a Demanda passa pelos dois
   perfis, são duas sessões separadas — uma chamada para cada.
3. **Entrevista só as lacunas técnicas do seu perfil**, em rodadas. Você responde ou adia; nada é
   fechado por inferência.
4. **Baixa a versão remota** antes de escrever, para preservar a subseção que o outro perfil possa ter
   publicado.
5. **Investiga o código e escreve só a sua subseção** (`### Escopo Fullstack (API/Web)` ou
   `### Escopo Mobile`) em `## Abordagem técnica`, citando `caminho:linha`.
6. **Sugere Story Points** de cada História/Bug com base em itens fechados do mesmo Area Path. Sem
   base, pergunta a você — nunca inventa.
7. **Mostra a `spec.md` completa e pede a frase de autorização.** Só depois grava em
   `Custom.DemandaSpecTecnica` e reanexa `spec.md`/`backlog.md` na Demanda. Copie a frase
   **exatamente**; qualquer variação é recusada sem tocar no Azure Boards.

### `decompor-tasks` — ID da História ou Bug

```text
/decompor-tasks 4321
```

1. Lê a História/Bug 4321, sobe até a Demanda e lê a abordagem técnica já registrada. **Se a
   Demanda ainda não passou pelo `refinar-tecnicamente`, não há abordagem para decompor** — refine
   primeiro.
2. Propõe a lista de Tasks a partir da abordagem. Você ajusta, remove ou acrescenta.
3. Para cada Task, busca horas em Tasks fechadas comparáveis. Sem base, pergunta a estimativa a você.
4. Monta o plano, mostra completo e pede a frase de autorização. Só então cria as Tasks como filhas
   da História/Bug, atribuídas a você (o usuário do PAT).

Se a criação falhar no meio, chame a skill de novo: ela retoma do manifesto e não duplica Tasks. Se
uma Task ficar marcada "em andamento" por timeout, a skill recusa continuar até você conferir no
Azure Boards se ela foi criada.

### `preparar-implementacao` — ID da História, Bug ou Task

```text
/preparar-implementacao 4321
```

1. Lê o item, sobe até a Demanda, lê a abordagem técnica e as Tasks irmãs com suas estimativas. Se
   você passar o ID de uma Task, ela sobe sozinha até a História/Bug pai e avisa no topo do briefing.
2. Verifica o mínimo: abordagem técnica, critério de aceitação e todas as Tasks estimadas. Se faltar
   algo, **recusa montar o briefing** e diz exatamente o quê — volte para `refinar-tecnicamente` ou
   `decompor-tasks`.
3. Monta o briefing em Markdown. Não escreve nada no Azure Boards.
4. Você leva o briefing ao `superpowers:brainstorming` e depois ao `superpowers:writing-plans` na
   mesma sessão.

### Ordem de uso

`refinar-tecnicamente` (Demanda, uma vez por perfil) → `decompor-tasks` (cada História/Bug, por quem
vai executar) → `preparar-implementacao` (ao começar a codar). Cada skill recusa quando falta o que a
anterior produz.

## Referência das CLIs

Esta seção descreve os comandos que o agente roda por baixo. Só precisa dela para rodar uma etapa à
mão ou diagnosticar um erro.

### Como rodar os comandos abaixo

Não há binário instalado globalmente — cada skill roda dentro do seu próprio ambiente `uv`. Padrão
para qualquer comando, de qualquer uma das três skills, a partir da raiz do projeto:

```bash
export $(grep -v '^#' <pasta-da-skill>/.env | xargs)   # uma vez por sessão de shell — ver Configuração
uv run --directory <pasta-da-skill> <comando> <argumentos>
```

`--directory` muda o diretório de trabalho do comando para dentro da pasta da skill — por isso todo
argumento de arquivo (`spec.md`, `plano.json`, manifesto) precisa ser **caminho absoluto**; um
caminho relativo seria resolvido dentro da pasta da skill, não do seu projeto. Os blocos abaixo já
seguem esse padrão; troque só os caminhos e valores pelos da sua Demanda.

### `refinar-tecnicamente`

Na reunião técnica, sobre a `spec.md` de uma Demanda já publicada:

- resolve `spec.md`/`backlog.md` só pelo ID da Demanda — usa a pasta local
  `docs/specs/DN-<id>-<slug>/` quando existe, ou baixa o anexo mais recente da própria Demanda e
  materializa a pasta, sem nunca pedir caminho manualmente;
- pergunta o **perfil** de quem conduz a sessão — `fullstack` (backend + frontend web) ou `mobile` —
  porque uma Demanda pode passar por duas sessões, uma por perfil, conduzidas por pessoas diferentes;
- fecha por entrevista, em rodadas, as lacunas rotuladas `Técnico` **do próprio perfil**. Cada lacuna
  é classificada pelo repositório dos caminhos `repo/arquivo` que cita (nome do repositório com
  `mobile` = mobile); lacuna sem caminho, ou que cita os dois perfis, entra nas duas sessões — a
  heurística só erra para o lado de mostrar a pergunta a mais, nunca de escondê-la;
- investiga o código e registra a abordagem técnica em `## Abordagem técnica` de `spec.md`, com uma
  subseção por perfil (`### Escopo Fullstack (API/Web)` e `### Escopo Mobile`). Cada sessão escreve
  **só a sua**: antes de escrever, baixa a versão remota mais recente e copia intacta a subseção do
  outro perfil, para uma sessão nunca apagar o trabalho da outra;
- estima Story Points de cada História/Bug, ancorado em itens fechados comparáveis no mesmo Area
  Path — sem análogo, pergunta a quem está na reunião;
- grava a spec atualizada (Markdown, sem conversão — o campo já é Markdown nativo no Azure Boards) em
  `Custom.DemandaSpecTecnica`, só após confirmação textual exata — e, na mesma operação, reanexa
  `spec.md` (e `backlog.md`, se houver) à Demanda,
  para a próxima pessoa que rodar `resolver-spec` recuperar a versão mais recente.

```bash
export $(grep -v '^#' refinar-tecnicamente/.env | xargs)
uv run --directory refinar-tecnicamente refinar-tecnicamente resolver-spec \
  --demanda 13959 --raiz /caminho/absoluto/do/repositorio
uv run --directory refinar-tecnicamente refinar-tecnicamente resolver-spec \
  --demanda 13959 --raiz /caminho/absoluto/do/repositorio --forcar-remoto
uv run --directory refinar-tecnicamente refinar-tecnicamente ler-lacunas \
  /caminho/absoluto/para/spec.md --perfil mobile
uv run --directory refinar-tecnicamente refinar-tecnicamente sugerir-story-points \
  --area-path "Projeto\\Time A" --tipo "User Story" --tipo Bug
uv run --directory refinar-tecnicamente refinar-tecnicamente gravar-spec-tecnica \
  --demanda 13959 --spec /caminho/absoluto/para/spec.md --backlog /caminho/absoluto/para/backlog.md
```

Detalhes dos comandos:

- `resolver-spec` sozinho devolve a pasta local quando ela existe e **nunca baixa nada**. Com
  `--forcar-remoto`, baixa o anexo mais recente para uma pasta irmã `DN-<id>-<slug>.remoto/` sem
  tocar na local (o caminho sai em `stdout`; sem anexo, recusa). É como uma sessão lê o que o outro
  perfil publicou. A pasta `.remoto` herda o nome da local e está no `.gitignore`
  (`docs/specs/*.remoto/`).
- `ler-lacunas --perfil {fullstack,mobile}` filtra as lacunas técnicas pelo perfil; sem a flag, devolve
  todas, como antes. Qualquer outro valor é recusado pelo `argparse` antes de ler o arquivo.
- `gravar-spec-tecnica --backlog` é opcional — sem ele, o anexo remoto de `backlog.md` não é
  atualizado e os Story Points gravados ficam só na cópia local.

### `decompor-tasks`

No planning, por item, pelo desenvolvedor que vai executá-lo:

- decompõe a História/Bug em Tasks a partir da abordagem técnica já registrada — nunca reabre o
  desenho técnico, e nunca copia Story Points para a Task;
- estima horas (Original Estimate/Remaining) ancoradas em Tasks fechadas comparáveis;
- cria as Tasks como filhas da História/Bug, atribuídas ao usuário do PAT, sob confirmação textual
  exata e manifesto de retomada — uma reexecução após falha parcial nunca duplica Tasks.

```bash
export $(grep -v '^#' decompor-tasks/.env | xargs)
uv run --directory decompor-tasks decompor-tasks sugerir-horas \
  --area-path "Projeto\\Time A" --tipo-task Task --titulo "Criar endpoint"
uv run --directory decompor-tasks decompor-tasks criar \
  /caminho/absoluto/plano.json --manifesto /caminho/absoluto/historia-100.json
```

### `preparar-implementacao`

Ao começar a codar, pelo mesmo desenvolvedor:

- aceita o ID da História/Bug **ou de uma Task específica** — se for uma Task, sobe até a
  História/Bug pai sozinha (é dela que vêm as Tasks irmãs e o critério de aceitação) e nomeia
  essa troca no topo do briefing;
- lê a História/Bug e sobe a hierarquia até a Demanda;
- lê `Custom.DemandaSpecTecnica` e as Tasks irmãs com suas estimativas;
- verifica suficiência — se faltar abordagem técnica, critério de aceitação ou alguma Task sem
  estimativa, recusa montar o briefing e nomeia exatamente o que falta;
- monta um briefing único em Markdown, sem nenhuma escrita no Azure Boards e sem invocar
  `brainstorming`/`writing-plans` — o desenvolvedor leva o briefing a eles, na própria sessão.

```bash
export $(grep -v '^#' preparar-implementacao/.env | xargs)
uv run --directory preparar-implementacao preparar-implementacao montar 100
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

# instalar todas, no projeto atual, para Claude Code, Cursor e Codex — os agentes que o time usa
npx skills add pedroct/refinamento-planejamento-tecnico --all -a claude-code -a cursor -a codex

# instalar só num agente
npx skills add pedroct/refinamento-planejamento-tecnico --all -a claude-code
npx skills add pedroct/refinamento-planejamento-tecnico --all -a cursor
npx skills add pedroct/refinamento-planejamento-tecnico --all -a codex

# instalar só uma skill, num agente
npx skills add pedroct/refinamento-planejamento-tecnico --skill decompor-tasks -a claude-code
```

Sem `-a`, o comando pergunta interativamente qual(is) agente(s) instalados na máquina você quer usar —
útil quando você tem mais de um dos três configurados e quer escolher na hora, em vez de fixar no
comando.

A instalação pode ser por projeto (padrão) ou global:

| Escopo | Flag | Onde fica |
|---|---|---|
| Projeto | *(nenhuma)* | `./<agente>/skills/` — versionado com o projeto, compartilhado com o time |
| Global | `-g` | `~/<agente>/skills/` — disponível em qualquer projeto da máquina |

```bash
# instalar globalmente, disponível em todos os projetos, nos três agentes
npx skills add pedroct/refinamento-planejamento-tecnico --all -a claude-code -a cursor -a codex -g
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
Use-o como sincronização periódica, não o `update`. O script `scripts/sincronizar-skills.sh` embala
exatamente esse comando (mesmo repositório, mesmos curingas), para não depender de lembrar a forma
exata:

```bash
scripts/sincronizar-skills.sh          # escopo projeto
scripts/sincronizar-skills.sh -g       # escopo global
scripts/sincronizar-skills.sh -a claude-code -a cursor   # só nesses agentes
```

Duas armadilhas que motivam a forma exata acima (e que o script já evita):

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
| `AZURE_DEVOPS_TIPO_TASK` | — | ✅ (`Task`) | ✅ (`Task`) |
| `AZURE_DEVOPS_TIPO_DEMANDA` | — | — | ✅ (`Demanda de Negócio`) |

O `.env.example` já vem com os valores padrão preenchidos para os campos e tipos — normalmente só
`ORGANIZACAO`, `PROJETO` e `TOKEN` ficam em branco para você completar. O `.env` nunca deve ser
versionado (já está no `.gitignore`).

### 3. Exportar as variáveis antes de rodar os comandos

**Nenhuma das skills lê o `.env` automaticamente.** O `.env` é só um lugar para guardar os valores —
quem os coloca no ambiente é você, antes de chamar o comando (na primeira vez, rode também `uv sync
--directory <pasta-da-skill>`):

```bash
uv sync --directory refinar-tecnicamente   # só na primeira vez, ou após atualizar dependências
export $(grep -v '^#' refinar-tecnicamente/.env | xargs)
uv run --directory refinar-tecnicamente refinar-tecnicamente sugerir-story-points \
  --area-path "Projeto\\Time A" --tipo "User Story"
```

Isso vale para as três skills, cada uma com seu próprio `.env` — exportar o de uma não configura as
outras. Veja [Como rodar os comandos abaixo](#como-rodar-os-comandos-abaixo) para o padrão completo
usado em cada skill.

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

## Documentação de design

Specs e planos de implementação de cada mudança ficam em `docs/superpowers/specs/` e
`docs/superpowers/plans/`, com data no nome. O desenho da separação por perfil está em
`docs/superpowers/specs/2026-09-29-refinamento-por-perfil-fullstack-mobile-design.md`.

## Pré-requisitos

- `gerador-hu` publicado e configurado, com uma spec (`spec.md`) já gerada para a Demanda.
- O campo customizado `Custom.DemandaSpecTecnica`, criado no processo do Azure DevOps (página
  "Spec" da Demanda de Negócio).
- Um PAT do Azure DevOps com permissão de leitura e escrita em work items (inclui anexos —
  `resolver-spec`/`gravar-spec-tecnica` usam a Attachments API do próprio work item).

## Estado do projeto

As três skills estão implementadas e testadas (241 testes no total, um pacote por skill —
`refinar-tecnicamente` 139, `decompor-tasks` 54, `preparar-implementacao` 48; os dois primeiros em
100% de cobertura, `preparar-implementacao` em 99%, com uma única linha estruturalmente
inalcançável). Lacunas conhecidas em relação à spec original,
ainda não implementadas:

- `decompor-tasks` não tem comando de CLI para subir até a Demanda nem para consultar o usuário
  autenticado do PAT (`usuario_autenticado()` existe no cliente, mas não é exposto).
- Nenhum pacote lê `.env` automaticamente nem pede o PAT interativamente sem eco — a configuração
  hoje depende de variáveis de ambiente já exportadas no shell.
- A heurística de perfil do `refinar-tecnicamente` só reconhece repositórios cujo nome tem hífen
  (`diligencia-api`, `diligencia-mobile`) e usa "mobile" como substring do nome; caminhos fora desse
  formato não classificam e a lacuna aparece nas duas sessões.
- A sugestão de Story Points não compara item a item — devolve a mesma mediana do Area Path para
  toda História/Bug do backlog.
