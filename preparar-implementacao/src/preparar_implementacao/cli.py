"""CLI de apoio à skill: leitura, verificação de suficiência e montagem do briefing.
Nenhum comando escreve no Azure Boards."""

from __future__ import annotations

import argparse
from collections.abc import Mapping

from preparar_implementacao.briefing import montar_briefing
from preparar_implementacao.cliente_azure_devops import (
    ClienteAzureDevOps,
    ErroDestinoInvalido,
    ErroFalhaTransitoria,
    ErroRespostaInvalida,
)
from preparar_implementacao.configuracao import ErroConfiguracao, carregar_configuracao
from preparar_implementacao.contexto import extrair_campo_demanda, ids_tasks_filhas, ler_tasks
from preparar_implementacao.hierarquia import ErroHierarquiaIncompleta, subir_ate_demanda
from preparar_implementacao.suficiencia import ErroSuficienciaInsuficiente, verificar_suficiencia


def executar(argv: list[str], *, env: Mapping[str, str]) -> int:
    parser = _construir_parser()
    args = parser.parse_args(argv)
    try:
        config = carregar_configuracao(env)
    except ErroConfiguracao as erro:
        print(f"Configuração inválida: {erro}")
        return 2
    if args.comando != "montar":
        parser.error("comando desconhecido")
        return 2
    try:
        with ClienteAzureDevOps(
            config.organizacao, config.projeto, config.token.get_secret_value()
        ) as cliente:
            work_item = cliente.ler_work_item(args.work_item_id)
            cadeia = subir_ate_demanda(cliente, args.work_item_id, config.tipo_demanda)
            spec_tecnica = extrair_campo_demanda(
                cadeia, config.tipo_demanda, config.campo_spec_tecnica
            )
            tasks = ler_tasks(cliente, ids_tasks_filhas(work_item))
            criterios = work_item["fields"].get("Microsoft.VSTS.Common.AcceptanceCriteria")
            verificar_suficiencia(
                spec_tecnica=spec_tecnica,
                criterios_aceitacao=criterios,
                tasks=tasks,
                campo_spec_tecnica=config.campo_spec_tecnica,
            )
    except ErroSuficienciaInsuficiente as erro:
        print(str(erro))
        return 1
    except ErroHierarquiaIncompleta as erro:
        print(str(erro))
        return 1
    except (ErroDestinoInvalido, ErroFalhaTransitoria, ErroRespostaInvalida) as erro:
        print(f"Falha ao falar com o Azure Boards: {erro}")
        return 1
    briefing = montar_briefing(
        work_item=work_item,
        spec_tecnica=spec_tecnica or "",
        tasks=tasks,
    )
    print(briefing)
    return 0


def _construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="preparar-implementacao")
    subs = parser.add_subparsers(dest="comando", required=True)
    montar = subs.add_parser("montar")
    montar.add_argument("work_item_id", type=int)
    return parser
