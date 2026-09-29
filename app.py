"""News Intelligence Hub — Radar Político, Financeiro & Tecnologia."""
import time
from datetime import date, timedelta
from html import escape
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src import analytics, config, export, portfolio, preferences, rss_reader, summarizer, trends

st.set_page_config(page_title="News Intelligence Hub", page_icon="📡", layout="wide")
st.markdown(f"<style>{(Path(__file__).parent / 'assets/styles.css').read_text()}</style>", unsafe_allow_html=True)

# Inicializa preferências do usuário
preferences.init_session_state()

# Inicializa controle de atualização automática
if "_last_refresh_time" not in st.session_state:
    st.session_state["_last_refresh_time"] = time.time()
if "refresh_interval" not in st.session_state:
    st.session_state["refresh_interval"] = 3600  # 1 hora por padrão


@st.cache_data(ttl=config.CACHE_TTL, show_spinner=False)
def load_news() -> tuple[pd.DataFrame, list[str], pd.Timestamp]:
    df, errors = rss_reader.fetch_all()
    return df, errors, pd.Timestamp.now(tz=config.TIMEZONE)


def check_refresh() -> None:
    """Verifica se deve limpar cache e recarregar baseado no intervalo configurado."""
    if st.session_state.refresh_interval is None:
        return  # Atualização desativada
    
    current_time = time.time()
    time_elapsed = current_time - st.session_state.get("_last_refresh_time", current_time)
    
    if time_elapsed >= st.session_state.refresh_interval - 5:
        st.session_state["_last_refresh_time"] = current_time
        st.cache_data.clear()
        st.rerun()


def kpi(col, label: str, value) -> None:
    col.markdown(f'<div class="kpi"><div class="l">{label}</div><div class="v">{value}</div></div>', unsafe_allow_html=True)


def card(r: pd.Series) -> str:
    tags = "".join(f'<span class="tag">#{escape(t)}</span>' for t in r["tags"])
    portfolio_badge = ""
    if "portfolio_badge" in r and pd.notna(r.get("portfolio_badge")):
        portfolio_badge = f'<span class="badge b-portfolio">{r["portfolio_badge"]} {r.get("portfolio_relevance", "")}</span>'
    return (f'<div class="card"><h4>{escape(r["titulo"])}</h4>'
            f'<div class="meta"><span class="badge b-cat">{escape(r["categoria"])}</span>'
            f'<span class="badge b-{r["sentimento"]}">{ {"Positivo":"🟢","Neutro":"🟡","Negativo":"🔴"}[r["sentimento"]] } {r["sentimento"]}</span>'
            f'{portfolio_badge}'
            f'{escape(r["fonte"])} · {r["data"]:%d/%m/%Y %H:%M}</div>'
            f'<p>{escape(r["resumo"])}</p><div>{tags}</div>'
            f'<a href="{escape(r["link"])}" target="_blank" rel="noopener">🔗 Ler notícia completa</a></div>')


@st.fragment(run_every=5)
def auto_refresh_checker() -> None:
    """Verifica a cada 5 segundos se deve fazer atualização automática."""
    check_refresh()


# ---------- Header + carga ----------
st.markdown('<div class="hero"><h1>📡 News Intelligence Hub</h1>'
            '<p>Radar Político, Financeiro & Tecnologia — monitoramento em tempo real via RSS</p></div>', unsafe_allow_html=True)
slot = st.empty()
slot.markdown('<div class="skel"></div>' * 3, unsafe_allow_html=True)
with st.spinner("Coletando notícias…"):
    df, errors, fetched_at = load_news()
slot.empty()
check_refresh()
auto_refresh_checker()

if errors:
    with st.expander(f"⚠️ {len(errors)} fonte(s) com problema"):
        st.write("\n".join(f"- {e}" for e in errors))
if df.empty:
    st.error("Não foi possível carregar nenhuma notícia. Verifique sua conexão e tente atualizar.")
    st.stop()

