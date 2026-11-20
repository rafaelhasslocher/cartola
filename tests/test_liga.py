import pandas as pd

from config_temporada import RegrasLiga
from liga.estatisticas import (
    calcular_maior_pontuador_mas_empatou,
    calcular_top_n_mas_nao_venceu,
    calcular_top_n_por_rodada,
    montar_tabela_estatisticas,
)
from liga.ranking import (
    construir_offsets_rodada_liga,
    montar_ranking_final,
    montar_ranking_todas_rodadas,
    montar_tabela_resultados,
    rodada_liga_relativa,
    turno_da_rodada,
)

REGRAS = RegrasLiga(
    margem_empate=2.0,
    rodada_corte_turno=19,
    pontos_vitoria=3,
    pontos_empate=1,
    pontos_derrota=0,
)


def test_margem_empate_e_vitoria():
    confrontos = [
        {"rodada_brasileirao": 1, "rodada_liga": 1, "time1": "A", "time2": "B"},
        {"rodada_brasileirao": 1, "rodada_liga": 1, "time1": "C", "time2": "D"},
    ]
    pontuacoes = pd.DataFrame(
        [
            {"nome_time": "A", "rodada": 1, "pontuacao": 60.00, "definitivo": True},
            {"nome_time": "B", "rodada": 1, "pontuacao": 58.01, "definitivo": True},  # dif 1.99 -> empate
            {"nome_time": "C", "rodada": 1, "pontuacao": 60.00, "definitivo": True},
            {"nome_time": "D", "rodada": 1, "pontuacao": 58.00, "definitivo": True},  # dif 2.00 -> vitória C
        ]
    )
    res = montar_tabela_resultados(confrontos, pontuacoes, REGRAS)
    jogo_ab = res[res["time1"] == "A"].iloc[0]
    jogo_cd = res[res["time1"] == "C"].iloc[0]

    assert jogo_ab["pontos_vencedor"] == 1
    assert jogo_ab["pontos_perdedor"] == 1
    assert jogo_cd["vencedor"] == "C"
    assert jogo_cd["pontos_vencedor"] == 3
    assert jogo_cd["pontos_perdedor"] == 0


def test_turno_e_rodada_dupla_com_desempate():
    assert turno_da_rodada(19, 19) == 1
    assert turno_da_rodada(20, 19) == 2

    confrontos = [
        {"rodada_brasileirao": 7, "rodada_liga": 7, "time1": "A", "time2": "B"},
        {"rodada_brasileirao": 7, "rodada_liga": 8, "time1": "A", "time2": "C"},
        {"rodada_brasileirao": 7, "rodada_liga": 8, "time1": "B", "time2": "D"},
        {"rodada_brasileirao": 20, "rodada_liga": 23, "time1": "A", "time2": "B"},
    ]
    offsets = construir_offsets_rodada_liga(confrontos, rodada_corte_turno=19)
    assert rodada_liga_relativa(23, 2, offsets) == 1

    pontuacoes = pd.DataFrame(
        [
            {"nome_time": "A", "rodada": 7, "pontuacao": 70.0, "definitivo": True},
            {"nome_time": "B", "rodada": 7, "pontuacao": 65.0, "definitivo": True},
            {"nome_time": "C", "rodada": 7, "pontuacao": 80.0, "definitivo": True},
            {"nome_time": "D", "rodada": 7, "pontuacao": 50.0, "definitivo": True},
            {"nome_time": "A", "rodada": 20, "pontuacao": 50.0, "definitivo": False},
            {"nome_time": "B", "rodada": 20, "pontuacao": 51.0, "definitivo": False},
        ]
    )
    res = montar_tabela_resultados(confrontos, pontuacoes, REGRAS)
    ranking_r7 = montar_ranking_final(res[res["rodada_brasileirao"] <= 7], 7)
    # A (1V 1D = 3 pts, 140.0), B (1V 1D = 3 pts, 130.0), C (1V = 3 pts, 80.0)
    assert ranking_r7["time"].tolist()[:3] == ["A", "B", "C"]

    snapshots = montar_ranking_todas_rodadas(res)
    assert set(snapshots["rodada"].unique()) == {7, 20}
    assert snapshots[snapshots["rodada"] == 20]["definitivo"].eq(False).all()


def test_estatisticas_indicadores():
    confrontos = [
        {"rodada_brasileirao": 1, "rodada_liga": 1, "time1": "A", "time2": "B"},
        {"rodada_brasileirao": 1, "rodada_liga": 1, "time1": "C", "time2": "D"},
    ]
    pontuacoes = pd.DataFrame(
        [
            {"nome_time": "A", "rodada": 1, "pontuacao": 90.0, "definitivo": True},
            {"nome_time": "B", "rodada": 1, "pontuacao": 89.0, "definitivo": True},  # empate com líder
            {"nome_time": "C", "rodada": 1, "pontuacao": 70.0, "definitivo": True},
            {"nome_time": "D", "rodada": 1, "pontuacao": 50.0, "definitivo": True},
        ]
    )
    res = montar_tabela_resultados(confrontos, pontuacoes, REGRAS)
    por_rodada, por_confronto = montar_tabela_estatisticas(res)

    ident = lambda t: t
    assert [t for _, t, _ in calcular_top_n_por_rodada(por_rodada, 1, ident)] == ["A"]
    assert [t for _, t, _ in calcular_top_n_por_rodada(por_rodada, 3, ident)] == ["A", "B", "C"]
    # A e B estão no top 3 e empataram (saldo < 2.0)
    assert sorted(t for _, t, _ in calcular_top_n_mas_nao_venceu(por_confronto, 3, 2.0, ident)) == ["A", "B"]
    assert [t for _, t, _ in calcular_maior_pontuador_mas_empatou(por_confronto, 2.0, ident)] == ["A"]
