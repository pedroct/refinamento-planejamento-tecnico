"""Testa o entrypoint real da CLI (`main`), que o `pyproject.toml` registra em
`[project.scripts]`. Os demais módulos testam `executar` diretamente; aqui garantimos só que
`main` repassa `sys.argv`/`os.environ` para `executar` e converte o código de saída em
`SystemExit`, sem rodar a CLI de verdade."""

from __future__ import annotations

import os
import sys
from collections.abc import Mapping

import pytest

import decompor_tasks
from decompor_tasks import cli


def test_main_repassa_argv_sem_o_nome_do_programa_e_leva_o_codigo_como_saida(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    capturado: dict[str, object] = {}

    def executar_falso(argv: list[str], *, env: Mapping[str, str]) -> int:
        capturado["argv"] = argv
        capturado["env"] = env
        return 7

    monkeypatch.setattr(cli, "executar", executar_falso)
    monkeypatch.setattr(sys, "argv", ["decompor-tasks", "sugerir-horas", "--area-path", "x"])

    with pytest.raises(SystemExit) as excecao:
        decompor_tasks.main()

    assert excecao.value.code == 7
    assert capturado["argv"] == ["sugerir-horas", "--area-path", "x"]
    assert capturado["env"] is os.environ
