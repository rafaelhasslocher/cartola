"""Aba Regras."""

import streamlit as st

from ui.componentes import (
    COR_COPA,
    COR_LIGA,
    COR_REGRAS,
    exibir_cabecalho_secao,
    exibir_subtitulo,
)


def render():
    exibir_cabecalho_secao("Regras", COR_REGRAS)

    exibir_subtitulo("Liga", COR_LIGA)
    st.markdown("Em construção.")

    exibir_subtitulo("Copa", COR_COPA)
    st.markdown("Em construção.")
