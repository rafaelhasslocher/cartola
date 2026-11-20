import argparse
import sys

import requests

from caminhos import ano_padrao, caminho_pontuacoes
from campeonato import carregar_temporada
from config_temporada import carregar_config_temporada
from copa.logica import exibir_copa_rodada
from dados.api_cartola import (
    coletar_pontuacoes,
    coletar_pontuacoes_parciais,
    consultar_status_mercado,
    montar_dataframe_pontuacoes,
    validar_cobertura,
)
from dados.persistencia import salvar_pontuacoes_rodada
from liga.ranking import (
    exibir_confrontos_rodada,
    exibir_resultados,
    montar_ranking_final,
)


def _detectar_rodada_e_modo():
    try:
        status = consultar_status_mercado()
    except requests.RequestException as e:
        sys.exit(f"[ERRO] Não foi possível consultar /mercado/status: {e}")

    rodada_mercado = int(status["rodada_atual"])
    codigo_status = int(status["status_mercado"])

    if codigo_status == 2:
        print(
            f"[INFO] Mercado fechado na rodada {rodada_mercado}: "
            "detectado modo PARCIAL."
        )
        return rodada_mercado, True

    if codigo_status == 1:
        rodada_fechada = rodada_mercado - 1
        if rodada_fechada < 1:
            sys.exit("[AVISO] Mercado aberto na rodada 1; ainda não há rodada fechada.")
        print(
            f"[INFO] Mercado aberto (próxima rodada: {rodada_mercado}): "
            f"atualizando rodada {rodada_fechada} (definitivo)."
        )
        return rodada_fechada, False

    sys.exit(
        f"[AVISO] Status do mercado não reconhecido ({codigo_status}) na rodada "
        f"{rodada_mercado}. Informe o número da rodada explicitamente."
    )


def atualizar_rodada(rodada_desejada, parcial=False, ano=None):
    ano = ano_padrao() if ano is None else int(ano)
    config = carregar_config_temporada(ano)

    if parcial:
        print(
            f"[INFO] Coletando pontuação PARCIAL da rodada {rodada_desejada} "
            "(rodada ainda não fechou)..."
        )
        dados = coletar_pontuacoes_parciais(config.ids_times, rodada_desejada)
    else:
        dados = coletar_pontuacoes(config.ids_times, [rodada_desejada])

    if not dados:
        print(
            f"[AVISO] Nenhuma pontuação coletada para a rodada {rodada_desejada}. "
            "Nada foi atualizado."
        )
        return None

    validar_cobertura(dados, config.ids_times, config.id_nome_time, [rodada_desejada])
    df = montar_dataframe_pontuacoes(dados, config.id_nome_time)
    df["definitivo"] = not parcial

    salvar_pontuacoes_rodada(
        caminho_pontuacoes(ano), df, rodada_desejada, ordem_ids=config.ids_times
    )

    temporada = carregar_temporada(ano)
    tabela_ate_rodada = temporada.resultados_liga[
        temporada.resultados_liga["rodada_brasileirao"] <= rodada_desejada
    ]
    exibir_confrontos_rodada(tabela_ate_rodada, rodada_desejada)

    df_final = montar_ranking_final(
        tabela_ate_rodada, rodada_desejada, definitivo=not parcial
    )
    turno_atual = temporada.turno_da_rodada(rodada_desejada)
    exibir_resultados(df_final, turno=turno_atual)

    estado_copa = temporada.resolver_copa(
        rodada_exibida=rodada_desejada,
        rodada_maxima_disputada=rodada_desejada,
    )
    exibir_copa_rodada(estado_copa)

    if parcial:
        print(
            f"\n[AVISO] Os dados da rodada {rodada_desejada} acima são PARCIAIS "
            "(rodada em andamento). Rode de novo sem --parcial quando ela fechar "
            "para gravar o resultado definitivo."
        )

    return df_final


def _parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Atualiza os dados de uma rodada do Cartola. Sem argumentos, "
            "consulta /mercado/status para detectar a rodada e o modo."
        )
    )
    parser.add_argument(
        "rodada",
        type=int,
        nargs="?",
        default=None,
        help="Número da rodada a atualizar (opcional: detectado automaticamente).",
    )
    parser.add_argument(
        "--parcial",
        action="store_true",
        help=(
            "Atualiza com a pontuação AO VIVO da rodada, mesmo sem ela ter "
            "fechado (requer mercado fechado / jogos em andamento)."
        ),
    )
    parser.add_argument(
        "--ano",
        type=int,
        default=None,
        help="Ano da temporada (padrão: ano mais recente em config/).",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    if args.rodada is None:
        rodada, parcial = _detectar_rodada_e_modo()
        if args.parcial:
            parcial = True
    else:
        rodada, parcial = args.rodada, args.parcial
    atualizar_rodada(rodada, parcial=parcial, ano=args.ano)
