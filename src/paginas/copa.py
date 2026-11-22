"""Aba Tabela Copa."""

import pandas as pd
import streamlit as st

from ui.componentes import (
    COR_COPA,
    LARGURA_JOGOS,
    LARGURA_NOME_TIME,
    LARGURA_POSICAO,
    LARGURA_TOTAL,
    LARGURA_X,
    exibir_aviso_parcial,
    exibir_cabecalho_secao,
    exibir_seletor_rodada,
    exibir_subtitulo,
    exibir_tabela,
    obter_param_int,
)

NOMES_GRUPOS = {"grupo_a": "Grupo 1", "grupo_b": "Grupo 2"}
NOMES_FASES = {
    "fase_de_grupos": "Fase de Grupos",
    "quartas": "Quartas de Final",
    "semi": "Semifinal",
    "final": "Final",
}


def render(temporada):
    config = temporada.config
    pontuacoes_completas = temporada.pontuacoes

    rodadas_jogadas = sorted(int(r) for r in pontuacoes_completas["rodada"].unique())
    rodada_maxima_disputada = rodadas_jogadas[-1] if rodadas_jogadas else 0
    rodadas_disponiveis = sorted(
        set(rodadas_jogadas) | set(range(1, config.ultima_rodada_copa + 1))
    )
    definitivos_copa = (
        pontuacoes_completas.groupby("rodada")["definitivo"].first().fillna(True).to_dict()
        if not pontuacoes_completas.empty
        else {}
    )
    rodada_default = (
        rodada_maxima_disputada if rodada_maxima_disputada else rodadas_disponiveis[0]
    )
    valor_inicial = obter_param_int("rodada_copa", rodada_default)
    if valor_inicial not in rodadas_disponiveis:
        valor_inicial = rodada_default

    rodada_atual = exibir_seletor_rodada(
        rodadas_disponiveis,
        valor_inicial,
        param_nome="rodada_copa",
        definitivos=definitivos_copa,
    )

    estado = temporada.resolver_copa(rodada_exibida=rodada_atual)

    if estado.temporada is None:
        exibir_cabecalho_secao(f"Copa — Rodada {rodada_atual}", COR_COPA)
        if rodada_atual < config.primeira_rodada_copa:
            st.info("Copa ainda não começou.")
        else:
            st.info("Não há confronto de Copa nesta rodada.")
        return

    exibir_cabecalho_secao(
        f"Copa — {NOMES_FASES.get(estado.fase, estado.fase)}", COR_COPA
    )
    if estado.tem_parcial:
        exibir_aviso_parcial(
            "⏳ Rodada em andamento — os placares incluem pontuações parciais e podem mudar."
        )

    if estado.fase == "fase_de_grupos":
        n_jogos = len(estado.rodadas_fase)
        colunas_jogos = [f"jogo_{i}" for i in range(1, n_jogos + 1)]
        rotulos = (
            ["Pos.", "Nome do time"]
            + [f"{i}° Jogo" for i in range(1, n_jogos + 1)]
            + ["Total"]
        )
        larguras = (
            [LARGURA_POSICAO, LARGURA_NOME_TIME]
            + [LARGURA_JOGOS] * n_jogos
            + [LARGURA_TOTAL]
        )

        for nome_grupo, dados in estado.grupos.items():
            exibir_subtitulo(NOMES_GRUPOS.get(nome_grupo, nome_grupo), COR_COPA)
            tabela = dados["tabela_jogo_a_jogo"].copy()
            tabela.insert(0, "posicao", range(1, len(tabela) + 1))
            tabela["time"] = tabela["time"].map(config.nome_completo)
            exibir_tabela(
                tabela,
                rotulos=rotulos,
                tipo_destaque="copa",
                cor_accent=COR_COPA,
                colunas_total=["total"],
                colunas_formatar=colunas_jogos + ["total"],
                larguras_colunas=larguras,
            )

        if estado.times_fora:
            exibir_subtitulo("Já classificados para as quartas", COR_COPA)
            tabela_fora = pd.DataFrame(
                {"Nome do time": [config.nome_completo(t) for t in estado.times_fora]}
            )
            exibir_tabela(
                tabela_fora,
                rotulos=["Time"],
                cor_accent=COR_COPA,
                larguras_colunas=[LARGURA_NOME_TIME],
            )
        return

    if estado.motivo_bloqueio:
        st.info(estado.motivo_bloqueio)
        return

    n_jogos = len(estado.rodadas_fase)
    colunas_t1 = [f"jogo_{i}_time1" for i in range(1, n_jogos + 1)]
    colunas_t2 = [f"jogo_{i}_time2" for i in range(1, n_jogos + 1)]
    colunas_ordem = (
        ["time1"]
        + colunas_t1
        + ["total_time1", "sep", "total_time2"]
        + list(reversed(colunas_t2))
        + ["time2"]
    )
    tabela = estado.tabela_mata_mata[colunas_ordem].copy()
    tabela["time1"] = tabela["time1"].map(config.nome_completo)
    tabela["time2"] = tabela["time2"].map(config.nome_completo)

    rotulos = (
        ["Time"]
        + [f"{i}° Jogo" for i in range(1, n_jogos + 1)]
        + ["Total", "", "Total"]
        + [f"{i}° Jogo" for i in range(n_jogos, 0, -1)]
        + ["Time"]
    )
    exibir_tabela(
        tabela,
        rotulos=rotulos,
        tipo_destaque="mata_mata",
        cor_accent=COR_COPA,
        colunas_formatar=colunas_t1 + ["total_time1"] + colunas_t2 + ["total_time2"],
        larguras_colunas=(
            [LARGURA_NOME_TIME]
            + [LARGURA_JOGOS] * n_jogos
            + [LARGURA_TOTAL, LARGURA_X, LARGURA_TOTAL]
            + [LARGURA_JOGOS] * n_jogos
            + [LARGURA_NOME_TIME]
        ),
    )
