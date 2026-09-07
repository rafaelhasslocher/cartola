import pandas as pd
import requests
from cartolafc import Api, CartolaFCError
from dados.persistencia import ler_tabela_delta
from deltalake.exceptions import TableNotFoundError

_api_cartolafc = Api()


def get_pontuacao_time(id_time, rodada):
    url = f"https://api.cartola.globo.com/time/id/{id_time}/{rodada}"
    try:
        resp = requests.get(url, timeout=10)
    except requests.RequestException as e:
        print(f"[AVISO] Falha ao consultar time {id_time} na rodada {rodada}: {e}")
        return None
    if resp.status_code == 200:
        data = resp.json()
        return data.get("pontos", None)
    print(f"[AVISO] Status {resp.status_code} para time {id_time} na rodada {rodada}")
    return None


def coletar_pontuacoes(ids_times, rodadas):
    dados = []
    for id_time in ids_times:
        for rodada in rodadas:
            pontos = get_pontuacao_time(id_time, rodada)
            if pontos is not None:
                dados.append(
                    {
                        "id_time": id_time,
                        "rodada": rodada,
                        "pontuacao": round(pontos, 2),
                    }
                )
    return dados


def get_pontuacao_parcial_time(id_time, parciais):
    try:
        time = _api_cartolafc.time_parcial(id_time, parciais=parciais)
    except CartolaFCError as e:
        print(f"[AVISO] Falha ao calcular parcial do time {id_time}: {e}")
        return None
    return time.pontos


def coletar_pontuacoes_parciais(ids_times, rodada):
    """Coleta a pontuação AO VIVO da rodada em andamento (mercado fechado),
    usando /atletas/pontuados via python-cartolafc. Diferente de
    `coletar_pontuacoes`, aqui a rodada não precisa ter fechado: os pontos
    refletem só os jogadores que já entraram em campo até o momento.
    """
    try:
        parciais = _api_cartolafc.parciais()
    except CartolaFCError as e:
        print(f"[AVISO] Pontuação parcial indisponível agora: {e}")
        return []

    dados = []
    for id_time in ids_times:
        pontos = get_pontuacao_parcial_time(id_time, parciais)
        if pontos is not None:
            dados.append(
                {
                    "id_time": id_time,
                    "rodada": rodada,
                    "pontuacao": round(pontos, 2),
                }
            )
    return dados


def montar_dataframe_pontuacoes(dados, id_nome_time):
    df = pd.DataFrame(dados)
    df["nome_time"] = df["id_time"].map(id_nome_time)
    return df


def validar_cobertura(dados, ids_times, id_nome_time, rodadas):
    coletados = {(d["id_time"], d["rodada"]) for d in dados}
    faltando = [
        (id_nome_time[id_time], rodada)
        for id_time in ids_times
        for rodada in rodadas
        if (id_time, rodada) not in coletados
    ]
    if faltando:
        print(f"[AVISO] Faltando pontuação para: {faltando}")
    return faltando


def obter_ultima_rodada_registrada(caminho_dados):
    try:
        pontuacoes = ler_tabela_delta(caminho_dados)
    except TableNotFoundError:
        return 0
    if pontuacoes.empty:
        return 0
    return int(pontuacoes["rodada"].max())
