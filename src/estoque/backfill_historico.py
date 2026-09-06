import contextlib
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from atualizar_copa import exibir_resultados_copa
from calendario_liga import CONFRONTOS_LIGA
from caminhos import CAMINHO_DADOS, CAMINHO_RANKING, CAMINHO_RESULTADOS
from dados.persistencia import carregar_pontuacoes, salvar_ranking, salvar_resultados
from liga.ranking import montar_ranking_final, montar_tabela_resultados

RODADA_INICIAL = 1
RODADA_FINAL = 25


def backfill_historico(rodada_inicial, rodada_final):
    pontuacoes = carregar_pontuacoes(CAMINHO_DADOS)

    for rodada in range(rodada_inicial, rodada_final + 1):
        tabela_resultados = montar_tabela_resultados(CONFRONTOS_LIGA, pontuacoes)
        tabela_resultados = tabela_resultados[
            tabela_resultados["rodada_brasileirao"] <= rodada
        ]

        resultados_rodada = tabela_resultados[
            tabela_resultados["rodada_brasileirao"] == rodada
        ]
        if resultados_rodada.empty:
            print(f"Rodada {rodada}: sem pontuação disponível, pulando.")
            continue

        salvar_resultados(CAMINHO_RESULTADOS, resultados_rodada, rodada)

        df_final = montar_ranking_final(tabela_resultados, rodada)
        salvar_ranking(CAMINHO_RANKING, df_final, rodada)

        with contextlib.redirect_stdout(io.StringIO()):
            exibir_resultados_copa(rodada)

        print(f"Rodada {rodada}: resultados e ranking salvos.")


if __name__ == "__main__":
    backfill_historico(RODADA_INICIAL, RODADA_FINAL)