# ---------- Sidebar ----------
sb = st.sidebar
sb.header("🎛 Filtros")

# ===== BOTÃO DE ATUALIZAÇÃO MANUAL =====
if sb.button("🔄 Atualizar Notícias Agora", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

sb.divider()

# ---------- Seção de Carteira ----------
sb.divider()
sb.subheader("💼 Minha Carteira")

portfolio_list = st.session_state.preferences.get("portfolio", [])

search_query = sb.text_input(
    "Buscar ativo",
    placeholder="Digite o nome da empresa ou ticker...",
    key="asset_search",
    label_visibility="collapsed"
)

if search_query:
    matches = portfolio.search_assets(search_query)
    if matches:
        for m in matches:
            already_added = m["ticker"] in portfolio_list
            mcol1, mcol2 = sb.columns([4, 1])
            mcol1.caption(f"{m['ticker']} - {m['company']}")
            if already_added:
                mcol2.caption("✅")
            elif mcol2.button("➕", key=f"add_{m['ticker']}"):
                portfolio_list = portfolio.add_to_portfolio(portfolio_list, m["ticker"])
                preferences.update_preference("portfolio", portfolio_list)
                st.rerun()
    else:
        sb.caption("Nenhum ativo encontrado.")

sb.write("")
if portfolio_list:
    sb.caption(f"📊 {len(portfolio_list)} ativo(s) monitorado(s)")
    for ticker in portfolio_list:
        company_name = portfolio.B3_COMPANIES.get(ticker, {}).get("name", "Desconhecido")
        pcol1, pcol2 = sb.columns([4, 1])
        pcol1.caption(f"✅ **{ticker}** - {company_name}")
        if pcol2.button("❌", key=f"rm_{ticker}"):
            portfolio_list = portfolio.remove_from_portfolio(portfolio_list, ticker)
            preferences.update_preference("portfolio", portfolio_list)
            st.rerun()
else:
    sb.caption("Nenhum ativo monitorado ainda. Busque acima para adicionar.")

col1, col2, col3 = sb.columns(3)
if col1.button("💾 Salvar", use_container_width=True):
    preferences.save_preferences(st.session_state.preferences)
    st.toast("✅ Carteira salva!", icon="✅")

if col2.button("♻ Restaurar", use_container_width=True):
    prefs = preferences.load_preferences()
    st.session_state.preferences = prefs
    st.rerun()

if col3.button("🗑", use_container_width=True):
    st.session_state.preferences["portfolio"] = []
    preferences.save_preferences(st.session_state.preferences)
    st.rerun()

portfolio_list = st.session_state.preferences.get("portfolio", [])

# ---------- Backup da Carteira (CSV) ----------
if portfolio_list:
    sb.download_button(
        "⬇ Exportar Carteira (CSV)",
        portfolio.export_portfolio_csv(portfolio_list),
        "minha_carteira.csv", "text/csv", use_container_width=True
    )

csv_upload = sb.file_uploader("⬆ Importar Carteira (CSV)", type="csv", key="portfolio_csv_uploader")
if csv_upload is not None:
    try:
        imported = portfolio.import_portfolio_csv(csv_upload)
        merged = portfolio_list[:]
        for t in imported:
            merged = portfolio.add_to_portfolio(merged, t)
        if merged != portfolio_list:
            preferences.update_preference("portfolio", merged)
            st.toast(f"✅ {len(imported)} ativo(s) importado(s)!", icon="✅")
            st.rerun()
    except (ValueError, KeyError) as e:
        sb.warning(f"⚠️ CSV inválido: {e}")

# ---------- Filtros de Notícias ----------
sb.divider()
sb.subheader("🔎 Filtros de Notícias")
sb.caption("Customize como deseja ver as notícias")

prefs = st.session_state.preferences
cat_options = ["Todas"] + config.CATEGORIES
cat_default = prefs.get("selected_category", "Todas")
cat = sb.selectbox("📂 Categoria", cat_options,
                    index=cat_options.index(cat_default) if cat_default in cat_options else 0)

# ===== CONTROLES DE TEMPO (lado a lado) =====
periodo_options = ["Última hora", "Últimas 24h", "Últimos 7 dias", "Últimos 30 dias", "Personalizado"]
periodo_default = prefs.get("period", "Últimos 7 dias")
col1, col2 = sb.columns(2)
with col1:
    periodo = st.radio("📅 Período", periodo_options,
                        index=periodo_options.index(periodo_default) if periodo_default in periodo_options else 2,
                        key="periodo_radio")

with col2:
    refresh_option = st.radio(
        "⏱ Atualizar",
        options=list(config.REFRESH_INTERVALS.keys()),
        index=4,
        key="refresh_radio",
        help="Frequência de atualização automática"
    )
    st.session_state.refresh_interval = config.REFRESH_INTERVALS[refresh_option]

sb.divider()

fonte_options = sorted(df["fonte"].unique())
fontes_default = [s for s in prefs.get("selected_sources", []) if s in fonte_options]
fontes = sb.multiselect("📰 Fonte", fonte_options, default=fontes_default)

sent_options = ["Positivo", "Neutro", "Negativo"]
sent_default = [s for s in prefs.get("sentiment_filter", []) if s in sent_options]
sent = sb.multiselect("😊 Sentimento", sent_options, default=sent_default)

busca = sb.text_input("🔍 Busca (título/resumo)", value=prefs.get("search_term", ""))
st.session_state.setdefault("show_portfolio_only", False)
if st.session_state.pop("_apply_portfolio_filter", False):
    st.session_state["show_portfolio_only"] = True
show_portfolio_only = sb.checkbox("💼 Apenas minha carteira", key="show_portfolio_only") if portfolio_list else False

# Persiste filtros quando alterados
current_filters = {
    "selected_category": cat, "selected_sources": fontes,
    "sentiment_filter": sent, "search_term": busca, "period": periodo
}
if any(prefs.get(k) != v for k, v in current_filters.items()):
    prefs.update(current_filters)
    preferences.save_preferences(prefs)

now = pd.Timestamp.now(tz=config.TIMEZONE)
if periodo == "Personalizado":
    rng = sb.date_input("Intervalo", (date.today() - timedelta(days=7), date.today()))
    if len(rng) == 2:
        start = pd.Timestamp(rng[0], tz=config.TIMEZONE)
        end = pd.Timestamp(rng[1], tz=config.TIMEZONE) + pd.Timedelta(days=1)
    else:
        start, end = now - pd.Timedelta(days=7), now
else:
    start = now - pd.Timedelta(days={"Última hora": 1 / 24, "Últimas 24h": 1, "Últimos 7 dias": 7, "Últimos 30 dias": 30}[periodo])
    end = now + pd.Timedelta(minutes=1)

f = df[(df["data"] >= start) & (df["data"] <= end)]
if cat != "Todas":
    f = f[f["categoria"] == cat]
if fontes:
    f = f[f["fonte"].isin(fontes)]
if sent:
    f = f[f["sentimento"].isin(sent)]
if busca:
    f = f[(f["titulo"] + " " + f["resumo"]).str.contains(busca, case=False, regex=False)]
if show_portfolio_only and portfolio_list:
    f = portfolio.filter_by_portfolio(f, portfolio_list)

sb.caption(f"✅ {len(f)} de {len(df)} notícias após filtros")

# Calcula tempo até próxima atualização
if st.session_state.refresh_interval is not None:
    next_refresh = st.session_state["_last_refresh_time"] + st.session_state.refresh_interval
    time_until_refresh = max(0, int(next_refresh - time.time()))
    sb.caption(f"🕒 Última coleta: {fetched_at:%d/%m %H:%M} · próxima em {time_until_refresh}s")
else:
    sb.caption(f"🕒 Última coleta: {fetched_at:%d/%m %H:%M} · atualização desativada")

# ---------- KPIs ----------
cnt = f["categoria"].value_counts()
cols = st.columns(7)
kpi(cols[0], "📰 Total de Notícias", len(f))
kpi(cols[1], "🏛 Política", int(cnt.get("Política", 0)))
kpi(cols[2], "📈 Mercado Financeiro", int(cnt.get("Mercado Financeiro", 0)))
kpi(cols[3], "💻 Tecnologia", int(cnt.get("Tecnologia", 0)))
kpi(cols[4], "🤖 Inteligência Artificial", int(cnt.get("Inteligência Artificial", 0)))
kpi(cols[5], "😊 Sentimento Positivo", int((f["sentimento"] == "Positivo").sum()))
kpi(cols[6], "⚠ Notícias Relevantes", int((f["tags"].map(len) >= 2).sum()))
st.write("")

# ---------- Portfolio KPIs (se carteira configurada) ----------
if portfolio_list:
    st.divider()
    st.subheader("💼 Radar da Carteira")
    portfolio_news = portfolio.get_portfolio_news(f, portfolio_list)
    stats = portfolio.get_portfolio_stats(f, portfolio_list)
    
    pcols = st.columns(5)
    kpi(pcols[0], "💼 Notícias da Carteira", stats["total_relevant"])
    if pcols[0].button("🔍 Ver só essas", key="filter_portfolio_kpi", use_container_width=True):
        st.session_state["_apply_portfolio_filter"] = True
        st.rerun()
    most_cited = stats["most_cited"] if stats["most_cited"] else "—"
    kpi(pcols[1], "📊 Ativo Mais Citado", most_cited)
    kpi(pcols[2], "🟢 Positivas", stats["sentiment_counts"]["Positivo"])
    kpi(pcols[3], "🟡 Neutras", stats["sentiment_counts"]["Neutro"])
    kpi(pcols[4], "🔴 Negativas", stats["sentiment_counts"]["Negativo"])
    
    if stats["ticker_rankings"]:
        st.write("")
        st.caption("📈 Ranking de Ativos Mais Citados")
        ranking_df = pd.DataFrame(
            [(f"#{i+1}. {ticker}", mentions) for i, (ticker, mentions) in enumerate(stats["ticker_rankings"][:5])],
            columns=["Posição", "Menções"]
        )
        st.dataframe(ranking_df, hide_index=True, use_container_width=False)

if f.empty:
    st.info("Nenhuma notícia encontrada com os filtros atuais.")
    st.stop()

if portfolio_list:
    tab_news, tab_portfolio, tab_trend, tab_an, tab_ai = st.tabs(["📰 Notícias", "💼 Radar da Carteira", "🔥 Trending Topics", "📊 Painel Analítico", "🧠 Resumo Executivo"])
else:
    tab_news, tab_trend, tab_an, tab_ai = st.tabs(["📰 Notícias", "🔥 Trending Topics", "📊 Painel Analítico", "🧠 Resumo Executivo"])

with tab_news:
    c1, c2, c3 = st.columns([2, 1, 1])
    n = c1.slider("Quantidade exibida", 10, 100, 30, 10)
    c2.download_button("⬇ CSV", export.to_csv(f), "noticias.csv", "text/csv", use_container_width=True)
    c3.download_button("⬇ Excel", export.to_excel(f), "noticias.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    for _, row in f.head(n).iterrows():
        st.markdown(card(row), unsafe_allow_html=True)

if portfolio_list:
    with tab_portfolio:
        portfolio_news = portfolio.get_portfolio_news(f, portfolio_list)
        
        if portfolio_news.empty:
            st.info("Nenhuma notícia encontrada relacionada aos ativos da sua carteira.")
        else:
            c1, c2, c3 = st.columns([2, 1, 1])
            n_port = c1.slider("Quantidade exibida", 10, 100, 20, 10, key="portfolio_slider")
            c2.download_button("⬇ CSV", export.to_csv(portfolio_news), "carteira_noticias.csv", "text/csv", use_container_width=True)
            c3.download_button("⬇ Excel", export.to_excel(portfolio_news), "carteira_noticias.xlsx",
                               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
            
            for _, row in portfolio_news.head(n_port).iterrows():
                st.markdown(card(row), unsafe_allow_html=True)
        
        # Gráfico de notícias por ativo
        st.divider()
        st.subheader("📊 Notícias por Ativo")
        
        if not portfolio_news.empty:
            ticker_counts = {}
            for _, row in portfolio_news.iterrows():
                if "matched_tickers" in row and pd.notna(row["matched_tickers"]):
                    tickers = str(row["matched_tickers"]).split(", ")
                    for ticker in tickers:
                        ticker = ticker.strip()
                        if ticker:
                            ticker_counts[ticker] = ticker_counts.get(ticker, 0) + 1
            
            if ticker_counts:
                ticker_df = pd.DataFrame(
                    list(ticker_counts.items()),
                    columns=["Ticker", "Notícias"]
                ).sort_values("Notícias", ascending=False)
                
                fig = px.bar(
                    ticker_df,
                    x="Ticker",
                    y="Notícias",
                    title="Notícias por Ativo da Carteira",
                    labels={"Notícias": "Quantidade", "Ticker": "Ativo B3"},
                    color="Notícias",
                    color_continuous_scale="Blues"
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sem dados para exibir o gráfico.")

        # Gráfico de sentimento por ativo
        st.subheader("😊 Sentimento por Ativo")
        sentiment_df = portfolio.get_sentiment_by_asset(f, portfolio_list)
        if not sentiment_df.empty:
            sentiment_melted = sentiment_df.melt(id_vars="Ticker", var_name="Sentimento", value_name="Quantidade")
            fig_sent = px.bar(
                sentiment_melted,
                x="Ticker",
                y="Quantidade",
                color="Sentimento",
                title="Sentimento das Notícias por Ativo",
                barmode="stack",
                color_discrete_map={"Positivo": "#3FB950", "Neutro": "#D29922", "Negativo": "#F85149"}
            )
            st.plotly_chart(fig_sent, use_container_width=True)
        else:
            st.info("Sem dados de sentimento para exibir.")

with tab_trend:
    a, b, c = st.columns(3)
    a.subheader("Assuntos mais citados")
    a.dataframe(trends.top_tags(f), hide_index=True, use_container_width=True)
    b.subheader("Empresas mais citadas")
    b.dataframe(trends.top_companies(f), hide_index=True, use_container_width=True)
    c.subheader("Pessoas mais citadas")
    c.dataframe(trends.top_people(f), hide_index=True, use_container_width=True)

with tab_an:
    r1a, r1b = st.columns(2)
    r1a.plotly_chart(analytics.by_category(f), use_container_width=True)
    r1b.plotly_chart(analytics.sentiment_donut(f), use_container_width=True)
    st.plotly_chart(analytics.by_source(f), use_container_width=True)
    freq = st.radio("Granularidade", ["Dia", "Hora"], horizontal=True)
    st.plotly_chart(analytics.timeline(f, "D" if freq == "Dia" else "h"), use_container_width=True)
    r3a, r3b = st.columns(2)
    themes = trends.top_tags(f, 12)
    if not themes.empty:
        r3a.plotly_chart(analytics.top_themes(themes), use_container_width=True)
    r3b.plotly_chart(analytics.heatmap(f), use_container_width=True)

with tab_ai:
    st.caption("Baseline local. Preparado para OpenAI, Azure OpenAI e Gemini (ver src/summarizer.py).")
    st.markdown(summarizer.get_summarizer("local").summarize(f))
