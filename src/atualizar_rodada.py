import deltalake

from atualizar_copa import exibir_resultados_copa
from calendario_liga import CONFRONTOS_LIGA
from caminhos import CAMINHO_DADOS, CAMINHO_RANKING, CAMINHO_RESULTADOS
from dados.api_cartola import (
    coletar_pontuacoes,
    montar_dataframe_pontuacoes,
    validar_cobertura,
)
from dados.persistencia import carregar_pontuacoes, salvar_ranking, salvar_resultados
from liga.ranking import (
    exibir_confrontos_rodada,
    exibir_resultados,
    montar_ranking_final,
    montar_tabela_resultados,
)
from regras_liga import RODADA_CORTE_TURNO
from times import ID_NOME_TIME, IDS_TIMES


def atualizar_rodada(rodada_desejada):
    dados = coletar_pontuacoes(IDS_TIMES, [rodada_desejada])
    validar_cobertura(dados, IDS_TIMES, ID_NOME_TIME, [rodada_desejada])
    df = montar_dataframe_pontuacoes(dados, ID_NOME_TIME)

    deltalake.write_deltalake(
        CAMINHO_DADOS,
        df,
        mode="overwrite",
        predicate=f"rodada == {rodada_desejada}",
    )

    pontuacoes = carregar_pontuacoes(CAMINHO_DADOS)
    tabela_resultados = montar_tabela_resultados(CONFRONTOS_LIGA, pontuacoes)
    tabela_resultados = tabela_resultados[
        tabela_resultados["rodada_brasileirao"] <= rodada_desejada
    ]
    exibir_confrontos_rodada(tabela_resultados, rodada_desejada)

    resultados_rodada = tabela_resultados[
        tabela_resultados["rodada_brasileirao"] == rodada_desejada
    ]
    salvar_resultados(CAMINHO_RESULTADOS, resultados_rodada, rodada_desejada)

    df_final = montar_ranking_final(tabela_resultados, rodada_desejada)

    salvar_ranking(CAMINHO_RANKING, df_final, rodada_desejada)
    turno_atual = 1 if rodada_desejada <= RODADA_CORTE_TURNO else 2
    exibir_resultados(df_final, turno=turno_atual)

    exibir_resultados_copa(rodada_desejada)

    return df_final


if __name__ == "__main__":
    RODADA_ATUAL = 25

    atualizar_rodada(RODADA_ATUAL)
