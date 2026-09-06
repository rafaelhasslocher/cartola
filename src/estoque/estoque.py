import deltalake

from caminhos import CAMINHO_DADOS
from dados.api_cartola import (
    coletar_pontuacoes,
    montar_dataframe_pontuacoes,
    obter_ultima_rodada_registrada,
    validar_cobertura,
)
from times import ID_NOME_TIME, IDS_TIMES

RODADA_ATUAL = 25

ultima_rodada = obter_ultima_rodada_registrada(CAMINHO_DADOS)
if RODADA_ATUAL < ultima_rodada:
    raise ValueError(
        f"RODADA_ATUAL ({RODADA_ATUAL}) é menor que a última rodada já "
        f"registrada ({ultima_rodada}). O overwrite completo apagaria dados existentes."
    )

dados = coletar_pontuacoes(IDS_TIMES, range(1, RODADA_ATUAL + 1))
validar_cobertura(dados, IDS_TIMES, ID_NOME_TIME, range(1, RODADA_ATUAL + 1))
df = montar_dataframe_pontuacoes(dados, ID_NOME_TIME)

deltalake.write_deltalake(
    CAMINHO_DADOS,
    df,
    partition_by=["rodada"],
    mode="overwrite",
)
