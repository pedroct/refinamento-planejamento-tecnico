# refinar-tecnicamente

Skill de refinamento técnico: fecha as lacunas técnicas de uma spec já produzida pelo
[`gerador-hu`](https://github.com/pedroct/gerador-de-hu), registra a abordagem técnica e estima
Story Points ancorados em itens fechados comparáveis, gravando o resultado em
`Custom.DemandaSpecTecnica` na Demanda de Negócio.

## Instalação

```bash
npx skills add pedroct/refinamento-planejamento-tecnico --skill refinar-tecnicamente -a claude-code
```

## Configuração

Copie `.env.example` para `.env` e preencha organização, projeto e token do Azure DevOps. O token
nunca deve ser versionado.
