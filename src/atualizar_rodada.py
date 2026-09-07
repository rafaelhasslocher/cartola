import argparse

import deltalake

from atualizar_copa import exibir_resultados_copa
from calendario_liga import CONFRONTOS_LIGA
from caminhos import CAMINHO_DADOS, CAMINHO_RANKING, CAMINHO_RESULTADOS
from dados.api_cartola import (
    coletar_pontuacoes,
    coletar_pontuacoes_parciais,
    montar_dataframe_pontuacoes,
    validar_cobertura,
)
from dados.persistencia import carregar_pontuacoes, salvar_ranking, salvar_resultados
from liga.ranking import (
    exibir_confrontos_rodada,
    exibir_resultados,
    montar_ranking_final,
    montar_tabela_resultados,
)
from regras_liga import RODADA_CORTE_TURNO
from times import ID_NOME_TIME, IDS_TIMES


def atualizar_rodada(rodada_desejada, parcial=False):
    if parcial:
        print(
            f"[INFO] Coletando pontuação PARCIAL da rodada {rodada_desejada} "
            "(rodada ainda não fechou)..."
        )
        dados = coletar_pontuacoes_parciais(IDS_TIMES, rodada_desejada)
    else:
        dados = coletar_pontuacoes(IDS_TIMES, [rodada_desejada])

    if not dados:
        print(
            f"[AVISO] Nenhuma pontuação coletada para a rodada {rodada_desejada}. "
            "Nada foi atualizado."
        )
        return None

    validar_cobertura(dados, IDS_TIMES, ID_NOME_TIME, [rodada_desejada])
    df = montar_dataframe_pontuacoes(dados, ID_NOME_TIME)
    df["definitivo"] = not parcial

    deltalake.write_deltalake(
        CAMINHO_DADOS,
        df,
        mode="overwrite",
        predicate=f"rodada == {rodada_desejada}",
        schema_mode="merge",
    )

    pontuacoes = carregar_pontuacoes(CAMINHO_DADOS)
    tabela_resultados = montar_tabela_resultados(CONFRONTOS_LIGA, pontuacoes)
    tabela_resultados = tabela_resultados[
        tabela_resultados["rodada_brasileirao"] <= rodada_desejada
    ]
    exibir_confrontos_rodada(tabela_resultados, rodada_desejada)

    resultados_rodada = tabela_resultados[
        tabela_resultados["rodada_brasileirao"] == rodada_desejada
    ].copy()
    resultados_rodada["definitivo"] = not parcial
    salvar_resultados(CAMINHO_RESULTADOS, resultados_rodada, rodada_desejada)

    df_final = montar_ranking_final(
        tabela_resultados, rodada_desejada, definitivo=not parcial
    )

    salvar_ranking(CAMINHO_RANKING, df_final, rodada_desejada)
    turno_atual = 1 if rodada_desejada <= RODADA_CORTE_TURNO else 2
    exibir_resultados(df_final, turno=turno_atual)

    exibir_resultados_copa(rodada_desejada)

    if parcial:
        print(
            f"\n[AVISO] Os dados da rodada {rodada_desejada} acima são PARCIAIS "
            "(rodada em andamento). Rode de novo sem --parcial quando ela fechar "
            "para gravar o resultado definitivo."
        )

    return df_final


def _parse_args():
    parser = argparse.ArgumentParser(
        description="Atualiza os dados de uma rodada do Cartola."
    )
    parser.add_argument(
        "rodada",
        type=int,
        nargs="?",
        default=25,
        help="Número da rodada a atualizar (padrão: 25).",
    )
    parser.add_argument(
        "--parcial",
        action="store_true",
        help=(
            "Atualiza com a pontuação AO VIVO da rodada, mesmo sem ela ter "
            "fechado (requer mercado fechado / jogos em andamento)."
        ),
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    atualizar_rodada(args.rodada, parcial=args.parcial)
