"""Lógica unificada da Copa: grupos, chaveamento, mata-mata e exibição CLI."""

from dataclasses import dataclass

import pandas as pd

NOME_EXIBICAO_FASE = {"quartas": "quartas", "semi": "semifinal", "final": "final"}

MENSAGEM_BLOQUEIO_FASE = {
    "quartas": (
        "A fase de grupos ainda não terminou — o chaveamento das "
        "quartas de final será exibido assim que ela for definida."
    ),
    "semi": (
        "As quartas de final ainda não terminaram — o chaveamento da "
        "semifinal será exibido assim que elas forem definidas."
    ),
    "final": (
        "A semifinal ainda não terminou — o chaveamento da final será "
        "exibido assim que ela for definida."
    ),
}


@dataclass(frozen=True)
class EstadoCopa:
    temporada: int | None
    fase: str | None
    rodadas_fase: range | None = None
    definitivo: bool = False
    tem_parcial: bool = False
    motivo_bloqueio: str | None = None
    grupos: dict[str, dict] | None = None
    times_fora: list[str] | None = None
    resultados_mata_mata: list[dict] | None = None
    tabela_mata_mata: pd.DataFrame | None = None
    vencedores: list[str] | None = None


def _construir_indice_pontuacoes(pontuacoes):
    """Indexa pontuações por `(nome_time, rodada)` para consultas O(1)."""
    if pontuacoes.empty:
        return {}
    return {
        (row.nome_time, int(row.rodada)): round(float(row.pontuacao), 2)
        for row in pontuacoes[["nome_time", "rodada", "pontuacao"]].itertuples(index=False)
    }


def _rodadas_parciais(pontuacoes):
    """Conjunto de rodadas registradas que ainda estão com `definitivo == False`."""
    if pontuacoes.empty or "definitivo" not in pontuacoes.columns:
        return set()
    parciais = ~pontuacoes["definitivo"].astype("boolean").fillna(True).astype(bool)
    return {int(r) for r in pontuacoes.loc[parciais, "rodada"].unique()}


def _ultima_rodada_definitiva(pontuacoes):
    """Última rodada registrada com `definitivo == True` (ou 0 se não houver)."""
    if pontuacoes.empty:
        return 0
    if "definitivo" not in pontuacoes.columns:
        return int(pontuacoes["rodada"].max())
    defs = pontuacoes["definitivo"].astype("boolean").fillna(True).astype(bool)
    rodadas_def = pontuacoes.loc[defs, "rodada"]
    return int(rodadas_def.max()) if not rodadas_def.empty else 0


def determinar_temporada_e_fase_atual_copa(rodada_atual, temporadas_copa):
    for numero, config in temporadas_copa.items():
        for fase, rodadas in config.fases.items():
            if rodada_atual in rodadas:
                return numero, fase
    return None, None


def rodadas_disputadas(rodadas_fase, rodada_atual):
    fim = min(rodada_atual, rodadas_fase.stop - 1)
    return range(rodadas_fase.start, fim + 1)


def fase_esta_definida(rodada_definitiva, rodadas_fase):
    """Uma fase só está definida quando sua última rodada já é definitiva."""
    return rodada_definitiva >= rodadas_fase.stop - 1


def _montar_grupo(
    indice_pts, times_grupo, rodadas_fase, rodadas_validas, definitivo, n_classificados=3
):
    rodadas_todas = list(rodadas_fase)
    rodadas_ativas = set(rodadas_validas)
    linhas = []
    for time in times_grupo:
        linha = {"time": time}
        total = 0.0
        for i, rodada in enumerate(rodadas_todas, start=1):
            valor = indice_pts.get((time, rodada)) if rodada in rodadas_ativas else None
            linha[f"jogo_{i}"] = valor
            if valor is not None:
                total += valor
        linha["total"] = round(total, 2)
        linhas.append(linha)

    tabela = (
        pd.DataFrame(linhas)
        .sort_values("total", ascending=False, kind="stable")
        .reset_index(drop=True)
    )
    classificacao = (
        tabela[["time", "total"]]
        .rename(columns={"time": "nome_time", "total": "pontuacao_total"})
        .copy()
    )
    top_n = tabela["time"].head(n_classificados).tolist()
    dados = {
        "classificacao": classificacao,
        "tabela_jogo_a_jogo": tabela,
        "definitivo": definitivo,
    }
    if definitivo:
        dados["classificados"] = top_n
    else:
        dados["classificados_provisorios"] = top_n
    return dados


