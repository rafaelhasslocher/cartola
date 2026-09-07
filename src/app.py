import streamlit as st

from calendario_copa import (
    CALENDARIOS_COPA_POR_TEMPORADA,
    CHAVE_FINAL_POR_TEMPORADA,
    CHAVE_QUARTAS_POR_TEMPORADA,
    CHAVE_SEMI_POR_TEMPORADA,
    GRUPOS_COPA_POR_TEMPORADA,
    TIMES_FORA_POR_TEMPORADA,
)
from caminhos import CAMINHO_DADOS, CAMINHO_RANKING, CAMINHO_RESULTADOS
from copa.logica import (
    definir_classificados_fase_de_grupos,
    determinar_temporada_e_fase_atual_copa,
    montar_confrontos_iniciais,
    montar_confrontos_por_indice,
    montar_fase_mata_mata,
    montar_tabela_jogo_a_jogo_grupo,
    montar_tabela_jogo_a_jogo_mata_mata,
    rodadas_disputadas,
)
from dados.persistencia import carregar_pontuacoes, obter_ranking, obter_resultados
from regras_liga import RODADA_CORTE_TURNO

NOMES_GRUPOS = {"grupo_a": "Grupo 1", "grupo_b": "Grupo 2"}
NOMES_FASES = {
    "fase_de_grupos": "Fase de Grupos",
    "quartas": "Quartas de Final",
    "semi": "Semifinal",
    "final": "Final",
}


def formatar_pontuacao(valor):
    if valor is None:
        return ""
    texto = f"{valor:,.2f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def exibir_tabela(df, rotulos=None, tipo_destaque=None, qtd_classificados=3):
    colunas = rotulos if rotulos is not None else list(df.columns)

    cabecalho = "".join(
        f"<th style='text-align:center; padding: 12px; border-bottom: 2px solid rgba(128, 128, 128, 0.4); opacity: 0.8;'>{coluna}</th>"
        for coluna in colunas
    )

    linhas = ""
    for i, linha in enumerate(df.itertuples(index=False)):
        estilo_linha = "border-bottom: 1px solid rgba(128, 128, 128, 0.15);"
        celulas = ""

        if tipo_destaque == "liga":
            if i == 0:
                estilo_linha += (
                    " background-color: rgba(255, 215, 0, 0.20); font-weight: bold;"
                )
            elif i == 1:
                estilo_linha += " background-color: rgba(255, 215, 0, 0.05);"
        elif tipo_destaque == "copa" and i < qtd_classificados:
            estilo_linha += " background-color: rgba(46, 204, 113, 0.15);"

        if tipo_destaque == "mata_mata":
            n_jogos = (len(linha) - 5) // 2
            idx_total1 = n_jogos + 1
            idx_sep = n_jogos + 2
            idx_total2 = n_jogos + 3

            def parse_pontuacao(v):
                if not v or str(v).strip() == "":
                    return 0.0
                try:
                    return float(str(v).replace(".", "").replace(",", "."))
                except:
                    return 0.0

            total1 = parse_pontuacao(linha[idx_total1])
            total2 = parse_pontuacao(linha[idx_total2])

            cor_vencedor = "rgba(46, 204, 113, 0.15)"
            cor_perdedor = "rgba(231, 76, 60, 0.15)"

            for col_idx, valor in enumerate(linha):
                estilo_celula = "text-align:center; padding: 10px;"

                if total1 > total2:
                    if col_idx < idx_sep:
                        estilo_celula += f" background-color: {cor_vencedor};"
                    elif col_idx > idx_sep:
                        estilo_celula += f" background-color: {cor_perdedor};"
                elif total2 > total1:
                    if col_idx < idx_sep:
                        estilo_celula += f" background-color: {cor_perdedor};"
                    elif col_idx > idx_sep:
                        estilo_celula += f" background-color: {cor_vencedor};"

                celulas += f"<td style='{estilo_celula}'>{valor}</td>"
        else:
            for valor in linha:
                celulas += f"<td style='text-align:center; padding: 10px;'>{valor}</td>"

        linhas += f"<tr style='{estilo_linha}'>{celulas}</tr>"

    st.markdown(
        f"<div style='overflow-x: auto; margin-bottom: 32px; border: 1px solid rgba(128, 128, 128, 0.2); border-radius: 8px;'>"
        f"<table style='width: 100%; border-collapse: collapse;'>"
        f"<thead><tr>{cabecalho}</tr></thead>"
        f"<tbody>{linhas}</tbody></table></div>",
        unsafe_allow_html=True,
    )


