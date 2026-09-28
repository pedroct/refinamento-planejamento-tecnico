---
name: decompor-tasks
description: Use no planning, por item, pelo desenvolvedor que vai executá-lo, para decompor uma História/Bug já publicada em Tasks estimadas em horas e atribuídas a ele.
---

# Decompor uma História/Bug em Tasks

## Objetivo

Decompor uma História/Bug já publicada no Azure Boards em Tasks, a partir da abordagem técnica já
registrada em `Custom.DemandaSpecTecnica`, estimar cada Task em horas ancoradas em Tasks fechadas
comparáveis, atribuí-las a quem vai executar e criá-las sob autorização textual explícita.

## Fluxo obrigatório

1. Receba o ID da História/Bug — nunca de uma Task, que ainda não existe neste momento.
2. Leia a História/Bug e suba até a Demanda para ler `Custom.DemandaSpecTecnica`. Use o Story Points
   da História só como contexto de porte; nunca o copie para nenhuma Task.
3. Proponha a decomposição em Tasks a partir da abordagem técnica já registrada — não reabra desenho
   técnico.
4. Para cada Task proposta, rode `decompor-tasks sugerir-horas --area-path <Area Path da História>
   --tipo-task Task --titulo "<título da Task proposta>"`. Quando a sugestão vier sem base
   (`horas: null`), pergunte a estimativa ao desenvolvedor — a resposta se torna histórico para a
   próxima Task comparável.
5. Monte o plano (`historia_id` e a lista de Tasks com título, `original_estimate`, `remaining` e
   `assigned_to` = usuário do PAT) e grave num arquivo JSON temporário.
6. Rode `decompor-tasks criar <plano.json> --manifesto <caminho>`. A CLI mostra o plano completo e
   pede a frase de autorização; só cria (`POST`) as Tasks que a resposta exata autorizar. Uma
   reexecução após falha parcial retoma do manifesto sem duplicar.

## O que esta skill nunca faz

- Não cria Épico, Feature, História ou Bug.
- Não grava nem lê `Custom.DemandaSpecTecnica` — só o `refinar-tecnicamente` escreve; esta skill lê.
- Não copia Story Points para Task — esse campo não existe em Task no processo Agile.
- Não inventa horas sem ancoragem em histórico ou confirmação humana explícita.
