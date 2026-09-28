"""CLI de apoio à skill: cada subcomando cobre um passo do SKILL.md que precisa de rede
ou de parsing determinístico. A condução da entrevista e a investigação de código
continuam sendo trabalho do agente, fora deste arquivo."""

from __future__ import annotations

import argparse
import dataclasses
import json
from collections.abc import Callable, Mapping
from pathlib import Path

from refinar_tecnicamente.ancoragem_story_points import sugerir_story_points
from refinar_tecnicamente.cliente_azure_devops import ClienteAzureDevOps
from refinar_tecnicamente.configuracao import ErroConfiguracao, carregar_configuracao
from refinar_tecnicamente.gravar_spec_tecnica import (
    ErroConfirmacaoInvalida,
    gravar_spec_tecnica,
    montar_frase_autorizacao,
)
from refinar_tecnicamente.leitor_lacunas import filtrar_tecnicas, ler_lacunas


def executar(
    argv: list[str], *, env: Mapping[str, str], entrada: Callable[[str], str] = input
) -> int:
    parser = _construir_parser()
    args = parser.parse_args(argv)
    try:
        if args.comando == "ler-lacunas":
            return _ler_lacunas(args.spec)
        if args.comando == "sugerir-story-points":
            return _sugerir_story_points(args, env)
        if args.comando == "gravar-spec-tecnica":
            return _gravar_spec_tecnica(args, env, entrada)
    except ErroConfiguracao as erro:
        print(f"Configuração inválida: {erro}")
        return 2
    parser.error("comando desconhecido")
    return 2


def _construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="refinar-tecnicamente")
    subs = parser.add_subparsers(dest="comando", required=True)

    ler = subs.add_parser("ler-lacunas")
    ler.add_argument("spec")

    sugerir = subs.add_parser("sugerir-story-points")
    sugerir.add_argument("--area-path", required=True)
    sugerir.add_argument("--tipo", action="append", dest="tipos", required=True)

    gravar = subs.add_parser("gravar-spec-tecnica")
    gravar.add_argument("--demanda", type=int, required=True)
    gravar.add_argument("--spec", required=True)
    gravar.add_argument("--campo", default="Custom.DemandaSpecTecnica")

    return parser


def _ler_lacunas(caminho_spec: str) -> int:
    caminho = Path(caminho_spec)
    if not caminho.is_file():
        print(f"Spec não encontrada: {caminho_spec}")
        return 1
    lacunas = filtrar_tecnicas(ler_lacunas(caminho.read_text(encoding="utf-8")))
    print(json.dumps([dataclasses.asdict(l) for l in lacunas], ensure_ascii=False, indent=2))
    return 0


def _sugerir_story_points(args: argparse.Namespace, env: Mapping[str, str]) -> int:
    config = carregar_configuracao(env)
    with ClienteAzureDevOps(
        config.organizacao, config.projeto, config.token.get_secret_value()
    ) as cliente:
        sugestao = sugerir_story_points(
            cliente, projeto=config.projeto, area_path=args.area_path, tipos=tuple(args.tipos)
        )
    print(json.dumps(dataclasses.asdict(sugestao), ensure_ascii=False, indent=2))
    return 0


def _gravar_spec_tecnica(
    args: argparse.Namespace, env: Mapping[str, str], entrada: Callable[[str], str]
) -> int:
    config = carregar_configuracao(env)
    spec_md = Path(args.spec).read_text(encoding="utf-8")
    frase = montar_frase_autorizacao(args.demanda)
    print(f"Digite exatamente a frase abaixo para confirmar a gravação em {args.campo}:")
    print(frase)
    resposta = entrada("> ")
    try:
        with ClienteAzureDevOps(
            config.organizacao, config.projeto, config.token.get_secret_value()
        ) as cliente:
            gravar_spec_tecnica(
                cliente,
                id_demanda=args.demanda,
                campo=args.campo,
                spec_md=spec_md,
                resposta_confirmacao=resposta,
            )
    except ErroConfirmacaoInvalida as erro:
        print(str(erro))
        return 1
    print("Spec técnica gravada.")
    return 0
