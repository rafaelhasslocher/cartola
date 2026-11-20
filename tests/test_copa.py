import pandas as pd

from config_temporada import ConfigTemporadaCopa
from copa.logica import resolver_copa


def _config_copa_simples():
    return {
        1: ConfigTemporadaCopa(
            numero=1,
            fases={
                "fase_de_grupos": range(2, 4),  # rodadas 2 e 3
                "quartas": range(5, 7),         # rodadas 5 e 6
                "semi": range(7, 9),            # rodadas 7 e 8
                "final": range(9, 11),          # rodadas 9 e 10
            },
            grupos={
                "grupo_a": ["A1", "A2", "A3", "A4"],
                "grupo_b": ["B1", "B2", "B3", "B4"],
            },
            times_fora=["F1", "F2"],
            chave_quartas=[
                ("fora_1", "fora_2"),
                ("1_grupo_a", "3_grupo_b"),
                ("1_grupo_b", "3_grupo_a"),
                ("2_grupo_a", "2_grupo_b"),
            ],
            chave_semi=[(0, 1), (2, 3)],
            chave_final=[(0, 1)],
        )
    }


def _pontuacoes_base():
    linhas = []
    # Grupos (rodadas 2 e 3): ordem clara A1>A2>A3>A4 e B1>B2>B3>B4
    for r in (2, 3):
        for nome, pts in [
            ("A1", 80), ("A2", 70), ("A3", 60), ("A4", 50),
            ("B1", 85), ("B2", 75), ("B3", 65), ("B4", 55),
            ("F1", 40), ("F2", 40),
        ]:
            linhas.append({"nome_time": nome, "rodada": r, "pontuacao": float(pts)})
    # Quartas (rodadas 5 e 6): empate exato entre F1 e F2 favorece time1 (F1)
    for r in (5, 6):
        for nome, pts in [
            ("F1", 50), ("F2", 50),
            ("A1", 90), ("B3", 60),
            ("B1", 90), ("A3", 60),
            ("A2", 60), ("B2", 80),
        ]:
            linhas.append({"nome_time": nome, "rodada": r, "pontuacao": float(pts)})
    return pd.DataFrame(linhas)


def test_copa_bloqueia_fase_futura_antes_de_anterior_fechar():
    copa = _config_copa_simples()
    pts = _pontuacoes_base()
    # Apenas rodada 2 registrada -> fase de grupos (2..3) ainda não fechou
    estado = resolver_copa(pts[pts["rodada"] <= 2], copa, rodada_exibida=5, rodada_maxima_disputada=2)
    assert estado.motivo_bloqueio is not None
    assert "fase de grupos" in estado.motivo_bloqueio.lower()


def test_copa_chaveamento_quartas_e_desempate_time1():
    copa = _config_copa_simples()
    pts = _pontuacoes_base()

    # Grupos encerrados (rodada 3) -> quartas (rodada 5) já montam chaveamento mesmo sem jogos
    estado_q_futuro = resolver_copa(
        pts[pts["rodada"] <= 3], copa, rodada_exibida=5, rodada_maxima_disputada=3
    )
    assert estado_q_futuro.motivo_bloqueio is None
    assert estado_q_futuro.resultados_mata_mata[0]["time1"] == "F1"
    assert estado_q_futuro.resultados_mata_mata[0]["time2"] == "F2"
    assert estado_q_futuro.resultados_mata_mata[1]["time1"] == "A1"
    assert estado_q_futuro.resultados_mata_mata[1]["time2"] == "B3"

    # Fim das quartas (rodada 6): F1 == F2 -> F1 vence (>=)
    estado_q_final = resolver_copa(pts, copa, rodada_exibida=6, rodada_maxima_disputada=6)
    assert estado_q_final.definitivo is True
    assert estado_q_final.vencedores == ["F1", "A1", "B1", "B2"]

    # Semifinal (rodada 7 futura) já monta F1 x A1 e B1 x B2
    estado_semi = resolver_copa(pts, copa, rodada_exibida=7, rodada_maxima_disputada=6)
    assert estado_semi.motivo_bloqueio is None
    pares = [(r["time1"], r["time2"]) for r in estado_semi.resultados_mata_mata]
    assert pares == [("F1", "A1"), ("B1", "B2")]


def test_copa_rodada_sem_jogo():
    estado = resolver_copa(_pontuacoes_base(), _config_copa_simples(), rodada_exibida=1)
    assert estado.temporada is None
    assert estado.fase is None
