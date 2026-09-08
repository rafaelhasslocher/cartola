import pandas as pd
import requests
from deltalake.exceptions import TableNotFoundError

from dados.persistencia import ler_tabela_delta

MULTIPLICADOR_CAPITAO = 1.5


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


def _buscar_parciais_raw():
    """Busca as pontuações parciais da rodada em andamento com todos os campos
    originais da API (inclusive `entrou_em_campo`), necessários para aplicar
    as regras de substituição do banco de reservas.
    """
    url = "https://api.cartola.globo.com/atletas/pontuados"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    return resp.json().get("atletas", {})


def _buscar_escalacao_raw(id_time):
    """Busca a escalação atual do time (titulares, reservas, capitão e
    reserva de luxo) direto na API do Cartola.
    """
    url = f"https://api.cartola.globo.com/time/id/{id_time}"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    return resp.json()


def _pontos_e_status_atleta(atleta_id, parciais_raw):
    """Retorna (pontos, jogou) de um atleta a partir do dict cru de parciais
    (chaveado por atleta_id em string, vindo de /atletas/pontuados).
    """
    dado = parciais_raw.get(str(atleta_id))
    if dado is None:
        return 0.0, False
    pontos = dado.get("pontuacao", dado.get("pontos_num", 0.0)) or 0.0
    jogou = bool(dado.get("entrou_em_campo", False))
    return pontos, jogou


def get_pontuacao_parcial_time(id_time, parciais):
    """Calcula a pontuação parcial do time aplicando as regras do Cartola:
    1) se o titular não jogou, o reserva da mesma posição entra (desde que
       o reserva tenha jogado e não tenha pontuação negativa);
    2) o reserva de luxo entra se TODOS os titulares da sua posição jogaram
       e ele pontuar mais que o de menor pontuação entre eles (mesmo que a
       pontuação do reserva de luxo seja negativa);
    3) o capitão (ou quem ocupar a vaga dele) pontua x1,5.

    `parciais` deve ser o dict cru retornado por `_buscar_parciais_raw()`.
    """
    try:
        escalacao = _buscar_escalacao_raw(id_time)
    except requests.RequestException as e:
        print(f"[AVISO] Falha ao calcular parcial do time {id_time}: {e}")
        return None

    titulares = escalacao.get("atletas") or []
    reservas = escalacao.get("reservas") or []
    capitao_id = escalacao.get("capitao_id")
    reserva_luxo_id = escalacao.get("reserva_luxo_id")

    reservas_por_posicao = {r["posicao_id"]: r for r in reservas}
    reserva_luxo = next(
        (r for r in reservas if r["atleta_id"] == reserva_luxo_id), None
    )

    slots = []
    for titular in titulares:
        pontos, jogou = _pontos_e_status_atleta(titular["atleta_id"], parciais)
        slots.append(
            {
                "atleta_id": titular["atleta_id"],
                "posicao_id": titular["posicao_id"],
                "pontos": pontos,
                "jogou": jogou,
                "era_capitao": titular["atleta_id"] == capitao_id,
            }
        )

    # Regra 1: titular não jogou -> reserva da mesma posição entra
    for slot in slots:
        if slot["jogou"]:
            continue
        reserva = reservas_por_posicao.get(slot["posicao_id"])
        if reserva is None:
            continue
        pontos_reserva, jogou_reserva = _pontos_e_status_atleta(
            reserva["atleta_id"], parciais
        )
        if jogou_reserva and pontos_reserva >= 0:
            slot["atleta_id"] = reserva["atleta_id"]
            slot["pontos"] = pontos_reserva

    # Regra 2: reserva de luxo entra se TODOS os titulares da posição jogaram
    # e ele pontuar mais que o pior deles
    if reserva_luxo is not None:
        pontos_luxo, jogou_luxo = _pontos_e_status_atleta(
            reserva_luxo["atleta_id"], parciais
        )
        slots_posicao = [
            s for s in slots if s["posicao_id"] == reserva_luxo["posicao_id"]
        ]
        todos_jogaram = slots_posicao and all(s["jogou"] for s in slots_posicao)

        if jogou_luxo and todos_jogaram:
            pior_slot = min(slots_posicao, key=lambda s: s["pontos"])
            if pontos_luxo > pior_slot["pontos"]:
                pior_slot["atleta_id"] = reserva_luxo["atleta_id"]
                pior_slot["pontos"] = pontos_luxo

    # Regra 3: capitão pontua x1,5 (vale pra quem acabar ocupando a vaga dele)
    pontos_total = 0.0
    for slot in slots:
        pontos = slot["pontos"]
        if slot["era_capitao"]:
            pontos *= MULTIPLICADOR_CAPITAO
        pontos_total += pontos

    return round(pontos_total, 2)


def coletar_pontuacoes_parciais(ids_times, rodada):
    """Coleta a pontuação AO VIVO da rodada em andamento (mercado fechado),
    já aplicando as regras de substituição (banco + reserva de luxo) e
    capitão. Diferente de `coletar_pontuacoes`, aqui a rodada não precisa
    ter fechado: os pontos refletem só os jogadores que já entraram em
    campo até o momento.
    """
    try:
        parciais = _buscar_parciais_raw()
    except requests.RequestException as e:
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
