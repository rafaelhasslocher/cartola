"""Aba Regras (valores dinâmicos lidos de `config/{ano}/temporada.toml`)."""

import streamlit as st

from ui.componentes import (
    COR_COPA,
    COR_LIGA,
    COR_REGRAS,
    exibir_cabecalho_secao,
    exibir_subtitulo,
    formatar_pontuacao,
)


def _faixa(rodadas):
    return f"rodadas {rodadas.start} a {rodadas.stop - 1}"


def render(temporada):
    config = temporada.config
    regras = config.regras

    contagem_por_rodada = (
        config.confrontos_liga.groupby("rodada_brasileirao")["rodada_liga"].nunique()
    )
    rodadas_duplas = sorted(
        int(r) for r, qtd in contagem_por_rodada.items() if qtd > 1
    )
    duplas_texto = ", ".join(str(r) for r in rodadas_duplas)

    exibir_cabecalho_secao("Regras", COR_REGRAS)

    exibir_subtitulo("Liga", COR_LIGA)
    st.markdown(
        f"""
- **Formato:** pontos corridos em confrontos diretos entre os **{len(config.ids_times)} times**, com dois campeonatos independentes no ano:
  - **1º turno:** rodadas 1 a {regras.rodada_corte_turno} do Brasileirão;
  - **2º turno:** rodadas {regras.rodada_corte_turno + 1} a 38 do Brasileirão (pontuação zera na virada do turno).
- **Pontuação por confronto:**
  - Vitória: **{regras.pontos_vitoria} pontos**;
  - Empate (diferença inferior a **{formatar_pontuacao(regras.margem_empate)}** pontos no Cartola): **{regras.pontos_empate} ponto** para cada time;
  - Derrota: **{regras.pontos_derrota} pontos**.
- **Critério de desempate:** maior **pontuação total acumulada** no Cartola dentro do turno.
- **Rodadas duplas:** nas rodadas **{duplas_texto}** do Brasileirão cada time disputa dois confrontos da Liga com a mesma pontuação da rodada.
"""
    )

    exibir_subtitulo("Copa", COR_COPA)
    linhas_temporadas = []
    for num, temp in sorted(config.copa.items()):
        linhas_temporadas.append(
            f"  - **{num}ª temporada:** "
            f"Grupos ({_faixa(temp.fases['fase_de_grupos'])}), "
            f"Quartas ({_faixa(temp.fases['quartas'])}), "
            f"Semifinal ({_faixa(temp.fases['semi'])}) e "
            f"Final ({_faixa(temp.fases['final'])})."
        )
    st.markdown(
        f"""
- **Formato:** duas edições por ano, uma em cada turno:
{chr(10).join(linhas_temporadas)}
- **Acesso direto às quartas:** campeão e vice da Copa anterior entram direto nas quartas de final.
- **Fase de grupos:** os outros 10 times são divididos em 2 grupos de 5. Não há confronto direto — soma-se a pontuação bruta do Cartola nas rodadas da fase e os **3 melhores de cada grupo** avançam.
- **Mata-mata:** cada fase soma a pontuação bruta do Cartola nas suas rodadas. Avança quem somar mais pontos (sem margem de empate).
"""
    )
