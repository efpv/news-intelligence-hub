# 📡 News Intelligence Hub
Radar Político, Financeiro & Tecnologia — dashboard Streamlit que consolida feeds RSS (política, economia, mercado, tecnologia e IA) com análise de sentimento, tags automáticas, tendências e exportação.

## Funcionalidades
Filtros (categoria, fonte, período, sentimento, busca) · 7 KPIs · cards de notícia · tags automáticas · Trending Topics · 6 gráficos Plotly · exportação CSV/Excel · coleta automática de hora em hora (cache 1h + botão de atualização manual) · filtro "Última hora" · tratamento de erros por feed · módulo de resumo executivo (pronto para LLM).

## Tecnologias
Python 3.12+, Streamlit, feedparser, pandas, requests, BeautifulSoup4, Plotly, TextBlob, OpenPyXL.

## Estrutura
```
app.py · requirements.txt · src/ (config, rss_reader, sentiment, tags, trends, analytics, export, summarizer, utils)
assets/styles.css · .streamlit/config.toml · data/cache/
```

## Instalação local
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Configuração
Feeds em `src/config.py` (lista `FEEDS`). **Valide as URLs RSS** — portais mudam endpoints. Fontes sem RSS público (ex.: B3) usam Google News RSS. Chaves de API (V2) vão em `.streamlit/secrets.toml` (já no `.gitignore`).

## Deploy
```bash
git init && git add . && git commit -m "Initial Commit"
git branch -M main
git remote add origin URL_REPOSITORIO
git push -u origin main
```
1. Crie o repositório no GitHub e publique o código.
2. Acesse https://share.streamlit.io e conecte sua conta GitHub.
3. **New app** → selecione repositório e branch `main`.
4. Main file path: `app.py` → **Deploy**.
5. Cada `git push` na `main` redeploya automaticamente.

## Roadmap V2
Resumo com IA · RAG sobre histórico · PostgreSQL + banco vetorial · busca semântica · chat com notícias · agenda econômica/Copom · alertas Telegram/Discord/Teams · newsletter · API REST · autenticação.

## Screenshots
`docs/dashboard.png` · `docs/analytics.png` (placeholders)
