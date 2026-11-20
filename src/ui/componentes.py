"""Componentes visuais reutilizáveis e constantes de tema do app Streamlit."""

from pathlib import Path

import pandas as pd
import streamlit as st

COR_LIGA = "#D98CB3"
COR_COPA = "#B39DDB"
COR_ESTATISTICAS = "#4FB0AE"
COR_REGRAS = "#E3A857"
COR_HALL = "#4A7FC9"

COR_OURO = "rgba(255, 215, 0, 0.28)"
COR_PRATA = "rgba(192, 192, 192, 0.24)"

COR_VENCEDOR = "rgba(46, 204, 113, 0.20)"
COR_PERDEDOR = "rgba(231, 76, 60, 0.16)"
COR_EMPATE = "rgba(241, 196, 15, 0.22)"

COR_TOTAL_TEXTO = "#1F8A56"
COR_TOTAL_TEXTO_NEGATIVO = "#C0392B"

COR_ESTATISTICAS_LIDER = "#5FA8D3"
COR_ESTATISTICAS_TOP5 = "#6FBF8B"
COR_ESTATISTICAS_EMPATE_LIDER = "#7EC8E3"

LARGURA_NOME_TIME = "var(--largura-nome-time)"
LARGURA_PONTOS = "var(--largura-pontos)"
LARGURA_X = "var(--largura-x)"
LARGURA_POSICAO = "var(--largura-posicao)"
LARGURA_TOTAL = "var(--largura-total)"
LARGURA_JOGOS = "var(--largura-jogos)"

_CAMINHO_CSS = Path(__file__).resolve().parent / "estilo.css"


def injetar_estilos(nomes_completos):
    largura_nome_base = f"{max(len(n) for n in nomes_completos) + 2}ch"
    variaveis = (
        ":root {\n"
        f"    --largura-nome-time: {largura_nome_base};\n"
        f"    --cor-liga: {COR_LIGA};\n"
        f"    --cor-copa: {COR_COPA};\n"
        f"    --cor-hall: {COR_HALL};\n"
        f"    --cor-estatisticas: {COR_ESTATISTICAS};\n"
        f"    --cor-regras: {COR_REGRAS};\n"
        "}\n"
    )
    css = _CAMINHO_CSS.read_text(encoding="utf-8")
    st.markdown(f"<style>\n{variaveis}\n{css}\n</style>", unsafe_allow_html=True)


def formatar_pontuacao(valor):
    if valor is None or pd.isna(valor):
        return ""
    texto = f"{float(valor):,.2f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def _numero_ou_zero(valor):
    if valor is None or pd.isna(valor):
        return 0.0
    return float(valor)


def _celula(valor, extra_estilo=""):
    return (
        "<td style='text-align:center; padding: 10px 14px; white-space: nowrap; "
        f"box-sizing: border-box; {extra_estilo}'>{valor}</td>"
    )


def _cor_lado(col_idx, idx_sep, total1, total2, margem_empate=None):
    """Retorna a cor de fundo da célula conforme o resultado do confronto."""
    if margem_empate is not None and abs(total1 - total2) < margem_empate:
        return COR_EMPATE
    if total1 > total2:
        return COR_VENCEDOR if col_idx < idx_sep else COR_PERDEDOR
    if total2 > total1:
        return COR_PERDEDOR if col_idx < idx_sep else COR_VENCEDOR
    return ""


