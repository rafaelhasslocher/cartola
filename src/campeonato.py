"""Camada única de cálculo do campeonato (usada tanto pelo app quanto pelo CLI)."""

from dataclasses import dataclass

import pandas as pd

from caminhos import (
    CAMINHO_HISTORICO_CAMPEOES,
    ano_padrao,
    caminho_calendario_liga,
    caminho_config_temporada,
    caminho_pontuacoes,
)
from config_temporada import ConfigTemporada, carregar_config_temporada
from copa.logica import resolver_copa
from dados.persistencia import assinatura_arquivos, carregar_pontuacoes
from liga.estatisticas import montar_tabela_estatisticas
from liga.ranking import (
    construir_offsets_rodada_liga,
    montar_ranking_todas_rodadas,
    montar_tabela_resultados,
    rodada_liga_relativa,
    turno_da_rodada,
)


@dataclass(frozen=True)
class TemporadaCarregada:
    config: ConfigTemporada
    pontuacoes: pd.DataFrame
    resultados_liga: pd.DataFrame
    ranking_liga: pd.DataFrame
    estatisticas_por_rodada: pd.DataFrame
    estatisticas_por_confronto: pd.DataFrame
    offsets_rodada_liga: dict[int, int]

    def turno_da_rodada(self, rodada_brasileirao):
        return turno_da_rodada(rodada_brasileirao, self.config.regras.rodada_corte_turno)

    def rodada_liga_relativa(self, rodada_liga, turno):
        return rodada_liga_relativa(rodada_liga, turno, self.offsets_rodada_liga)

    @property
    def rodada_maxima_definitiva(self):
        if self.pontuacoes.empty:
            return 0
        defs = self.pontuacoes["definitivo"].astype("boolean").fillna(True).astype(bool)
        rodadas_def = self.pontuacoes.loc[defs, "rodada"]
        return int(rodadas_def.max()) if not rodadas_def.empty else 0

    def resolver_copa(self, rodada_exibida, apenas_ate_rodada=False):
        """Resolve a Copa na `rodada_exibida`.

        - No app (`apenas_ate_rodada=False`), usa a maior rodada definitiva já
          registrada na temporada (permite ver chaveamento futuro se a fase
          anterior já fechou).
        - No CLI (`apenas_ate_rodada=True`), restringe a referência à própria
          `rodada_exibida` (e seus dados definitivos até ela).
        """
        rodada_ref = None if apenas_ate_rodada else self.rodada_maxima_definitiva
        return resolver_copa(
            self.pontuacoes,
            self.config.copa,
            rodada_exibida,
            rodada_maxima_definitiva=rodada_ref,
        )


def arquivos_temporada(ano=None):
    ano = ano_padrao() if ano is None else int(ano)
    return (
        caminho_config_temporada(ano),
        caminho_calendario_liga(ano),
        caminho_pontuacoes(ano),
        CAMINHO_HISTORICO_CAMPEOES,
    )


def assinatura_temporada(ano=None):
    return assinatura_arquivos(*arquivos_temporada(ano))


def carregar_temporada(ano=None):
    ano = ano_padrao() if ano is None else int(ano)
    config = carregar_config_temporada(ano)
    pontuacoes = carregar_pontuacoes(caminho_pontuacoes(ano), config.id_nome_time)
    resultados_liga = montar_tabela_resultados(
        config.confrontos_liga, pontuacoes, config.regras
    )
    ranking_liga = montar_ranking_todas_rodadas(resultados_liga)
    est_rodada, est_confronto = montar_tabela_estatisticas(resultados_liga)
    offsets = construir_offsets_rodada_liga(
        config.confrontos_liga, config.regras.rodada_corte_turno
    )
    return TemporadaCarregada(
        config=config,
        pontuacoes=pontuacoes,
        resultados_liga=resultados_liga,
        ranking_liga=ranking_liga,
        estatisticas_por_rodada=est_rodada,
        estatisticas_por_confronto=est_confronto,
        offsets_rodada_liga=offsets,
    )
