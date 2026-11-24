# CLAUDE.md — Cartola Djamba Feipa

Guia para agentes de IA que forem alterar este repositório. Leia antes de qualquer mudança.

## 1. Visão geral

Repositório de organização dos campeonatos de **Cartola FC** de um grupo de amigos
("Cartola Djamba Feipa"). São 12 times disputando, ao longo do Brasileirão (38 rodadas):

- **Liga**: pontos corridos com confrontos diretos (vitória/empate/derrota), um campeonato
  por **turno** (1º turno = rodadas 1–19 do Brasileirão; 2º turno = rodadas 20–38).
- **Copa**: fase de grupos + mata-mata, duas **temporadas** por ano (uma por turno).

O repositório tem duas partes:

1. **Scripts de atualização (CLI)**: coletam pontuações da API do Cartola e gravam o CSV
   de pontuações em `data/{ano}/pontuacoes.csv`.
2. **App Streamlit** (`src/app.py`): somente leitura; carrega `config/` + `data/`,
   calcula Liga, Copa e estatísticas em memória (com cache) e exibe tabelas e gráficos.

Idioma: **todo o código, nomes de variáveis, comentários, mensagens e commits são em
português** (sem acentos em identificadores; com acentos em textos/comentários). Mantenha
esse padrão.

## 2. Stack e execução

- Python ≥ 3.11 (`.python-version`), gerenciado com **uv** (`pyproject.toml`, `uv.lock`).
- Dependências diretas: `numpy`, `pandas`, `requests`, `streamlit` (e `pytest`, `ruff` em `dev`).
  **Não adicione dependências sem pedir.**
- Ambiente local em `.venv/` (Windows; PowerShell). `.gitattributes` padroniza fins de linha em `LF`.
  Há também `.devcontainer/` (Codespaces) que usa `uv sync` e roda `uv run streamlit run src/app.py` na porta 8501.

Comandos (sempre a partir da raiz do repo):

```bash
uv run streamlit run src/app.py                     # app
uv run python src/atualizar_rodada.py               # detecta rodada e modo via /mercado/status
uv run python src/atualizar_rodada.py 35 --parcial  # rodada em andamento (ao vivo)
uv run python src/atualizar_rodada.py 35            # rodada fechada (definitivo)
uv run python src/estoque/estoque.py 35             # recoleta TODO o histórico 1..35 (destrutivo)
uv run pytest                                       # testes unitários e de integridade de dados
uv run ruff check .                                 # lint / consistência de estilo
uv run python ferramentas/verificar_saidas.py comparar  # compara saídas com .verificacao/referencia.json
```

Imports são "planos" a partir de `src/` (ex.: `from caminhos import ...`,
`from liga.ranking import ...`). Funciona porque o Python/Streamlit põe o diretório do
script no `sys.path`; `src/estoque/estoque.py`, `ferramentas/verificar_saidas.py` e
`tests/conftest.py` inserem `src/` manualmente. Não converta para imports relativos sem
pedido explícito.

## 3. Estrutura