def exibir_tabela(
    df,
    rotulos=None,
    tipo_destaque=None,
    qtd_classificados=3,
    cor_accent=COR_LIGA,
    colunas_total=None,
    colunas_formatar=None,
    larguras_colunas=None,
    bordas_internas=True,
    margem_empate=None,
):
    colunas_originais = list(df.columns)
    colunas = rotulos if rotulos is not None else colunas_originais
    colunas_total = set(colunas_total or ())
    colunas_formatar = set(colunas_formatar or ())

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
        "<th style='text-align:center; padding: 12px 14px; color: white; box-sizing: border-box; "
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
            cor = COR_VENCEDOR if i < qtd_classificados else COR_PERDEDOR
            estilo_linha += f" background-color: {cor};"

        if tipo_destaque in ("mata_mata", "confronto_liga"):
            if tipo_destaque == "mata_mata":
                n_jogos = (len(linha) - 5) // 2
                idx_total1 = n_jogos + 1
                idx_sep = n_jogos + 2
                idx_total2 = n_jogos + 3
                margem = None
            else:
                idx_total1 = colunas_originais.index("pontuacao_time1")
                idx_sep = colunas_originais.index("x")
                idx_total2 = colunas_originais.index("pontuacao_time2")
                margem = margem_empate

            total1 = _numero_ou_zero(linha[idx_total1])
            total2 = _numero_ou_zero(linha[idx_total2])

            for col_idx, valor in enumerate(linha):
                nome_col = colunas_originais[col_idx]
                texto = formatar_pontuacao(valor) if nome_col in colunas_formatar else valor

                if col_idx == idx_sep:
                    estilo_celula = (
                        f"font-weight: 700; color: {cor_accent}; font-size: 1.1rem;"
                    )
                else:
                    cor_fundo = _cor_lado(col_idx, idx_sep, total1, total2, margem_empate=margem)
                    if tipo_destaque == "mata_mata":
                        estilo_celula = " font-weight: 700;"
                        if cor_fundo:
                            estilo_celula += f"background-color: {cor_fundo};"
                        if col_idx in (idx_total1, idx_total2):
                            estilo_celula += (
                                f" color: {COR_TOTAL_TEXTO}; font-size: 1.02rem;"
                            )
                    else:
                        estilo_celula = (
                            f"background-color: {cor_fundo}; font-weight: 700;"
                            if cor_fundo
                            else ""
                        )

                celulas += _celula(texto, estilo_borda_base + estilo_celula)
        else:
            for col_idx, valor in enumerate(linha):
                estilo_celula = ""
                nome_original = (
                    colunas_originais[col_idx]
                    if col_idx < len(colunas_originais)
                    else None
                )
                texto = formatar_pontuacao(valor) if nome_original in colunas_formatar else valor

                if nome_original in ("Nome do time", "time1", "time2"):
                    estilo_celula += " font-weight: 700;"
                if tipo_destaque == "copa":
                    estilo_celula += " font-weight: 700;"

                if nome_original in colunas_total:
                    cor_total = (
                        COR_TOTAL_TEXTO_NEGATIVO
                        if tipo_destaque == "copa" and i >= qtd_classificados
                        else COR_TOTAL_TEXTO
                    )
                    estilo_celula += (
                        f"font-weight: 700; color: {cor_total}; font-size: 0.85rem;"
                    )
                if nome_original == "posicao":
                    estilo_celula += " font-weight: 700; opacity: 0.75;"
                if nome_original == "x":
                    estilo_celula += (
                        f"font-weight: 700; color: {cor_accent}; font-size: 1.1rem;"
                    )
                celulas += _celula(texto, estilo_borda_base + estilo_celula)

        linhas += f"<tr style='{estilo_linha}'>{celulas}</tr>"

    st.markdown(
        "<div class='tabela' style='overflow-x: auto; -webkit-overflow-scrolling: touch; "
        "margin-bottom: 10px; text-align: center; line-height: 1;'>"
        "<div style='display: inline-block; text-align: left; border-radius: 12px; "
        "box-shadow: 0 1px 6px rgba(0,0,0,0.10); border: 1px solid rgba(128,128,128,0.15); "
        "overflow: hidden; line-height: normal;'>"
        f"<table style='border-collapse: collapse; margin: 0;{' table-layout: fixed;' if larguras_colunas else ''}'>"
        f"{colgroup}"
        f"<thead><tr style='background: linear-gradient(90deg, {cor_accent}, {cor_accent}CC);'>"
        f"{cabecalho}</tr></thead>"
        f"<tbody>{linhas}</tbody></table></div></div>",
        unsafe_allow_html=True,
    )


def exibir_subtitulo(texto, cor_accent=COR_LIGA):
    st.markdown(
        "<div style='display:flex; align-items:center; justify-content:center; gap:10px; margin: 18px 0 8px 0;'>"
        f"<div style='width:5px; height:20px; border-radius:3px; background:{cor_accent};'></div>"
        "<h3 style='margin:0; font-size:1.1rem; font-weight:700; color: rgba(70,70,70,0.95);'>"
        f"{texto}</h3></div>",
        unsafe_allow_html=True,
    )


def exibir_cabecalho_secao(texto, cor_accent):
    st.markdown(
        "<div style='padding: 10px 18px; border-radius: 12px; margin-bottom: 12px; "
        f"background: linear-gradient(90deg, {cor_accent}22, transparent); "
        f"border-left: 5px solid {cor_accent};'>"
        f"<span style='font-size:1.25rem; font-weight:800;'>{texto}</span></div>",
        unsafe_allow_html=True,
    )


def obter_param_int(nome, valor_padrao):
    valor = st.query_params.get(nome)
    if valor is None:
        return valor_padrao
    try:
        return int(valor)
    except (TypeError, ValueError):
        return valor_padrao


def seletor_navegacao(chave, opcoes, rotulo_de, param, padrao):
    """Navegação nativa (`st.segmented_control`) sincronizada com `st.query_params`."""
    texto_url = st.query_params.get(param)
    na_url = next((o for o in opcoes if str(o) == texto_url), padrao)

    ultimo = st.session_state.get(f"{chave}_anterior")
    if chave not in st.session_state or (ultimo is not None and na_url != ultimo):
        st.session_state[chave] = na_url

    def _manter_selecao():
        if st.session_state.get(chave) is None:
            st.session_state[chave] = st.session_state.get(f"{chave}_anterior", na_url)

    escolha = st.segmented_control(
        param,
        options=opcoes,
        format_func=rotulo_de,
        key=chave,
        on_change=_manter_selecao,
        label_visibility="collapsed",
    )
    if escolha is None:
        escolha = na_url
    st.session_state[f"{chave}_anterior"] = escolha

    if param in st.query_params:
        if st.query_params[param] != str(escolha):
            st.query_params[param] = str(escolha)
    elif escolha != padrao:
        st.query_params[param] = str(escolha)
    return escolha