def resolver_posicao_copa(posicao, grupos_resolvidos, times_fora):
    if posicao.startswith("fora_"):
        return times_fora[int(posicao.split("_")[1]) - 1]

    colocacao, nome_grupo = posicao.split("_", 1)
    dados_grupo = grupos_resolvidos[nome_grupo]
    if not dados_grupo["definitivo"]:
        raise ValueError(f"{nome_grupo} ainda não fechou")
    return dados_grupo["classificados"][int(colocacao) - 1]


def _montar_fase_mata_mata(indice_pts, confrontos, rodadas_fase, rodadas_validas, definitivo):
    rodadas_todas = list(rodadas_fase)
    rodadas_ativas = list(rodadas_validas)
    rodadas_ativas_set = set(rodadas_ativas)

    resultados = []
    linhas_tabela = []
    for time1, time2 in confrontos:
        linha = {"time1": time1}
        total1 = 0.0
        for i, rodada in enumerate(rodadas_todas, start=1):
            valor = indice_pts.get((time1, rodada)) if rodada in rodadas_ativas_set else None
            linha[f"jogo_{i}_time1"] = valor
            if valor is not None:
                total1 += valor
        total1 = round(total1, 2)
        linha["total_time1"] = total1
        linha["sep"] = "x"

        total2 = 0.0
        for i, rodada in enumerate(rodadas_todas, start=1):
            valor = indice_pts.get((time2, rodada)) if rodada in rodadas_ativas_set else None
            linha[f"jogo_{i}_time2"] = valor
            if valor is not None:
                total2 += valor
        total2 = round(total2, 2)
        linha["total_time2"] = total2
        linha["time2"] = time2
        linhas_tabela.append(linha)

        time_a_frente = time1 if total1 >= total2 else time2
        resultado = {
            "time1": time1,
            "time2": time2,
            "pontuacao_time1": total1,
            "pontuacao_time2": total2,
            "rodadas": rodadas_ativas,
            "definitivo": definitivo,
        }
        if definitivo:
            resultado["vencedor"] = time_a_frente
        else:
            resultado["lider_parcial"] = time_a_frente
        resultados.append(resultado)

    vencedores = [r["vencedor"] for r in resultados] if definitivo else None
    return resultados, pd.DataFrame(linhas_tabela), vencedores


