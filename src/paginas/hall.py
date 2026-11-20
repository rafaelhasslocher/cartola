"""Aba Hall de Campeões."""

import streamlit as st

from ui.componentes import (
    COR_COPA,
    COR_LIGA,
    exibir_cabecalho_secao,
    exibir_linha_do_tempo_titulos,
    exibir_ranking_titulos,
    exibir_subtitulo,
    seletor_navegacao,
)


def _exibir_historico(titulos, cor_accent, nome_campeonato):
    exibir_cabecalho_secao(f"Histórico — {nome_campeonato}", cor_accent)
    exibir_ranking_titulos(titulos, cor_accent)
    exibir_subtitulo("Campeões por temporada", cor_accent)
    exibir_linha_do_tempo_titulos(titulos, cor_accent)


def render(historico):
    sub_inicial = st.query_params.get("sub_hall", "liga")
    if sub_inicial not in {"liga", "copa"}:
        sub_inicial = "liga"

    rotulos = {"liga": "Liga", "copa": "Copa"}
    sub_hall = seletor_navegacao(
        "nav_sub_hall", ["liga", "copa"], rotulos.get, "sub_hall", sub_inicial
    )
    if sub_hall == "liga":
        _exibir_historico(historico.get("liga", []), COR_LIGA, "Liga")
    else:
        _exibir_historico(historico.get("copa", []), COR_COPA, "Copa")
