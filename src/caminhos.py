from pathlib import Path

RAIZ_PROJETO = Path(__file__).resolve().parent.parent
DIR_CONFIG = RAIZ_PROJETO / "config"
DIR_DADOS = RAIZ_PROJETO / "data"
CAMINHO_HISTORICO_CAMPEOES = DIR_DADOS / "historico_campeoes.csv"


def ano_padrao():
    """Retorna o ano mais recente configurado em `config/`."""
    anos = [
        int(p.name)
        for p in DIR_CONFIG.iterdir()
        if p.is_dir() and p.name.isdigit()
    ]
    return max(anos) if anos else 2026


def caminho_config_temporada(ano):
    return DIR_CONFIG / str(ano) / "temporada.toml"


def caminho_calendario_liga(ano):
    return DIR_CONFIG / str(ano) / "calendario_liga.csv"


def caminho_pontuacoes(ano):
    return DIR_DADOS / str(ano) / "pontuacoes.csv"
