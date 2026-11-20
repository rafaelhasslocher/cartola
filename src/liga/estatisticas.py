"""Indicadores estatísticos da Liga calculados a partir dos confrontos."""

import pandas as pd


def montar_tabela_estatisticas(resultados):
    """Consolida, a partir dos confrontos da Liga:
    - `por_rodada`: uma linha por (rodada, time) com a pontuação bruta e a
      posição na rodada (1 = maior pontuador);
    - `por_confronto`: uma linha por participação em confronto direto (em
      rodadas duplas o time aparece duas vezes), já com a posição na rodada
      e o saldo do confronto (`pontuacao - pontuacao_adversario`).
    """
    if resultados.empty:
        vazio = pd.DataFrame()
        return vazio, vazio

    lado1 = resultados[["rodada_brasileirao", "time1", "pontuacao_time1", "pontuacao_time2"]].rename(
        columns={"time1": "time", "pontuacao_time1": "pontuacao", "pontuacao_time2": "pontuacao_adv"}
    )
    lado2 = resultados[["rodada_brasileirao", "time2", "pontuacao_time2", "pontuacao_time1"]].rename(
        columns={"time2": "time", "pontuacao_time2": "pontuacao", "pontuacao_time1": "pontuacao_adv"}
    )
    confrontos = pd.concat([lado1, lado2], ignore_index=True)
    confrontos["saldo"] = confrontos["pontuacao"] - confrontos["pontuacao_adv"]

    # Preserva a primeira aparição de cada time na rodada para desempate estável.
    por_rodada = (
        confrontos[["rodada_brasileirao", "time", "pontuacao"]]
        .drop_duplicates(subset=["rodada_brasileirao", "time"], keep="first")
        .sort_values(
            ["rodada_brasileirao", "pontuacao"],
            ascending=[True, False],
            kind="stable",
        )
        .reset_index(drop=True)
    )
    por_rodada["posicao_rodada"] = por_rodada.groupby("rodada_brasileirao").cumcount() + 1

    por_confronto = confrontos.merge(
        por_rodada[["rodada_brasileirao", "time", "posicao_rodada"]],
        on=["rodada_brasileirao", "time"],
        how="left",
    )
    return por_rodada, por_confronto


def _para_ocorrencias(df, nome_completo):
    return [
        (int(row.rodada_brasileirao), nome_completo(row.time), None)
        for row in df.itertuples(index=False)
    ]


def calcular_top_n_por_rodada(por_rodada, n, nome_completo):
    if por_rodada.empty:
        return []
    return _para_ocorrencias(por_rodada[por_rodada["posicao_rodada"] <= n], nome_completo)


def calcular_top_n_mas_nao_venceu(por_confronto, n, margem_empate, nome_completo):
    if por_confronto.empty:
        return []
    filtro = (por_confronto["posicao_rodada"] <= n) & (por_confronto["saldo"] < margem_empate)
    return _para_ocorrencias(por_confronto[filtro], nome_completo)


def calcular_maior_pontuador_mas_empatou(por_confronto, margem_empate, nome_completo):
    if por_confronto.empty:
        return []
    filtro = (por_confronto["posicao_rodada"] == 1) & (
        por_confronto["saldo"].abs() < margem_empate
    )
    return _para_ocorrencias(por_confronto[filtro], nome_completo)
