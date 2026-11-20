import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from caminhos import ano_padrao, caminho_pontuacoes
from config_temporada import carregar_config_temporada
from dados.api_cartola import (
    coletar_pontuacoes,
    montar_dataframe_pontuacoes,
    validar_cobertura,
)
from dados.persistencia import (
    obter_ultima_rodada_registrada,
    salvar_pontuacoes_completas,
)


def recriar_estoque_completo(rodada_atual, ano=None):
    """Recoleta e sobrescreve o histórico inteiro de pontuações (rodadas 1 a
    `rodada_atual`). Serve para reconstruir o estoque do zero; para atualizar
    só uma rodada, usar `atualizar_rodada.py`.
    """
    ano = ano_padrao() if ano is None else int(ano)
    config = carregar_config_temporada(ano)
    caminho = caminho_pontuacoes(ano)

    ultima_rodada = obter_ultima_rodada_registrada(caminho)
    if rodada_atual < ultima_rodada:
        raise ValueError(
            f"rodada_atual ({rodada_atual}) é menor que a última rodada já "
            f"registrada ({ultima_rodada}). O overwrite completo apagaria dados existentes."
        )

    dados = coletar_pontuacoes(config.ids_times, range(1, rodada_atual + 1))
    validar_cobertura(
        dados, config.ids_times, config.id_nome_time, range(1, rodada_atual + 1)
    )
    df = montar_dataframe_pontuacoes(dados, config.id_nome_time)
    df["definitivo"] = True

    salvar_pontuacoes_completas(caminho, df, ordem_ids=config.ids_times)
    print(f"Estoque recriado: rodadas 1..{rodada_atual} salvas em {caminho}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Recoleta todas as pontuações de 1 até a rodada informada."
    )
    parser.add_argument("rodada", type=int, help="Última rodada fechada a coletar.")
    parser.add_argument("--ano", type=int, default=None, help="Ano da temporada.")
    args = parser.parse_args()
    recriar_estoque_completo(args.rodada, ano=args.ano)
