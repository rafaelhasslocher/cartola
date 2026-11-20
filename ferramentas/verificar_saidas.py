"""Retrato das saídas do app e do CLI, para conferir refatorações.

Gera, sem tocar na API do Cartola nem gravar em `data/`:
- tudo o que o app desenha em cada aba/rodada/seletor (via Streamlit AppTest);
- o que `atualizar_rodada.py` imprime para cada rodada já registrada (com a
  coleta substituída pelos dados salvos e a gravação desligada).

Uso, na raiz do projeto:

    uv run python ferramentas/verificar_saidas.py gerar     # salva a referência
    uv run python ferramentas/verificar_saidas.py comparar  # compara com a referência

A referência fica em `.verificacao/` (fora do git).
"""

import base64
import contextlib
import difflib
import io
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SRC = RAIZ / "src"
APP = SRC / "app.py"
SAIDA = RAIZ / ".verificacao"
REFERENCIA = SAIDA / "referencia.json"
ATUAL = SAIDA / "atual.json"

sys.path.insert(0, str(SRC))


# --------------------------------------------------------------------------- app


def _decodificar_arrow(b64):
    import pyarrow as pa

    tabela = pa.ipc.open_stream(base64.b64decode(b64)).read_all()
    return tabela.to_pandas().to_csv(index=False)


def _limpar(obj):
    """Remove ids gerados pelo Streamlit e decodifica dados Arrow (o binário
    pode variar sem que o conteúdo mude)."""
    if isinstance(obj, dict):
        limpo = {}
        for chave, valor in obj.items():
            if chave in ("id", "formId"):
                continue
            if chave == "data" and isinstance(valor, str):
                try:
                    limpo[chave] = _decodificar_arrow(valor)
                    continue
                except Exception:
                    pass
            limpo[chave] = _limpar(valor)
        return limpo
    if isinstance(obj, list):
        return [_limpar(v) for v in obj]
    return obj


def _extrair(no, saida):
    from google.protobuf.json_format import MessageToDict

    filhos = getattr(no, "children", None)
    if not isinstance(filhos, dict):
        return
    for filho in filhos.values():
        proto = getattr(filho, "proto", None)
        registro = {"tipo": getattr(filho, "type", type(filho).__name__)}
        if proto is not None:
            try:
                registro["proto"] = _limpar(MessageToDict(proto))
            except Exception:
                registro["proto"] = str(proto)
        saida.append(registro)
        _extrair(filho, saida)


def _rodar_app(params, acoes=()):
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(str(APP), default_timeout=120)
    for chave, valor in params.items():
        at.query_params[chave] = str(valor)
    at.run()
    for acao in acoes:
        acao(at)
        at.run()
    if at.exception:
        return [{"excecao": [str(e.message) for e in at.exception]}]
    elementos = []
    _extrair(at.main, elementos)
    return elementos


def _cenarios_app():
    cenarios = {"app/padrao": ({}, ())}
    for rodada in range(1, 39):
        cenarios[f"app/liga/{rodada:02d}"] = ({"aba": "liga", "rodada_liga": rodada}, ())
        cenarios[f"app/copa/{rodada:02d}"] = ({"aba": "copa", "rodada_copa": rodada}, ())
    for sub in ("liga", "copa"):
        cenarios[f"app/hall/{sub}"] = ({"aba": "hall", "sub_hall": sub}, ())
    cenarios["app/regras"] = ({"aba": "regras"}, ())

    est = {"aba": "estatisticas"}
    for turno in (1, 2):
        cenarios[f"app/estatisticas/evolucao/turno{turno}"] = (
            est,
            (lambda at, t=turno: at.radio(key="turno_evolucao").set_value(t),),
        )
    for secao, indicadores in (
        ("Desempenho", ("Maior pontuador", "Top 3")),
        ("Confrontos", ("Top 5 sem vitória", "Líder com empate")),
    ):
        for indicador in indicadores:
            cenarios[f"app/estatisticas/{secao}/{indicador}"] = (
                est,
                (
                    lambda at, s=secao: at.radio(key="secao_estatisticas").set_value(s),
                    lambda at, s=secao, i=indicador: at.selectbox(
                        key=f"indicador_{s}"
                    ).set_value(i),
                ),
            )
    return cenarios


# --------------------------------------------------------------------------- CLI


def _saidas_cli():
    import atualizar_rodada
    from caminhos import ano_padrao, caminho_pontuacoes
    from dados.persistencia import carregar_pontuacoes

    ano = ano_padrao()
    pontuacoes = carregar_pontuacoes(caminho_pontuacoes(ano))

    def _coletar_salvo(ids_times, rodadas):
        filtro = pontuacoes[pontuacoes["rodada"].isin(list(rodadas))]
        return filtro[["id_time", "rodada", "pontuacao"]].to_dict("records")

    atualizar_rodada.coletar_pontuacoes = _coletar_salvo
    atualizar_rodada.salvar_pontuacoes_rodada = lambda *a, **k: None  # nada é gravado

    saidas = {}
    for rodada in sorted(int(r) for r in pontuacoes["rodada"].unique()):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            atualizar_rodada.atualizar_rodada(rodada, ano=ano)
        saidas[f"cli/rodada/{rodada:02d}"] = buffer.getvalue()
    return saidas


# ----------------------------------------------------------------------- comando


def gerar():
    import logging

    logging.getLogger("streamlit").setLevel(logging.ERROR)
    resultado = {}
    for nome, (params, acoes) in _cenarios_app().items():
        resultado[nome] = _rodar_app(params, acoes)
    resultado.update(_saidas_cli())
    return resultado


def _texto(valor):
    return json.dumps(valor, ensure_ascii=False, indent=1, sort_keys=True).splitlines()


def main():
    comando = sys.argv[1] if len(sys.argv) > 1 else "comparar"
    SAIDA.mkdir(exist_ok=True)
    resultado = gerar()
    destino = REFERENCIA if comando == "gerar" else ATUAL
    destino.write_text(
        json.dumps(resultado, ensure_ascii=False, indent=1, sort_keys=True),
        encoding="utf-8",
    )
    print(f"{len(resultado)} cenários salvos em {destino.relative_to(RAIZ)}")
    if comando == "gerar":
        return

    referencia = json.loads(REFERENCIA.read_text(encoding="utf-8"))
    diferentes = [
        n for n in sorted(set(referencia) | set(resultado))
        if referencia.get(n) != resultado.get(n)
    ]
    if not diferentes:
        print("OK: todas as saídas são idênticas à referência.")
        return
    print(f"{len(diferentes)} cenário(s) diferente(s):")
    for nome in diferentes:
        print(f"\n=== {nome}")
        diff = difflib.unified_diff(
            _texto(referencia.get(nome)), _texto(resultado.get(nome)), lineterm="", n=1
        )
        for i, linha in enumerate(diff):
            if i >= 40:
                print("   ...")
                break
            print("  ", linha[:300])
    sys.exit(1)


if __name__ == "__main__":
    main()
