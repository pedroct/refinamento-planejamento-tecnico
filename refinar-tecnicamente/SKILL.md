---
name: refinar-tecnicamente
description: Use na reunião técnica de refinamento, sobre a spec.md de uma Demanda já publicada no Azure Boards, para fechar as lacunas técnicas, registrar a abordagem e estimar Story Points.
---

# Refinar tecnicamente uma Demanda já publicada

## Objetivo

Fechar as lacunas rotuladas `Técnico` de `spec.md`, investigar o código e registrar a abordagem
técnica como seção nova da spec, estimar Story Points de cada História/Bug do backlog associado —
ancorado em itens fechados comparáveis, nunca inventado — e prender a spec atualizada à Demanda de
Negócio via `Custom.DemandaSpecTecnica`.

## Fluxo obrigatório

1. Receba o caminho da pasta `DN-<id>-<slug>/` (ou o ID da Demanda, resolvendo a pasta pela
   convenção de nomes do `gerador-hu`) e o ID da Demanda no Azure Boards.
2. Rode `ler-lacunas spec.md` para isolar as lacunas técnicas (e as sem rótulo, que entram em toda
   rodada). Conduza a entrevista em rodadas, no mesmo mecanismo de fronteira do
   `entrevistar-lacunas-requisito`: pergunte os itens que não dependem de resposta ainda em aberto,
   aceite adiamento explícito, nunca feche uma lacuna por inferência silenciosa.
3. Com as lacunas técnicas fechadas, investigue o código-fonte e escreva a seção
   `## Abordagem técnica` em `spec.md`: camadas tocadas, migração quando houver, estratégia de teste.
   Cite `caminho:linha` para cada afirmação, na mesma disciplina do resto da spec.
4. Para cada História/Bug do `backlog.md` associado, rode `sugerir-story-points --area-path <Area
   Path da Demanda> --tipo "User Story" --tipo Bug`. Quando a sugestão vier com `pontos: null`, não
   prossiga sozinho — pergunte a pontuação a quem está na reunião e registre a resposta no backlog;
   ela se torna histórico para a próxima execução.
5. Grave os Story Points sugeridos ou confirmados em `backlog.md`, um por História/Bug.
6. Rode `gravar-spec-tecnica --demanda <id> --spec spec.md`. Mostre a `spec.md` completa antes de
   confirmar. A CLI pede a frase de autorização; ela só grava (`PATCH`) se a resposta for
   **exatamente** igual — variação de caixa, acentuação ou Demanda errada é recusada sem chamada
   alguma ao Azure Boards.

## O que esta skill nunca faz

- Não cria Épico, Feature, História ou Bug — isso é exclusivo de
  `publicar-backlog-demanda-azure-boards`, no `gerador-hu`.
- Não decompõe em Tasks nem estima horas — isso é `decompor-tasks`, no momento do planning, pelo
  desenvolvedor que vai executar.
- Não inventa Story Points sem ancoragem em histórico ou confirmação humana explícita.
