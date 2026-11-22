"""Valida a integridade estrutural dos arquivos reais em `config/` e `data/`."""

import pandas as pd

from caminhos import CAMINHO_HISTORICO_CAMPEOES, DIR_CONFIG, caminho_pontuacoes
from config_temporada import carregar_config_temporada
from dados.persistencia import carregar_pontuacoes


def _anos_configurados():
    return sorted(
        int(p.name) for p in DIR_CONFIG.iterdir() if p.is_dir() and p.name.isdigit()
    )


def test_integridade_config_e_calendario_liga():
    anos = _anos_configurados()
    assert anos, "Nenhum ano configurado em config/"

    for ano in anos:
        cfg = carregar_config_temporada(ano)
        n_times = len(cfg.ids_times)
        assert n_times == 12
        assert len(set(cfg.ids_times)) == n_times
        assert len(set(cfg.id_nome_time.values())) == n_times
        assert len(set(cfg.id_jogador.values())) == n_times

        cal = cfg.confrontos_liga
        assert (cal["time1"] != cal["time2"]).all(), "Time jogando contra si mesmo"

        # Cada rodada da Liga deve ter exatamente 6 confrontos com todos os 12 times
        for rl, grupo in cal.groupby("rodada_liga"):
            assert len(grupo) == n_times // 2, f"Rodada da Liga {rl} sem {n_times // 2} jogos"
            participantes = list(grupo["time1"]) + list(grupo["time2"])
            assert len(set(participantes)) == n_times, (
                f"Rodada da Liga {rl} com times duplicados ou ausentes"
            )

        # Cada rodada do Brasileirão (1..38) tem 6 jogos (simples) ou 12 (dupla)
        assert set(cal["rodada_brasileirao"].unique()) == set(range(1, 39))
        for rb, grupo in cal.groupby("rodada_brasileirao"):
            assert len(grupo) in (6, 12), f"Rodada {rb} com {len(grupo)} jogos"


def test_integridade_config_copa():
    for ano in _anos_configurados():
        cfg = carregar_config_temporada(ano)
        todos_times = set(cfg.id_nome_time.values())

        rodadas_usadas = set()
        for num, temp in cfg.copa.items():
            # Fases sem sobreposição
            for fase, faixa in temp.fases.items():
                rodadas = set(faixa)
                assert rodadas, f"Copa T{num} fase {fase} vazia"
                assert not (rodadas & rodadas_usadas), f"Sobreposição na Copa T{num} {fase}"
                rodadas_usadas |= rodadas

            # Grupos + times_fora particionam exatamente os 12 times
            participantes = list(temp.times_fora)
            for times_grupo in temp.grupos.values():
                participantes.extend(times_grupo)
            assert len(participantes) == len(todos_times), (
                f"Copa T{num}: time repetido ou faltando entre grupos e times_fora"
            )
            assert set(participantes) == todos_times

            # Chaves válidas
            assert len(temp.chave_quartas) == 4
            assert len(temp.chave_semi) == 2
            assert len(temp.chave_final) == 1


def test_integridade_pontuacoes_e_historico():
    for ano in _anos_configurados():
        cfg = carregar_config_temporada(ano)
        pts = carregar_pontuacoes(caminho_pontuacoes(ano), cfg.id_nome_time)
        assert not pts.empty
        assert pts.isna().sum().sum() == 0
        assert pts.duplicated(subset=["rodada", "id_time"]).sum() == 0
        assert set(pts["id_time"].unique()).issubset(set(cfg.ids_times))

        # Toda rodada registrada cobre todos os 12 times
        for rodada, grupo in pts.groupby("rodada"):
            assert set(grupo["id_time"]) == set(cfg.ids_times), (
                f"Rodada {rodada} incompleta em pontuacoes.csv"
            )

    hist = pd.read_csv(CAMINHO_HISTORICO_CAMPEOES, keep_default_na=False)
    assert set(hist["competicao"].unique()).issubset({"liga", "copa"})
    assert hist.duplicated(subset=["temporada", "competicao"]).sum() == 0
    assert (hist["jogador"].str.strip() != "").all()
