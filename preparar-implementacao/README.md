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
nunca deve ser versionado. Detalhes (escopo do PAT, variáveis de cada skill) no
[README da raiz](../README.md#configuração).

## Como executar

Não há binário instalado globalmente — a CLI roda dentro do próprio ambiente `uv` desta pasta. As
variáveis do `.env` não são lidas automaticamente: exporte-as antes de chamar o comando.

```bash
uv sync --directory preparar-implementacao   # só na primeira vez, ou após atualizar dependências
export $(grep -v '^#' preparar-implementacao/.env | xargs)

uv run --directory preparar-implementacao preparar-implementacao montar 100
```

O comando acima assume que você está na raiz do repositório `refinamento-planejamento-tecnico`;
rodando já de dentro desta pasta, omita o prefixo `preparar-implementacao/` e o `--directory
preparar-implementacao`.