def resolver_copa(
    pontuacoes,
    temporadas_copa,
    rodada_exibida,
    rodada_maxima_definitiva=None,
):
    """Resolve a Copa até a fase correspondente a `rodada_exibida`.

    - `rodada_exibida`: rodada sendo consultada (pode ser futura no app).
    - `rodada_maxima_definitiva`: última rodada com pontuação **definitiva**
      (usada para saber se a fase já fechou de verdade). Se omitida, usa a
      maior rodada definitiva presente em `pontuacoes` até `rodada_exibida`.
    """
    temporada_num, fase_atual = determinar_temporada_e_fase_atual_copa(
        rodada_exibida, temporadas_copa
    )
    if temporada_num is None:
        return EstadoCopa(temporada=None, fase=None)

    config = temporadas_copa[temporada_num]
    pontuacoes_ate = pontuacoes[pontuacoes["rodada"] <= rodada_exibida]
    rodada_ref = (
        _ultima_rodada_definitiva(pontuacoes_ate)
        if rodada_maxima_definitiva is None
        else rodada_maxima_definitiva
    )
    parciais = _rodadas_parciais(pontuacoes_ate)
    indice_pts = _construir_indice_pontuacoes(pontuacoes_ate)

    # 1) Fase de grupos (base para todo o mata-mata)
    rodadas_grupos = config.fases["fase_de_grupos"]
    rodadas_grupos_ativas = rodadas_disputadas(rodadas_grupos, rodada_exibida)
    definitivo_grupos = fase_esta_definida(rodada_ref, rodadas_grupos)
    grupos = {
        nome_grupo: _montar_grupo(
            indice_pts,
            times_grupo,
            rodadas_grupos,
            rodadas_grupos_ativas,
            definitivo_grupos,
        )
        for nome_grupo, times_grupo in config.grupos.items()
    }
    if fase_atual == "fase_de_grupos":
        return EstadoCopa(
            temporada=temporada_num,
            fase="fase_de_grupos",
            rodadas_fase=rodadas_grupos,
            definitivo=definitivo_grupos,
            tem_parcial=any(r in parciais for r in rodadas_grupos_ativas),
            grupos=grupos,
            times_fora=config.times_fora,
        )

    if not definitivo_grupos:
        return EstadoCopa(
            temporada=temporada_num,
            fase=fase_atual,
            rodadas_fase=config.fases[fase_atual],
            motivo_bloqueio=MENSAGEM_BLOQUEIO_FASE["quartas"],
        )

    # 2) Fases mata-mata: quartas -> semi -> final
    confrontos = [
        (
            resolver_posicao_copa(p1, grupos, config.times_fora),
            resolver_posicao_copa(p2, grupos, config.times_fora),
        )
        for p1, p2 in config.chave_quartas
    ]
    chaves_seguintes = {"quartas": config.chave_semi, "semi": config.chave_final}
    ordem_mata_mata = ("quartas", "semi", "final")

    for i, fase in enumerate(ordem_mata_mata):
        rodadas_fase = config.fases[fase]
        rodadas_fase_ativas = rodadas_disputadas(rodadas_fase, rodada_exibida)
        definitivo_fase = fase_esta_definida(rodada_ref, rodadas_fase)
        resultados, tabela, vencedores = _montar_fase_mata_mata(
            indice_pts,
            confrontos,
            rodadas_fase,
            rodadas_fase_ativas,
            definitivo_fase,
        )
        if fase == fase_atual:
            return EstadoCopa(
                temporada=temporada_num,
                fase=fase,
                rodadas_fase=rodadas_fase,
                definitivo=definitivo_fase,
                tem_parcial=any(r in parciais for r in rodadas_fase_ativas),
                resultados_mata_mata=resultados,
                tabela_mata_mata=tabela,
                vencedores=vencedores,
            )

        proxima_fase = ordem_mata_mata[i + 1]
        if vencedores is None:
            return EstadoCopa(
                temporada=temporada_num,
                fase=fase_atual,
                rodadas_fase=config.fases[fase_atual],
                motivo_bloqueio=MENSAGEM_BLOQUEIO_FASE[proxima_fase],
            )
        confrontos = [(vencedores[a], vencedores[b]) for a, b in chaves_seguintes[fase]]

    return EstadoCopa(temporada=temporada_num, fase=fase_atual)


def exibir_classificacao_grupos(grupos):
    for nome_grupo, dados in grupos.items():
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


def exibir_resultado_mata_mata(resultados, nome_fase):
    print(f"Resultados {nome_fase} (rodadas {resultados[0]['rodadas']}):\n")
    for r in resultados:
        desfecho = (
            f"{r['vencedor']} (vencedor)"
            if r["definitivo"]
            else f"{r['lider_parcial']} (parcial)"
        )
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


def exibir_copa_rodada(estado):
    if estado.temporada is None or estado.motivo_bloqueio:
        return
    if estado.fase == "fase_de_grupos":
        exibir_classificacao_grupos(estado.grupos)
        return
    exibir_resultado_mata_mata(
        estado.resultados_mata_mata, NOME_EXIBICAO_FASE[estado.fase]
    )
    if estado.fase == "final" and estado.definitivo and estado.vencedores:
        print(f"Campeão da copa: {estado.vencedores[0]}")
