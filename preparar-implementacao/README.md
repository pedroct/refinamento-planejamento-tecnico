# preparar-implementacao

Skill de implementação: lê um work item já refinado e decomposto no Azure Boards, reúne a
abordagem técnica, o contexto de negócio e as Tasks estimadas, e monta um briefing único em
Markdown — sem nenhuma escrita no Azure Boards.

## Instalação

```bash
npx skills add pedroct/refinamento-planejamento-tecnico --skill preparar-implementacao -a claude-code
```

## Configuração

Copie `.env.example` para `.env` e preencha organização, projeto e token do Azure DevOps. O token
nunca deve ser versionado.
