from pathlib import Path
from typing import Any

import pytest

from refinar_tecnicamente.cliente_azure_devops import ErroDestinoInvalido
from refinar_tecnicamente.resolver_spec import (
    ErroPastaAmbigua,
    ErroSpecNaoEncontrada,
    localizar_pasta_local,
    montar_nome_pasta,
    resolver_spec,
)


class ClienteFalso:
    def __init__(
        self, anexos: dict[str, bytes] | None = None, titulo: str = "Emissão de convites"
    ) -> None:
        self._anexos = anexos or {}
        self._titulo = titulo

    def baixar_anexo(self, work_item_id: int, nome_arquivo: str) -> bytes | None:
        return self._anexos.get(nome_arquivo)

    def ler_work_item(self, work_item_id: int) -> dict[str, Any]:
        return {"id": work_item_id, "fields": {"System.Title": self._titulo}}


class ClienteFalsoComFalhaNoBacklog:
    """Simula spec.md baixado com sucesso e backlog.md falhando por erro do cliente."""

    def __init__(self, titulo: str = "Emissão de convites") -> None:
        self._titulo = titulo

    def baixar_anexo(self, work_item_id: int, nome_arquivo: str) -> bytes | None:
        if nome_arquivo == "spec.md":
            return b"# Spec\n"
        raise ErroDestinoInvalido("falha simulada ao baixar backlog.md")

    def ler_work_item(self, work_item_id: int) -> dict[str, Any]:
        return {"id": work_item_id, "fields": {"System.Title": self._titulo}}


def test_montar_nome_pasta_normaliza_titulo() -> None:
    assert montar_nome_pasta(14125, "Emissão de Convites!") == "DN-14125-emissao-de-convites"


def test_montar_nome_pasta_sem_caractere_aproveitavel_usa_so_o_id() -> None:
    assert montar_nome_pasta(14125, "!!!") == "DN-14125"


def test_montar_nome_pasta_trunca_em_60_sem_hifen_na_ponta() -> None:
    titulo_longo = "palavra " * 20
    nome = montar_nome_pasta(1, titulo_longo)
    assert len(nome) <= len("DN-1-") + 60
    assert not nome.endswith("-")


def test_localizar_pasta_local_sem_docs_specs_devolve_none(tmp_path: Path) -> None:
    assert localizar_pasta_local(tmp_path, 13959) is None


def test_localizar_pasta_local_com_docs_specs_mas_sem_pasta_correspondente_devolve_none(
    tmp_path: Path,
) -> None:
    """`docs/specs/` existe (outras Demandas já publicadas), mas nenhuma pasta corresponde
    a este ID — diferente do caso sem `docs/specs/` nenhum, testado acima."""
    outra = tmp_path / "docs" / "specs" / "DN-1-outra-demanda"
    outra.mkdir(parents=True)
    assert localizar_pasta_local(tmp_path, 13959) is None


def test_localizar_pasta_local_encontra_pasta_com_slug(tmp_path: Path) -> None:
    pasta = tmp_path / "docs" / "specs" / "DN-13959-emissao-de-convites"
    pasta.mkdir(parents=True)
    assert localizar_pasta_local(tmp_path, 13959) == pasta


def test_localizar_pasta_local_com_duas_pastas_do_mesmo_id_recusa(tmp_path: Path) -> None:
    base = tmp_path / "docs" / "specs"
    (base / "DN-13959-slug-antigo").mkdir(parents=True)
    (base / "DN-13959-slug-novo").mkdir(parents=True)
    with pytest.raises(ErroPastaAmbigua):
        localizar_pasta_local(tmp_path, 13959)


def test_resolver_spec_prioriza_pasta_local(tmp_path: Path) -> None:
    pasta = tmp_path / "docs" / "specs" / "DN-13959-slug"
    pasta.mkdir(parents=True)
    cliente = ClienteFalso({"spec.md": b"nao deveria ser usado"})
    resultado = resolver_spec(cliente, raiz=tmp_path, id_demanda=13959)
    assert resultado == pasta


def test_resolver_spec_sem_pasta_local_baixa_anexos_na_convencao_de_pasta(
    tmp_path: Path,
) -> None:
    cliente = ClienteFalso(
        {"spec.md": b"# Spec\n", "backlog.md": b"# Backlog\n"}, titulo="Emissão de Convites"
    )
    resultado = resolver_spec(cliente, raiz=tmp_path, id_demanda=13959)
    esperado = tmp_path / "docs" / "specs" / "DN-13959-emissao-de-convites"
    assert resultado == esperado
    assert (esperado / "spec.md").read_bytes() == b"# Spec\n"
    assert (esperado / "backlog.md").read_bytes() == b"# Backlog\n"


def test_resolver_spec_sem_pasta_local_e_sem_backlog_anexado_nao_cria_backlog(
    tmp_path: Path,
) -> None:
    cliente = ClienteFalso({"spec.md": b"# Spec\n"})
    resolver_spec(cliente, raiz=tmp_path, id_demanda=13959)
    esperado = tmp_path / "docs" / "specs" / "DN-13959-emissao-de-convites"
    assert not (esperado / "backlog.md").exists()


def test_resolver_spec_sem_pasta_local_e_sem_anexo_recusa(tmp_path: Path) -> None:
    cliente = ClienteFalso({})
    with pytest.raises(ErroSpecNaoEncontrada):
        resolver_spec(cliente, raiz=tmp_path, id_demanda=13959)


def test_resolver_spec_com_falha_ao_baixar_backlog_nao_grava_nada_em_disco(
    tmp_path: Path,
) -> None:
    """Achado 3 da revisão whole-branch: se o download de backlog.md falhar depois de
    spec.md já ter sido baixado, nada pode ser gravado em disco — nem a pasta, nem
    spec.md sozinho — senão a próxima execução acharia essa pasta incompleta e a
    devolveria como resultado válido, sem nunca baixar o backlog."""
    cliente = ClienteFalsoComFalhaNoBacklog()
    with pytest.raises(ErroDestinoInvalido):
        resolver_spec(cliente, raiz=tmp_path, id_demanda=13959)
    assert not (tmp_path / "docs").exists()
