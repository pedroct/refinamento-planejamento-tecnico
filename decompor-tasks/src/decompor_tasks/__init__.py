"""Skill de planejamento: decompõe uma História/Bug em Tasks estimadas em horas."""

from __future__ import annotations

import os
import sys


def main() -> None:
    from decompor_tasks.cli import executar

    raise SystemExit(executar(sys.argv[1:], env=os.environ))
