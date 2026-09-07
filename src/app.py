import os
import time
from urllib.parse import urlencode

import pandas as pd
import streamlit as st

from calendario_copa import (
    CALENDARIOS_COPA_POR_TEMPORADA,
    CHAVE_FINAL_POR_TEMPORADA,
    CHAVE_QUARTAS_POR_TEMPORADA,
    CHAVE_SEMI_POR_TEMPORADA,
    GRUPOS_COPA_POR_TEMPORADA,
    TIMES_FORA_POR_TEMPORADA,
)
from calendario_liga import CONFRONTOS_LIGA
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
from regras_liga import MARGEM_EMPATE, RODADA_CORTE_TURNO


def _versao_arquivo(caminho):
    try:
        return os.path.getmtime(caminho)
    except (OSError, TypeError):
        return int(time.time() // 30)


@st.cache_data(show_spinner=False)
def _obter_ranking_cache(caminho, _versao):
    return obter_ranking(caminho)


@st.cache_data(show_spinner=False)
def _obter_resultados_cache(caminho, _versao):
    return obter_resultados(caminho)


@st.cache_data(show_spinner=False)
def _carregar_pontuacoes_cache(caminho, _versao):
    return carregar_pontuacoes(caminho)


NOMES_GRUPOS = {"grupo_a": "Grupo 1", "grupo_b": "Grupo 2"}
NOMES_FASES = {
    "fase_de_grupos": "Fase de Grupos",
    "quartas": "Quartas de Final",
    "semi": "Semifinal",
    "final": "Final",
}


COR_LIGA = "#D98CB3"
COR_COPA = "#B39DDB"

COR_OURO = "rgba(255, 215, 0, 0.28)"
COR_PRATA = "rgba(192, 192, 192, 0.24)"

COR_VENCEDOR = "rgba(46, 204, 113, 0.20)"
COR_PERDEDOR = "rgba(231, 76, 60, 0.16)"
COR_EMPATE = "rgba(241, 196, 15, 0.22)"

COR_TOTAL_TEXTO = "#1F8A56"
COR_TOTAL_TEXTO_NEGATIVO = "#C0392B"


_NOMES_TIMES_LIGA = {c["time1"] for c in CONFRONTOS_LIGA} | {
    c["time2"] for c in CONFRONTOS_LIGA
}
LARGURA_NOME_TIME = f"{max(len(n) for n in _NOMES_TIMES_LIGA) + 2}ch"
LARGURA_PONTOS = "90px"
LARGURA_X = "50px"
LARGURA_POSICAO = "60px"
LARGURA_TOTAL = "150px"
LARGURA_JOGOS = "70px"


CAMPEOES_LIGA = [
    ("2017/2", "Gui", "*"),
    ("2018/1", "Rafa", None),
    ("2018/2", "Gui", None),
    ("2019/1", "Rafa", None),
    ("2019/2", "PV", None),
    ("2020/1", "Rafa", None),
    ("2020/2", "PV", None),
    ("2021/1", "Rafa", None),
    ("2021/2", "Diego", None),
    ("2022/1", "Renata", None),
    ("2022/2", "Ruy", None),
    ("2023/1", "Matheus", None),
    ("2023/2", "Ruy", None),
    ("2024/1", "Matheus", None),
    ("2024/2", "Matheus", None),
    ("2025/1", "Camilla", None),
    ("2025/2", "Rafa", None),
    ("2026/1", "Gui", None),
]

CAMPEOES_COPA = [
    ("2018/1", "Renata", None),
    ("2018/2", "Gui", None),
    ("2019/1", "PV", None),
    ("2019/2", "PV", None),
    ("2020/1", "Renata", None),
    ("2020/2", "Ruy", None),
    ("2021/1", "Diego", None),
    ("2021/2", "Ruy", None),
    ("2022/1", "Ruy", None),
    ("2022/2", "Renata", None),
    ("2023/1", "Gui", None),
    ("2023/2", "Matheus", None),
    ("2024/1", "Iago", None),
    ("2024/2", "Ruy", None),
    ("2025/1", "Matheus", None),
    ("2025/2", "Ian", None),
    ("2026/1", "Gui", None),
]


MAPA_RODADA_LIGA = {
    (c["rodada_brasileirao"], c["time1"], c["time2"]): c["rodada_liga"]
    for c in CONFRONTOS_LIGA
}


def _turno_da_rodada_brasileirao(rodada_brasileirao):
    return 1 if rodada_brasileirao <= RODADA_CORTE_TURNO else 2


def _construir_offsets_rodada_liga_por_turno():
    """A rodada_liga em CONFRONTOS_LIGA é uma contagem acumulada desde o
    início do campeonato (não reinicia no 2º turno). Aqui calculamos, para
    cada turno, o quanto subtrair dela para obter a numeração relativa ao
    turno (que sempre começa em 1)."""
    minimo_por_turno = {}
    for c in CONFRONTOS_LIGA:
        turno = _turno_da_rodada_brasileirao(c["rodada_brasileirao"])
        minimo_atual = minimo_por_turno.get(turno)
        if minimo_atual is None or c["rodada_liga"] < minimo_atual:
            minimo_por_turno[turno] = c["rodada_liga"]
    return {turno: minimo - 1 for turno, minimo in minimo_por_turno.items()}


_OFFSET_RODADA_LIGA_POR_TURNO = _construir_offsets_rodada_liga_por_turno()


def rodada_liga_relativa(rodada_liga, turno):
    """Converte a rodada_liga (numeração acumulada desde o início do
    campeonato) para a numeração relativa ao turno, que reinicia em 1 a
    cada novo turno."""
    return rodada_liga - _OFFSET_RODADA_LIGA_POR_TURNO.get(turno, 0)


def jogos_disputados_no_turno(rodada_brasileirao_atual, turno):
    """Quantidade de rodadas da Liga já disputadas no turno informado, até a
    rodada do Brasileirão selecionada (inclusive)."""
    valores_rodada_liga = [
        c["rodada_liga"]
        for c in CONFRONTOS_LIGA
        if _turno_da_rodada_brasileirao(c["rodada_brasileirao"]) == turno
        and c["rodada_brasileirao"] <= rodada_brasileirao_atual
    ]
    if not valores_rodada_liga:
        return 0
    return rodada_liga_relativa(max(valores_rodada_liga), turno)


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
    return f"<td style='text-align:center; padding: 10px 14px; white-space: nowrap; box-sizing: border-box; {extra_estilo}'>{valor}</td>"


def exibir_tabela(
    df,
    rotulos=None,
    tipo_destaque=None,
    qtd_classificados=3,
    cor_accent=COR_LIGA,
    colunas_total=None,
    larguras_colunas=None,
    bordas_internas=True,
):
    colunas_originais = list(df.columns)
    colunas = rotulos if rotulos is not None else colunas_originais
    colunas_total = colunas_total or []

    colgroup = ""
    if larguras_colunas:
        colgroup = (
            "<colgroup>"
            + "".join(
                f"<col style='width:{largura}; min-width:{largura};'>"
                for largura in larguras_colunas
            )
            + "</colgroup>"
        )

    cabecalho = "".join(
        f"<th style='text-align:center; padding: 12px 14px; color: white; box-sizing: border-box; "
        f"border: none; white-space: nowrap; font-weight: 600; letter-spacing: 0.02em; font-size: 0.9rem;'>{coluna}</th>"
        for coluna in colunas
    )

    estilo_borda_base = (
        "border: none; border-bottom: 1px solid rgba(128, 128, 128, 0.15);"
        if bordas_internas
        else "border: none;"
    )

    linhas = ""
    for i, linha in enumerate(df.itertuples(index=False)):
        estilo_linha = "transition: background-color 0.15s;"
        celulas = ""

        if tipo_destaque == "liga":
            if i == 0:
                estilo_linha += f" background-color: {COR_OURO}; font-weight: 700;"
            elif i == 1:
                estilo_linha += f" background-color: {COR_PRATA}; font-weight: 700;"
            else:
                estilo_linha += " font-weight:620"
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
                estilo_celula = " font-weight: 700;"
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

                celulas += _celula(valor, estilo_borda_base + estilo_celula)

        elif tipo_destaque == "confronto_liga":
            idx_p1 = colunas_originais.index("pontuacao_time1")
            idx_x = colunas_originais.index("x")
            idx_p2 = colunas_originais.index("pontuacao_time2")

            total1 = parse_pontuacao(linha[idx_p1])
            total2 = parse_pontuacao(linha[idx_p2])

            for col_idx, valor in enumerate(linha):
                estilo_celula = ""
                if abs(total1 - total2) < MARGEM_EMPATE and col_idx != idx_x:
                    # empate pela margem
                    estilo_celula += (
                        f"background-color: {COR_EMPATE}; font-weight: 700;"
                    )
                elif total1 > total2:
                    # time1 venceu
                    if col_idx < idx_x:
                        estilo_celula += (
                            f"background-color: {COR_VENCEDOR}; font-weight: 700;"
                        )
                    elif col_idx > idx_x:
                        estilo_celula += (
                            f"background-color: {COR_PERDEDOR}; font-weight: 700;"
                        )
                elif total2 > total1:
                    # time2 venceu
                    if col_idx < idx_x:
                        estilo_celula += (
                            f"background-color: {COR_PERDEDOR}; font-weight: 700;"
                        )
                    elif col_idx > idx_x:
                        estilo_celula += (
                            f"background-color: {COR_VENCEDOR}; font-weight: 700;"
                        )

                celulas += _celula(valor, estilo_borda_base + estilo_celula)

        else:
            for col_idx, valor in enumerate(linha):
                estilo_celula = ""
                nome_original = (
                    colunas_originais[col_idx]
                    if col_idx < len(colunas_originais)
                    else None
                )
                if nome_original in ("Nome do time", "time1", "time2"):
                    estilo_celula += " font-weight: 700;"
                if tipo_destaque == "copa":
                    # times e pontuações da fase de grupos da Copa em negrito,
                    # no mesmo padrão da tabela de confrontos da Liga
                    estilo_celula += " font-weight: 700;"

                if nome_original in colunas_total:
                    cor_total = COR_TOTAL_TEXTO
                    if tipo_destaque == "copa" and i >= qtd_classificados:
                        cor_total = COR_TOTAL_TEXTO_NEGATIVO
                    estilo_celula += (
                        f"font-weight: 700; color: {cor_total}; font-size: 0.85rem;"
                    )
                if nome_original == "posicao":
                    estilo_celula += " font-weight: 700; opacity: 0.75;"
                if nome_original == "x":
                    estilo_celula += (
                        f"font-weight: 700; color: {cor_accent}; font-size: 1.1rem;"
                    )
                celulas += _celula(valor, estilo_borda_base + estilo_celula)

        linhas += f"<tr style='{estilo_linha}'>{celulas}</tr>"

    st.markdown(
        f"<div style='overflow-x: auto; -webkit-overflow-scrolling: touch; "
        f"margin-bottom: 10px; text-align: center; line-height: 1;'>"
        f"<div style='display: inline-block; text-align: left; border-radius: 12px; "
        f"box-shadow: 0 1px 6px rgba(0,0,0,0.10); border: 1px solid rgba(128,128,128,0.15); "
        f"overflow: hidden; line-height: normal;'>"
        f"<table style='border-collapse: collapse; margin: 0;{' table-layout: fixed;' if larguras_colunas else ''}'>"
        f"{colgroup}"
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


def exibir_confrontos_liga(
    df_confrontos, cor_accent, com_pontuacao, rodada_brasileirao, turno
):
    """Exibe a tabela de confrontos da Liga. O título mostra a rodada da Liga
    já relativa ao turno (reiniciando em 1 a cada turno) junto da rodada do
    Brasileirão correspondente. Se houver mais de uma rodada da Liga dentro
    da rodada do Brasileirão selecionada (rodada dupla), separa em uma
    tabela por rodada da Liga, cada uma com seu próprio título."""
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
    else:
        rotulos = ["Mandante", "", "Visitante"]
        larguras = [LARGURA_NOME_TIME, LARGURA_X, LARGURA_NOME_TIME]
        tipo_destaque = None

    rodadas_liga = sorted(
        v for v in df_confrontos["rodada_liga"].unique() if v is not None
    )

    if len(rodadas_liga) > 1:
        for rl in rodadas_liga:
            rl_relativa = rodada_liga_relativa(rl, turno)
            exibir_subtitulo(
                f"Confrontos da Rodada {rl_relativa}",
                cor_accent,
            )
            subset = df_confrontos[df_confrontos["rodada_liga"] == rl].drop(
                columns=["rodada_liga"]
            )
            exibir_tabela(
                subset,
                rotulos=rotulos,
                tipo_destaque=tipo_destaque,
                cor_accent=cor_accent,
                larguras_colunas=larguras,
                bordas_internas=False,
            )
    else:
        if rodadas_liga:
            rl_relativa = rodada_liga_relativa(rodadas_liga[0], turno)
            titulo = f"Confrontos da Rodada {rl_relativa}"
        else:
            titulo = f"Confrontos da Rodada (Brasileirão {rodada_brasileirao})"
        exibir_subtitulo(titulo, cor_accent)
        subset = df_confrontos.drop(columns=["rodada_liga"], errors="ignore")
        exibir_tabela(
            subset,
            rotulos=rotulos,
            tipo_destaque=tipo_destaque,
            cor_accent=cor_accent,
            larguras_colunas=larguras,
            bordas_internas=False,
        )


def construir_href(**overrides):
    """Monta a query string da URL atual, sobrescrevendo apenas as chaves
    passadas em overrides e preservando as demais (ex.: ao trocar a rodada
    da Liga, a aba atual e a rodada da Copa continuam na URL)."""
    params = dict(st.query_params)
    for chave, valor in overrides.items():
        params[chave] = str(valor)
    return "?" + urlencode(params)


def obter_param_int(nome, valor_padrao):
    valor = st.query_params.get(nome)
    if valor is None:
        return valor_padrao
    try:
        return int(valor)
    except (TypeError, ValueError):
        return valor_padrao


ABAS = [
    ("liga", "🏆 Liga", "liga"),
    ("hist_liga", "📜 Histórico Liga", "liga"),
    ("copa", "🥇 Copa", "copa"),
    ("hist_copa", "📜 Histórico Copa", "copa"),
]


def exibir_navegacao_abas(aba_atual):
    """Barra de abas 100% própria (HTML/CSS puro), com uma divisória rosa
    fixa entre o grupamento da Liga e o da Copa. Não depende de nenhuma
    classe interna do Streamlit/BaseWeb, então o visual não pode "quebrar"
    por causa de mudanças de versão."""
    itens_html = ""
    for chave, rotulo, grupo in ABAS:
        classes = "tab-item"
        if chave == aba_atual:
            classes += f" ativa grupo-{grupo}"
        if chave == "copa":
            classes += " divisor"
        href = construir_href(aba=chave)
        itens_html += f"<a class='{classes}' href='{href}' target='_self'>{rotulo}</a>"
    st.markdown(f"<div class='tab-nav'>{itens_html}</div>", unsafe_allow_html=True)


def exibir_seletor_rodada(
    rodadas, valor_atual, param_nome, aba_nome, cor_accent, definitivos=None
):
    """Seletor de rodada 100% próprio (HTML/CSS puro). Cada rodada é um link
    que atualiza a URL; nenhum CSS aqui depende de estrutura de terceiros,
    então as bordas ficam sempre quadradas e não há "brilho" de seleção que
    possa vazar sobre o botão vizinho (usamos box-shadow inset, que nunca
    ultrapassa os limites do próprio elemento)."""
    definitivos = definitivos or {}
    itens_html = ""
    for r in rodadas:
        parcial = not definitivos.get(r, True)
        classes = "rodada-pill"
        if r == valor_atual:
            classes += " ativa"
        if parcial:
            classes += " parcial"
        href = construir_href(aba=aba_nome, **{param_nome: r})
        rotulo = f"{r} - Parcial" if parcial else str(r)
        titulo = " title='Rodada parcial'" if parcial else ""
        itens_html += (
            f"<a class='{classes}' href='{href}' target='_self'{titulo}>{rotulo}</a>"
        )
    st.markdown(
        f"<div class='rodada-nav' style='--accent:{cor_accent};'>{itens_html}</div>",
        unsafe_allow_html=True,
    )


def exibir_ranking_titulos(titulos, cor_accent):
    """Mini painel com o número de títulos por campeão, em forma de barras."""
    contagem = {}
    for _, campeao, _ in titulos:
        contagem[campeao] = contagem.get(campeao, 0) + 1

    ranking_ordenado = sorted(contagem.items(), key=lambda item: (-item[1], item[0]))
    maior_qtd = ranking_ordenado[0][1] if ranking_ordenado else 1

    linhas_html = ""
    for posicao, (nome, qtd) in enumerate(ranking_ordenado):
        largura_barra = round((qtd / maior_qtd) * 100)
        medalha = ["🥇", "🥈", "🥉"][posicao] if posicao < 3 else "▫️"
        linhas_html += (
            "<div style='display:flex; align-items:center; gap:10px; margin-bottom:9px;'>"
            f"<div style='width:22px; text-align:center; font-size:1rem;'>{medalha}</div>"
            f"<div style='width:100px; font-weight:700; font-size:0.92rem; "
            f"white-space:nowrap; overflow:hidden; text-overflow:ellipsis;'>{nome}</div>"
            "<div style='flex:1; background:rgba(128,128,128,0.12); border-radius:6px; height:16px; overflow:hidden;'>"
            f"<div style='width:{largura_barra}%; height:100%; "
            f"background:linear-gradient(90deg, {cor_accent}, {cor_accent}AA); border-radius:6px;'></div>"
            "</div>"
            f"<div style='width:22px; text-align:right; font-weight:800; color:{cor_accent}; font-size:0.95rem;'>{qtd}</div>"
            "</div>"
        )

    st.markdown(
        "<div style='padding:16px 20px; border-radius:14px; margin-bottom:22px; "
        f"background:{cor_accent}14; border:1px solid {cor_accent}40;'>"
        "<div style='font-weight:800; font-size:1rem; margin-bottom:14px; color:rgba(60,60,60,0.9);'>"
        "🏅 Maiores campeões</div>"
        f"{linhas_html}</div>",
        unsafe_allow_html=True,
    )


def exibir_linha_do_tempo_titulos(titulos, cor_accent):
    """Lista cronológica (mais recente primeiro) de campeões por temporada."""
    itens_html = ""
    tem_observacao = False
    for temporada, campeao, nota in reversed(titulos):
        marcador = ""
        if nota:
            tem_observacao = True
            marcador = f" <span style='opacity:0.75; font-weight:700;'>{nota}</span>"
        itens_html += (
            "<div style='display:flex; align-items:center; gap:16px; padding:11px 18px; "
            "border-radius:10px; margin-bottom:6px; background:rgba(128,128,128,0.05); "
            "transition: background-color 0.15s;'>"
            f"<div style='min-width:64px; font-weight:800; color:{cor_accent}; font-size:0.95rem;'>{temporada}</div>"
            "<div style='font-size:1.15rem;'>🏆</div>"
            f"<div style='font-weight:600; font-size:1rem;'>{campeao}{marcador}</div>"
            "</div>"
        )

    st.markdown(f"<div>{itens_html}</div>", unsafe_allow_html=True)

    if tem_observacao:
        st.caption("*Campeonato não premiado financeiramente.")


def exibir_historico(titulos, cor_accent, nome_campeonato):
    exibir_cabecalho_secao(f"Histórico — {nome_campeonato}", cor_accent)
    exibir_ranking_titulos(titulos, cor_accent)
    exibir_subtitulo("Campeões por temporada", cor_accent)
    exibir_linha_do_tempo_titulos(titulos, cor_accent)


st.set_page_config(
    page_title="Cartola Djamba Feipa - 2026",
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
    h1 {{
        font-weight: 800 !important;
        letter-spacing: -0.02em;
        font-size: 2.8rem !important;
        text-align: center;
        color: rgba(20, 19, 20, 0.75) !important;
    }}

    /* ---------- Navegação por abas (HTML/CSS próprio) ---------- */
    .tab-nav {{
        display: flex;
        justify-content: flex-start;
        gap: 8px;
        row-gap: 10px;
        margin-top: 24px;
        margin-bottom: 14px;
        border-bottom: 2px solid rgba(128, 128, 128, 0.15);
        flex-wrap: wrap;
    }}
    .tab-item {{
        padding: 6px 10px 10px 10px;
        font-weight: 800;
        font-size: 0.90rem;
        text-decoration: none !important;
        color: rgba(120, 120, 120, 0.85);
        border-bottom: 4px solid transparent;
        position: relative;
        white-space: nowrap;
    }}
    /* garante que nenhum estilo global de link (ex.: sublinhado padrão do
       navegador ou de folhas de estilo do Streamlit) apareça nas abas */
    .tab-nav a, .tab-nav a:hover, .tab-nav a:visited, .tab-nav a:active {{
        text-decoration: none !important;
    }}
    .tab-item:hover {{
        color: rgba(80, 80, 80, 0.95);
    }}
    .tab-item.ativa.grupo-liga {{
        color: {COR_LIGA};
        border-bottom-color: {COR_LIGA};
    }}
    .tab-item.ativa.grupo-copa {{
        color: {COR_COPA};
        border-bottom-color: {COR_COPA};
    }}
    /* divisória rosa fixa entre o grupamento da Liga e o da Copa */
    .tab-item.divisor {{
        margin-left: 36px;
    }}
    .tabela td, .tabela th {{
        font-size: 0.85rem !important;
        padding: 6px 8px !important;
    }}
    .tab-item.divisor::before {{
        content: "";
        position: absolute;
        left: -20px;
        top: -0.25em;
        bottom: -0.25em;
        width: 4px;
        border-radius: 3px;
        background: {COR_LIGA};
        opacity: 0.9;
    }}
    

    /* ---------- Seletor de rodada (HTML/CSS próprio) ---------- */
    .rodada-nav {{
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 6px;
        margin: 4px 0 18px 0;
    }}
    .rodada-pill {{
        flex: 0 0 46px;
        width: 46px;
        height: 34px;
        display: flex;
        align-items: center;
        justify-content: center;
        text-decoration: none;
        font-weight: 700;
        font-size: 0.85rem;
        color: inherit;
        border: 1px solid rgba(128, 128, 128, 0.35);
        border-radius: 0;
        box-sizing: border-box;
        background: transparent;
    }}
    .rodada-pill:hover {{
        border-color: var(--accent);
    }}
    .rodada-pill.ativa {{
        background: var(--accent);
        border-color: var(--accent);
        color: #fff;
    }}
    /* indicador de "rodada parcial": o rótulo mostra "N - Parcial" por
       extenso, então o botão precisa de largura livre (os demais continuam
       com o tamanho fixo, em formato de quadrado) */
    .rodada-pill.parcial {{
        flex: 0 0 auto;
        width: auto;
        padding: 0 10px;
    }}
    .rodada-pill.parcial:not(.ativa) {{
        border-color: var(--accent);
        box-shadow: inset 0 -3px 0 var(--accent);
    }}
    .rodada-pill.parcial.ativa {{
        box-shadow: inset 0 -3px 0 rgba(255, 255, 255, 0.85);
    }}

    /* ---------- Ajustes só para telas estreitas (celular) ----------
       Tudo aqui fica dentro da media query, então a visualização em
       telas largas (desktop) permanece exatamente igual. */
    @media (max-width: 600px) {{
        .block-container {{
            padding-left: 0.8rem;
            padding-right: 0.8rem;
        }}
        h1 {{
            font-size: 1.9rem !important;
        }}
        .tab-nav {{
            gap: 4px;
        }}
        .tab-item {{
            font-size: 0.75rem;
            padding: 6px 8px 10px 8px;
        }}
        .tab-item.divisor {{
            margin-left: 18px;
        }}
        .tab-item.divisor::before {{
            left: -11px;
        }}
        .rodada-pill {{
            flex: 0 0 38px;
            width: 38px;
            height: 30px;
            font-size: 0.78rem;
        }}
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Cartola Djamba Feipa - 2026")

aba_atual = st.query_params.get("aba", "liga")
if aba_atual not in {chave for chave, _, _ in ABAS}:
    aba_atual = "liga"

exibir_navegacao_abas(aba_atual)

if aba_atual == "liga":
    ranking = _obter_ranking_cache(CAMINHO_RANKING, _versao_arquivo(CAMINHO_RANKING))
    resultados = _obter_resultados_cache(
        CAMINHO_RESULTADOS, _versao_arquivo(CAMINHO_RESULTADOS)
    )

    rodadas_jogadas = sorted(ranking["rodada"].unique())
    rodadas_calendario = sorted({c["rodada_brasileirao"] for c in CONFRONTOS_LIGA})
    rodadas_disponiveis = sorted(set(rodadas_jogadas) | set(rodadas_calendario))

    definitivos_liga = (
        ranking.groupby("rodada")["definitivo"].first().fillna(True).to_dict()
        if "definitivo" in ranking.columns
        else {}
    )
    rodada_default = rodadas_jogadas[-1] if rodadas_jogadas else rodadas_disponiveis[-1]
    rodada_atual = obter_param_int("rodada_liga", rodada_default)
    if rodada_atual not in rodadas_disponiveis:
        rodada_atual = rodada_default

    exibir_seletor_rodada(
        rodadas_disponiveis,
        rodada_atual,
        param_nome="rodada_liga",
        aba_nome="liga",
        cor_accent=COR_LIGA,
        definitivos=definitivos_liga,
    )

    rodada_ja_ocorreu = rodada_atual in rodadas_jogadas
    turno_atual = _turno_da_rodada_brasileirao(rodada_atual)

    if rodada_ja_ocorreu:
        exibir_cabecalho_secao(f"Liga — Rodada {rodada_atual}", COR_LIGA)

        confrontos_rodada = resultados[
            resultados["rodada_brasileirao"] == rodada_atual
        ][["time1", "pontuacao_time1", "pontuacao_time2", "time2"]].copy()
        confrontos_rodada["rodada_liga"] = confrontos_rodada.apply(
            lambda row: MAPA_RODADA_LIGA.get(
                (rodada_atual, row["time1"], row["time2"])
            ),
            axis=1,
        )
        confrontos_rodada.insert(2, "x", "x")
        confrontos_rodada["pontuacao_time1"] = confrontos_rodada["pontuacao_time1"].map(
            formatar_pontuacao
        )
        confrontos_rodada["pontuacao_time2"] = confrontos_rodada["pontuacao_time2"].map(
            formatar_pontuacao
        )

        exibir_confrontos_liga(
            confrontos_rodada,
            COR_LIGA,
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

        confrontos_futuros = pd.DataFrame(
            [
                {
                    "time1": c["time1"],
                    "x": "x",
                    "time2": c["time2"],
                    "rodada_liga": c["rodada_liga"],
                }
                for c in CONFRONTOS_LIGA
                if c["rodada_brasileirao"] == rodada_atual
            ]
        )

        if confrontos_futuros.empty:
            exibir_subtitulo(
                f"Confrontos da Rodada (Brasileirão {rodada_atual})", COR_LIGA
            )
            st.info("Não há confrontos cadastrados para essa rodada.")
        else:
            exibir_confrontos_liga(
                confrontos_futuros,
                COR_LIGA,
                com_pontuacao=False,
                rodada_brasileirao=rodada_atual,
                turno=turno_atual,
            )
            st.caption("A classificação aparece aqui assim que a rodada acontecer.")

elif aba_atual == "hist_liga":
    exibir_historico(CAMPEOES_LIGA, COR_LIGA, "Liga")

elif aba_atual == "copa":
    pontuacoes_completas = _carregar_pontuacoes_cache(
        CAMINHO_DADOS, _versao_arquivo(CAMINHO_DADOS)
    )
    rodadas_disponiveis_copa = sorted(pontuacoes_completas["rodada"].unique())
    definitivos_copa = (
        pontuacoes_completas.groupby("rodada")["definitivo"]
        .first()
        .fillna(True)
        .to_dict()
        if "definitivo" in pontuacoes_completas.columns
        else {}
    )
    rodada_default_copa = rodadas_disponiveis_copa[-1]
    rodada_atual_copa = obter_param_int("rodada_copa", rodada_default_copa)
    if rodada_atual_copa not in rodadas_disponiveis_copa:
        rodada_atual_copa = rodada_default_copa

    exibir_seletor_rodada(
        rodadas_disponiveis_copa,
        rodada_atual_copa,
        param_nome="rodada_copa",
        aba_nome="copa",
        cor_accent=COR_COPA,
        definitivos=definitivos_copa,
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

            if TIMES_FORA_COPA:
                exibir_subtitulo("Já classificados para as quartas", COR_COPA)
                tabela_times_fora = pd.DataFrame({"Nome do time": TIMES_FORA_COPA})
                exibir_tabela(
                    tabela_times_fora,
                    rotulos=["Time"],
                    cor_accent=COR_COPA,
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

elif aba_atual == "hist_copa":
    exibir_historico(CAMPEOES_COPA, COR_COPA, "Copa")
