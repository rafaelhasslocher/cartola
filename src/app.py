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

# ---------------------------------------------------------------------------
# Paleta de cores da aplicação
# ---------------------------------------------------------------------------
COR_LIGA = "#D98CB3"  # rosa pastel — identidade da aba Liga
COR_COPA = "#B39DDB"  # lilás pastel — identidade da aba Copa

COR_OURO = "rgba(255, 215, 0, 0.28)"
COR_PRATA = "rgba(192, 192, 192, 0.24)"

COR_VENCEDOR = "rgba(46, 204, 113, 0.20)"
COR_PERDEDOR = "rgba(231, 76, 60, 0.16)"

COR_TOTAL_TEXTO = "#1F8A56"  # verde escuro para destacar valores de total


def formatar_pontuacao(valor):
    if valor is None:
        return ""
    texto = f"{valor:,.2f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def parse_pontuacao(v):
    if not v or str(v).strip() == "":
        return 0.0
    try:
        return float(str(v).replace(".", "").replace(",", "."))
    except Exception:
        return 0.0


def _celula(valor, extra_estilo=""):
    return f"<td style='text-align:center; padding: 10px 14px; white-space: nowrap; {extra_estilo}'>{valor}</td>"


def exibir_tabela(
    df,
    rotulos=None,
    tipo_destaque=None,
    qtd_classificados=3,
    cor_accent=COR_LIGA,
    colunas_total=None,
):
    """Renderiza uma tabela HTML estilizada, com largura ajustada ao conteúdo.

    tipo_destaque:
        - "liga": destaca ouro/prata nas 2 primeiras posições
        - "copa": destaca classificados (verde) e eliminados (vermelho) no grupo
        - "confronto_liga": destaca vencedor/perdedor de cada confronto da rodada
        - "mata_mata": destaca vencedor/perdedor com base nos totais
    colunas_total: nomes ORIGINAIS das colunas do df (não o rótulo exibido)
        que devem ser destacadas em negrito/verde como "total".
    """
    colunas_originais = list(df.columns)
    colunas = rotulos if rotulos is not None else colunas_originais
    colunas_total = colunas_total or []

    cabecalho = "".join(
        f"<th style='text-align:center; padding: 12px 14px; color: white; "
        f"white-space: nowrap; font-weight: 600; letter-spacing: 0.02em; font-size: 0.9rem;'>{coluna}</th>"
        for coluna in colunas
    )

    linhas = ""
    for i, linha in enumerate(df.itertuples(index=False)):
        estilo_linha = "border-bottom: 1px solid rgba(128, 128, 128, 0.15); transition: background-color 0.15s;"
        celulas = ""

        if tipo_destaque == "liga":
            if i == 0:
                estilo_linha += f" background-color: {COR_OURO}; font-weight: 600;"
            elif i == 1:
                estilo_linha += f" background-color: {COR_PRATA}; font-weight: 600;"
        elif tipo_destaque == "copa":
            if i < qtd_classificados:
                estilo_linha += f" background-color: {COR_VENCEDOR};"
            else:
                estilo_linha += f" background-color: {COR_PERDEDOR};"

        if tipo_destaque == "mata_mata":
            n_jogos = (len(linha) - 5) // 2
            idx_total1 = n_jogos + 1
            idx_sep = n_jogos + 2
            idx_total2 = n_jogos + 3

            total1 = parse_pontuacao(linha[idx_total1])
            total2 = parse_pontuacao(linha[idx_total2])

            for col_idx, valor in enumerate(linha):
                estilo_celula = ""

                if total1 > total2:
                    if col_idx < idx_sep:
                        estilo_celula += f"background-color: {COR_VENCEDOR};"
                    elif col_idx > idx_sep:
                        estilo_celula += f"background-color: {COR_PERDEDOR};"
                elif total2 > total1:
                    if col_idx < idx_sep:
                        estilo_celula += f"background-color: {COR_PERDEDOR};"
                    elif col_idx > idx_sep:
                        estilo_celula += f"background-color: {COR_VENCEDOR};"

                if col_idx in (idx_total1, idx_total2):
                    estilo_celula += f" font-weight: 700; color: {COR_TOTAL_TEXTO}; font-size: 1.02rem;"
                if col_idx == idx_sep:
                    estilo_celula += (
                        f" font-weight: 700; color: {cor_accent}; font-size: 1.1rem;"
                    )

                celulas += _celula(valor, estilo_celula)

        elif tipo_destaque == "confronto_liga":
            idx_p1 = colunas_originais.index("pontuacao_time1")
            idx_x = colunas_originais.index("x")
            idx_p2 = colunas_originais.index("pontuacao_time2")

            total1 = parse_pontuacao(linha[idx_p1])
            total2 = parse_pontuacao(linha[idx_p2])

            for col_idx, valor in enumerate(linha):
                estilo_celula = ""
                if total1 > total2:
                    if col_idx < idx_x:
                        estilo_celula += f"background-color: {COR_VENCEDOR};"
                    elif col_idx > idx_x:
                        estilo_celula += f"background-color: {COR_PERDEDOR};"
                elif total2 > total1:
                    if col_idx < idx_x:
                        estilo_celula += f"background-color: {COR_PERDEDOR};"
                    elif col_idx > idx_x:
                        estilo_celula += f"background-color: {COR_VENCEDOR};"
                if col_idx == idx_x:
                    estilo_celula += (
                        f"font-weight: 700; color: {cor_accent}; font-size: 1.1rem;"
                    )
                celulas += _celula(valor, estilo_celula)

        else:
            for col_idx, valor in enumerate(linha):
                estilo_celula = ""
                nome_original = (
                    colunas_originais[col_idx]
                    if col_idx < len(colunas_originais)
                    else None
                )
                if nome_original in colunas_total:
                    estilo_celula += f"font-weight: 700; color: {COR_TOTAL_TEXTO}; font-size: 1.02rem;"
                if nome_original == "posicao":
                    estilo_celula += " font-weight: 700; opacity: 0.75;"
                celulas += _celula(valor, estilo_celula)

        linhas += f"<tr style='{estilo_linha}'>{celulas}</tr>"

    st.markdown(
        f"<div style='overflow-x: auto; margin-bottom: 10px; display: flex; justify-content: center; line-height: 1;'>"
        f"<div style='border-radius: 12px; box-shadow: 0 1px 6px rgba(0,0,0,0.10); "
        f"border: 1px solid rgba(128,128,128,0.15); overflow: hidden; line-height: normal;'>"
        f"<table style='border-collapse: collapse; margin: 0;'>"
        f"<thead><tr style='background: linear-gradient(90deg, {cor_accent}, {cor_accent}CC);'>"
        f"{cabecalho}</tr></thead>"
        f"<tbody>{linhas}</tbody></table></div></div>",
        unsafe_allow_html=True,
    )


