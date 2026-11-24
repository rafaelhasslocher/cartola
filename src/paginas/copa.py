"""Aba Tabela Copa."""

import pandas as pd
import streamlit as st

from ui.componentes import (
    COR_COPA,
    LARGURA_NOME_TIME,
    exibir_aviso_parcial,
    exibir_cabecalho_secao,
    exibir_grupo_copa,
    exibir_mata_mata_copa,
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

    titulo_fase = NOMES_FASES.get(estado.fase, estado.fase)
    exibir_cabecalho_secao(f"Copa — {titulo_fase}", COR_COPA)
    if estado.tem_parcial:
        exibir_aviso_parcial(
            "⏳ Rodada em andamento — os placares incluem pontuações parciais e podem mudar."
        )

    n_jogos = len(estado.rodadas_fase)

    if estado.fase == "fase_de_grupos":
        for nome_grupo, dados in estado.grupos.items():
            exibir_subtitulo(NOMES_GRUPOS.get(nome_grupo, nome_grupo), COR_COPA)
            exibir_grupo_copa(
                dados["tabela_jogo_a_jogo"],
                config.jogador_por_nome_time,
                n_jogos=n_jogos,
                cor_accent=COR_COPA,
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

    exibir_mata_mata_copa(
        estado.tabela_mata_mata,
        config.jogador_por_nome_time,
        n_jogos=n_jogos,
        titulo_fase=titulo_fase,
        cor_accent=COR_COPA,
    )
