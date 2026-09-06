import numpy as np
import pandas as pd

from regras_liga import (
    MARGEM_EMPATE,
    PONTOS_DERROTA,
    PONTOS_EMPATE,
    PONTOS_VITORIA,
    RODADA_CORTE_TURNO,
)


def montar_tabela_resultados(confrontos, pontuacoes):
    df = pd.DataFrame(confrontos)

    df = df.merge(
        pontuacoes.rename(
            columns={"nome_time": "time1", "pontuacao": "pontuacao_time1"}
        ),
        left_on=["time1", "rodada_brasileirao"],
        right_on=["time1", "rodada"],
        how="left",
    ).drop(columns="rodada")

    df = df.merge(
        pontuacoes.rename(
            columns={"nome_time": "time2", "pontuacao": "pontuacao_time2"}
        ),
        left_on=["time2", "rodada_brasileirao"],
        right_on=["time2", "rodada"],
        how="left",
    ).drop(columns="rodada")

    df = df.dropna(subset=["pontuacao_time1", "pontuacao_time2"])

    time1_venceu = df["pontuacao_time1"] >= df["pontuacao_time2"]

    df["vencedor"] = np.where(time1_venceu, df["time1"], df["time2"])
    df["perdedor"] = np.where(time1_venceu, df["time2"], df["time1"])
    df["diferenca_pontos"] = (
        (df["pontuacao_time1"] - df["pontuacao_time2"]).abs().round(2)
    )

    empate = df["diferenca_pontos"] < MARGEM_EMPATE
    df["pontos_vencedor"] = np.where(empate, PONTOS_EMPATE, PONTOS_VITORIA)
    df["pontos_perdedor"] = np.where(empate, PONTOS_EMPATE, PONTOS_DERROTA)

    df["turno"] = np.where(df["rodada_brasileirao"] <= RODADA_CORTE_TURNO, 1, 2)

    return df[
        [
            "rodada_brasileirao",
            "rodada_liga",
            "time1",
            "time2",
            "vencedor",
            "perdedor",
            "pontuacao_time1",
            "pontuacao_time2",
            "diferenca_pontos",
            "pontos_vencedor",
            "pontos_perdedor",
            "turno",
        ]
    ]


def _pontos_por_time(tabela_resultados):
    return pd.concat(
        [
            tabela_resultados[["vencedor", "pontos_vencedor", "turno"]].rename(
                columns={"vencedor": "time", "pontos_vencedor": "pontos"}
            ),
            tabela_resultados[["perdedor", "pontos_perdedor", "turno"]].rename(
                columns={"perdedor": "time", "pontos_perdedor": "pontos"}
            ),
        ],
        ignore_index=True,
    )


def _pontuacao_total_por_time(tabela_resultados):
    return pd.concat(
        [
            tabela_resultados[["turno", "time1", "pontuacao_time1"]].rename(
                columns={"time1": "time", "pontuacao_time1": "pontuacao_total"}
            ),
            tabela_resultados[["turno", "time2", "pontuacao_time2"]].rename(
                columns={"time2": "time", "pontuacao_time2": "pontuacao_total"}
            ),
        ],
        ignore_index=True,
    )


def montar_ranking_final(tabela_resultados, rodada):
    pontos = (
        _pontos_por_time(tabela_resultados)
        .groupby(["time", "turno"], as_index=False)["pontos"]
        .sum()
    )

    totais = (
        _pontuacao_total_por_time(tabela_resultados)
        .groupby(["time", "turno"], as_index=False)["pontuacao_total"]
        .sum()
    )

    ranking = pontos.merge(totais, on=["time", "turno"], how="left")
    ranking["rodada"] = rodada

    return ranking.sort_values(
        by=["turno", "pontos", "pontuacao_total"], ascending=False
    ).reset_index(drop=True)


def exibir_resultados(df_final, turno=None):
    turnos = [turno] if turno is not None else sorted(df_final["turno"].unique())
    for t in turnos:
        resultados_turno = df_final[df_final["turno"] == t].reset_index(drop=True)
        resultados_turno.index += 1
        print(f"Resultados {t}º turno:")
        print(
            resultados_turno.drop(columns=["turno", "rodada"])
            .rename(
                columns={
                    "time": "Nome do time",
                    "pontos": "Pontos",
                    "pontuacao_total": "Pontuação Total",
                }
            )
            .to_csv(sep="\t", index_label="Posição", float_format="%.2f")
        )


def exibir_confrontos_rodada(tabela_resultados, rodada):
    confrontos_rodada = tabela_resultados[
        tabela_resultados["rodada_brasileirao"] == rodada
    ]
    print(f"Confrontos da rodada {rodada}:\n")
    for _, row in confrontos_rodada.iterrows():
        print(
            "\t".join(
                [
                    row["time1"],
                    f"{row['pontuacao_time1']:.2f}",
                    "x",
                    f"{row['pontuacao_time2']:.2f}",
                    row["time2"],
                ]
            )
        )
    print()
