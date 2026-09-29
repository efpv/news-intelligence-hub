"""News Intelligence Hub — Radar Político, Financeiro & Tecnologia."""
import time
from datetime import date, timedelta
from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st

from src import analytics, config, export, rss_reader, summarizer, trends

st.set_page_config(page_title="News Intelligence Hub", page_icon="📡", layout="wide")
st.markdown(f"<style>{(Path(__file__).parent / 'assets/styles.css').read_text()}</style>", unsafe_allow_html=True)


@st.cache_data(ttl=config.CACHE_TTL, show_spinner=False)
def load_news() -> tuple[pd.DataFrame, list[str], pd.Timestamp]:
    df, errors = rss_reader.fetch_all()
    return df, errors, pd.Timestamp.now(tz=config.TIMEZONE)


@st.fragment(run_every=config.REFRESH_SECONDS)
def hourly_refresh() -> None:
    """Com a sessão aberta, limpa o cache e recarrega quando passou 1h desde a última coleta."""
    last = st.session_state.get("_last_refresh")
    if last is None:
        st.session_state["_last_refresh"] = time.time()
    elif time.time() - last >= config.REFRESH_SECONDS - 5:
        st.session_state["_last_refresh"] = time.time()
        st.cache_data.clear()
        st.rerun()


def kpi(col, label: str, value) -> None:
    col.markdown(f'<div class="kpi"><div class="l">{label}</div><div class="v">{value}</div></div>', unsafe_allow_html=True)


def card(r: pd.Series) -> str:
    tags = "".join(f'<span class="tag">#{escape(t)}</span>' for t in r["tags"])
    return (f'<div class="card"><h4>{escape(r["titulo"])}</h4>'
            f'<div class="meta"><span class="badge b-cat">{escape(r["categoria"])}</span>'
            f'<span class="badge b-{r["sentimento"]}">{ {"Positivo":"🟢","Neutro":"🟡","Negativo":"🔴"}[r["sentimento"]] } {r["sentimento"]}</span>'
            f'{escape(r["fonte"])} · {r["data"]:%d/%m/%Y %H:%M}</div>'
            f'<p>{escape(r["resumo"])}</p><div>{tags}</div>'
            f'<a href="{escape(r["link"])}" target="_blank" rel="noopener">🔗 Ler notícia completa</a></div>')


# ---------- Header + carga ----------
st.markdown('<div class="hero"><h1>📡 News Intelligence Hub</h1>'
            '<p>Radar Político, Financeiro & Tecnologia — monitoramento em tempo real via RSS</p></div>', unsafe_allow_html=True)
slot = st.empty()
slot.markdown('<div class="skel"></div>' * 3, unsafe_allow_html=True)
with st.spinner("Coletando notícias…"):
    df, errors, fetched_at = load_news()
slot.empty()
hourly_refresh()

if errors:
    with st.expander(f"⚠️ {len(errors)} fonte(s) com problema"):
        st.write("\n".join(f"- {e}" for e in errors))
if df.empty:
    st.error("Não foi possível carregar nenhuma notícia. Verifique sua conexão e tente atualizar.")
    st.stop()

# ---------- Sidebar ----------
sb = st.sidebar
sb.header("🎛 Filtros")
if sb.button("🔄 Atualizar Notícias", use_container_width=True):
    st.cache_data.clear()
    st.rerun()
cat = sb.selectbox("Categoria", ["Todas"] + config.CATEGORIES)
fontes = sb.multiselect("Fonte", sorted(df["fonte"].unique()))
periodo = sb.radio("Período", ["Última hora", "Últimas 24h", "Últimos 7 dias", "Últimos 30 dias", "Personalizado"], index=2)
sent = sb.multiselect("Sentimento", ["Positivo", "Neutro", "Negativo"])
busca = sb.text_input("🔍 Busca (título/resumo)")

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
sb.caption(f"✅ {len(f)} de {len(df)} notícias após filtros")
sb.caption(f"🕒 Última coleta: {fetched_at:%d/%m %H:%M} · próxima automática em até 1h")

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

if f.empty:
    st.info("Nenhuma notícia encontrada com os filtros atuais.")
    st.stop()

tab_news, tab_trend, tab_an, tab_ai = st.tabs(["📰 Notícias", "🔥 Trending Topics", "📊 Painel Analítico", "🧠 Resumo Executivo"])

with tab_news:
    c1, c2, c3 = st.columns([2, 1, 1])
    n = c1.slider("Quantidade exibida", 10, 100, 30, 10)
    c2.download_button("⬇ CSV", export.to_csv(f), "noticias.csv", "text/csv", use_container_width=True)
    c3.download_button("⬇ Excel", export.to_excel(f), "noticias.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    for _, row in f.head(n).iterrows():
        st.markdown(card(row), unsafe_allow_html=True)

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
