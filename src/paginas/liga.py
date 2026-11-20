"""Aba Tabela Liga."""

import pandas as pd
import streamlit as st

from ui.componentes import (
    COR_LIGA,
    LARGURA_NOME_TIME,
    LARGURA_PONTOS,
    LARGURA_POSICAO,
    LARGURA_TOTAL,
    LARGURA_X,
    exibir_cabecalho_secao,
    exibir_seletor_rodada,
    exibir_subtitulo,
    exibir_tabela,
    obter_param_int,
)


def _exibir_confrontos_liga(
    df_confrontos, temporada, com_pontuacao, rodada_brasileirao, turno
):
    if com_pontuacao:
        rotulos = ["Mandante", "Pontos", "", "Pontos", "Visitante"]
        larguras = [
            LARGURA_NOME_TIME,
            LARGURA_PONTOS,
            LARGURA_X,
            LARGURA_PONTOS,
            LARGURA_NOME_TIME,
        ]
        tipo_destaque = "confronto_liga"
        colunas_formatar = ("pontuacao_time1", "pontuacao_time2")
    else:
        rotulos = ["Mandante", "", "Visitante"]
        larguras = [LARGURA_NOME_TIME, LARGURA_X, LARGURA_NOME_TIME]
        tipo_destaque = None
        colunas_formatar = ()

    rodadas_liga = sorted(
        v for v in df_confrontos["rodada_liga"].unique() if pd.notna(v)
    )
    grupos = (
        [
            (
                f"Confrontos da Rodada {temporada.rodada_liga_relativa(rl, turno)}",
                df_confrontos[df_confrontos["rodada_liga"] == rl].drop(
                    columns=["rodada_liga"]
                ),
            )
            for rl in rodadas_liga
        ]
        if rodadas_liga
        else [
            (
                f"Confrontos da Rodada (Brasileirão {rodada_brasileirao})",
                df_confrontos.drop(columns=["rodada_liga"], errors="ignore"),
            )
        ]
    )

    for titulo, subset in grupos:
        exibir_subtitulo(titulo, COR_LIGA)
        exibir_tabela(
            subset,
            rotulos=rotulos,
            tipo_destaque=tipo_destaque,
            cor_accent=COR_LIGA,
            colunas_formatar=colunas_formatar,
            larguras_colunas=larguras,
            bordas_internas=False,
            margem_empate=temporada.config.regras.margem_empate,
        )


def render(temporada):
    config = temporada.config
    ranking = temporada.ranking_liga
    resultados = temporada.resultados_liga

    rodadas_jogadas = sorted(int(r) for r in ranking["rodada"].unique())
    rodadas_calendario = sorted(
        int(r) for r in config.confrontos_liga["rodada_brasileirao"].unique()
    )
    rodadas_disponiveis = sorted(set(rodadas_jogadas) | set(rodadas_calendario))

    definitivos_liga = (
        ranking.groupby("rodada")["definitivo"].first().fillna(True).to_dict()
        if not ranking.empty
        else {}
    )
    rodada_default = rodadas_jogadas[-1] if rodadas_jogadas else rodadas_disponiveis[-1]
    valor_inicial = obter_param_int("rodada_liga", rodada_default)
    if valor_inicial not in rodadas_disponiveis:
        valor_inicial = rodada_default

    rodada_atual = exibir_seletor_rodada(
        rodadas_disponiveis,
        valor_inicial,
        param_nome="rodada_liga",
        definitivos=definitivos_liga,
    )

    rodada_ja_ocorreu = rodada_atual in rodadas_jogadas
    turno_atual = temporada.turno_da_rodada(rodada_atual)

    if rodada_ja_ocorreu:
        exibir_cabecalho_secao(f"Liga — Rodada {rodada_atual}", COR_LIGA)

        confrontos_rodada = resultados[
            resultados["rodada_brasileirao"] == rodada_atual
        ][["time1", "pontuacao_time1", "pontuacao_time2", "time2", "rodada_liga"]].copy()
        confrontos_rodada["time1"] = confrontos_rodada["time1"].map(config.nome_completo)
        confrontos_rodada["time2"] = confrontos_rodada["time2"].map(config.nome_completo)
        confrontos_rodada.insert(2, "x", "x")

        _exibir_confrontos_liga(
            confrontos_rodada,
            temporada,
            com_pontuacao=True,
            rodada_brasileirao=rodada_atual,
            turno=turno_atual,
        )

        ranking_turno = (
            ranking[
                (ranking["rodada"] == rodada_atual) & (ranking["turno"] == turno_atual)
            ]
            .drop(columns=["turno", "rodada", "definitivo"], errors="ignore")
            .sort_values(by=["pontos", "pontuacao_total"], ascending=False)
            .reset_index(drop=True)
            .copy()
        )
        ranking_turno["time"] = ranking_turno["time"].map(config.nome_completo)
        ranking_turno.insert(0, "posicao", range(1, len(ranking_turno) + 1))

        exibir_subtitulo(f"Classificação {turno_atual}º turno", COR_LIGA)
        exibir_tabela(
            ranking_turno,
            rotulos=["Pos.", "Nome do time", "Pontos", "Pontuação Total"],
            tipo_destaque="liga",
            cor_accent=COR_LIGA,
            colunas_total=["pontuacao_total"],
            colunas_formatar=["pontuacao_total"],
            larguras_colunas=[
                LARGURA_POSICAO,
                LARGURA_NOME_TIME,
                LARGURA_PONTOS,
                LARGURA_TOTAL,
            ],
        )
    else:
        exibir_cabecalho_secao(
            f"Liga — Rodada {rodada_atual} (ainda não disputada)", COR_LIGA
        )

        futuros = config.confrontos_liga[
            config.confrontos_liga["rodada_brasileirao"] == rodada_atual
        ]
        if futuros.empty:
            exibir_subtitulo(
                f"Confrontos da Rodada (Brasileirão {rodada_atual})", COR_LIGA
            )
            st.info("Não há confrontos cadastrados para essa rodada.")
        else:
            confrontos_futuros = pd.DataFrame(
                {
                    "time1": futuros["time1"].map(config.nome_completo),
                    "x": "x",
                    "time2": futuros["time2"].map(config.nome_completo),
                    "rodada_liga": futuros["rodada_liga"],
                }
            )
            _exibir_confrontos_liga(
                confrontos_futuros,
                temporada,
                com_pontuacao=False,
                rodada_brasileirao=rodada_atual,
                turno=turno_atual,
            )
            st.caption("A classificação aparece aqui assim que a rodada acontecer.")
