# 📡 News Intelligence Hub
Radar Político, Financeiro & Tecnologia — dashboard Streamlit que consolida feeds RSS (política, economia, mercado, tecnologia, IA e notícias internacionais) com análise de sentimento, tags automáticas, tendências e exportação.

## Funcionalidades
- **Cards Interativos na "Visão Geral"**: KPIs estilizados que funcionam como filtros de categoria clicáveis com destaque visual ativo; o card "Total de Notícias" limpa os filtros e restaura a listagem completa.
- **Filtragem Reativa em Memória**: Carregamento único dos feeds na inicialização, permitindo alternância instantânea entre filtros sem requisições de rede ou recarregamentos de página desnecessários.
- **Sincronização Multi-dispositivo por E-mail**: O e-mail informado funciona como chave única e determinística para salvar e recuperar carteira de ativos (tickers B3) e filtros personalizados em qualquer dispositivo.
- **Filtros Avançados**: Categoria, fontes, período ("Última hora", "Últimas 24h", "Últimos 7 dias", "Últimos 30 dias" ou personalizado), análise de sentimento (Positivo, Neutro, Negativo), busca textual e modo "Apenas minha carteira".
- **Inteligência e Análise**: Cards de notícia com tags automáticas, Radar da Carteira B3, Trending Topics, 6 gráficos interativos Plotly e módulo de resumo executivo pronto para LLM.
- **Coleta e Exportação**: Atualização automática configurável (padrão 10 min) + botão manual (🔄), tolerância a falhas por feed e exportação em CSV/Excel e JSON de backup.

## Tecnologias
Python 3.12+, Streamlit, feedparser, pandas, requests, BeautifulSoup4, Plotly, TextBlob, OpenPyXL, gspread (Google Sheets API).

## Estrutura
```
app.py · requirements.txt · src/ (analytics, config, export, portfolio, preferences, rss_reader, sentiment, sheets_store, summarizer, tags, trends, utils)
assets/styles.css · .streamlit/config.toml · data/cache/ · data/user_prefs/
```

## Instalação local
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Configuração
- **Feeds RSS**: Configurados em `src/config.py` (lista `FEEDS`). Fontes sem RSS público (ex.: B3) usam Google News RSS.
- **Segredos e Credenciais**: Chaves de API e credenciais de nuvem vão em `.streamlit/secrets.toml` (ignorado pelo Git).

## Persistência e Sincronização de Preferências
A aplicação utiliza o **e-mail informado pelo usuário** como chave única determinística para recuperar sua carteira de ativos e preferências de filtro em qualquer lugar, sem necessidade de senha:

- **Chave Única (`user_id`)**: O e-mail informado é normalizado (`trim` + `lowercase`) e transformado em um hash SHA-256 estável, garantindo a mesma identidade em qualquer dispositivo.
- **Camadas de Armazenamento**:
  1. **Google Sheets (`src/sheets_store.py`)**: Persistência centralizada em nuvem (abas `users`, `portfolio` e `filters`). Garante a sincronização contínua entre computadores, celulares e tablets diferentes, sobrevivendo a reinicializações em plataformas como Streamlit Community Cloud.
  2. **Arquivos JSON (`data/user_prefs/{user_id}.json`)**: Armazenamento no disco local do servidor.
  3. **Cookies do Navegador (`nih_email` e `nih_prefs`)**: Conveniência para login automático e backup offline no mesmo navegador.
- **Configuração do Google Sheets**:
  Para ativar a sincronização na nuvem em produção, adicione a conta de serviço no `.streamlit/secrets.toml` (ou nas configurações de Secrets do Streamlit Cloud):
  ```toml
  [gcp_service_account]
  type = "service_account"
  project_id = "seu-projeto"
  private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
  client_email = "seu-service-account@projeto.iam.gserviceaccount.com"
  # ... demais campos da conta de serviço Google Cloud
  ```

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
