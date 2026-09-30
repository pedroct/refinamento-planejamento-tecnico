---
name: refinar-tecnicamente
description: Use na reunião técnica de refinamento, sobre a spec.md de uma Demanda já publicada no Azure Boards, para fechar as lacunas técnicas, registrar a abordagem e estimar Story Points. A sessão roda por perfil (fullstack ou mobile): cada perfil trata só as suas lacunas e escreve só a sua subseção da abordagem técnica.
---

# Refinar tecnicamente uma Demanda já publicada

## Objetivo

Fechar as lacunas rotuladas `Técnico` de `spec.md`, investigar o código e registrar a abordagem
técnica como seção nova da spec — cada Demanda pode passar por duas sessões, uma por perfil (`fullstack` ou `mobile`), e cada sessão trata só as lacunas e escreve só a subseção do próprio perfil —, estimar Story Points de cada História/Bug do backlog associado —
ancorado em itens fechados comparáveis, nunca inventado — e prender a spec atualizada à Demanda de
Negócio via `Custom.DemandaSpecTecnica`.

## Fluxo obrigatório

1. Receba o ID da Demanda no Azure Boards. Rode `resolver-spec --demanda <id> --raiz <raiz do
   repositório atualmente aberto>`: ele procura `docs/specs/DN-<id>-*/` sob essa raiz e, se não
   encontrar, baixa `spec.md`/`backlog.md` do anexo mais recente da própria Demanda e materializa
   uma pasta local a partir deles. Use o caminho impresso em `stdout` nos passos seguintes. Se a
   CLI recusar (nem pasta local, nem anexo), pare e informe que a Demanda ainda não tem spec
   publicada — não peça o caminho manualmente, nem sugira rodar `gerador-hu` você mesmo.

   Antes de ler as lacunas, pergunte **qual o perfil de quem está conduzindo esta sessão**: `fullstack`
   (backend + frontend web) ou `mobile`. Cada Demanda pode passar por duas sessões separadas,
   uma por perfil, conduzidas por profissionais diferentes — a resposta desta pergunta decide o
   filtro do passo 2 e a subseção do passo 3.

2. Rode `ler-lacunas spec.md --perfil <fullstack|mobile>` para isolar as lacunas técnicas do
   próprio perfil (e as sem rótulo, que entram em toda rodada; lacunas que citam evidência dos
   dois perfis ao mesmo tempo também entram, por segurança). Conduza a entrevista em rodadas, no
   mesmo mecanismo de fronteira do `entrevistar-lacunas-requisito`: pergunte os itens que não
   dependem de resposta ainda em aberto, aceite adiamento explícito, nunca feche uma lacuna por
   inferência silenciosa.
3. Com as lacunas técnicas do próprio perfil fechadas, investigue o código-fonte e escreva **só a
   subseção do próprio perfil** dentro de `## Abordagem técnica` em `spec.md`:

   ```markdown
   ## Abordagem técnica

   ### Escopo Fullstack (API/Web)
   <camadas tocadas, migração quando houver, estratégia de teste — só repositórios não-mobile>

   ### Escopo Mobile
   <camadas tocadas, migração quando houver, estratégia de teste — só repositórios mobile>
   ```

   Antes de escrever, busque a versão remota mais recente: `resolver-spec --demanda <id> --raiz
   <raiz> --forcar-remoto`. Sem essa flag `resolver-spec` devolve a pasta local existente e nunca
   baixa nada; com ela, o anexo mais recente vai para uma pasta irmã `DN-<id>-<slug>.remoto/`,
   sem tocar na local (o caminho sai em `stdout`; sem anexo, a CLI recusa). Leia dessa cópia
   remota a subseção do outro perfil, que a sessão dele pode ter publicado em paralelo. Monte o
   `spec.md` final substituindo **só** a subseção do próprio perfil; a do outro perfil entra
   intacta, sem alteração nenhuma, copiada da cópia remota. Se a subseção do outro perfil
   ainda não existir nela (o outro perfil não publicou), mantenha o que já houver no `spec.md` local
   para ela ou deixe-a ausente — nunca a invente. Cite `caminho:linha` para cada afirmação, na
   mesma disciplina do resto da spec.
4. Para cada História/Bug do `backlog.md` associado, rode `sugerir-story-points --area-path <Area
   Path da Demanda> --tipo "User Story" --tipo Bug`. Quando a sugestão vier com `pontos: null`, não
   prossiga sozinho — pergunte a pontuação a quem está na reunião e registre a resposta no backlog;
   ela se torna histórico para a próxima execução.
5. Grave os Story Points sugeridos ou confirmados em `backlog.md`, um por História/Bug.
6. Rode `gravar-spec-tecnica --demanda <id> --spec spec.md`. Se `backlog.md` existir na pasta da
   Demanda, inclua `--backlog <caminho>/backlog.md` no mesmo comando — sem essa flag, o anexo
   remoto de `backlog.md` não é atualizado e os Story Points gravados nos passos 4-5 ficam só
   localmente. Mostre a `spec.md` completa antes de confirmar. A CLI pede a frase de autorização;
   ela só grava (`PATCH`) se a resposta for **exatamente** igual — variação de caixa, acentuação
   ou Demanda errada é recusada sem chamada alguma ao Azure Boards.

## O que esta skill nunca faz

- Não cria Épico, Feature, História ou Bug — isso é exclusivo de
  `publicar-backlog-demanda-azure-boards`, no `gerador-hu`.
- Não decompõe em Tasks nem estima horas — isso é `decompor-tasks`, no momento do planning, pelo
  desenvolvedor que vai executar.
- Não inventa Story Points sem ancoragem em histórico ou confirmação humana explícita.