```
config/
  2026/
    temporada.toml          # Ano, título, regras da Liga, times (id/nome/jogador), config da Copa
    calendario_liga.csv     # Confrontos da Liga (264 linhas: rodada_brasileirao,rodada_liga,time1,time2)
data/
  2026/
    pontuacoes.csv          # Fonte única da verdade (rodada,id_time,pontuacao,definitivo)
  historico_campeoes.csv    # Hall de Campeões (temporada,competicao,jogador,time,nota)
src/
  .streamlit/config.toml    # Tema (primaryColor #E0559B)
  app.py                    # Ponto de entrada do deploy (~65 linhas): config, CSS, navegação e roteamento
  campeonato.py             # Camada única de cálculo: carrega config + CSV e calcula Liga/Copa/Estatísticas
  config_temporada.py       # Leitura e validação de temporada.toml, calendario_liga.csv e historico_campeoes.csv
  caminhos.py               # Caminhos de config/ e data/ por ano (+ detecção automática do ano mais recente)
  atualizar_rodada.py       # CLI principal de atualização de uma rodada (Liga + Copa no terminal)
  dados/
    api_cartola.py          # API do Cartola (status do mercado, definitiva e parcial ao vivo, Session + paralelo)
    persistencia.py         # Leitura/escrita de pontuacoes.csv (idempotente por rodada) e assinatura de cache
  liga/
    ranking.py              # turno_da_rodada, confrontos, snapshots de classificação, offsets e impressão CLI
    estatisticas.py         # Tabela consolidada por rodada/confronto e indicadores estatísticos
    evolucao.py             # Dados + spec Vega-Lite do gráfico "Evolução da classificação"
  copa/
    logica.py               # resolver_copa() unificado, índice O(1), grupos, mata-mata e impressão CLI
  estoque/
    estoque.py              # Recria data/{ano}/pontuacoes.csv do zero (CLI com argumento de rodada)
  ui/
    estilo.css              # CSS global (sem repetição, usando variáveis CSS)
    componentes.py          # exibir_tabela, subtítulo, cabeçalho, navegação, ranking de títulos, formatação
  paginas/
    liga.py                 # Aba Tabela Liga
    copa.py                 # Aba Tabela Copa
    hall.py                 # Aba Hall de Campeões
    estatisticas.py         # Aba Estatísticas
    regras.py               # Aba Regras
ferramentas/
  verificar_saidas.py       # Script de regressão (app + CLI) contra .verificacao/referencia.json
tests/                      # Testes unitários (pytest)
auxiliar_jornal/            # (gitignored) briefing/manual para gerar a "capa de jornal" por IA
```

## 4. Domínio e regras de negócio

### 4.1 Times e configuração por temporada (`config/{ano}/temporada.toml`)
- Cada temporada tem seu diretório em `config/{ano}/`. O sistema detecta automaticamente o
  maior ano configurado (`ano_padrao()`).
- `[[times]]` lista os 12 times com `id` (Cartola), `nome` e `jogador` (apelido do dono).
  `config.nome_completo(nome_time)` → `"Time (Pessoa)"`, formato usado em toda a exibição.
- Em `data/{ano}/pontuacoes.csv` a chave é `id_time` (estável); o `nome_time` é mapeado na
  leitura a partir de `temporada.toml`. Em `calendario_liga.csv` e nas seções de Copa de
  `temporada.toml` os nomes são validados automaticamente no carregamento.
- Atenção a caracteres especiais nos nomes (`"CAIO JÚNIOR F.C. ®️"`, `"Arãcanela F.C."`).

### 4.2 Liga (`liga/ranking.py`, `config/{ano}/calendario_liga.csv`)
- Cada confronto compara as pontuações brutas do Cartola dos dois times na rodada.
- `margem_empate = 2.0`: se `|p1 - p2|` (arredondado para 2 casas) `< 2.0` é **empate**
  (1 ponto para cada). Senão vitória = 3, derrota = 0.
- Mesmo em empate, `vencedor`/`perdedor` são preenchidos (`time1` se `p1 >= p2`);
  quem distingue empate são `pontos_vencedor == pontos_perdedor == 1`.
- `rodada_corte_turno = 19`: turno 1 = rodadas ≤ 19; turno 2 = rodadas > 19.
  Regra centralizada em `liga.ranking.turno_da_rodada`. Cada turno é um campeonato separado.
- Classificação: ordenar por `pontos` desc, depois `pontuacao_total` (soma das
  pontuações brutas no turno) desc.
- **Rodadas duplas**: as rodadas 7, 8, 9, 27, 28 e 29 do Brasileirão têm **dois**
  confrontos da Liga cada (12 linhas no calendário). Por isso há 22 rodadas da Liga por
  turno e `rodada_liga` vai de 1 a 44 (numeração **acumulada**, não reinicia no turno).
  `temporada.rodada_liga_relativa(rodada_liga, turno)` converte para a numeração do turno.

### 4.3 Copa (`copa/logica.py`, `config/{ano}/temporada.toml`)
- Em `temporada.toml`, as fases são definidas por intervalos **inclusivos** `[inicio, fim]`,
  convertidos para `range(inicio, fim + 1)` ao carregar:
  - T1: grupos 2–6, quartas 10–12, semi 13–15, final 16–18.
  - T2: grupos 22–26, quartas 30–32, semi 33–35, final 36–38.
- **Fase de grupos**: 2 grupos de 5 (`grupo_a`/`grupo_b`, exibidos como "Grupo 1/2").
  Classificação = soma das pontuações brutas nas rodadas da fase. Top 3 de cada grupo
  avança. Não há confronto direto nos grupos.
