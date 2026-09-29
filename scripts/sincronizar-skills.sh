#!/usr/bin/env bash
# scripts/sincronizar-skills.sh
# Traz para os agentes instalados qualquer skill nova neste repositório.
#
# `npx skills update` só ressincroniza o que já está listado no
# skills-lock.json — uma skill nova aqui não é instalada nem mencionada,
# e o comando ainda assim termina com "✓ Updated N skill(s)" (ver README,
# seção "Instalação e atualização" > "`update` não traz skills novas").
#
# Este script roda o comando que de fato traz skills novas: `add` com
# curinga de skill e de agente. Ele é idempotente — repõe o que falta,
# preserva o que já está instalado e mantém o layout canônico
# (.agents/skills/ com symlink por agente) — então rodar de novo sem
# nenhuma skill nova não duplica nem quebra nada.
#
# Uso:
#   scripts/sincronizar-skills.sh          # escopo projeto (padrão do `add`)
#   scripts/sincronizar-skills.sh -g       # escopo global, todos os projetos
#   scripts/sincronizar-skills.sh -a claude-code -a cursor   # só nesses agentes

set -euo pipefail

REPOSITORIO="pedroct/refinamento-planejamento-tecnico"

if ! command -v npx >/dev/null 2>&1; then
    echo "Erro: npx não encontrado no PATH — instale o Node.js para usar o npx skills." >&2
    exit 1
fi

echo "==> Sincronizando skills de $REPOSITORIO (traz skills novas; não usa 'skills update')"
npx skills add "$REPOSITORIO" --skill '*' -a '*' -y "$@"
