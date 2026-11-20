"""Ponto de entrada do aplicativo Streamlit (Cartola Djamba Feipa)."""

import streamlit as st

from caminhos import ano_padrao
from campeonato import assinatura_temporada, carregar_temporada
from config_temporada import carregar_config_temporada, carregar_historico_campeoes
from paginas import copa, estatisticas, hall, liga, regras
from ui.componentes import injetar_estilos, seletor_navegacao


@st.cache_data(show_spinner=False)
def _obter_temporada_cache(ano, _assinatura):
    return carregar_temporada(ano)


@st.cache_data(show_spinner=False)
def _obter_historico_cache(_assinatura):
    return carregar_historico_campeoes()


ano = ano_padrao()
config_inicial = carregar_config_temporada(ano)
titulo_pagina = f"{config_inicial.titulo} - {config_inicial.ano}"

st.set_page_config(page_title=titulo_pagina, layout="centered")

assinatura = assinatura_temporada(ano)
temporada = _obter_temporada_cache(ano, assinatura)
config = temporada.config

nomes_completos = [
    config.nome_completo(nome) for nome in config.id_nome_time.values()
]
injetar_estilos(nomes_completos)

# Voltar/Avançar do navegador: o Streamlit não refaz a tela quando só a query
# string muda por popstate. Recarrega a página apenas nesse caso.
st.html(
    "<div class='nav-popstate'></div>"
    "<script>if (!window.__navPopstate) { window.__navPopstate = true;"
    " window.addEventListener('popstate', () => window.location.reload()); }</script>",
    unsafe_allow_javascript=True,
)

st.markdown(f"<h1 style='margin:0;'>{titulo_pagina}</h1>", unsafe_allow_html=True)

abas = [
    ("liga", "🏆 Tabela Liga"),
    ("copa", "🥇 Tabela Copa"),
    ("hall", "🏛️ Hall de Campeões"),
    ("estatisticas", f"📊 Estatísticas {config.ano}"),
    ("regras", "📖 Regras"),
]
rotulos_abas = dict(abas)
aba_atual = seletor_navegacao(
    "nav_aba", [chave for chave, _ in abas], rotulos_abas.get, "aba", "liga"
)

if aba_atual == "liga":
    liga.render(temporada)
elif aba_atual == "copa":
    copa.render(temporada)
elif aba_atual == "hall":
    hall.render(_obter_historico_cache(assinatura))
elif aba_atual == "estatisticas":
    estatisticas.render(temporada)
elif aba_atual == "regras":
    regras.render()