- **Times "fora"** (`times_fora`): 2 times que não jogam os grupos e entram direto nas
  quartas. São o **campeão (`fora_1`) e o vice (`fora_2`) da Copa anterior** (cadastrados
  à mão no `temporada.toml`).
- **Chaveamento**: `chave_quartas` usa posições simbólicas (`"1_grupo_a"`, `"fora_2"`...);
  `chave_semi` e `chave_final` usam índices dos vencedores da fase anterior.
- **Mata-mata**: soma das pontuações brutas das rodadas da fase; maior soma vence.
  Empate exato favorece `time1` (`>=`). Não há margem de empate na Copa.
- `resolver_copa(pontuacoes, temporadas_copa, rodada_exibida, rodada_maxima_definitiva)`
  é a função única usada tanto pelo app quanto pelo CLI:
  - uma fase só é definitiva quando sua última rodada já tem `definitivo = true`
    (`rodada_maxima_definitiva >= rodadas_fase.stop - 1`);
  - se a fase anterior ainda não fechou (ou está parcial), devolve `EstadoCopa` com
    `motivo_bloqueio`.

### 4.4 Pontuação parcial (`dados/api_cartola.py`)
- Definitiva: `GET https://api.cartola.globo.com/time/id/{id}/{rodada}` → campo `pontos`.
- Parcial (ao vivo, mercado fechado): combina `GET /atletas/pontuados` com
  `GET /time/id/{id}` (escalação atual) em `calcular_pontuacao_parcial_escalacao`:
  1. titular que não entrou em campo é substituído pelo reserva da mesma posição
     (se o reserva jogou e tem pontuação ≥ 0);
  2. reserva de luxo substitui o pior titular da sua posição se todos jogaram e ele
     pontuou mais;
  3. capitão (ou quem ocupar a vaga) × 1,5 (`MULTIPLICADOR_CAPITAO`).
- Só funciona para a rodada **em andamento** (a escalação consultada é a atual).
- `consultar_status_mercado()` usa `GET /mercado/status` para detectar automaticamente
  rodada e modo quando `atualizar_rodada.py` é chamado sem argumentos.

## 5. Dados (`data/`)

- **`data/{ano}/pontuacoes.csv`** é a **única fonte da verdade** das pontuações:
  colunas `rodada,id_time,pontuacao,definitivo` (ordenado por rodada e ordem dos times em
  `temporada.toml`, 2 casas decimais, `true`/`false`).
- Todas as tabelas derivadas (confrontos da Liga, snapshots de classificação por rodada,
  tabelas/chaveamentos da Copa e estatísticas) são calculadas em memória em
  `campeonato.carregar_temporada(ano)` — não há tabelas derivadas gravadas em disco nem
  necessidade de backfill.
- **`data/historico_campeoes.csv`** guarda o Hall de Campeões
  (`temporada,competicao,jogador,time,nota`), lido pela aba Hall.
- Escritas de uma rodada (`salvar_pontuacoes_rodada`) substituem apenas as linhas daquela
  rodada, então reexecutar a mesma rodada é idempotente.
- `definitivo = false` indica rodada parcial (`--parcial`); o app mostra "⏳" no seletor.
- Nunca altere `data/{ano}/pontuacoes.csv` manualmente nem o regenere sem pedido.

## 6. Fluxo operacional de uma rodada

1. Durante a rodada (mercado fechado): `uv run python src/atualizar_rodada.py` (ou
   `35 --parcial`) → commit `update: atualização dos dados parciais da rodada N`.
2. Após fechar (mercado aberto): `uv run python src/atualizar_rodada.py` (ou `35`) →
   commit `update: atualização dos dados finais da rodada N`.
3. `atualizar_rodada` coleta as pontuações, grava a rodada em `data/{ano}/pontuacoes.csv`,
   recalcula a temporada em memória via `carregar_temporada(ano)` e imprime confrontos,
   classificação do turno atual e resultados da Copa (se aplicável).
4. **Deploy**: o ponto de entrada em produção é `src/app.py`, que lê os arquivos
   commitados em `config/` e `data/`. Por isso, dar push dos dados atualiza o app. Não
   renomeie nem mova `src/app.py` (nem `src/.streamlit/`) sem avisar: isso quebra o deploy.

