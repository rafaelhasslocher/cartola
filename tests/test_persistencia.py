import pandas as pd

from campeonato import carregar_temporada
from config_temporada import carregar_historico_campeoes
from dados.persistencia import (
    carregar_pontuacoes,
    obter_ultima_rodada_registrada,
    salvar_pontuacoes_rodada,
)


def test_salvar_pontuacoes_rodada_idempotente(tmp_path):
    csv_path = tmp_path / "pontuacoes.csv"
    r1 = pd.DataFrame(
        [
            {"rodada": 1, "id_time": 10, "pontuacao": 55.5, "definitivo": False},
            {"rodada": 1, "id_time": 20, "pontuacao": 42.1, "definitivo": False},
        ]
    )
    salvar_pontuacoes_rodada(csv_path, r1, rodada=1, ordem_ids=[20, 10])
    assert obter_ultima_rodada_registrada(csv_path) == 1

    # Sobrescreve rodada 1 com definitivo=True mantendo a ordem de ordem_ids
    r1_final = pd.DataFrame(
        [
            {"rodada": 1, "id_time": 10, "pontuacao": 60.0, "definitivo": True},
            {"rodada": 1, "id_time": 20, "pontuacao": 45.0, "definitivo": True},
        ]
    )
    salvar_pontuacoes_rodada(csv_path, r1_final, rodada=1, ordem_ids=[20, 10])
    carregado = carregar_pontuacoes(csv_path)
    assert len(carregado) == 2
    assert carregado["id_time"].tolist() == [20, 10]
    assert carregado["definitivo"].all()


def test_carregar_temporada_2026_e_historico():
    temp = carregar_temporada(2026)
    assert temp.config.ano == 2026
    assert len(temp.config.ids_times) == 12
    n_rodadas = temp.pontuacoes["rodada"].nunique()
    assert n_rodadas >= 35
    assert len(temp.pontuacoes) == n_rodadas * 12
    assert len(temp.resultados_liga) > 0
    assert len(temp.ranking_liga) > 0

    historico = carregar_historico_campeoes()
    assert len(historico["liga"]) >= 19
    assert len(historico["copa"]) >= 17