def exibir_seletor_rodada(rodadas, valor_atual, param_nome, definitivos=None):
    """Seletor de rodada nativo. Rodadas parciais ganham "⏳" no rótulo."""
    definitivos = definitivos or {}

    def _rotulo(r):
        return f"{r} ⏳" if not definitivos.get(r, True) else str(r)

    return seletor_navegacao(
        f"nav_{param_nome}", list(rodadas), _rotulo, param_nome, valor_atual
    )


def exibir_ranking_titulos(
    titulos, cor_accent, titulo="🏅 Maiores campeões", nomes_longos=False
):
    contagem = {}
    for _, campeao, *_ in titulos:
        contagem[campeao] = contagem.get(campeao, 0) + 1

    ranking_ordenado = sorted(contagem.items(), key=lambda item: (-item[1], item[0]))
    maior_qtd = ranking_ordenado[0][1] if ranking_ordenado else 1

    if nomes_longos:
        estilo_nome = (
            "width:var(--largura-nome-ranking-longo); font-weight:700; "
            "font-size:0.92rem; white-space:normal; overflow:visible; "
            "word-break:break-word; line-height:1.2;"
        )
        largura_qtd = "26px"
    else:
        estilo_nome = (
            "width:100px; font-weight:700; font-size:0.92rem; "
            "white-space:nowrap; overflow:hidden; text-overflow:ellipsis;"
        )
        largura_qtd = "22px"

    linhas_html = ""
    for posicao, (nome, qtd) in enumerate(ranking_ordenado):
        largura_barra = round((qtd / maior_qtd) * 100)
        medalha = ["🥇", "🥈", "🥉"][posicao] if posicao < 3 else "▫️"
        linhas_html += (
            "<div style='display:flex; align-items:center; gap:10px; margin-bottom:9px;'>"
            f"<div style='width:22px; text-align:center; font-size:1rem;'>{medalha}</div>"
            f"<div style='{estilo_nome}'>{nome}</div>"
            "<div style='flex:1; background:rgba(128,128,128,0.12); border-radius:6px; height:16px; overflow:hidden;'>"
            f"<div style='width:{largura_barra}%; height:100%; "
            f"background:linear-gradient(90deg, {cor_accent}, {cor_accent}AA); border-radius:6px;'></div>"
            "</div>"
            f"<div style='width:{largura_qtd}; text-align:right; font-weight:800; color:{cor_accent}; font-size:0.95rem;'>{qtd}</div>"
            "</div>"
        )

    st.markdown(
        "<div style='padding:16px 20px; border-radius:14px; margin-bottom:22px; "
        f"background:{cor_accent}14; border:1px solid {cor_accent}40;'>"
        "<div style='font-weight:800; font-size:1rem; margin-bottom:14px; color:rgba(60,60,60,0.9);'>"
        f"{titulo}</div>"
        f"{linhas_html}</div>",
        unsafe_allow_html=True,
    )


def exibir_linha_do_tempo_titulos(titulos, cor_accent):
    """Lista cronológica (mais recente primeiro) de campeões `(temporada, jogador, time, nota)`."""
    itens_html = ""
    tem_observacao = False
    for temporada, campeao, nome_time, nota in reversed(titulos):
        marcador = ""
        if nota:
            tem_observacao = True
            marcador = f" <span style='opacity:0.75; font-weight:700;'>{nota}</span>"
        rotulo_campeao = (
            f"{nome_time} — <span style='font-weight:800;'>{campeao}</span>"
            if nome_time
            else f"<span style='font-weight:800;'>{campeao}</span>"
        )
        itens_html += (
            "<div style='display:flex; align-items:center; gap:16px; padding:11px 18px; "
            "border-radius:10px; margin-bottom:6px; background:rgba(128,128,128,0.05); "
            "transition: background-color 0.15s;'>"
            f"<div style='min-width:64px; font-weight:800; color:{cor_accent}; font-size:0.95rem;'>{temporada}</div>"
            "<div style='font-size:1.15rem;'>🏆</div>"
            f"<div style='font-weight:600; font-size:1rem;'>{rotulo_campeao}{marcador}</div>"
            "</div>"
        )

    st.markdown(f"<div>{itens_html}</div>", unsafe_allow_html=True)

    if tem_observacao:
        st.caption("*Campeonato não premiado financeiramente.")