Ao fim de cada campeonato:
- adicione a linha do campeão em `data/historico_campeoes.csv`;
- ao fim de uma Copa, campeão e vice viram `times_fora` da próxima temporada, e os grupos
  e chaves dela são cadastrados em `config/{ano}/temporada.toml`.

## 7. App Streamlit (`src/app.py`, `src/ui/`, `src/paginas/`)

- `src/app.py` configura a página (`st.set_page_config` primeiro), carrega a temporada e
  o histórico com `@st.cache_data` (chaveado por `assinatura_temporada(ano)` com `mtime_ns`
  e tamanho dos arquivos), injeta `src/ui/estilo.css` + variáveis CSS, renderiza as abas e
  delega para `src/paginas/*.py`.
- **Abas** (ordem fixa em `app.py`): `liga`, `copa`, `hall`, `estatisticas`, `regras`.
  A ordem importa: `estilo.css` colore a aba ativa por `:nth-child`. Ao adicionar/reordenar
  abas, ajuste `src/ui/estilo.css`.
- **Navegação sincronizada com a URL** (`ui.componentes.seletor_navegacao`): usa
  `st.segmented_control` + `st.query_params` (`aba`, `rodada_liga`, `rodada_copa`,
  `sub_hall`). Há um script `popstate` em `app.py` que recarrega no Voltar/Avançar.
- **Tabelas e componentes** (`src/ui/componentes.py` + `src/ui/estilo.css`): HTML limpo com
  classes CSS (sem estilos inline repetidos); `exibir_tabela(...)` atende a Liga e recebe
  números crus para decidir as classes (`_classe_lado`) antes de formatar com
  `formatar_pontuacao` (`1.234,56`). A Copa usa cartões em CSS Grid
  (`exibir_grupo_copa` e `exibir_mata_mata_copa`) com os dois times empilhados por
  confronto, eliminando scroll horizontal no desktop e no celular. Rodadas parciais
  exibem `⏳` no seletor e banner discreto (`exibir_aviso_parcial`) nas abas Liga e Copa.
- **CSS** (`src/ui/estilo.css`): lido uma vez por processo (`lru_cache`); usa apenas hooks
  estáveis (`[class*="st-key-nav_"]`, `.st-key-*`, `data-testid`, `aria-checked`, `role`) —
  **nunca** classes `st-emotion-cache-*`. Adaptado a celular (`@media (max-width: 600px)`)
  e tema escuro (`prefers-color-scheme: dark`).
- **Estatísticas** (`paginas/estatisticas.py` + `liga/estatisticas.py` + `liga/evolucao.py`):
  "Evolução" (Vega-Lite sem novas dependências), "Desempenho" e "Confrontos". Comportamento
  detalhado do gráfico está no `README.md`.
- **Regras** (`paginas/regras.py`): gera o texto dinamicamente a partir de `config.regras`
  e `config.copa`.

## 8. Convenções para alterações

- Responda e documente em português. Commits seguem `tipo: descrição` em português
  (`feat:`, `update:`, `remove:`, `fix:`, `refactor:`...).
- Regras de negócio ficam fora da camada de UI: configuração em `config/`, cálculo em
  `liga/`, `copa/`, `dados/` e `campeonato.py`; `src/paginas/` e `src/ui/` apenas exibem.
- Ao mudar o comportamento do app ou a arquitetura, atualize `README.md` e este `CLAUDE.md`.
- Para validar mudanças:
  - rode `uv run ruff check .` e `uv run pytest`;
  - rode `uv run streamlit run src/app.py` e confira desktop e celular (< 600 px);
  - se houver referência em `.verificacao/referencia.json`, rode
    `uv run python ferramentas/verificar_saidas.py comparar`.
- Não faça chamadas à API do Cartola nem grave em `data/` em testes exploratórios.

## 9. `auxiliar_jornal/` (fora do git)

Material para gerar, via modelo de imagem, uma "capa de jornal" vintage do campeonato a
cada marco: `Manual_Identidade_Cartola_Djamba_Feipa.md` (regras permanentes de
identidade visual), `Briefing_Nova_Edicao_...md` (o que muda na edição) e imagens de
referência (última versão aprovada + fotos). Não faz parte do app.
