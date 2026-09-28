# Refinamento e Planejamento Técnico

Skills para a equipe técnica: refinamento técnico de uma Demanda já publicada pelo
[`gerador-hu`](https://github.com/pedroct/gerador-de-hu), planejamento de capacidade por pessoa e
preparação do material de implementação.

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

- **Refinamento técnico:** fecha as lacunas técnicas de `spec.md`, investiga o código, registra a
  abordagem técnica e estima Story Points ancorados em Histórias/Bugs fechados comparáveis. Grava a
  spec atualizada em `Custom.DemandaSpecTecnica`, na Demanda de Negócio.
- **Decomposição em Tasks:** no planning, por item, pelo desenvolvedor que vai executá-lo. Decompõe
  a História/Bug em Tasks a partir da abordagem já registrada, estima horas ancoradas em Tasks
  fechadas comparáveis e cria as Tasks atribuídas a si.
- **Preparação da implementação:** ao começar a codar, monta um briefing único — work item,
  hierarquia, spec técnica e de negócio, Tasks e estimativas — para o desenvolvedor levar ao
  Superpowers (`brainstorming` → `writing-plans`).

## Invariante de escrita

Nenhum tipo de work item é escrito por dois repositórios. `gerador-hu` é o único que cria Epic,
Feature, User Story e Bug. Este repositório é o único que cria Task e o único que escreve em
`Custom.DemandaSpecTecnica`.

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

## Pré-requisitos

- `gerador-hu` publicado e configurado, com uma spec (`spec.md`) já gerada para a Demanda.
- Os campos customizados `Custom.DemandaSpecTecnica` e `Custom.DemandaSpecNegocios`, criados no
  processo do Azure DevOps (página "Spec" da Demanda de Negócio).
- Um PAT do Azure DevOps com permissão de leitura e escrita em work items.
