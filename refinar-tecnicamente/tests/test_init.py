import pytest

import refinar_tecnicamente
import refinar_tecnicamente.cli as cli_modulo


def test_main_levanta_system_exit_com_o_codigo_de_executar(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`main()` é só o entrypoint real da CLI: repassa argv/env para `executar` e propaga
    o código de saída via SystemExit, sem interpretar nada por conta própria."""
    capturado: dict[str, object] = {}

    def _executar_falso(argv: list[str], *, env: object) -> int:
        capturado["argv"] = argv
        capturado["env"] = env
        return 7

    monkeypatch.setattr(cli_modulo, "executar", _executar_falso)
    monkeypatch.setattr("sys.argv", ["refinar-tecnicamente", "ler-lacunas", "spec.md"])

    with pytest.raises(SystemExit) as excinfo:
        refinar_tecnicamente.main()

    assert excinfo.value.code == 7
    assert capturado["argv"] == ["ler-lacunas", "spec.md"]
