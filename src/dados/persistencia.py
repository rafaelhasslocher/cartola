import deltalake
import pyarrow as pa


def ler_tabela_delta(caminho):
    return deltalake.DeltaTable(str(caminho)).to_pandas()


def carregar_pontuacoes(caminho_dados):
    return ler_tabela_delta(caminho_dados)


def salvar_ranking(caminho_ranking, df_final, rodada):
    deltalake.write_deltalake(
        caminho_ranking,
        df_final,
        mode="overwrite",
        partition_by=["rodada"],
        predicate=f"rodada == {rodada}",
    )


def obter_ranking(caminho_ranking):
    return ler_tabela_delta(caminho_ranking)


def salvar_resultados(caminho_resultados, tabela_resultados, rodada):
    deltalake.write_deltalake(
        caminho_resultados,
        tabela_resultados,
        mode="overwrite",
        partition_by=["rodada_brasileirao"],
        predicate=f"rodada_brasileirao == {rodada}",
    )


def obter_resultados(caminho_resultados):
    return ler_tabela_delta(caminho_resultados)


SCHEMA_COPA = pa.schema(
    [
        ("rodada", pa.int64()),
        ("temporada", pa.int64()),
        ("fase", pa.string()),
        ("jogo_da_fase", pa.int64()),
        ("definitivo", pa.bool_()),
        ("grupo", pa.string()),
        ("time", pa.string()),
        ("posicao", pa.int64()),
        ("pontuacao_total", pa.float64()),
        ("time1", pa.string()),
        ("time2", pa.string()),
        ("pontuacao_time1", pa.float64()),
        ("pontuacao_time2", pa.float64()),
        ("vencedor", pa.string()),
        ("lider_parcial", pa.string()),
    ]
)


def obter_copa(caminho):
    return ler_tabela_delta(caminho)


def salvar_copa(caminho, df, rodada, temporada):

    df = df[[campo.name for campo in SCHEMA_COPA]]
    tabela = pa.Table.from_pandas(df, schema=SCHEMA_COPA, preserve_index=False)

    deltalake.write_deltalake(
        caminho,
        tabela,
        mode="overwrite",
        partition_by=["rodada"],
        predicate=f"rodada == {rodada} and temporada == {temporada}",
    )
