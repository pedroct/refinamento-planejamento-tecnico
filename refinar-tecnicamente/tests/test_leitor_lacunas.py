import pytest

from refinar_tecnicamente.leitor_lacunas import (
    ErroLacunaAmbigua,
    Lacuna,
    filtrar_tecnicas,
    ler_lacunas,
)

SPEC_COM_ROTULOS = """# Spec

## Comportamento esperado

...

## Lacunas e perguntas abertas

- **N3 · Negócio** — A data que o usuário vê deve ser a mesma que expira?
  <!-- evidência: MinhaDiligenciaDTO.java:76-78 -->
- **T2 · Técnico** — `PENDENTE` vira enum persistido ou é rótulo de exibição?
  <!-- evidência: DiligenciaService.java:120 -->
- **T5 · Técnico** — Onde persistir o prazo vigente?
"""

SPEC_SEM_ROTULOS = """# Spec

## Lacunas e perguntas abertas

- Qual o prazo padrão de expiração?
- Quem pode renovar uma diligência?
"""


def test_le_lacunas_rotuladas() -> None:
    lacunas = ler_lacunas(SPEC_COM_ROTULOS)
    assert len(lacunas) == 3
    assert lacunas[0] == Lacuna(
        id="N3",
        audiencia="Negócio",
        pergunta="A data que o usuário vê deve ser a mesma que expira?",
        evidencia="MinhaDiligenciaDTO.java:76-78",
    )
    assert lacunas[1].id == "T2"
    assert lacunas[1].audiencia == "Técnico"
    assert lacunas[2].evidencia is None


def test_le_lacunas_sem_rotulo() -> None:
    lacunas = ler_lacunas(SPEC_SEM_ROTULOS)
    assert len(lacunas) == 2
    assert lacunas[0].id is None
    assert lacunas[0].audiencia is None
    assert lacunas[0].pergunta == "Qual o prazo padrão de expiração?"


def test_spec_sem_secao_devolve_lista_vazia() -> None:
    assert ler_lacunas("# Spec\n\n## Comportamento esperado\n\nTexto.\n") == []


def test_secao_seguida_de_outra_secao_para_no_limite() -> None:
    """A seção de lacunas não vai até o fim do arquivo — para na próxima `## `. Cobre o
    ramo de corte de `_corpo_secao_lacunas` quando existe conteúdo depois da seção."""
    spec = """# Spec

## Lacunas e perguntas abertas

- Qual o prazo padrão de expiração?

## Riscos

- Não deveria aparecer como lacuna.
"""
    lacunas = ler_lacunas(spec)
    assert len(lacunas) == 1
    assert lacunas[0].pergunta == "Qual o prazo padrão de expiração?"


def test_filtrar_tecnicas_exclui_negocio_rotulado() -> None:
    lacunas = ler_lacunas(SPEC_COM_ROTULOS)
    tecnicas = filtrar_tecnicas(lacunas)
    assert [l.id for l in tecnicas] == ["T2", "T5"]


def test_filtrar_tecnicas_inclui_sem_rotulo() -> None:
    lacunas = ler_lacunas(SPEC_SEM_ROTULOS)
    tecnicas = filtrar_tecnicas(lacunas)
    assert len(tecnicas) == 2


def test_lacuna_ambigua_separador_errado() -> None:
    spec = """# Spec

## Lacunas e perguntas abertas

- **N3 - Negócio** — pergunta
"""
    with pytest.raises(ErroLacunaAmbigua):
        ler_lacunas(spec)


def test_lacuna_ambigua_casing_errado() -> None:
    spec = """# Spec

## Lacunas e perguntas abertas

- **N3 · negócio** — pergunta
"""
    with pytest.raises(ErroLacunaAmbigua):
        ler_lacunas(spec)


def test_lacuna_ambigua_dash_errado() -> None:
    spec = """# Spec

## Lacunas e perguntas abertas

- **N3 · Negócio** - pergunta
"""
    with pytest.raises(ErroLacunaAmbigua):
        ler_lacunas(spec)
