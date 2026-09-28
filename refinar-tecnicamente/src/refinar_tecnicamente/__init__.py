"""Skill de refinamento técnico: fecha lacunas técnicas, registra abordagem e Story Points."""

from __future__ import annotations

import os
import sys


def main() -> None:
    from refinar_tecnicamente.cli import executar

    raise SystemExit(executar(sys.argv[1:], env=os.environ))
