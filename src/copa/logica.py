import pandas as pd


def montar_classificacao_grupo(pontuacoes, times_grupo, rodadas):

    pontuacoes_grupo = pontuacoes[
        pontuacoes["nome_time"].isin(times_grupo) & pontuacoes["rodada"].isin(rodadas)
    ]

    soma = (
        pontuacoes_grupo.groupby("nome_time", as_index=False)["pontuacao"]
        .sum()
        .rename(columns={"pontuacao": "pontuacao_total"})
    )

    classificacao = (
        pd.DataFrame({"nome_time": times_grupo})
        .merge(soma, on="nome_time", how="left")
        .fillna({"pontuacao_total": 0})
    )
    classificacao["pontuacao_total"] = classificacao["pontuacao_total"].round(2)

    return classificacao.sort_values("pontuacao_total", ascending=False).reset_index(
        drop=True
    )


def determinar_fase_atual_copa(rodada_atual, calendario_copa):

    for fase, rodadas in calendario_copa.items():
        if rodada_atual in rodadas:
            return fase
    return None


def determinar_temporada_e_fase_atual_copa(rodada_atual, calendarios_copa):

    for temporada, calendario in calendarios_copa.items():
        fase = determinar_fase_atual_copa(rodada_atual, calendario)
        if fase is not None:
            return temporada, fase
    return None, None


def rodadas_disputadas(rodadas_fase, rodada_atual):

    fim = min(rodada_atual, rodadas_fase.stop - 1)
    return range(rodadas_fase.start, fim + 1)


def fase_esta_definida(rodada_atual, rodadas_fase):

    return rodada_atual >= rodadas_fase.stop - 1


def definir_classificados_fase_de_grupos(
    pontuacoes, grupos, rodadas, definitivo, n_classificados=3
):
    resultado = {}
    for nome_grupo, times_grupo in grupos.items():
        classificacao = montar_classificacao_grupo(pontuacoes, times_grupo, rodadas)
        top_n = classificacao["nome_time"].head(n_classificados).tolist()
        resultado[nome_grupo] = {
            "classificacao": classificacao,
            "definitivo": definitivo,
        }
        if definitivo:
            resultado[nome_grupo]["classificados"] = top_n
        else:
            resultado[nome_grupo]["classificados_provisorios"] = top_n
    return resultado


def exibir_classificacao_grupos(classificados_grupos):
    for nome_grupo, dados in classificados_grupos.items():
        classificacao = dados["classificacao"].copy()
        classificacao.index += 1
        print(f"Classificação {nome_grupo}:")
        print(
            classificacao.rename(
                columns={
                    "nome_time": "Nome do time",
                    "pontuacao_total": "Pontuação Total",
                }
            ).to_csv(sep="\t", index_label="Posição", float_format="%.2f")
        )


def montar_confronto_mata_mata(pontuacoes, time1, time2, rodadas, definitivo):
    pontuacoes_confronto = pontuacoes[
        pontuacoes["nome_time"].isin([time1, time2])
        & pontuacoes["rodada"].isin(rodadas)
    ]
    somas = pontuacoes_confronto.groupby("nome_time")["pontuacao"].sum()

    pontuacao_time1 = round(somas.get(time1, 0), 2)
    pontuacao_time2 = round(somas.get(time2, 0), 2)
    time_a_frente = time1 if pontuacao_time1 >= pontuacao_time2 else time2

    resultado = {
        "time1": time1,
        "time2": time2,
        "pontuacao_time1": pontuacao_time1,
        "pontuacao_time2": pontuacao_time2,
        "rodadas": list(rodadas),
        "definitivo": definitivo,
    }
    if definitivo:
        resultado["vencedor"] = time_a_frente
    else:
        resultado["lider_parcial"] = time_a_frente
    return resultado


def montar_fase_mata_mata(pontuacoes, confrontos, rodadas, definitivo):
    resultados = [
        montar_confronto_mata_mata(pontuacoes, time1, time2, rodadas, definitivo)
        for time1, time2 in confrontos
    ]
    vencedores = [r["vencedor"] for r in resultados] if definitivo else None
    return resultados, vencedores


def exibir_resultado_mata_mata(resultados, nome_fase):
    print(f"Resultados {nome_fase} (rodadas {resultados[0]['rodadas']}):\n")
    for r in resultados:
        if r["definitivo"]:
            desfecho = f"{r['vencedor']} (vencedor)"
        else:
            desfecho = f"{r['lider_parcial']} (parcial)"
        print(
            "\t".join(
                [
                    r["time1"],
                    f"{r['pontuacao_time1']:.2f}",
                    "x",
                    f"{r['pontuacao_time2']:.2f}",
                    r["time2"],
                    desfecho,
                ]
            )
        )
    print()


def resolver_posicao_copa(posicao, classificados_grupos, times_fora):

    if posicao.startswith("fora_"):
        indice = int(posicao.split("_")[1]) - 1
        return times_fora[indice]

    colocacao, nome_grupo = posicao.split("_", 1)
    indice = int(colocacao) - 1

    dados_grupo = classificados_grupos[nome_grupo]
    if not dados_grupo["definitivo"]:
        raise ValueError(f"{nome_grupo} ainda não fechou")
    return dados_grupo["classificados"][indice]


def montar_confrontos_iniciais(chave_quartas, classificados_grupos, times_fora):

    return [
        (
            resolver_posicao_copa(posicao1, classificados_grupos, times_fora),
            resolver_posicao_copa(posicao2, classificados_grupos, times_fora),
        )
        for posicao1, posicao2 in chave_quartas
    ]


def montar_confrontos_por_indice(chave, vencedores_fase_anterior):

    return [
        (vencedores_fase_anterior[i], vencedores_fase_anterior[j]) for i, j in chave
    ]


def montar_linhas_classificacao(
    classificados_grupos, temporada, rodada, fase, jogo_da_fase
):

    linhas = []
    for nome_grupo, dados in classificados_grupos.items():
        classificacao = dados["classificacao"].copy()
        classificacao["posicao"] = range(1, len(classificacao) + 1)
        classificacao = classificacao.rename(columns={"nome_time": "time"})
        classificacao["grupo"] = nome_grupo
        classificacao["definitivo"] = dados["definitivo"]
        linhas.append(classificacao)

    df = pd.concat(linhas, ignore_index=True)
    df["rodada"] = rodada
    df["temporada"] = temporada
    df["fase"] = fase
    df["jogo_da_fase"] = jogo_da_fase

    for coluna in (
        "time1",
        "time2",
        "pontuacao_time1",
        "pontuacao_time2",
        "vencedor",
        "lider_parcial",
    ):
        df[coluna] = None

    return df


def montar_linhas_mata_mata(resultados, temporada, rodada, fase, jogo_da_fase):

    df = pd.DataFrame(resultados).drop(columns="rodadas")
    if "vencedor" not in df.columns:
        df["vencedor"] = None
    if "lider_parcial" not in df.columns:
        df["lider_parcial"] = None

    df["rodada"] = rodada
    df["temporada"] = temporada
    df["fase"] = fase
    df["jogo_da_fase"] = jogo_da_fase

    for coluna in ("grupo", "time", "posicao", "pontuacao_total"):
        df[coluna] = None

    return df
