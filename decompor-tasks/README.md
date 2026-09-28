# decompor-tasks

Skill de planejamento: decompõe uma História/Bug já publicada no Azure Boards em Tasks estimadas
em horas, atribuídas a quem vai executar, ancoradas em Tasks fechadas comparáveis.

## Instalação

```bash
npx skills add pedroct/refinamento-planejamento-tecnico --skill decompor-tasks -a claude-code
```

## Configuração

Copie `.env.example` para `.env` e preencha organização, projeto e token do Azure DevOps. O token
nunca deve ser versionado. Detalhes (escopo do PAT, variáveis de cada skill) no
[README da raiz](../README.md#configuração).

## Como executar

Não há binário instalado globalmente — a CLI roda dentro do próprio ambiente `uv` desta pasta. As
variáveis do `.env` não são lidas automaticamente: exporte-as antes de chamar o comando, e use
caminho absoluto para argumentos de arquivo (o `--directory` muda o diretório de trabalho para
dentro desta pasta).

```bash
uv sync --directory decompor-tasks   # só na primeira vez, ou após atualizar dependências
export $(grep -v '^#' decompor-tasks/.env | xargs)

uv run --directory decompor-tasks decompor-tasks sugerir-horas \
  --area-path "Projeto\\Time A" --tipo-task Task --titulo "Criar endpoint"
uv run --directory decompor-tasks decompor-tasks criar \
  /caminho/absoluto/plano.json --manifesto /caminho/absoluto/historia-100.json
```

Os comandos acima assumem que você está na raiz do repositório `refinamento-planejamento-tecnico`;
rodando já de dentro desta pasta, omita o prefixo `decompor-tasks/` e o `--directory
decompor-tasks`.
