"""Trajetórias da Liga a partir dos snapshots de classificação por rodada."""

from regras_liga import RODADA_CORTE_TURNO


# Abaixo desta largura do contêiner (px) o gráfico usa os nomes quebrados em
# linhas mais curtas. Equivale ao limite anterior (600 px de área útil mais
# ~60 px do eixo vertical). Não pode usar `width`: a área útil agora resulta do
# layout, que depende do tamanho dos nomes, e a escolha ficaria oscilando.
LARGURA_CONTAINER_COMPACTA = 660

# Folga mínima (px) entre o fim do texto e a borda do gráfico: absorve diferenças
# de renderização entre navegadores, para que o ")" final nunca seja cortado.
FOLGA_DIREITA_NOMES = 2

CORES_EVOLUCAO = [
    "#4E79A7", "#F28E2B", "#E15759", "#358D88", "#59A14F", "#A98400",
    "#B07AA1", "#C45E89", "#9C755F", "#777077", "#6F63C2", "#17A2B8",
]


def montar_evolucao_classificacao(ranking, turno):
    """Calcula posições antes de qualquer filtro de times, como na tabela da Liga.

    Snapshots do segundo turno também carregam o primeiro turno encerrado;
    estes registros não devem prolongar artificialmente sua trajetória.
    """
    no_turno = ranking["rodada"].le(RODADA_CORTE_TURNO)
    if turno == 2:
        no_turno = ~no_turno
    dados = ranking.loc[(ranking["turno"] == turno) & no_turno].copy()
    if "definitivo" not in dados:
        dados["definitivo"] = True
    dados["definitivo"] = dados["definitivo"].astype("boolean").fillna(True).astype(bool)
    # Ordenar cada snapshot separadamente reproduz a classificação exibida.
    dados = dados.sort_values(
        ["rodada", "pontos", "pontuacao_total"], ascending=[True, False, False],
        kind="stable",
    )
    dados["posicao"] = dados.groupby("rodada").cumcount() + 1
    dados["situacao"] = dados["definitivo"].map({True: "Definitiva", False: "Parcial"})
    return dados


def montar_spec_evolucao(evolucao, times, nome_completo):
    """Especificação Vega-Lite, sem adicionar dependências ao aplicativo."""
    rodadas = sorted(int(r) for r in evolucao["rodada"].unique())
    spec = {
        "height": 540,
        # Linhas e nomes ocupam a largura do contêiner. Com `fit`, o Vega mede o
        # texto que passa da área do gráfico e reserva exatamente esse espaço à
        # direita: o fim do maior nome encosta na borda, em qualquer tela e
        # fonte, sem largura fixa chutada. Não há margem espelhada à esquerda.
        "autosize": {"type": "fit-x", "contains": "padding"},
        "padding": {"right": FOLGA_DIREITA_NOMES},
        "mark": {"type": "line", "point": {"filled": True, "size": 55}, "strokeWidth": 2.5},
        "encoding": {
            "x": {
                "field": "rodada", "type": "quantitative",
                "title": "Rodada",
                "scale": {"zero": False, "nice": False, "domain": [rodadas[0] - 0.3, rodadas[-1]]},
                "axis": {"values": rodadas, "format": "d", "labelOverlap": True},
            },
            "y": {
                "field": "posicao", "type": "quantitative", "title": "Posição",
                "scale": {"domain": [12.3, 0.7], "nice": False, "zero": False},
                "axis": {"values": list(range(1, 13)), "labelExpr": "datum.value + 'º'"},
            },
            "color": {
                "field": "nome", "type": "nominal", "title": "Time",
                "scale": {"domain": [nome_completo(t) for t in times], "range": CORES_EVOLUCAO},
                "legend": None,
            },
            "order": {"field": "rodada", "type": "quantitative"},
            "tooltip": [
                {"field": "nome", "type": "nominal", "title": "Time"},
                {"field": "rodada", "type": "quantitative", "title": "Rodada", "format": "d"},
                {"field": "posicao", "type": "quantitative", "title": "Posição", "format": "d"},
                {"field": "pontos", "type": "quantitative", "title": "Pontos na Liga", "format": "d"},
                {"field": "pontuacao_total", "type": "quantitative", "title": "Pontuação acumulada", "format": ".2f"},
                {"field": "situacao", "type": "nominal", "title": "Classificação"},
            ],
        },
        "config": {"view": {"stroke": None}},
    }

    linhas = spec.pop("mark")
    # Uma etiqueta por time, inclusive se algum snapshot estiver incompleto.
    # O filtro de participantes não altera posições nem a associação de cores.
    spec["layer"] = [
        {"mark": linhas},
        {
            "transform": [
                {"joinaggregate": [{"op": "max", "field": "rodada", "as": "ultima_rodada"}],
                 "groupby": ["nome"]},
                {"filter": "datum.rodada === datum.ultima_rodada"},
            ],
            "mark": {
                "type": "text", "align": "left", "baseline": "middle",
                "dx": 10, "fontSize": 11, "fontWeight": 600, "lineHeight": 14,
                "lineBreak": "\n",
                "text": {"expr": (
                    f"(containerSize()[0] || windowSize()[0]) < {LARGURA_CONTAINER_COMPACTA}"
                    " ? datum.rotulo_mobile : datum.rotulo_desktop"
                )},
            },
        },
    ]
    return spec
