"""News Intelligence Hub — Radar Político, Financeiro & Tecnologia."""
import json
import time
from datetime import date, timedelta
from html import escape
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components

from src import analytics, config, export, portfolio, preferences, rss_reader, summarizer, trends

st.set_page_config(page_title="News Intelligence Hub", page_icon="📡", layout="wide")
st.markdown(f"<style>{(Path(__file__).parent / 'assets/styles.css').read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def inject_pwa() -> None:
    """Registra manifest, ícones e service worker no documento pai (a página real, não o iframe do componente)."""
    components.html(
        """
        <script>
        (function() {
            const doc = window.parent.document;
            if (doc.getElementById('nih-pwa-manifest')) return;

            const manifest = doc.createElement('link');
            manifest.id = 'nih-pwa-manifest';
            manifest.rel = 'manifest';
            manifest.href = '/app/static/manifest.json';
            doc.head.appendChild(manifest);

            const theme = doc.createElement('meta');
            theme.name = 'theme-color';
            theme.content = '#0D1117';
            doc.head.appendChild(theme);

            const appleIcon = doc.createElement('link');
            appleIcon.rel = 'apple-touch-icon';
            appleIcon.href = '/app/static/icons/icon-192.png';
            doc.head.appendChild(appleIcon);

            const appleCapable = doc.createElement('meta');
            appleCapable.name = 'apple-mobile-web-app-capable';
            appleCapable.content = 'yes';
            doc.head.appendChild(appleCapable);

            const appleTitle = doc.createElement('meta');
            appleTitle.name = 'apple-mobile-web-app-title';
            appleTitle.content = 'NIH';
            doc.head.appendChild(appleTitle);

            if ('serviceWorker' in navigator) {
                navigator.serviceWorker.register('/app/static/service-worker.js').catch(console.warn);
            }
        })();
        </script>
        """,
        height=0,
    )


inject_pwa()

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


def kpi_row(items: list[tuple[str, object]]) -> None:
    """Renderiza KPIs em uma faixa flex (rolagem horizontal em telas pequenas)."""
    cards = "".join(f'<div class="kpi"><div class="l">{label}</div><div class="v">{value}</div></div>'
                     for label, value in items)
    st.markdown(f'<div class="kpi-row">{cards}</div>', unsafe_allow_html=True)


def card_html(r: pd.Series) -> str:
    """Card de notícia (sempre visível, sem acordeão)."""
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


def render_news_list(df_slice: pd.DataFrame) -> None:
    """Renderiza a lista de cards de notícia."""
    for _, row in df_slice.iterrows():
        st.markdown(card_html(row), unsafe_allow_html=True)


@st.fragment(run_every=5)
def auto_refresh_checker() -> None:
    """Verifica a cada 5 segundos se deve fazer atualização automática."""
    check_refresh()


# ---------- Header + carga ----------
hcol1, hcol2 = st.columns([1.6, 1])
with hcol1:
    st.markdown('<div class="hero"><h1>📡 News Intelligence Hub</h1>'
                '<p>Radar Político, Financeiro & Tecnologia — monitoramento em tempo real via RSS</p></div>', unsafe_allow_html=True)
with hcol2:
    with st.container(key="update_info_card"):
        info_col, btn_col = st.columns([6, 1], vertical_alignment="center")
        with info_col:
            update_slot = st.empty()
        with btn_col:
            reload_clicked = st.button("🔄", key="reload_page_btn")
    if reload_clicked:
        st.cache_data.clear()
        st.rerun()
slot = st.empty()
slot.markdown('<div class="skel"></div>' * 3, unsafe_allow_html=True)
with st.spinner("Coletando notícias…"):
    df, errors, fetched_at = load_news()
slot.empty()
check_refresh()
auto_refresh_checker()
update_slot.markdown(f'<span class="update-info-line">🕒 Última atualização • <strong>{fetched_at:%d/%m %H:%M}</strong></span>', unsafe_allow_html=True)

# ---------- Persistência de preferências por e-mail ----------
if st.session_state.get("email"):
    lcol1, lcol2 = st.columns([5, 1])
    lcol1.caption(f"💾 Preferências salvas para **{st.session_state['email']}**")
    if lcol2.button("Sair", key="email_logout_btn", width="content"):
        preferences.logout()
        st.rerun()
else:
    with st.expander("💾 Salvar minhas preferências por e-mail", expanded=False):
        st.caption("Informe seu e-mail para salvar sua carteira e filtros. Ao voltar, digite o mesmo "
                   "e-mail para recuperá-los automaticamente — não é necessário criar senha.")
        st.caption("⚠️ Não é um login seguro: quem souber o e-mail pode carregar as mesmas preferências.")
        ecol1, ecol2 = st.columns([3, 1])
        email_input = ecol1.text_input("E-mail", key="email_login_input",
                                        placeholder="voce@exemplo.com", label_visibility="collapsed")
        if ecol2.button("💾 Salvar/Carregar", key="email_login_btn", width="stretch"):
            if preferences.login_with_email(email_input):
                st.toast("✅ Preferências vinculadas ao seu e-mail!", icon="✅")
                st.rerun()
            else:
                st.warning("⚠️ Informe um e-mail válido.")

if errors:
    with st.expander(f"⚠️ {len(errors)} fonte(s) com problema"):
        st.write("\n".join(f"- {e}" for e in errors))
if df.empty:
    st.error("Não foi possível carregar nenhuma notícia. Verifique sua conexão e tente atualizar.")
    st.stop()

# ---------- Sidebar ----------
sb = st.sidebar
sb.header("🎛 Filtros")
prefs = st.session_state.preferences
busca = sb.text_input("🔍 Busca (título/resumo)", value=prefs.get("search_term", ""))
# ===== BOTÃO DE ATUALIZAÇÃO MANUAL =====
if sb.button("🔄 Atualizar Notícias Agora", width="stretch"):
    st.cache_data.clear()
    st.rerun()

# ---------- Seção de Carteira ----------
with sb.expander("💼 Minha Carteira", expanded=False):
    portfolio_list = st.session_state.preferences.get("portfolio", [])

    asset_catalog = portfolio.get_asset_catalog()
    asset_options = {portfolio.asset_label(a): a["ticker"] for a in asset_catalog}

    def _add_selected_asset() -> None:
        label = st.session_state.get("asset_picker")
        if label:
            current = st.session_state.preferences.get("portfolio", [])
            preferences.update_preference("portfolio", portfolio.add_to_portfolio(current, asset_options[label]))
        st.session_state["asset_picker"] = None

    st.selectbox(
        "Buscar ativo",
        list(asset_options),
        index=None,
        placeholder="Digite o ticker ou o nome da empresa...",
        key="asset_picker",
        on_change=_add_selected_asset,
        label_visibility="collapsed",
    )

    st.write("")
    if portfolio_list:
        st.caption(f"📊 {len(portfolio_list)} ativo(s) monitorado(s)")
        with st.container(key="portfolio_ticker_list"):
            for ticker in portfolio_list:
                company_name = portfolio.get_company_name(ticker)
                pcol1, pcol2 = st.columns([4, 1], gap="small")
                pcol1.caption(f"✅ **{ticker}** - {company_name}")
                if pcol2.button("🗑", key=f"rm_{ticker}", width="content"):
                    portfolio_list = portfolio.remove_from_portfolio(portfolio_list, ticker)
                    preferences.update_preference("portfolio", portfolio_list)
                    st.rerun()
    else:
        st.caption("Nenhum ativo monitorado ainda. Busque acima para adicionar.")

    col1, col2, col3 = st.columns(3)
    if col1.button("💾 Salvar", width="stretch"):
        preferences.save_preferences(st.session_state.preferences)
        st.toast("✅ Carteira salva!", icon="✅")

    if col2.button("♻ Restaurar", width="stretch"):
        user_id = st.session_state.get("_user_id")
        if user_id:
            st.session_state.preferences = preferences.load_preferences(user_id)
            st.rerun()
        else:
            st.warning("⚠️ Salve suas preferências com um e-mail (no topo da página) antes de restaurar.")

    if col3.button("🗑", width="stretch"):
        st.session_state.preferences["portfolio"] = []
        preferences.save_preferences(st.session_state.preferences)
        st.rerun()

    portfolio_list = st.session_state.preferences.get("portfolio", [])

    if not st.session_state.get("_user_id"):
        st.caption("💡 Salve suas preferências com um e-mail (no topo da página) para não perdê-las ao fechar o navegador.")

    # ---------- Backup da Carteira e Filtros (JSON) ----------
    if portfolio_list:
        st.download_button(
            "⬇ Exportar Carteira e Filtros",
            portfolio.export_backup(portfolio_list, st.session_state.preferences),
            "minha_carteira.json", "application/json", width="stretch"
        )

    backup_upload = st.file_uploader("⬆ Importar Carteira e Filtros", type="json", key="portfolio_backup_uploader")
    if backup_upload is not None:
        try:
            imported_tickers, imported_filters = portfolio.import_backup(backup_upload)
            merged = portfolio_list[:]
            for t in imported_tickers:
                merged = portfolio.add_to_portfolio(merged, t)
            st.session_state.preferences["portfolio"] = merged
            st.session_state.preferences.update(imported_filters)
            preferences.save_preferences(st.session_state.preferences)
            st.toast(f"✅ {len(imported_tickers)} ativo(s) e filtros importados!", icon="✅")
            st.rerun()
        except (ValueError, KeyError, json.JSONDecodeError) as e:
            st.warning(f"⚠️ CSV inválido: {e}")

# ---------- Filtros de Notícias ----------
sb.subheader("🔎 Filtros de Notícias")
sb.caption("Customize como deseja ver as notícias")

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
    refresh_options = list(config.REFRESH_INTERVALS.keys())
    refresh_default = prefs.get("refresh_option", "1 hora")
    refresh_option = st.radio(
        "⏱ Atualizar",
        options=refresh_options,
        index=refresh_options.index(refresh_default) if refresh_default in refresh_options else 4,
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

st.session_state.setdefault("show_portfolio_only", False)
if st.session_state.pop("_apply_portfolio_filter", False):
    st.session_state["show_portfolio_only"] = True
show_portfolio_only = sb.checkbox("💼 Apenas minha carteira", key="show_portfolio_only") if portfolio_list else False

# Persiste filtros quando alterados
current_filters = {
    "selected_category": cat, "selected_sources": fontes,
    "sentiment_filter": sent, "search_term": busca, "period": periodo, "refresh_option": refresh_option
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
with st.expander("📊 Visão Geral", expanded=False):
    kpi_row([
        ("📰 Total de Notícias", len(f)),
        ("🏛 Política", int(cnt.get("Política", 0))),
        ("📈 Mercado Financeiro", int(cnt.get("Mercado Financeiro", 0))),
        ("💻 Tecnologia", int(cnt.get("Tecnologia", 0))),
        ("🤖 Inteligência Artificial", int(cnt.get("Inteligência Artificial", 0))),
        ("😊 Sentimento Positivo", int((f["sentimento"] == "Positivo").sum())),
        ("⚠ Notícias Relevantes", int((f["tags"].map(len) >= 2).sum())),
    ])

# ---------- Portfolio KPIs (se carteira configurada) ----------
if portfolio_list:
    portfolio_news = portfolio.get_portfolio_news(f, portfolio_list)
    stats = portfolio.get_portfolio_stats(f, portfolio_list)

    with st.expander("💼 Radar da Carteira", expanded=True):
        most_cited = stats["most_cited"] if stats["most_cited"] else "—"
        kpi_row([
            ("💼 Notícias da Carteira", stats["total_relevant"]),
            ("📊 Ativo Mais Citado", most_cited),
            ("🟢 Positivas", stats["sentiment_counts"]["Positivo"]),
            ("🟡 Neutras", stats["sentiment_counts"]["Neutro"]),
            ("🔴 Negativas", stats["sentiment_counts"]["Negativo"]),
        ])
        if st.button("🔍 Ver apenas notícias da carteira", key="filter_portfolio_kpi", width="stretch"):
            st.session_state["_apply_portfolio_filter"] = True
            st.rerun()

        if stats["ticker_rankings"]:
            st.write("")
            st.caption("📈 Ranking de Ativos Mais Citados")
            ranking_df = pd.DataFrame(
                [(f"#{i+1}. {ticker}", mentions) for i, (ticker, mentions) in enumerate(stats["ticker_rankings"][:5])],
                columns=["Posição", "Menções"]
            )
            st.dataframe(ranking_df, hide_index=True, width="content")

if f.empty:
    st.info("Nenhuma notícia encontrada com os filtros atuais.")
    st.stop()

if portfolio_list:
    tab_news, tab_portfolio, tab_trend, tab_an, tab_ai = st.tabs(["📰 Notícias", "💼 Radar da Carteira", "🔥 Trending Topics", "📊 Painel Analítico", "🧠 Resumo Executivo"])
else:
    tab_news, tab_trend, tab_an, tab_ai = st.tabs(["📰 Notícias", "🔥 Trending Topics", "📊 Painel Analítico", "🧠 Resumo Executivo"])

with tab_news:
    n = st.slider("Quantidade exibida", 10, 100, 30, 10)
    render_news_list(f.head(n))

if portfolio_list:
    with tab_portfolio:
        portfolio_news = portfolio.get_portfolio_news(f, portfolio_list)
        
        if portfolio_news.empty:
            st.info("Nenhuma notícia encontrada relacionada aos ativos da sua carteira.")
        else:
            c1, c2, c3 = st.columns([2, 1, 1])
            n_port = c1.slider("Quantidade exibida", 10, 100, 20, 10, key="portfolio_slider")
            c2.download_button("⬇ CSV", export.to_csv(portfolio_news), "carteira_noticias.csv", "text/csv", width="stretch")
            c3.download_button("⬇ Excel", export.to_excel(portfolio_news), "carteira_noticias.xlsx",
                               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", width="stretch")
            
            render_news_list(portfolio_news.head(n_port))
        
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
                st.plotly_chart(fig, width="stretch")
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
            st.plotly_chart(fig_sent, width="stretch")
        else:
            st.info("Sem dados de sentimento para exibir.")

with tab_trend:
    a, b, c = st.columns(3)
    a.subheader("Assuntos mais citados")
    a.dataframe(trends.top_tags(f), hide_index=True, width="stretch")
    b.subheader("Empresas mais citadas")
    b.dataframe(trends.top_companies(f), hide_index=True, width="stretch")
    c.subheader("Pessoas mais citadas")
    c.dataframe(trends.top_people(f), hide_index=True, width="stretch")

with tab_an:
    r1a, r1b = st.columns(2)
    r1a.plotly_chart(analytics.by_category(f), width="stretch")
    r1b.plotly_chart(analytics.sentiment_donut(f), width="stretch")
    st.plotly_chart(analytics.by_source(f), width="stretch")
    freq = st.radio("Granularidade", ["Dia", "Hora"], horizontal=True)
    st.plotly_chart(analytics.timeline(f, "D" if freq == "Dia" else "h"), width="stretch")
    r3a, r3b = st.columns(2)
    themes = trends.top_tags(f, 12)
    if not themes.empty:
        r3a.plotly_chart(analytics.top_themes(themes), width="stretch")
    r3b.plotly_chart(analytics.heatmap(f), width="stretch")

with tab_ai:
    st.caption("Baseline local. Preparado para OpenAI, Azure OpenAI e Gemini (ver src/summarizer.py).")
    st.markdown(summarizer.get_summarizer("local").summarize(f))