def exibir_subtitulo(texto):
    st.markdown(f"<h3 style='text-align:center'>{texto}</h3>", unsafe_allow_html=True)


def montar_rotulo_rodada(definitivos):
    def rotulo(rodada):
        if not definitivos.get(rodada, True):
            return f"{rodada} - Parcial"
        return str(rodada)

    return rotulo


st.title("Cartola - Liga e Copa")

st.markdown(
    """
    <style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        margin-bottom: 16px;
    }
    .stTabs [data-baseweb="tab"] {
        font-weight: 600;
        padding-bottom: 8px;
    }
    h3 {
        color: rgba(128, 128, 128, 0.9);
        margin-top: 24px;
        margin-bottom: 16px;
        font-size: 1.3rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

aba_liga, aba_copa = st.tabs(["Liga", "Copa"])

with aba_liga:
    ranking = obter_ranking(CAMINHO_RANKING)
    resultados = obter_resultados(CAMINHO_RESULTADOS)

    rodadas_disponiveis = sorted(ranking["rodada"].unique())
    definitivos_liga = (
        ranking.groupby("rodada")["definitivo"].first().fillna(True).to_dict()
        if "definitivo" in ranking.columns
        else {}
    )
    rodada_atual = st.segmented_control(
        "Rodada",
        rodadas_disponiveis,
        default=rodadas_disponiveis[-1],
        format_func=montar_rotulo_rodada(definitivos_liga),
        key="rodada_liga",
    )
    turno_atual = 1 if rodada_atual <= RODADA_CORTE_TURNO else 2

    st.header(f"Liga - Rodada {rodada_atual}")

    confrontos_rodada = resultados[resultados["rodada_brasileirao"] == rodada_atual][
        ["time1", "pontuacao_time1", "pontuacao_time2", "time2"]
    ].copy()
    confrontos_rodada["pontuacao_time1"] = confrontos_rodada["pontuacao_time1"].map(
        formatar_pontuacao
    )
    confrontos_rodada["pontuacao_time2"] = confrontos_rodada["pontuacao_time2"].map(
        formatar_pontuacao
    )
    exibir_subtitulo("Confrontos da rodada")
    exibir_tabela(
        confrontos_rodada, rotulos=["Mandante", "Pontos", "Pontos", "Visitante"]
    )

    ranking_turno = (
        ranking[(ranking["rodada"] == rodada_atual) & (ranking["turno"] == turno_atual)]
        .drop(columns=["turno", "rodada", "definitivo"], errors="ignore")
        .sort_values(by=["pontos", "pontuacao_total"], ascending=False)
        .copy()
    )
    ranking_turno["pontuacao_total"] = ranking_turno["pontuacao_total"].map(
        formatar_pontuacao
    )
    exibir_subtitulo(f"Classificação {turno_atual}º turno")
    exibir_tabela(
        ranking_turno,
        rotulos=["Nome do time", "Pontos", "Pontuação Total"],
        tipo_destaque="liga",
    )

with aba_copa:
    pontuacoes_completas = carregar_pontuacoes(CAMINHO_DADOS)
    rodadas_disponiveis_copa = sorted(pontuacoes_completas["rodada"].unique())
    definitivos_copa = (
        pontuacoes_completas.groupby("rodada")["definitivo"]
        .first()
        .fillna(True)
        .to_dict()
        if "definitivo" in pontuacoes_completas.columns
        else {}
    )
    rodada_atual_copa = st.segmented_control(
        "Rodada",
        rodadas_disponiveis_copa,
        default=rodadas_disponiveis_copa[-1],
        format_func=montar_rotulo_rodada(definitivos_copa),
        key="rodada_copa",
    )
    pontuacoes = pontuacoes_completas[
        pontuacoes_completas["rodada"] <= rodada_atual_copa
    ]

    temporada_atual, fase_atual = determinar_temporada_e_fase_atual_copa(
        rodada_atual_copa, CALENDARIOS_COPA_POR_TEMPORADA
    )

    if temporada_atual is None:
        st.write("Copa ainda não começou.")
    else:
        GRUPOS_COPA = GRUPOS_COPA_POR_TEMPORADA[temporada_atual]
        TIMES_FORA_COPA = TIMES_FORA_POR_TEMPORADA[temporada_atual]
        CHAVE_QUARTAS_COPA = CHAVE_QUARTAS_POR_TEMPORADA[temporada_atual]
        CHAVE_SEMI_COPA = CHAVE_SEMI_POR_TEMPORADA[temporada_atual]
        CHAVE_FINAL_COPA = CHAVE_FINAL_POR_TEMPORADA[temporada_atual]

        calendario_copa = CALENDARIOS_COPA_POR_TEMPORADA[temporada_atual]
        RODADAS_FASE_DE_GRUPOS = calendario_copa["fase_de_grupos"]
        RODADAS_QUARTAS = calendario_copa["quartas"]
        RODADAS_SEMI = calendario_copa["semi"]
        RODADAS_FINAL = calendario_copa["final"]

        st.header(f"Copa - {NOMES_FASES.get(fase_atual, fase_atual)}")

        if fase_atual == "fase_de_grupos":
            for nome_grupo, times_grupo in GRUPOS_COPA.items():
                exibir_subtitulo(NOMES_GRUPOS.get(nome_grupo, nome_grupo))
                tabela_grupo = montar_tabela_jogo_a_jogo_grupo(
                    pontuacoes, times_grupo, RODADAS_FASE_DE_GRUPOS
                )
                n_jogos = len(list(RODADAS_FASE_DE_GRUPOS))
                for i in range(1, n_jogos + 1):
                    tabela_grupo[f"jogo_{i}"] = tabela_grupo[f"jogo_{i}"].map(
                        formatar_pontuacao
                    )
                tabela_grupo["total"] = tabela_grupo["total"].map(formatar_pontuacao)
                rotulos = (
                    ["Nome do time"]
                    + [f"{i}° Jogo" for i in range(1, n_jogos + 1)]
                    + ["Total"]
                )
                exibir_tabela(tabela_grupo, rotulos=rotulos, tipo_destaque="copa")

        else:
            classificados_grupos = definir_classificados_fase_de_grupos(
                pontuacoes,
                GRUPOS_COPA,
                rodadas_disputadas(RODADAS_FASE_DE_GRUPOS, rodada_atual_copa),
                True,
            )
            confrontos_quartas = montar_confrontos_iniciais(
                CHAVE_QUARTAS_COPA, classificados_grupos, TIMES_FORA_COPA
            )

            if fase_atual == "quartas":
                confrontos_fase = confrontos_quartas
                rodadas_fase = RODADAS_QUARTAS
            else:
                _, vencedores_quartas = montar_fase_mata_mata(
                    pontuacoes,
                    confrontos_quartas,
                    rodadas_disputadas(RODADAS_QUARTAS, rodada_atual_copa),
                    True,
                )
                confrontos_semi = montar_confrontos_por_indice(
                    CHAVE_SEMI_COPA, vencedores_quartas
                )

                if fase_atual == "semi":
                    confrontos_fase = confrontos_semi
                    rodadas_fase = RODADAS_SEMI
                else:
                    _, vencedores_semi = montar_fase_mata_mata(
                        pontuacoes,
                        confrontos_semi,
                        rodadas_disputadas(RODADAS_SEMI, rodada_atual_copa),
                        True,
                    )
                    confrontos_fase = montar_confrontos_por_indice(
                        CHAVE_FINAL_COPA, vencedores_semi
                    )
                    rodadas_fase = RODADAS_FINAL

            tabela_mata_mata = montar_tabela_jogo_a_jogo_mata_mata(
                pontuacoes, confrontos_fase, rodadas_fase
            )
            n_jogos = len(list(rodadas_fase))
            colunas_time1 = [f"jogo_{i}_time1" for i in range(1, n_jogos + 1)]
            colunas_time2 = [f"jogo_{i}_time2" for i in range(1, n_jogos + 1)]
            for coluna in (
                colunas_time1 + ["total_time1"] + colunas_time2 + ["total_time2"]
            ):
                tabela_mata_mata[coluna] = tabela_mata_mata[coluna].map(
                    formatar_pontuacao
                )

            colunas_ordem = (
                ["time1"]
                + colunas_time1
                + ["total_time1", "sep", "total_time2"]
                + list(reversed(colunas_time2))
                + ["time2"]
            )
            tabela_mata_mata = tabela_mata_mata[colunas_ordem]
            rotulos = (
                ["Time"]
                + [f"{i}° Jogo" for i in range(1, n_jogos + 1)]
                + ["Total", "x", "Total"]
                + [f"{i}° Jogo" for i in range(n_jogos, 0, -1)]
                + ["Time"]
            )
            exibir_tabela(tabela_mata_mata, rotulos=rotulos, tipo_destaque="mata_mata")
