from calendario_copa import (
    CALENDARIOS_COPA_POR_TEMPORADA,
    CHAVE_FINAL_POR_TEMPORADA,
    CHAVE_QUARTAS_POR_TEMPORADA,
    CHAVE_SEMI_POR_TEMPORADA,
    GRUPOS_COPA_POR_TEMPORADA,
    TIMES_FORA_POR_TEMPORADA,
)
from caminhos import CAMINHO_DADOS, CAMINHO_RESULTADOS_COPA
from copa.logica import (
    definir_classificados_fase_de_grupos,
    determinar_temporada_e_fase_atual_copa,
    exibir_classificacao_grupos,
    exibir_resultado_mata_mata,
    fase_esta_definida,
    montar_confrontos_iniciais,
    montar_confrontos_por_indice,
    montar_fase_mata_mata,
    montar_linhas_classificacao,
    montar_linhas_mata_mata,
    rodadas_disputadas,
)
from dados.persistencia import carregar_pontuacoes, salvar_copa

NOME_EXIBICAO_FASE = {"quartas": "quartas", "semi": "semifinal", "final": "final"}


def _salvar_e_exibir_mata_mata(resultados, temporada, rodada, fase, rodadas_fase):
    jogo_da_fase = rodada - rodadas_fase.start + 1
    df = montar_linhas_mata_mata(resultados, temporada, rodada, fase, jogo_da_fase)
    salvar_copa(CAMINHO_RESULTADOS_COPA, df, rodada, temporada)
    exibir_resultado_mata_mata(resultados, NOME_EXIBICAO_FASE[fase])


def exibir_resultados_copa(rodada_atual):
    temporada_atual, fase_atual = determinar_temporada_e_fase_atual_copa(
        rodada_atual, CALENDARIOS_COPA_POR_TEMPORADA
    )
    if temporada_atual is None:
        return

    grupos_copa = GRUPOS_COPA_POR_TEMPORADA[temporada_atual]
    times_fora_copa = TIMES_FORA_POR_TEMPORADA[temporada_atual]
    chave_quartas = CHAVE_QUARTAS_POR_TEMPORADA[temporada_atual]
    chave_semi = CHAVE_SEMI_POR_TEMPORADA[temporada_atual]
    chave_final = CHAVE_FINAL_POR_TEMPORADA[temporada_atual]

    calendario_copa = CALENDARIOS_COPA_POR_TEMPORADA[temporada_atual]
    rodadas_grupos = calendario_copa["fase_de_grupos"]
    rodadas_quartas = calendario_copa["quartas"]
    rodadas_semi = calendario_copa["semi"]
    rodadas_final = calendario_copa["final"]

    pontuacoes = carregar_pontuacoes(CAMINHO_DADOS)

    # A classificação dos grupos é a base de tudo: mesmo quando a fase atual
    # já é uma fase mata-mata, ela precisa ser recalculada aqui para montar
    # o chaveamento das quartas. Cada bloco abaixo reaproveita o resultado
    # do anterior em vez de recomeçar do zero, avançando fase a fase até
    # chegar na fase atual.
    definitivo = fase_esta_definida(rodada_atual, rodadas_grupos)
    classificados_grupos = definir_classificados_fase_de_grupos(
        pontuacoes,
        grupos_copa,
        rodadas_disputadas(rodadas_grupos, rodada_atual),
        definitivo,
    )
    if fase_atual == "fase_de_grupos":
        jogo_da_fase = rodada_atual - rodadas_grupos.start + 1
        df = montar_linhas_classificacao(
            classificados_grupos, temporada_atual, rodada_atual, fase_atual, jogo_da_fase
        )
        salvar_copa(CAMINHO_RESULTADOS_COPA, df, rodada_atual, temporada_atual)
        exibir_classificacao_grupos(classificados_grupos)
        return

    confrontos_quartas = montar_confrontos_iniciais(
        chave_quartas, classificados_grupos, times_fora_copa
    )
    definitivo = fase_esta_definida(rodada_atual, rodadas_quartas)
    resultados_quartas, vencedores_quartas = montar_fase_mata_mata(
        pontuacoes,
        confrontos_quartas,
        rodadas_disputadas(rodadas_quartas, rodada_atual),
        definitivo,
    )
    if fase_atual == "quartas":
        _salvar_e_exibir_mata_mata(
            resultados_quartas, temporada_atual, rodada_atual, fase_atual, rodadas_quartas
        )
        return

    confrontos_semi = montar_confrontos_por_indice(chave_semi, vencedores_quartas)
    definitivo = fase_esta_definida(rodada_atual, rodadas_semi)
    resultados_semi, vencedores_semi = montar_fase_mata_mata(
        pontuacoes,
        confrontos_semi,
        rodadas_disputadas(rodadas_semi, rodada_atual),
        definitivo,
    )
    if fase_atual == "semi":
        _salvar_e_exibir_mata_mata(
            resultados_semi, temporada_atual, rodada_atual, fase_atual, rodadas_semi
        )
        return

    confronto_final = montar_confrontos_por_indice(chave_final, vencedores_semi)
    definitivo = fase_esta_definida(rodada_atual, rodadas_final)
    resultado_final, vencedor_final = montar_fase_mata_mata(
        pontuacoes,
        confronto_final,
        rodadas_disputadas(rodadas_final, rodada_atual),
        definitivo,
    )
    _salvar_e_exibir_mata_mata(
        resultado_final, temporada_atual, rodada_atual, fase_atual, rodadas_final
    )
    if definitivo:
        print(f"Campeão da copa: {vencedor_final[0]}")
