---
name: preparar-implementacao
description: Use ao começar a codar uma História/Bug já refinada e decomposta, para montar o briefing que você leva ao superpowers:brainstorming e superpowers:writing-plans.
---

# Preparar o material de implementação

## Objetivo

Ler o work item, subir até a Demanda, reunir a abordagem técnica (`Custom.DemandaSpecTecnica`), o
contexto de negócio (`Custom.DemandaSpecNegocios`) e as Tasks já estimadas, verificar se há o mínimo
necessário e montar um briefing único em Markdown. Esta skill nunca escreve no Azure Boards e nunca
invoca `brainstorming` nem `writing-plans` — você leva o briefing a eles, na sua própria sessão.

## Fluxo obrigatório

1. Receba o ID da História/Bug (ou de uma Task específica, se você já souber qual).
2. Rode `preparar-implementacao montar <id>`.
3. Se faltar spec técnica, critério de aceitação ou alguma Task sem estimativa, a CLI recusa montar o
   briefing e nomeia exatamente o que falta — volte para `refinar-tecnicamente` ou `decompor-tasks`
   antes de prosseguir. Nunca preencha a lacuna você mesmo para contornar o aviso.
4. Com o briefing pronto, leve-o ao `superpowers:brainstorming` para desenhar a abordagem e depois ao
   `superpowers:writing-plans` para gerar o plano de implementação.

## O que esta skill nunca faz

- Não escreve em nenhum campo nem cria nenhum work item.
- Não invoca `brainstorming` nem `writing-plans` diretamente.
- Não preenche uma lacuna de suficiência com conteúdo inventado.
