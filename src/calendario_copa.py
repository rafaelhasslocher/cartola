CALENDARIOS_COPA_POR_TEMPORADA = {
    1: {
        "fase_de_grupos": range(2, 7),
        "quartas": range(10, 13),
        "semi": range(13, 16),
        "final": range(16, 19),
    },
    2: {
        "fase_de_grupos": range(22, 27),
        "quartas": range(30, 33),
        "semi": range(33, 36),
        "final": range(36, 39),
    },
}


GRUPOS_COPA_POR_TEMPORADA = {
    1: {
        "grupo_a": [
            "Pigeon Boiteux OSC",
            "Baguetty e os perus",
            "Kyrolina FC",
            "Club silencio",
            "Paquetetra",
        ],
        "grupo_b": [
            "Ansiedade Prime FC",
            "GARANTES",
            "Arãcanela F.C.",
            "Travesseiros confortáveis FC",
            "São Janumário FC",
        ],
    },
    2: {
        "grupo_a": [
            "CAIO JÚNIOR F.C. ®️",
            "Baguetty e os perus",
            "Arãcanela F.C.",
            "Inhames",
            "São Janumário FC",
        ],
        "grupo_b": [
            "Pigeon Boiteux OSC",
            "GARANTES",
            "Travesseiros confortáveis FC",
            "Paquetetra",
            "Club silencio",
        ],
    },
}


TIMES_FORA_POR_TEMPORADA = {
    1: ["CAIO JÚNIOR F.C. ®️", "Inhames"],
    2: ["Ansiedade Prime FC", "Kyrolina FC"],
}


CHAVE_QUARTAS_POR_TEMPORADA = {
    1: [
        ("fora_1", "fora_2"),
        ("1_grupo_b", "1_grupo_a"),
        ("2_grupo_a", "2_grupo_b"),
        ("3_grupo_a", "3_grupo_b"),
    ],
    2: [
        ("1_grupo_a", "2_grupo_b"),
        ("1_grupo_b", "2_grupo_a"),
        ("fora_1", "3_grupo_a"),
        ("fora_2", "3_grupo_b"),
    ],
}


CHAVE_SEMI_POR_TEMPORADA = {
    1: [(0, 3), (1, 2)],
    2: [(0, 1), (2, 3)],
}


CHAVE_FINAL_POR_TEMPORADA = {
    1: [(0, 1)],
    2: [(0, 1)],
}
