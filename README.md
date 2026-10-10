# Cartola — Djamba Feipa

Aplicação Streamlit para acompanhamento da Liga e da Copa.

## Execução

Na raiz do projeto, com as dependências instaladas:

```bash
uv run streamlit run src/app.py
```

## Evolução da classificação

Na aba **Estatísticas**, a seção **Evolução da classificação** apresenta a
trajetória dos 12 times, com seleção independente de 1º ou 2º turno e filtro
de participantes. O turno mais recente com dados é selecionado inicialmente.

- Eixo horizontal: rodada do Brasileirão, apenas com classificações registradas.
- Eixo vertical: posição na Liga, com o 1º lugar no topo e o 12º na base.
- Rodadas duplas aparecem uma única vez, após considerar todos os confrontos.
- As posições seguem os snapshots de `ranking_liga`: pontos na Liga e pontuação
  acumulada, em ordem decrescente, como na tabela da Liga.
- Selecionar menos times não recalcula suas posições.
- Os detalhes de cada ponto mostram time, rodada, posição, pontos na Liga,
  pontuação acumulada e situação parcial ou definitiva.
- Snapshots do primeiro turno repetidos durante o segundo são desconsiderados.
- Não são criadas posições iniciais fictícias nem pontos para rodadas futuras.

O preparo dos dados e a especificação do gráfico ficam em
`src/liga/evolucao.py`; os controles e a exibição ficam em `src/app.py`.
O gráfico usa o suporte Vega-Lite do Streamlit, sem novas dependências.

## Organização da aba Estatísticas

- **Evolução**: trajetória por turno; filtro de times recolhível e nomes completos
  no formato `Time (Pessoa)` à direita do último ponto de cada linha. Os nomes
  quebram por palavras conforme a largura do contêiner (abaixo de 660 px usam
  linhas mais curtas). O gráfico tem 540 px de altura. O conjunto de linhas e
  nomes ocupa a largura da caixa de seleção de times, sem uma margem vazia
  adicional à esquerda. O espaço à direita não é fixo: o próprio gráfico mede
  o texto e reserva exatamente a largura do maior nome exibido, de modo que o
  fim dele coincide com a borda direita da caixa (folga de 2 px para que
  nenhum navegador corte o último caractere). Ao filtrar times, a faixa se
  ajusta aos nomes que restaram.
  A consulta de posições e pontos por rodada permite ler detalhes no celular
  sem depender de passar o mouse sobre o gráfico.
- **Desempenho**: seletor entre maior pontuador e Top 3.
- **Confrontos**: seletor entre Top 5 sem vitória e líder com empate.

Os seletores **Explorar estatísticas** e **Campeonato** usam rótulos compactos
e opções com destaque suave na cor da aba, sem cartões ou títulos grandes.
As opções quebram em linhas e mantêm uma área de toque de 44 px no celular.

Uma análise é exibida por vez. Os quatro indicadores existentes continuam
considerando ambos os turnos, incluindo resultados parciais registrados.
