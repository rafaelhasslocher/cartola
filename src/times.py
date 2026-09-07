IDS_TIMES = [
    11659945,
    20987264,
    50236495,
    4626226,
    3394005,
    13986579,
    50285685,
    12054764,
    11727630,
    256207,
    11958779,
    49230944,
]


ID_NOME_TIME = {
    11659945: "CAIO JÚNIOR F.C. ®️",
    20987264: "Ansiedade Prime FC",
    50236495: "Baguetty e os perus",
    4626226: "Pigeon Boiteux OSC",
    3394005: "GARANTES",
    13986579: "Arãcanela F.C.",
    50285685: "Travesseiros confortáveis FC",
    12054764: "Kyrolina FC",
    11727630: "São Janumário FC",
    256207: "Paquetetra",
    11958779: "Club silencio",
    49230944: "Inhames",
}

ID_JOGADOR = {
    11659945: "Rafa",
    20987264: "Gui",
    50236495: "Camilla",
    4626226: "PV",
    3394005: "Garantes",
    13986579: "Feijó",
    50285685: "Bruna",
    12054764: "Renata",
    11727630: "Mario",
    256207: "Hammes",
    11958779: "Ruy",
    49230944: "Ian",
}

NOME_TIME_POR_JOGADOR = {
    ID_JOGADOR[id_time]: ID_NOME_TIME[id_time] for id_time in IDS_TIMES
}
JOGADOR_POR_NOME_TIME = {
    ID_NOME_TIME[id_time]: ID_JOGADOR[id_time] for id_time in IDS_TIMES
}


def nome_completo(nome_time):
    return f"{nome_time} ({JOGADOR_POR_NOME_TIME[nome_time]})"