def exibir_subtitulo(texto, cor_accent=COR_LIGA):
    st.markdown(
        f"<div style='display:flex; align-items:center; justify-content:center; gap:10px; margin: 18px 0 8px 0;'>"
        f"<div style='width:5px; height:20px; border-radius:3px; background:{cor_accent};'></div>"
        f"<h3 style='margin:0; font-size:1.1rem; font-weight:700; color: rgba(70,70,70,0.95);'>"
        f"{texto}</h3></div>",
        unsafe_allow_html=True,
    )


def exibir_cabecalho_secao(texto, cor_accent):
    st.markdown(
        f"<div style='padding: 10px 18px; border-radius: 12px; margin-bottom: 12px; "
        f"background: linear-gradient(90deg, {cor_accent}22, transparent); "
        f"border-left: 5px solid {cor_accent};'>"
        f"<span style='font-size:1.25rem; font-weight:800;'>{texto}</span></div>",
        unsafe_allow_html=True,
    )


def montar_rotulo_rodada(definitivos):
    def rotulo(rodada):
        if not definitivos.get(rodada, True):
            return f"{rodada} - Parcial"
        return str(rodada)

    return rotulo


st.set_page_config(
    page_title="Cartola Djamba Feipa - 2026",
    page_icon="⚽",
    layout="centered",
)

