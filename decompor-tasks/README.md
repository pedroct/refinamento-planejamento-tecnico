# decompor-tasks

Skill de planejamento: decompõe uma História/Bug já publicada no Azure Boards em Tasks estimadas
em horas, atribuídas a quem vai executar, ancoradas em Tasks fechadas comparáveis.

## Instalação

```bash
npx skills add pedroct/refinamento-planejamento-tecnico --skill decompor-tasks -a claude-code
```

## Configuração

Copie `.env.example` para `.env` e preencha organização, projeto e token do Azure DevOps. O token
nunca deve ser versionado.
