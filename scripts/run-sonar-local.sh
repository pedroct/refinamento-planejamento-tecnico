#!/usr/bin/env bash
# scripts/run-sonar-local.sh
# Roda o pysonar localmente contra o SonarQube pessoal. Projeto/host/sources
# ficam em sonar-project.properties (versionado); só o token é segredo e
# fica no .env da raiz (gitignored).
#
# Cada skill (decompor-tasks, preparar-implementacao, refinar-tecnicamente) é
# um pacote uv independente, com seu próprio ambiente — não há pyproject.toml
# nem venv compartilhado na raiz. Por isso o coverage.xml é gerado pacote a
# pacote, com `uv run --directory <pacote>`, e listado em
# sonar.python.coverage.reportPaths com um caminho por pacote.

set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

if [ ! -f .env ]; then
    echo "Erro: .env não encontrado em $(pwd) — copie de .env.example e preencha SONAR_TOKEN." >&2
    exit 1
fi

if ! command -v uv >/dev/null 2>&1; then
    echo "Erro: uv não encontrado no PATH." >&2
    exit 1
fi

# Exporta só SONAR_TOKEN, nunca o .env inteiro: cada skill guarda suas próprias credenciais
# reais do Azure DevOps no seu próprio .env, mas um `set -a; source .env` da raiz exportaria
# qualquer segredo presente aqui para os subprocessos de `pytest` deste script — que os
# herdariam mesmo sem precisar deles, e uma suíte com uma lacuna de isolamento de ambiente usaria
# a credencial real em vez do valor de teste, sem avisar ninguém.
SONAR_TOKEN="$(grep -E '^SONAR_TOKEN=' .env | tail -1 | cut -d= -f2-)"

if [ -z "${SONAR_TOKEN:-}" ]; then
    echo "Erro: SONAR_TOKEN não definido no .env." >&2
    exit 1
fi
export SONAR_TOKEN

PACOTES=(decompor-tasks preparar-implementacao refinar-tecnicamente)

for pacote in "${PACOTES[@]}"; do
    echo "==> Gerando coverage.xml de $pacote"
    # Regenera o coverage.xml IMEDIATAMENTE antes do scan. Sem isto, o pysonar
    # lê um relatório ausente/desatualizado e o Sonar reporta cobertura 0%.
    uv run --directory "$pacote" pytest --cov --cov-report=xml
done

uvx --from pysonar pysonar
