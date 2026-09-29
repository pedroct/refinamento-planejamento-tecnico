"""Testa o entrypoint real da CLI (`main`), que o `pyproject.toml` registra em
`[project.scripts]`. Os demais módulos testam `executar` diretamente; aqui garantimos só que
`main` repassa `sys.argv`/`os.environ` para `executar` e converte o código de saída em
`SystemExit`, sem rodar a CLI de verdade."""

from __future__ import annotations

import os
import sys
from collections.abc import Mapping

import pytest

import preparar_implementacao
from preparar_implementacao import cli


def test_main_repassa_argv_sem_o_nome_do_programa_e_leva_o_codigo_como_saida(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    capturado: dict[str, object] = {}

    def executar_falso(argv: list[str], *, env: Mapping[str, str]) -> int:
        capturado["argv"] = argv
        capturado["env"] = env
        return 7

    monkeypatch.setattr(cli, "executar", executar_falso)
    monkeypatch.setattr(sys, "argv", ["preparar-implementacao", "montar", "123"])

    with pytest.raises(SystemExit) as excecao:
        preparar_implementacao.main()

    assert excecao.value.code == 7
    assert capturado["argv"] == ["montar", "123"]
    assert capturado["env"] is os.environ
