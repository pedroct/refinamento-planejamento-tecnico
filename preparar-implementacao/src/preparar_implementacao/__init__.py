"""Skill de implementação: monta o briefing consolidado a partir de um work item refinado."""

from __future__ import annotations

import os
import sys


def main() -> None:
    from preparar_implementacao.cli import executar

    raise SystemExit(executar(sys.argv[1:], env=os.environ))
