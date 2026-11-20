"""Leitura e escrita das pontuações em CSV (fonte única da verdade)."""

import csv
from pathlib import Path

import pandas as pd

COLUNAS_CSV = ["rodada", "id_time", "pontuacao", "definitivo"]


def assinatura_arquivos(*caminhos):
    """Identificador estável para invalidar caches quando algum arquivo muda."""
    partes = []
    for caminho in caminhos:
        p = Path(caminho)
        try:
            st = p.stat()
            partes.append((str(p), st.st_mtime_ns, st.st_size))
        except OSError:
            partes.append((str(p), 0, 0))
    return tuple(partes)


def carregar_pontuacoes(caminho, id_nome_time=None):
    """Lê `pontuacoes.csv`. Se `id_nome_time` for informado, adiciona `nome_time`."""
    caminho = Path(caminho)
    if not caminho.is_file():
        colunas = COLUNAS_CSV + (["nome_time"] if id_nome_time is not None else [])
        return pd.DataFrame(columns=colunas)

    df = pd.read_csv(
        caminho,
        dtype={"rodada": "int64", "id_time": "int64", "pontuacao": "float64"},
    )
    if df["definitivo"].dtype != bool:
        df["definitivo"] = (
            df["definitivo"].astype(str).str.strip().str.lower().isin({"true", "1"})
        )
    if id_nome_time is not None:
        df["nome_time"] = df["id_time"].map(id_nome_time)
    return df


def salvar_pontuacoes_completas(caminho, df, ordem_ids=None):
    """Grava o DataFrame completo em `pontuacoes.csv` em ordem determinística."""
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)

    saida = df[COLUNAS_CSV].copy()
    if ordem_ids:
        indice_id = {int(id_t): i for i, id_t in enumerate(ordem_ids)}
        saida["_ord"] = saida["id_time"].map(lambda x: indice_id.get(int(x), len(indice_id)))
        saida = saida.sort_values(["rodada", "_ord"]).drop(columns="_ord")
    else:
        saida = saida.sort_values(["rodada", "id_time"])

    with caminho.open("w", encoding="utf-8", newline="") as f:
        escritor = csv.writer(f, lineterminator="\n")
        escritor.writerow(COLUNAS_CSV)
        for linha in saida.itertuples(index=False):
            escritor.writerow(
                [
                    int(linha.rodada),
                    int(linha.id_time),
                    f"{float(linha.pontuacao):.2f}",
                    "true" if bool(linha.definitivo) else "false",
                ]
            )


def salvar_pontuacoes_rodada(caminho, df_rodada, rodada, ordem_ids=None):
    """Substitui apenas as linhas da `rodada` informada (idempotente)."""
    existente = carregar_pontuacoes(caminho)
    restante = existente[existente["rodada"] != rodada]
    combinado = pd.concat([restante, df_rodada[COLUNAS_CSV]], ignore_index=True)
    salvar_pontuacoes_completas(caminho, combinado, ordem_ids=ordem_ids)


def obter_ultima_rodada_registrada(caminho):
    pontuacoes = carregar_pontuacoes(caminho)
    if pontuacoes.empty:
        return 0
    return int(pontuacoes["rodada"].max())
