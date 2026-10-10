"""Aplica o ajuste do gráfico "Evolução da classificação".

Equivale ao ajuste_evolucao_classificacao.patch, mas respeita o fim de linha
(CRLF ou LF) que cada arquivo já usa, o que o `git apply` não faz no Windows.

Uso, na raiz do projeto (a pasta que contém `src/` e `README.md`):

    python aplicar_ajuste.py            # ou: uv run python aplicar_ajuste.py

Nada é gravado se algum trecho esperado não for encontrado (por exemplo, se o
arquivo local já foi alterado depois do zip enviado) ou se o ajuste já estiver
aplicado.
"""

import sys
from pathlib import Path

# Cada edição: (arquivo, trecho antigo, trecho novo). Escritos com \n; na hora de
# aplicar, são convertidos para o fim de linha do arquivo de destino.
EDICOES = [
    (
        "src/liga/evolucao.py",
        "CORES_EVOLUCAO = [",
        '''# Abaixo desta largura do contêiner (px) o gráfico usa os nomes quebrados em
# linhas mais curtas. Equivale ao limite anterior (600 px de área útil mais
# ~60 px do eixo vertical). Não pode usar `width`: a área útil agora resulta do
# layout, que depende do tamanho dos nomes, e a escolha ficaria oscilando.
LARGURA_CONTAINER_COMPACTA = 660

# Folga mínima (px) entre o fim do texto e a borda do gráfico: absorve diferenças
# de renderização entre navegadores, para que o ")" final nunca seja cortado.
FOLGA_DIREITA_NOMES = 2

CORES_EVOLUCAO = [''',
    ),
    (
        "src/liga/evolucao.py",
        '''        # O conjunto de linhas e nomes ocupa a largura do contêiner.
        # Só a direita reserva espaço para os nomes; não há margem espelhada.
        "autosize": {"type": "fit-x", "contains": "padding"},''',
        '''        # Linhas e nomes ocupam a largura do contêiner. Com `fit`, o Vega mede o
        # texto que passa da área do gráfico e reserva exatamente esse espaço à
        # direita: o fim do maior nome encosta na borda, em qualquer tela e
        # fonte, sem largura fixa chutada. Não há margem espelhada à esquerda.
        "autosize": {"type": "fit-x", "contains": "padding"},
        "padding": {"right": FOLGA_DIREITA_NOMES},''',
    ),
    (
        "src/liga/evolucao.py",
        '''                "scale": {"zero": False, "nice": False, "domain": [rodadas[0] - 0.3, rodadas[-1]],
                          "range": [0, {"expr": "max(60, width - (width < 600 ? 145 : 205))"}]},''',
        '''                "scale": {"zero": False, "nice": False, "domain": [rodadas[0] - 0.3, rodadas[-1]]},''',
    ),
    (
        "src/liga/evolucao.py",
        '''                "text": {"expr": "width < 600 ? datum.rotulo_mobile : datum.rotulo_desktop"},''',
        '''                "text": {"expr": (
                    f"(containerSize()[0] || windowSize()[0]) < {LARGURA_CONTAINER_COMPACTA}"
                    " ? datum.rotulo_mobile : datum.rotulo_desktop"
                )},''',
    ),
    (
        "README.md",
        '''  no formato `Time (Pessoa)` à direita do último ponto de cada linha. Os nomes
  quebram por palavras conforme a largura da tela, reduzindo a faixa lateral
  reservada aos rótulos. O gráfico tem 540 px de altura. O conjunto
  de linhas e nomes ocupa a largura da caixa de seleção de times, sem uma
  margem vazia adicional à esquerda. Apenas os nomes à direita têm espaço
  reservado, adaptado à largura da tela.
''',
        '''  no formato `Time (Pessoa)` à direita do último ponto de cada linha. Os nomes
  quebram por palavras conforme a largura do contêiner (abaixo de 660 px usam
  linhas mais curtas). O gráfico tem 540 px de altura. O conjunto de linhas e
  nomes ocupa a largura da caixa de seleção de times, sem uma margem vazia
  adicional à esquerda. O espaço à direita não é fixo: o próprio gráfico mede
  o texto e reserva exatamente a largura do maior nome exibido, de modo que o
  fim dele coincide com a borda direita da caixa (folga de 2 px para que
  nenhum navegador corte o último caractere). Ao filtrar times, a faixa se
  ajusta aos nomes que restaram.
''',
    ),
]


def fim_de_linha(texto):
    """CRLF se o arquivo usa majoritariamente CRLF; senão LF."""
    crlf = texto.count("\r\n")
    lf_puro = texto.count("\n") - crlf
    return "\r\n" if crlf > lf_puro else "\n"


def main():
    raiz = Path.cwd()
    arquivos = {}
    for caminho, _, _ in EDICOES:
        if caminho not in arquivos:
            alvo = raiz / caminho
            if not alvo.is_file():
                sys.exit(f"Não encontrei {caminho}. Rode o script na raiz do projeto.")
            arquivos[caminho] = alvo.read_bytes().decode("utf-8")

    novos = dict(arquivos)
    problemas = []
    for caminho, antigo, novo in EDICOES:
        texto = novos[caminho]
        eol = fim_de_linha(texto)
        antigo_e = antigo.replace("\n", eol)
        novo_e = novo.replace("\n", eol)
        if texto.count(antigo_e) == 1:
            novos[caminho] = texto.replace(antigo_e, novo_e)
        elif novo_e in texto:
            problemas.append(f"{caminho}: trecho já aplicado -> {antigo.splitlines()[0].strip()[:60]!r}")
        else:
            problemas.append(f"{caminho}: trecho esperado não encontrado -> {antigo.splitlines()[0].strip()[:60]!r}")

    if problemas:
        print("Nada foi alterado. Motivo(s):")
        for p in problemas:
            print("  -", p)
        print("\nSe o arquivo local mudou depois do zip enviado, me mande o conteúdo atual "
              "de src/liga/evolucao.py para eu adaptar o ajuste.")
        sys.exit(1)

    for caminho, texto in novos.items():
        # newline="" evita que o Python converta os fins de linha ao gravar.
        with open(raiz / caminho, "w", encoding="utf-8", newline="") as f:
            f.write(texto)
        print(f"Atualizado: {caminho}")
    print("\nPronto. Rode o app e confira a aba Estatísticas > Evolução.")


if __name__ == "__main__":
    main()
