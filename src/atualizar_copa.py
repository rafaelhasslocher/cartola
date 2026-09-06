from calendario_copa import (
    CALENDARIOS_COPA_POR_TEMPORADA,
    CHAVE_FINAL_POR_TEMPORADA,
    CHAVE_QUARTAS_POR_TEMPORADA,
    CHAVE_SEMI_POR_TEMPORADA,
    GRUPOS_COPA_POR_TEMPORADA,
    TIMES_FORA_POR_TEMPORADA,
)
from caminhos import CAMINHO_RESULTADOS_COPA
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
from dados.persistencia import salvar_copa

RODADA_ATUAL = 25


def exibir_resultados_copa(rodada_atual):
    from caminhos import CAMINHO_DADOS
    from dados.persistencia import carregar_pontuacoes

    temporada_atual, fase_atual = determinar_temporada_e_fase_atual_copa(
        rodada_atual, CALENDARIOS_COPA_POR_TEMPORADA
    )

    if temporada_atual is None:
        return

    GRUPOS_COPA = GRUPOS_COPA_POR_TEMPORADA[temporada_atual]
    TIMES_FORA_COPA = TIMES_FORA_POR_TEMPORADA[temporada_atual]
    CHAVE_QUARTAS_COPA = CHAVE_QUARTAS_POR_TEMPORADA[temporada_atual]
    CHAVE_SEMI_COPA = CHAVE_SEMI_POR_TEMPORADA[temporada_atual]
    CHAVE_FINAL_COPA = CHAVE_FINAL_POR_TEMPORADA[temporada_atual]

    calendario_copa = CALENDARIOS_COPA_POR_TEMPORADA[temporada_atual]
    RODADAS_FASE_DE_GRUPOS = calendario_copa["fase_de_grupos"]
    RODADAS_QUARTAS = calendario_copa["quartas"]
    RODADAS_SEMI = calendario_copa["semi"]
    RODADAS_FINAL = calendario_copa["final"]

    pontuacoes = carregar_pontuacoes(CAMINHO_DADOS)

    if fase_atual == "fase_de_grupos":
        definitivo = fase_esta_definida(rodada_atual, RODADAS_FASE_DE_GRUPOS)
        classificados_grupos = definir_classificados_fase_de_grupos(
            pontuacoes,
            GRUPOS_COPA,
            rodadas_disputadas(RODADAS_FASE_DE_GRUPOS, rodada_atual),
            definitivo,
        )
        jogo_da_fase = rodada_atual - RODADAS_FASE_DE_GRUPOS.start + 1
        df = montar_linhas_classificacao(
            classificados_grupos,
            temporada_atual,
            rodada_atual,
            "fase_de_grupos",
            jogo_da_fase,
        )
        salvar_copa(CAMINHO_RESULTADOS_COPA, df, rodada_atual, temporada_atual)
        exibir_classificacao_grupos(classificados_grupos)

    elif fase_atual == "quartas":
        classificados_grupos = definir_classificados_fase_de_grupos(
            pontuacoes,
            GRUPOS_COPA,
            rodadas_disputadas(RODADAS_FASE_DE_GRUPOS, rodada_atual),
            True,
        )
        confrontos_quartas = montar_confrontos_iniciais(
            CHAVE_QUARTAS_COPA, classificados_grupos, TIMES_FORA_COPA
        )
        definitivo = fase_esta_definida(rodada_atual, RODADAS_QUARTAS)
        resultados_quartas, _ = montar_fase_mata_mata(
            pontuacoes,
            confrontos_quartas,
            rodadas_disputadas(RODADAS_QUARTAS, rodada_atual),
            definitivo,
        )
        jogo_da_fase = rodada_atual - RODADAS_QUARTAS.start + 1
        df = montar_linhas_mata_mata(
            resultados_quartas, temporada_atual, rodada_atual, "quartas", jogo_da_fase
        )
        salvar_copa(CAMINHO_RESULTADOS_COPA, df, rodada_atual, temporada_atual)
        exibir_resultado_mata_mata(resultados_quartas, "quartas")

    elif fase_atual == "semi":
        classificados_grupos = definir_classificados_fase_de_grupos(
            pontuacoes,
            GRUPOS_COPA,
            rodadas_disputadas(RODADAS_FASE_DE_GRUPOS, rodada_atual),
            True,
        )
        confrontos_quartas = montar_confrontos_iniciais(
            CHAVE_QUARTAS_COPA, classificados_grupos, TIMES_FORA_COPA
        )
        _, vencedores_quartas = montar_fase_mata_mata(
            pontuacoes,
            confrontos_quartas,
            rodadas_disputadas(RODADAS_QUARTAS, rodada_atual),
            True,
        )
        confrontos_semi = montar_confrontos_por_indice(
            CHAVE_SEMI_COPA, vencedores_quartas
        )
        definitivo = fase_esta_definida(rodada_atual, RODADAS_SEMI)
        resultados_semi, _ = montar_fase_mata_mata(
            pontuacoes,
            confrontos_semi,
            rodadas_disputadas(RODADAS_SEMI, rodada_atual),
            definitivo,
        )
        jogo_da_fase = rodada_atual - RODADAS_SEMI.start + 1
        df = montar_linhas_mata_mata(
            resultados_semi, temporada_atual, rodada_atual, "semi", jogo_da_fase
        )
        salvar_copa(CAMINHO_RESULTADOS_COPA, df, rodada_atual, temporada_atual)
        exibir_resultado_mata_mata(resultados_semi, "semifinal")

    elif fase_atual == "final":
        classificados_grupos = definir_classificados_fase_de_grupos(
            pontuacoes,
            GRUPOS_COPA,
            rodadas_disputadas(RODADAS_FASE_DE_GRUPOS, rodada_atual),
            True,
        )
        confrontos_quartas = montar_confrontos_iniciais(
            CHAVE_QUARTAS_COPA, classificados_grupos, TIMES_FORA_COPA
        )
        _, vencedores_quartas = montar_fase_mata_mata(
            pontuacoes,
            confrontos_quartas,
            rodadas_disputadas(RODADAS_QUARTAS, rodada_atual),
            True,
        )
        confrontos_semi = montar_confrontos_por_indice(
            CHAVE_SEMI_COPA, vencedores_quartas
        )
        _, vencedores_semi = montar_fase_mata_mata(
            pontuacoes,
            confrontos_semi,
            rodadas_disputadas(RODADAS_SEMI, rodada_atual),
            True,
        )
        confronto_final = montar_confrontos_por_indice(
            CHAVE_FINAL_COPA, vencedores_semi
        )
        definitivo = fase_esta_definida(rodada_atual, RODADAS_FINAL)
        resultado_final, vencedor_final = montar_fase_mata_mata(
            pontuacoes,
            confronto_final,
            rodadas_disputadas(RODADAS_FINAL, rodada_atual),
            definitivo,
        )
        jogo_da_fase = rodada_atual - RODADAS_FINAL.start + 1
        df = montar_linhas_mata_mata(
            resultado_final, temporada_atual, rodada_atual, "final", jogo_da_fase
        )
        salvar_copa(CAMINHO_RESULTADOS_COPA, df, rodada_atual, temporada_atual)
        exibir_resultado_mata_mata(resultado_final, "final")
        if definitivo:
            print(f"Campeão da copa: {vencedor_final[0]}")
