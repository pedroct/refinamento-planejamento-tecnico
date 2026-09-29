import pytest

from refinar_tecnicamente.leitor_lacunas import (
    ErroLacunaAmbigua,
    Lacuna,
    filtrar_tecnicas,
    ler_lacunas,
    perfil_da_lacuna,
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
    assert [lacuna.id for lacuna in tecnicas] == ["T2", "T5"]


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


def _lacuna(pergunta: str, evidencia: str | None = None) -> Lacuna:
    return Lacuna(id="T1", audiencia="Técnico", pergunta=pergunta, evidencia=evidencia)


def test_perfil_da_lacuna_so_caminho_mobile_na_pergunta() -> None:
    lacuna = _lacuna(
        "O app deve exibir o novo campo? Ver `diligencia-mobile/lib/data/models/x.dart:10`."
    )
    assert perfil_da_lacuna(lacuna) == "mobile"


def test_perfil_da_lacuna_so_caminho_nao_mobile_na_pergunta() -> None:
    lacuna = _lacuna(
        "O filtro deve considerar isso? Ver `diligencia-api/src/main/java/Servico.java:20`."
    )
    assert perfil_da_lacuna(lacuna) == "fullstack"


def test_perfil_da_lacuna_caminhos_mistos_na_pergunta() -> None:
    lacuna = _lacuna(
        "Os dois lados precisam mudar? Ver `diligencia-api/Servico.java:20` e "
        "`diligencia-mobile/lib/x.dart:5`."
    )
    assert perfil_da_lacuna(lacuna) == "ambos"


def test_perfil_da_lacuna_sem_nenhum_caminho() -> None:
    lacuna = _lacuna("Qual a granularidade do acesso a órgãos inativos?")
    assert perfil_da_lacuna(lacuna) == "ambos"


def test_perfil_da_lacuna_usa_evidencia_estruturada() -> None:
    lacuna = _lacuna(
        "O prazo persiste como enum?", evidencia="diligencia-mobile/lib/data/x.dart:12"
    )
    assert perfil_da_lacuna(lacuna) == "mobile"


def test_perfil_da_lacuna_mistura_entre_pergunta_e_evidencia() -> None:
    """Um caminho mobile na pergunta e um não-mobile só na evidência (ou vice-versa) também
    conta como mistura — a classificação olha os dois campos juntos, não cada um isolado."""
    lacuna = _lacuna(
        "Isso afeta os dois lados? Ver `diligencia-mobile/lib/x.dart:5`.",
        evidencia="diligencia-api/Servico.java:20",
    )
    assert perfil_da_lacuna(lacuna) == "ambos"


def test_perfil_da_lacuna_repositorio_com_mobile_como_substring() -> None:
    """A heurística é substring simples, documentada como limitação conhecida — um repositório
    hipotético cujo nome contenha 'mobile' sem ser o app mobile de verdade também classificaria
    como mobile. Este teste fixa o comportamento documentado, não uma falha a corrigir aqui."""
    lacuna = _lacuna("Pergunta qualquer. Ver `algo-mobile-legado/arquivo.py:1`.")
    assert perfil_da_lacuna(lacuna) == "mobile"


_SPEC_MISTA = """# Spec

## Lacunas e perguntas abertas

- **N1 · Negócio** — Pergunta de negócio, nunca deve aparecer em nenhum filtro por perfil.
- **T1 · Técnico** — Endpoint novo? Ver `diligencia-api/Servico.java:10`.
- **T2 · Técnico** — Tela nova? Ver `diligencia-mobile/lib/x.dart:5`.
- **T3 · Técnico** — Pergunta conceitual, sem caminho nenhum citado.
"""


def test_filtrar_tecnicas_por_perfil_fullstack() -> None:
    lacunas = ler_lacunas(_SPEC_MISTA)
    tecnicas = filtrar_tecnicas(lacunas, perfil="fullstack")
    assert [lacuna.id for lacuna in tecnicas] == ["T1", "T3"]


def test_filtrar_tecnicas_por_perfil_mobile() -> None:
    lacunas = ler_lacunas(_SPEC_MISTA)
    tecnicas = filtrar_tecnicas(lacunas, perfil="mobile")
    assert [lacuna.id for lacuna in tecnicas] == ["T2", "T3"]


def test_filtrar_tecnicas_sem_perfil_preserva_comportamento_atual() -> None:
    """Regressão: omitir `perfil` (ou passar None) devolve exatamente o que `filtrar_tecnicas`
    já devolvia antes desta task — todas as lacunas Técnico e sem rótulo, sem filtro nenhum por
    repositório."""
    lacunas = ler_lacunas(_SPEC_MISTA)
    assert [lacuna.id for lacuna in filtrar_tecnicas(lacunas)] == ["T1", "T2", "T3"]
    assert [lacuna.id for lacuna in filtrar_tecnicas(lacunas, perfil=None)] == ["T1", "T2", "T3"]


def test_perfil_da_lacuna_evidencia_texto_livre_sem_caminho() -> None:
    """Texto livre sem '/' na evidência não contribui com caminho, mesmo que tenha palavras.
    Sem caminho nenhum, resultado é 'ambos'."""
    lacuna = _lacuna("Qual a granularidade?", evidencia="Nenhuma referência encontrada no código")
    assert perfil_da_lacuna(lacuna) == "ambos"


def test_perfil_da_lacuna_evidencia_contendo_mobile_mas_sem_caminho() -> None:
    """Texto livre contendo a palavra 'mobile' mas sem padrão de caminho não classifica como
    mobile; é ignorado pois não é um caminho de verdade."""
    lacuna = _lacuna("Pergunta.", evidencia="Ver documentação mobile no README")
    assert perfil_da_lacuna(lacuna) == "ambos"


def test_perfil_da_lacuna_evidencia_texto_com_pergunta_caminho_mobile() -> None:
    """Mesmo que a evidência seja texto livre, se a pergunta tiver um caminho mobile,
    a classificação é mobile."""
    lacuna = _lacuna(
        "Fazer isso? Ver `diligencia-mobile/lib/x.dart:5`.",
        evidencia="Sem referência no repositório",
    )
    assert perfil_da_lacuna(lacuna) == "mobile"


def test_perfil_da_lacuna_multiplos_caminhos_sem_crases_mistos_fullstack_primeiro() -> None:
    """Múltiplos caminhos separados por vírgula, com mistura (fullstack e mobile) => 'ambos'.
    Testa ordem: fullstack primeiro."""
    lacuna = _lacuna(
        "Pergunta.",
        evidencia="diligencia-api/Servico.java:1, diligencia-mobile/lib/x.dart:2",
    )
    assert perfil_da_lacuna(lacuna) == "ambos"


def test_perfil_da_lacuna_multiplos_caminhos_sem_crases_mistos_mobile_primeiro() -> None:
    """Múltiplos caminhos separados por vírgula, com mistura (mobile e fullstack) => 'ambos'.
    Testa ordem: mobile primeiro."""
    lacuna = _lacuna(
        "Pergunta.",
        evidencia="diligencia-mobile/lib/x.dart:2, diligencia-api/Servico.java:1",
    )
    assert perfil_da_lacuna(lacuna) == "ambos"


def test_perfil_da_lacuna_multiplos_caminhos_sem_crases_mesmo_perfil() -> None:
    """Múltiplos caminhos sem crases, todos do mesmo perfil (mobile) => 'mobile'."""
    lacuna = _lacuna(
        "Pergunta.",
        evidencia="diligencia-mobile/lib/x.dart:1, diligencia-mobile/lib/y.dart:2",
    )
    assert perfil_da_lacuna(lacuna) == "mobile"


def test_perfil_da_lacuna_evidencia_na_ou_eou_sem_caminho() -> None:
    """Palavras-chave 'n/a' e 'e/ou' que casam \\S+/\\S+ mas não são caminhos
    devem ser ignoradas => 'ambos'."""
    lacuna1 = _lacuna("Pergunta.", evidencia="n/a")
    assert perfil_da_lacuna(lacuna1) == "ambos"

    lacuna2 = _lacuna("Pergunta.", evidencia="e/ou")
    assert perfil_da_lacuna(lacuna2) == "ambos"
