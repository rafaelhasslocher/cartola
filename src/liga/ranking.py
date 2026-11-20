import numpy as np
import pandas as pd


def turno_da_rodada(rodada_brasileirao, rodada_corte_turno=19):
    return 1 if rodada_brasileirao <= rodada_corte_turno else 2


def construir_offsets_rodada_liga(confrontos, rodada_corte_turno=19):
    """A `rodada_liga` no calendário é acumulada desde o início do campeonato.
    Calcula quanto subtrair dela em cada turno para reiniciar a contagem em 1.
    """
    df = confrontos if isinstance(confrontos, pd.DataFrame) else pd.DataFrame(confrontos)
    turnos = np.where(df["rodada_brasileirao"] <= rodada_corte_turno, 1, 2)
    minimos = df.groupby(turnos)["rodada_liga"].min()
    return {int(turno): int(minimo) - 1 for turno, minimo in minimos.items()}


def rodada_liga_relativa(rodada_liga, turno, offsets):
    return int(rodada_liga) - offsets.get(turno, 0)


def montar_tabela_resultados(confrontos, pontuacoes, regras):
    df = (
        confrontos.copy()
        if isinstance(confrontos, pd.DataFrame)
        else pd.DataFrame(confrontos)
    )

    pts = pontuacoes[["nome_time", "rodada", "pontuacao", "definitivo"]]

    df = df.merge(
        pts.rename(
            columns={
                "nome_time": "time1",
                "pontuacao": "pontuacao_time1",
                "definitivo": "definitivo_1",
            }
        ),
        left_on=["time1", "rodada_brasileirao"],
        right_on=["time1", "rodada"],
        how="left",
    ).drop(columns="rodada")

    df = df.merge(
        pts[["nome_time", "rodada", "pontuacao"]].rename(
            columns={"nome_time": "time2", "pontuacao": "pontuacao_time2"}
        ),
        left_on=["time2", "rodada_brasileirao"],
        right_on=["time2", "rodada"],
        how="left",
    ).drop(columns="rodada")

    df = df.dropna(subset=["pontuacao_time1", "pontuacao_time2"]).copy()
    if df.empty:
        return pd.DataFrame(
            columns=[
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
                "definitivo",
            ]
        )

    time1_venceu = df["pontuacao_time1"] >= df["pontuacao_time2"]

    df["vencedor"] = np.where(time1_venceu, df["time1"], df["time2"])
    df["perdedor"] = np.where(time1_venceu, df["time2"], df["time1"])
    df["diferenca_pontos"] = (
        (df["pontuacao_time1"] - df["pontuacao_time2"]).abs().round(2)
    )

    empate = df["diferenca_pontos"] < regras.margem_empate
    df["pontos_vencedor"] = np.where(empate, regras.pontos_empate, regras.pontos_vitoria)
    df["pontos_perdedor"] = np.where(empate, regras.pontos_empate, regras.pontos_derrota)

    df["turno"] = np.where(
        df["rodada_brasileirao"] <= regras.rodada_corte_turno, 1, 2
    )
    df["definitivo"] = df["definitivo_1"].astype("boolean").fillna(True).astype(bool)

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
            "definitivo",
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


def montar_ranking_final(tabela_resultados, rodada, definitivo=True):
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
    ranking["definitivo"] = definitivo

    return ranking.sort_values(
        by=["turno", "pontos", "pontuacao_total"], ascending=False
    ).reset_index(drop=True)


def montar_ranking_todas_rodadas(tabela_resultados):
    """Monta os snapshots de classificação acumulada para todas as rodadas registradas."""
    if tabela_resultados.empty:
        return pd.DataFrame(
            columns=["time", "turno", "pontos", "pontuacao_total", "rodada", "definitivo"]
        )

    definitivo_por_rodada = (
        tabela_resultados.groupby("rodada_brasileirao")["definitivo"].all().to_dict()
    )
    snapshots = []
    for rodada in sorted(int(r) for r in tabela_resultados["rodada_brasileirao"].unique()):
        ate_rodada = tabela_resultados[
            tabela_resultados["rodada_brasileirao"] <= rodada
        ]
        snapshots.append(
            montar_ranking_final(
                ate_rodada, rodada, definitivo=bool(definitivo_por_rodada.get(rodada, True))
            )
        )
    return pd.concat(snapshots, ignore_index=True)


def exibir_resultados(df_final, turno=None):
    turnos = [turno] if turno is not None else sorted(df_final["turno"].unique())
    for t in turnos:
        resultados_turno = df_final[df_final["turno"] == t].reset_index(drop=True)
        resultados_turno.index += 1
        print(f"Resultados {t}º turno:")
        print(
            resultados_turno.drop(columns=["turno", "rodada", "definitivo"])
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
