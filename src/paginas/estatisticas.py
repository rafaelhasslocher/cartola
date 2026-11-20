"""Aba Estatísticas."""

from textwrap import fill

import streamlit as st

from liga.estatisticas import (
    calcular_maior_pontuador_mas_empatou,
    calcular_top_n_mas_nao_venceu,
    calcular_top_n_por_rodada,
)
from liga.evolucao import montar_evolucao_classificacao, montar_spec_evolucao
from ui.componentes import (
    COR_ESTATISTICAS,
    COR_ESTATISTICAS_EMPATE_LIDER,
    COR_ESTATISTICAS_LIDER,
    COR_ESTATISTICAS_TOP5,
    exibir_cabecalho_secao,
    exibir_ranking_titulos,
    exibir_subtitulo,
)


def render(temporada):
    config = temporada.config
    ranking = temporada.ranking_liga

    exibir_cabecalho_secao(f"Estatísticas {config.ano}", COR_ESTATISTICAS)

    secao = st.radio(
        "Explorar estatísticas",
        ["Evolução", "Desempenho", "Confrontos"],
        horizontal=True,
        key="secao_estatisticas",
    )

    if secao == "Evolução":
        turno_evolucao = st.radio(
            "Campeonato",
            [1, 2],
            format_func=lambda turno: f"{turno}º turno",
            index=(
                1
                if not ranking.empty
                and ranking["rodada"].max() > config.regras.rodada_corte_turno
                else 0
            ),
            horizontal=True,
            key="turno_evolucao",
        )
        exibir_subtitulo("Evolução da classificação", COR_ESTATISTICAS)
        evolucao = montar_evolucao_classificacao(
            ranking,
            turno_evolucao,
            rodada_corte_turno=config.regras.rodada_corte_turno,
        )
        if evolucao.empty:
            st.info("Ainda não há classificação registrada para este turno.")
            return

        times_evolucao = sorted(evolucao["time"].unique())
        with st.expander("Selecionar times", expanded=False):
            selecionados = st.multiselect(
                "Times no gráfico",
                times_evolucao,
                default=times_evolucao,
                format_func=config.nome_completo,
                key="times_evolucao",
            )
        st.caption(
            "Posição por rodada do Brasileirão · 1º lugar no topo · Rodadas duplas consolidadas"
        )
        if not selecionados:
            st.info("Selecione pelo menos um time para visualizar sua trajetória.")
            return

        dados_grafico = evolucao[evolucao["time"].isin(selecionados)].copy()
        dados_grafico["nome"] = dados_grafico["time"].map(config.nome_completo)
        dados_grafico["rotulo_mobile"] = dados_grafico["nome"].map(
            lambda nome: fill(
                nome, width=22, break_long_words=False, break_on_hyphens=False
            )
        )
        dados_grafico["rotulo_desktop"] = dados_grafico["nome"].map(
            lambda nome: fill(
                nome, width=30, break_long_words=False, break_on_hyphens=False
            )
        )
        st.vega_lite_chart(
            dados_grafico,
            montar_spec_evolucao(evolucao, times_evolucao, config.nome_completo),
            width="stretch",
        )
        if not evolucao["definitivo"].all():
            st.caption(
                "Rodadas parciais estão identificadas nos detalhes dos pontos e podem mudar."
            )
        return

    st.caption(
        f"Temporada {config.ano} · Ambos os turnos · Inclui resultados parciais registrados"
    )
    margem = config.regras.margem_empate
    if secao == "Desempenho":
        indicadores = {
            "Maior pontuador": (
                lambda: calcular_top_n_por_rodada(
                    temporada.estatisticas_por_rodada, 1, config.nome_completo
                ),
                COR_ESTATISTICAS_LIDER,
                "Mais vezes maior pontuador da rodada",
            ),
            "Top 3": (
                lambda: calcular_top_n_por_rodada(
                    temporada.estatisticas_por_rodada, 3, config.nome_completo
                ),
                COR_ESTATISTICAS,
                "Mais vezes no Top 3 da rodada",
            ),
        }
    else:
        indicadores = {
            "Top 5 sem vitória": (
                lambda: calcular_top_n_mas_nao_venceu(
                    temporada.estatisticas_por_confronto, 5, margem, config.nome_completo
                ),
                COR_ESTATISTICAS_TOP5,
                "Mais vezes top 5 da rodada, mas perdeu ou empatou na Liga",
            ),
            "Líder com empate": (
                lambda: calcular_maior_pontuador_mas_empatou(
                    temporada.estatisticas_por_confronto, margem, config.nome_completo
                ),
                COR_ESTATISTICAS_EMPATE_LIDER,
                "Mais vezes líder da rodada, mas empatou na Liga",
            ),
        }

    indicador = st.selectbox("Indicador", list(indicadores), key=f"indicador_{secao}")
    calcular, cor, titulo = indicadores[indicador]
    ocorrencias = calcular()
    if ocorrencias:
        exibir_ranking_titulos(ocorrencias, cor, titulo=titulo, nomes_longos=True)
    else:
        st.info("Nenhuma ocorrência registrada para este indicador.")
