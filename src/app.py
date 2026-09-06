import streamlit as st

from caminhos import CAMINHO_RANKING, CAMINHO_RESULTADOS, CAMINHO_RESULTADOS_COPA
from dados.persistencia import obter_copa, obter_ranking, obter_resultados
from regras_liga import RODADA_CORTE_TURNO

st.title("Cartola - Liga e Copa")

ranking = obter_ranking(CAMINHO_RANKING)
resultados = obter_resultados(CAMINHO_RESULTADOS)

rodada_atual = ranking["rodada"].max()
turno_atual = 1 if rodada_atual <= RODADA_CORTE_TURNO else 2

st.header(f"Liga - rodada {rodada_atual}")

confrontos_rodada = resultados[resultados["rodada_brasileirao"] == rodada_atual][
    ["time1", "pontuacao_time1", "pontuacao_time2", "time2"]
].rename(
    columns={
        "time1": "Mandante",
        "pontuacao_time1": "Pontos Mandante",
        "pontuacao_time2": "Pontos Visitante",
        "time2": "Visitante",
    }
)
st.subheader("Confrontos da rodada")
st.dataframe(confrontos_rodada, hide_index=True)

ranking_turno = (
    ranking[(ranking["rodada"] == rodada_atual) & (ranking["turno"] == turno_atual)]
    .drop(columns=["turno", "rodada"])
    .sort_values(by=["pontos", "pontuacao_total"], ascending=False)
    .rename(
        columns={
            "time": "Nome do time",
            "pontos": "Pontos",
            "pontuacao_total": "Pontuação Total",
        }
    )
)
st.subheader(f"Classificação {turno_atual}º turno")
st.dataframe(ranking_turno, hide_index=True)

st.header("Copa")

copa = obter_copa(CAMINHO_RESULTADOS_COPA)

if copa.empty:
    st.write("Copa ainda não começou.")
else:
    rodada_copa_atual = copa["rodada"].max()
    copa_atual = copa[copa["rodada"] == rodada_copa_atual]
    fase_atual = copa_atual["fase"].iloc[0]

    if fase_atual == "fase_de_grupos":
        st.subheader(f"Classificação dos grupos - rodada {rodada_copa_atual}")
        for grupo in sorted(copa_atual["grupo"].dropna().unique()):
            st.write(f"Grupo {grupo}")
            classificacao_grupo = (
                copa_atual[copa_atual["grupo"] == grupo][
                    ["posicao", "time", "pontuacao_total"]
                ]
                .sort_values(by="posicao")
                .rename(
                    columns={
                        "posicao": "Posição",
                        "time": "Nome do time",
                        "pontuacao_total": "Pontuação Total",
                    }
                )
            )
            st.dataframe(classificacao_grupo, hide_index=True)
    else:
        st.subheader(f"{fase_atual} - rodada {rodada_copa_atual}")
        mata_mata = copa_atual[
            [
                "time1",
                "pontuacao_time1",
                "pontuacao_time2",
                "time2",
                "vencedor",
                "lider_parcial",
            ]
        ].rename(
            columns={
                "time1": "Mandante",
                "pontuacao_time1": "Pontos Mandante",
                "pontuacao_time2": "Pontos Visitante",
                "time2": "Visitante",
                "vencedor": "Vencedor",
                "lider_parcial": "Líder parcial",
            }
        )
        st.dataframe(mata_mata, hide_index=True)
