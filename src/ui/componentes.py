"""Componentes visuais reutilizáveis e constantes de tema do app Streamlit."""

from functools import lru_cache
from pathlib import Path

import pandas as pd
import streamlit as st

COR_LIGA = "#D98CB3"
COR_COPA = "#B39DDB"
COR_ESTATISTICAS = "#4FB0AE"
COR_REGRAS = "#E3A857"
COR_HALL = "#4A7FC9"

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


@lru_cache(maxsize=1)
def _ler_css_base():
    return _CAMINHO_CSS.read_text(encoding="utf-8")


def _estilo_accent(cor):
    return (
        f"--accent:{cor}; --accent-cc:{cor}CC; --accent-aa:{cor}AA; "
        f"--accent-40:{cor}40; --accent-22:{cor}22; --accent-14:{cor}14;"
    )


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
    st.markdown(f"<style>\n{variaveis}\n{_ler_css_base()}\n</style>", unsafe_allow_html=True)


def formatar_pontuacao(valor):
    if valor is None or pd.isna(valor):
        return ""
    texto = f"{float(valor):,.2f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def _numero_ou_zero(valor):
    if valor is None or pd.isna(valor):
        return 0.0
    return float(valor)


def _celula(valor, classes=()):
    attr = f" class='{' '.join(classes)}'" if classes else ""
    return f"<td{attr}>{valor}</td>"


def _classe_lado(col_idx, idx_sep, total1, total2, margem_empate=None):
    if margem_empate is not None and abs(total1 - total2) < margem_empate:
        return "celula-empate"
    if total1 > total2:
        return "celula-vencedor" if col_idx < idx_sep else "celula-perdedor"
    if total2 > total1:
        return "celula-perdedor" if col_idx < idx_sep else "celula-vencedor"
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

    cabecalho = "".join(f"<th>{coluna}</th>" for coluna in colunas)

    linhas = []
    for i, linha in enumerate(df.itertuples(index=False)):
        classe_linha = ""
        if tipo_destaque == "liga":
            classe_linha = "linha-ouro" if i == 0 else ("linha-prata" if i == 1 else "linha-normal")
        elif tipo_destaque == "copa":
            classe_linha = "linha-classificado" if i < qtd_classificados else "linha-eliminado"

        celulas = []
        if tipo_destaque in ("mata_mata", "confronto_liga"):
            if tipo_destaque == "mata_mata":
                n_jogos = (len(linha) - 5) // 2
                idx_total1, idx_sep, idx_total2 = n_jogos + 1, n_jogos + 2, n_jogos + 3
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
                    classes = ["celula-sep"]
                else:
                    classes = ["celula-negrito"]
                    lado = _classe_lado(col_idx, idx_sep, total1, total2, margem_empate=margem)
                    if lado:
                        classes.append(lado)
                    if tipo_destaque == "mata_mata" and col_idx in (idx_total1, idx_total2):
                        classes.append("celula-total-destaque")
                celulas.append(_celula(texto, classes))
        else:
            for col_idx, valor in enumerate(linha):
                nome_original = (
                    colunas_originais[col_idx] if col_idx < len(colunas_originais) else None
                )
                texto = formatar_pontuacao(valor) if nome_original in colunas_formatar else valor
                classes = []
                if nome_original in ("Nome do time", "time1", "time2") or tipo_destaque == "copa":
                    classes.append("celula-negrito")
                if nome_original in colunas_total:
                    classes.append(
                        "celula-total-negativo"
                        if tipo_destaque == "copa" and i >= qtd_classificados
                        else "celula-total"
                    )
                if nome_original == "posicao":
                    classes.append("celula-posicao")
                if nome_original == "x":
                    classes.append("celula-sep")
                celulas.append(_celula(texto, classes))

        tr_attr = f" class='{classe_linha}'" if classe_linha else ""
        linhas.append(f"<tr{tr_attr}>{''.join(celulas)}</tr>")

    classes_tabela = ["tabela-dados"]
    if larguras_colunas:
        classes_tabela.append("largura-fixa")
    if not bordas_internas:
        classes_tabela.append("sem-bordas")

    st.markdown(
        f"<div class='tabela-wrapper'>"
        f"<div class='tabela-card' style='{_estilo_accent(cor_accent)}'>"
        f"<table class='{' '.join(classes_tabela)}'>"
        f"{colgroup}"
        f"<thead><tr>{cabecalho}</tr></thead>"
        f"<tbody>{''.join(linhas)}</tbody></table></div></div>",
        unsafe_allow_html=True,
    )


def exibir_subtitulo(texto, cor_accent=COR_LIGA):
    st.markdown(
        f"<div class='subtitulo-bloco' style='{_estilo_accent(cor_accent)}'>"
        "<div class='subtitulo-barra'></div>"
        f"<h3 class='subtitulo-texto'>{texto}</h3></div>",
        unsafe_allow_html=True,
    )


def exibir_cabecalho_secao(texto, cor_accent):
    st.markdown(
        f"<div class='secao-cabecalho' style='{_estilo_accent(cor_accent)}'>"
        f"<span class='secao-titulo'>{texto}</span></div>",
        unsafe_allow_html=True,
    )


def exibir_aviso_parcial(texto):
    st.markdown(f"<div class='aviso-parcial'>{texto}</div>", unsafe_allow_html=True)


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

    classe_nome = "ranking-nome-longo" if nomes_longos else "ranking-nome"
    classe_qtd = "ranking-qtd ranking-qtd-longo" if nomes_longos else "ranking-qtd"

    linhas_html = []
    for posicao, (nome, qtd) in enumerate(ranking_ordenado):
        largura_barra = round((qtd / maior_qtd) * 100)
        medalha = ["🥇", "🥈", "🥉"][posicao] if posicao < 3 else "▫️"
        linhas_html.append(
            "<div class='ranking-linha'>"
            f"<div class='ranking-medalha'>{medalha}</div>"
            f"<div class='{classe_nome}'>{nome}</div>"
            "<div class='ranking-trilha'>"
            f"<div class='ranking-barra' style='width:{largura_barra}%;'></div>"
            "</div>"
            f"<div class='{classe_qtd}'>{qtd}</div>"
            "</div>"
        )

    st.markdown(
        f"<div class='ranking-card' style='{_estilo_accent(cor_accent)}'>"
        f"<div class='ranking-titulo'>{titulo}</div>"
        f"{''.join(linhas_html)}</div>",
        unsafe_allow_html=True,
    )


def exibir_linha_do_tempo_titulos(titulos, cor_accent):
    """Lista cronológica (mais recente primeiro) de campeões `(temporada, jogador, time, nota)`."""
    itens_html = []
    tem_observacao = False
    for temporada, campeao, nome_time, nota in reversed(titulos):
        marcador = ""
        if nota:
            tem_observacao = True
            marcador = f" <span class='timeline-nota'>{nota}</span>"
        rotulo_campeao = (
            f"{nome_time} — <span class='timeline-campeao'>{campeao}</span>"
            if nome_time
            else f"<span class='timeline-campeao'>{campeao}</span>"
        )
        itens_html.append(
            "<div class='timeline-item'>"
            f"<div class='timeline-temporada'>{temporada}</div>"
            "<div class='timeline-trofeu'>🏆</div>"
            f"<div class='timeline-texto'>{rotulo_campeao}{marcador}</div>"
            "</div>"
        )

    st.markdown(
        f"<div style='{_estilo_accent(cor_accent)}'>{''.join(itens_html)}</div>",
        unsafe_allow_html=True,
    )

    if tem_observacao:
        st.caption("*Campeonato não premiado financeiramente.")
