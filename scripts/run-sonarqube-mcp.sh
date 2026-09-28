#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$PROJECT_ROOT/.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "Erro: .env não encontrado em $PROJECT_ROOT." >&2
    exit 1
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

SONARQUBE_TOKEN="${SONARQUBE_TOKEN:-${SONAR_TOKEN:-}}"
if [ -z "$SONARQUBE_TOKEN" ]; then
    echo "Erro: defina SONAR_TOKEN no .env." >&2
    exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
    echo "Erro: docker não encontrado no PATH." >&2
    exit 1
fi

if ! docker info >/dev/null 2>&1; then
    if ! command -v colima >/dev/null 2>&1; then
        echo "Erro: Colima não encontrado para iniciar o runtime Docker." >&2
        exit 1
    fi
    colima start --mount "$PROJECT_ROOT:ro" >/dev/null
fi

exec docker run \
    --init \
    -i \
    --rm \
    --pull=always \
    -e SONARQUBE_URL="https://sonar.pedroct.com.br" \
    -e SONARQUBE_TOKEN \
    -e SONARQUBE_PROJECT_KEY="refinamento-planejamento-tecnico" \
    -e STORAGE_PATH=/tmp/sonarqube-mcp-storage \
    -v "$PROJECT_ROOT:/app/mcp-workspace:ro" \
    mcp/sonarqube
