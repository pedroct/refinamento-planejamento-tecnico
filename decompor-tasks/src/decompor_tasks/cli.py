"""CLI de apoio à skill: a decomposição em si (quais Tasks, a partir de qual abordagem
técnica) é trabalho do agente, guiado pelo SKILL.md; este arquivo cobre rede, ancoragem
de estimativa e a criação sob confirmação."""

from __future__ import annotations

import argparse
import dataclasses
import json
from collections.abc import Callable, Mapping
from pathlib import Path

from decompor_tasks.ancoragem_horas import sugerir_horas
from decompor_tasks.cliente_azure_devops import ClienteAzureDevOps
from decompor_tasks.configuracao import ErroConfiguracao, carregar_configuracao
from decompor_tasks.criar_tasks import ErroConfirmacaoInvalida, criar_tasks_pendentes
from decompor_tasks.manifesto import (
    PlanoTasks,
    TaskProposta,
    ler_manifesto,
    montar_frase_autorizacao,
)


def executar(
    argv: list[str], *, env: Mapping[str, str], entrada: Callable[[str], str] = input
) -> int:
    parser = _construir_parser()
    args = parser.parse_args(argv)
    try:
        if args.comando == "sugerir-horas":
            return _sugerir_horas(args, env)
        if args.comando == "criar":
            return _criar(args, env, entrada)
    except ErroConfiguracao as erro:
        print(f"Configuração inválida: {erro}")
        return 2
    parser.error("comando desconhecido")
    return 2


def _construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="decompor-tasks")
    subs = parser.add_subparsers(dest="comando", required=True)

    sugerir = subs.add_parser("sugerir-horas")
    sugerir.add_argument("--area-path", required=True)
    sugerir.add_argument("--tipo-task", default="Task")
    sugerir.add_argument("--titulo", required=True, dest="titulo_aproximado")

    criar = subs.add_parser("criar")
    criar.add_argument("plano", help="Caminho de um JSON com historia_id e a lista de tasks")
    criar.add_argument("--manifesto", required=True)

    return parser


def _sugerir_horas(args: argparse.Namespace, env: Mapping[str, str]) -> int:
    config = carregar_configuracao(env)
    with ClienteAzureDevOps(
        config.organizacao, config.projeto, config.token.get_secret_value()
    ) as cliente:
        sugestao = sugerir_horas(
            cliente,
            projeto=config.projeto,
            area_path=args.area_path,
            tipo_task=args.tipo_task,
            titulo_aproximado=args.titulo_aproximado,
        )
    print(json.dumps(dataclasses.asdict(sugestao), ensure_ascii=False, indent=2))
    return 0


def _carregar_plano(caminho: str) -> PlanoTasks:
    dados = json.loads(Path(caminho).read_text(encoding="utf-8"))
    tasks = tuple(TaskProposta(**t) for t in dados["tasks"])
    return PlanoTasks(historia_id=dados["historia_id"], tasks=tasks)


def _criar(args: argparse.Namespace, env: Mapping[str, str], entrada: Callable[[str], str]) -> int:
    config = carregar_configuracao(env)
    plano = _carregar_plano(args.plano)
    caminho_manifesto = Path(args.manifesto)
    manifesto_atual = ler_manifesto(caminho_manifesto)
    frase = montar_frase_autorizacao(plano.historia_id)
    print(f"{len(plano.tasks)} Task(s) no plano. Digite exatamente a frase para confirmar:")
    print(frase)
    resposta = entrada("> ")
    try:
        with ClienteAzureDevOps(
            config.organizacao, config.projeto, config.token.get_secret_value()
        ) as cliente:
            criar_tasks_pendentes(
                cliente,
                organizacao=config.organizacao,
                projeto=config.projeto,
                tipo_task=config.tipo_task,
                plano=plano,
                manifesto_atual=manifesto_atual,
                caminho_manifesto=caminho_manifesto,
                resposta_confirmacao=resposta,
            )
    except ErroConfirmacaoInvalida as erro:
        print(str(erro))
        return 1
    print("Tasks pendentes criadas.")
    return 0