st.markdown(
    f"""
    <style>
    .block-container {{
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 900px;
    }}
    .stTabs [data-baseweb="tab-list"] {{
        gap: 36px;
        margin-bottom: 14px;
        border-bottom: 2px solid rgba(128, 128, 128, 0.15);
        justify-content: center;
    }}
    .stTabs [data-baseweb="tab"] {{
        font-weight: 800;
        font-size: 1.3rem;
        padding: 6px 4px 10px 4px;
    }}
    .stTabs [aria-selected="true"] {{
        color: {COR_LIGA} !important;
    }}
    div[role="radiogroup"] label, .stSegmentedControl label {{
        font-weight: 600;
    }}
    h1 {{
        font-weight: 800 !important;
        letter-spacing: -0.02em;
        font-size: 1.8rem !important;
        text-align: center;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("⚽ Cartola Djamba Feipa - 2026")

aba_liga, aba_copa = st.tabs(["🏆 Liga", "🥇 Copa"])

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

    exibir_cabecalho_secao(f"Liga — Rodada {rodada_atual}", COR_LIGA)

    confrontos_rodada = resultados[resultados["rodada_brasileirao"] == rodada_atual][
        ["time1", "pontuacao_time1", "pontuacao_time2", "time2"]
    ].copy()
    confrontos_rodada.insert(2, "x", "x")
    confrontos_rodada["pontuacao_time1"] = confrontos_rodada["pontuacao_time1"].map(
        formatar_pontuacao
    )
    confrontos_rodada["pontuacao_time2"] = confrontos_rodada["pontuacao_time2"].map(
        formatar_pontuacao
    )

    exibir_subtitulo("Confrontos da rodada", COR_LIGA)
    exibir_tabela(
        confrontos_rodada,
        rotulos=["Mandante", "Pontos", "", "Pontos", "Visitante"],
        tipo_destaque="confronto_liga",
        cor_accent=COR_LIGA,
    )

    ranking_turno = (
        ranking[(ranking["rodada"] == rodada_atual) & (ranking["turno"] == turno_atual)]
        .drop(columns=["turno", "rodada", "definitivo"], errors="ignore")
        .sort_values(by=["pontos", "pontuacao_total"], ascending=False)
        .reset_index(drop=True)
        .copy()
    )
    ranking_turno.insert(0, "posicao", range(1, len(ranking_turno) + 1))
    ranking_turno["pontuacao_total"] = ranking_turno["pontuacao_total"].map(
        formatar_pontuacao
    )

    exibir_subtitulo(f"Classificação {turno_atual}º turno", COR_LIGA)
    exibir_tabela(
        ranking_turno,
        rotulos=["Pos.", "Nome do time", "Pontos", "Pontuação Total"],
        tipo_destaque="liga",
        cor_accent=COR_LIGA,
        colunas_total=["pontuacao_total"],
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
        st.info("Copa ainda não começou.")
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

        exibir_cabecalho_secao(
            f"Copa — {NOMES_FASES.get(fase_atual, fase_atual)}", COR_COPA
        )

        if fase_atual == "fase_de_grupos":
            for nome_grupo, times_grupo in GRUPOS_COPA.items():
                exibir_subtitulo(NOMES_GRUPOS.get(nome_grupo, nome_grupo), COR_COPA)
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
                exibir_tabela(
                    tabela_grupo,
                    rotulos=rotulos,
                    tipo_destaque="copa",
                    cor_accent=COR_COPA,
                    colunas_total=["total"],
                )

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
                + ["Total", "", "Total"]
                + [f"{i}° Jogo" for i in range(n_jogos, 0, -1)]
                + ["Time"]
            )
            exibir_tabela(
                tabela_mata_mata,
                rotulos=rotulos,
                tipo_destaque="mata_mata",
                cor_accent=COR_COPA,
            )
