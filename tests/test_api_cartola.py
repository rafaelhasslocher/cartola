from dados.api_cartola import calcular_pontuacao_parcial_escalacao


def test_substituicao_banco_reserva_e_capitao():
    escalacao = {
        "capitao_id": 1,
        "reserva_luxo_id": None,
        "atletas": [
            {"atleta_id": 1, "posicao_id": 5},  # capitão não jogou
            {"atleta_id": 2, "posicao_id": 3},  # titular não jogou, reserva negativou
        ],
        "reservas": [
            {"atleta_id": 10, "posicao_id": 5},  # entra na vaga do capitão (x1.5)
            {"atleta_id": 20, "posicao_id": 3},  # negativo -> não entra
        ],
    }
    parciais = {
        "10": {"pontuacao": 10.0, "entrou_em_campo": True},
        "20": {"pontuacao": -2.0, "entrou_em_campo": True},
    }
    # Atleta 10 ocupa vaga do capitão: 10 * 1.5 = 15.0; atleta 20 não entra (0.0)
    assert calcular_pontuacao_parcial_escalacao(escalacao, parciais) == 15.0


def test_reserva_de_luxo_substitui_pior_titular_se_todos_jogaram():
    escalacao = {
        "capitao_id": 2,
        "reserva_luxo_id": 99,
        "atletas": [
            {"atleta_id": 1, "posicao_id": 4},
            {"atleta_id": 2, "posicao_id": 4},  # pior titular e capitão
        ],
        "reservas": [
            {"atleta_id": 99, "posicao_id": 4},
        ],
    }
    parciais = {
        "1": {"pontuacao": 8.0, "entrou_em_campo": True},
        "2": {"pontuacao": 2.0, "entrou_em_campo": True},
        "99": {"pontuacao": 12.0, "entrou_em_campo": True},
    }
    # Reserva de luxo (12.0) entra no lugar do pior titular (2, que era capitão -> x1.5)
    # Total: 8.0 + 12.0 * 1.5 = 26.0
    assert calcular_pontuacao_parcial_escalacao(escalacao, parciais) == 26.0


def test_reserva_de_luxo_nao_entra_se_algum_titular_nao_jogou():
    escalacao = {
        "capitao_id": None,
        "reserva_luxo_id": 99,
        "atletas": [
            {"atleta_id": 1, "posicao_id": 4},
            {"atleta_id": 2, "posicao_id": 4},  # não jogou
        ],
        "reservas": [
            {"atleta_id": 99, "posicao_id": 4},
        ],
    }
    parciais = {
        "1": {"pontuacao": 8.0, "entrou_em_campo": True},
        "99": {"pontuacao": 12.0, "entrou_em_campo": True},
    }
    # Regra 1 já coloca o reserva 99 na vaga de 2; regra 2 não substitui o titular 1.
    assert calcular_pontuacao_parcial_escalacao(escalacao, parciais) == 20.0
