"""Leitura e validação das configurações de temporada e histórico de campeões."""

from dataclasses import dataclass
import tomllib

import pandas as pd

from caminhos import (
    CAMINHO_HISTORICO_CAMPEOES,
    ano_padrao,
    caminho_calendario_liga,
    caminho_config_temporada,
)


@dataclass(frozen=True)
class RegrasLiga:
    margem_empate: float
    rodada_corte_turno: int
    pontos_vitoria: int
    pontos_empate: int
    pontos_derrota: int


@dataclass(frozen=True)
class ConfigTemporadaCopa:
    numero: int
    fases: dict[str, range]
    grupos: dict[str, list[str]]
    times_fora: list[str]
    chave_quartas: list[tuple[str, str]]
    chave_semi: list[tuple[int, int]]
    chave_final: list[tuple[int, int]]


@dataclass(frozen=True)
class ConfigTemporada:
    ano: int
    titulo: str
    regras: RegrasLiga
    ids_times: list[int]
    id_nome_time: dict[int, str]
    id_jogador: dict[int, str]
    jogador_por_nome_time: dict[str, str]
    confrontos_liga: pd.DataFrame
    copa: dict[int, ConfigTemporadaCopa]

    def nome_completo(self, nome_time):
        return f"{nome_time} ({self.jogador_por_nome_time[nome_time]})"

    @property
    def primeira_rodada_copa(self):
        return min(
            fase.start
            for temp in self.copa.values()
            for fase in temp.fases.values()
        )

    @property
    def ultima_rodada_copa(self):
        return max(
            fase.stop - 1
            for temp in self.copa.values()
            for fase in temp.fases.values()
        )


def _validar_nomes_times(nomes_conhecidos, confrontos_liga, copa):
    desconhecidos = set()
    for col in ("time1", "time2"):
        desconhecidos.update(set(confrontos_liga[col].unique()) - nomes_conhecidos)
    for temp in copa.values():
        desconhecidos.update(set(temp.times_fora) - nomes_conhecidos)
        for times_grupo in temp.grupos.values():
            desconhecidos.update(set(times_grupo) - nomes_conhecidos)
    if desconhecidos:
        raise ValueError(
            f"Times desconhecidos na configuração da temporada: {sorted(desconhecidos)}"
        )


def carregar_config_temporada(ano=None):
    ano = ano_padrao() if ano is None else int(ano)
    with caminho_config_temporada(ano).open("rb") as f:
        bruto = tomllib.load(f)

    geral = bruto["geral"]
    liga = bruto["liga"]
    regras = RegrasLiga(
        margem_empate=float(liga["margem_empate"]),
        rodada_corte_turno=int(liga["rodada_corte_turno"]),
        pontos_vitoria=int(liga["pontos_vitoria"]),
        pontos_empate=int(liga["pontos_empate"]),
        pontos_derrota=int(liga["pontos_derrota"]),
    )

    times = bruto["times"]
    ids_times = [int(t["id"]) for t in times]
    id_nome_time = {int(t["id"]): t["nome"] for t in times}
    id_jogador = {int(t["id"]): t["jogador"] for t in times}
    jogador_por_nome_time = {t["nome"]: t["jogador"] for t in times}

    confrontos_liga = pd.read_csv(caminho_calendario_liga(ano))

    copa = {}
    for num_str, dados_temp in bruto["copa"]["temporadas"].items():
        numero = int(num_str)
        fases = {
            nome_fase: range(int(inicio), int(fim) + 1)
            for nome_fase, (inicio, fim) in dados_temp["fases"].items()
        }
        copa[numero] = ConfigTemporadaCopa(
            numero=numero,
            fases=fases,
            grupos={k: list(v) for k, v in dados_temp["grupos"].items()},
            times_fora=list(dados_temp["times_fora"]),
            chave_quartas=[tuple(par) for par in dados_temp["chave_quartas"]],
            chave_semi=[tuple(int(i) for i in par) for par in dados_temp["chave_semi"]],
            chave_final=[tuple(int(i) for i in par) for par in dados_temp["chave_final"]],
        )

    _validar_nomes_times(set(jogador_por_nome_time), confrontos_liga, copa)

    return ConfigTemporada(
        ano=int(geral["ano"]),
        titulo=geral["titulo"],
        regras=regras,
        ids_times=ids_times,
        id_nome_time=id_nome_time,
        id_jogador=id_jogador,
        jogador_por_nome_time=jogador_por_nome_time,
        confrontos_liga=confrontos_liga,
        copa=copa,
    )


def carregar_historico_campeoes(caminho=CAMINHO_HISTORICO_CAMPEOES):
    """Retorna `{competicao: [(temporada, jogador, time, nota), ...]}`."""
    df = pd.read_csv(caminho, keep_default_na=False)
    historico = {}
    for competicao, grupo in df.groupby("competicao", sort=False):
        historico[competicao] = [
            (
                row["temporada"],
                row["jogador"],
                row["time"] or None,
                row["nota"] or None,
            )
            for _, row in grupo.iterrows()
        ]
    return historico
