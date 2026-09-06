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
            "Pigeon Boiteux OSC (PV)",
            "Baguetty e os perus (Camilla)",
            "Kyrolina FC (Renata)",
            "Club silencio (Ruy)",
            "Paquetetra (Hammes)",
        ],
        "grupo_b": [
            "Ansiedade Prime FC (Gui)",
            "GARANTES (Garantes)",
            "Arãcanela F.C. (Feijó)",
            "Travesseiros confortáveis FC (Bruna)",
            "São Janumário FC (Mario)",
        ],
    },
    2: {
        "grupo_a": [
            "CAIO JÚNIOR F.C. ®️ (Rafa)",
            "Baguetty e os perus (Camilla)",
            "Arãcanela F.C. (Feijó)",
            "Inhames (Ian)",
            "São Janumário FC (Mario)",
        ],
        "grupo_b": [
            "Pigeon Boiteux OSC (PV)",
            "GARANTES (Garantes)",
            "Travesseiros confortáveis FC (Bruna)",
            "Paquetetra (Hammes)",
            "Club silencio (Ruy)",
        ],
    },
}


TIMES_FORA_POR_TEMPORADA = {
    1: ["CAIO JÚNIOR F.C. ®️ (Rafa)", "Inhames (Ian)"],
    2: ["Ansiedade Prime FC (Gui)", "Kyrolina FC (Renata)"],
}


CHAVE_QUARTAS_POR_TEMPORADA = {
    1: [
        ("fora_1", "fora_2"),
        ("1_grupo_b", "1_grupo_a"),
        ("2_grupo_a", "2_grupo_b"),
        ("3_grupo_a", "3_grupo_b"),
    ],
    2: [
        ("1_grupo_a", "3_grupo_b"),
        ("1_grupo_b", "3_grupo_a"),
        ("fora_1", "2_grupo_b"),
        ("fora_2", "2_grupo_a"),
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
