"""Gráficos Plotly no tema escuro."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from .config import COLORS

SENT_COLORS = {"Positivo": COLORS["pos"], "Neutro": COLORS["neu"], "Negativo": COLORS["neg"]}


def _style(fig: go.Figure, title: str) -> go.Figure:
    fig.update_layout(title=title, template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=10, r=10, t=50, b=10), font_color="#F0F6FC")
    return fig


def by_category(df: pd.DataFrame) -> go.Figure:
    d = df["categoria"].value_counts().rename_axis("categoria").reset_index(name="n")
    return _style(px.bar(d, x="categoria", y="n", color_discrete_sequence=[COLORS["primary"]]), "Notícias por Categoria")


def by_source(df: pd.DataFrame) -> go.Figure:
    d = df["fonte"].value_counts().sort_values().rename_axis("fonte").reset_index(name="n")
    return _style(px.bar(d, x="n", y="fonte", orientation="h", color_discrete_sequence=[COLORS["primary"]]),
                  "Notícias por Fonte")


def sentiment_donut(df: pd.DataFrame) -> go.Figure:
    d = df["sentimento"].value_counts().rename_axis("sentimento").reset_index(name="n")
    fig = px.pie(d, names="sentimento", values="n", hole=0.55, color="sentimento", color_discrete_map=SENT_COLORS)
    return _style(fig, "Sentimento Geral")


def timeline(df: pd.DataFrame, freq: str = "D") -> go.Figure:
    d = df.set_index("data").resample(freq).size().reset_index(name="n")
    fig = px.line(d, x="data", y="n", markers=True, color_discrete_sequence=[COLORS["primary"]])
    return _style(fig, "Evolução Temporal (" + ("por dia" if freq == "D" else "por hora") + ")")


def top_themes(themes: pd.DataFrame) -> go.Figure:
    return _style(px.bar(themes, x="Tema", y="Menções", color_discrete_sequence=[COLORS["ai"]]), "Temas Mais Citados")


def heatmap(df: pd.DataFrame) -> go.Figure:
    days = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
    d = pd.crosstab(df["data"].dt.dayofweek, df["data"].dt.hour).reindex(index=range(7), columns=range(24), fill_value=0)
    fig = px.imshow(d.values, x=list(range(24)), y=days, aspect="auto",
                    color_continuous_scale=["#161B22", "#58A6FF"], labels=dict(x="Hora", y="Dia", color="Notícias"))
    return _style(fig, "Mapa de Calor — Atividade por Horário")
