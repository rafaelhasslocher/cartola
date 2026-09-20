import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import deltalake

from caminhos import CAMINHO_DADOS
from dados.api_cartola import (
    coletar_pontuacoes,
    montar_dataframe_pontuacoes,
    obter_ultima_rodada_registrada,
    validar_cobertura,
)
from times import ID_NOME_TIME, IDS_TIMES

RODADA_ATUAL = 26


def recriar_estoque_completo(rodada_atual):
    """Recoleta e sobrescreve o histórico inteiro de pontuações (rodadas 1 a
    `rodada_atual`). Serve para reconstruir o estoque do zero; para atualizar
    só uma rodada, usar `atualizar_rodada.py`."""
    ultima_rodada = obter_ultima_rodada_registrada(CAMINHO_DADOS)
    if rodada_atual < ultima_rodada:
        raise ValueError(
            f"rodada_atual ({rodada_atual}) é menor que a última rodada já "
            f"registrada ({ultima_rodada}). O overwrite completo apagaria dados existentes."
        )

    dados = coletar_pontuacoes(IDS_TIMES, range(1, rodada_atual + 1))
    validar_cobertura(dados, IDS_TIMES, ID_NOME_TIME, range(1, rodada_atual + 1))
    df = montar_dataframe_pontuacoes(dados, ID_NOME_TIME)
    df["definitivo"] = True

    deltalake.write_deltalake(
        CAMINHO_DADOS,
        df,
        partition_by=["rodada"],
        mode="overwrite",
    )


if __name__ == "__main__":
    recriar_estoque_completo(RODADA_ATUAL)
