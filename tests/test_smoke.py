"""Testes mínimos: garantem que o app e a configuração sobem sem erros (sem rede)."""
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from src import config, portfolio, preferences, rss_reader, sentiment, tags

ROOT = Path(__file__).resolve().parent.parent


def test_feeds_are_valid():
    assert config.FEEDS
    urls = [f.url for f in config.FEEDS]
    assert len(urls) == len(set(urls)), "URLs de feed duplicadas"
    for f in config.FEEDS:
        assert f.url.startswith("http"), f.name
        assert f.category and f.name


def test_every_category_has_feeds():
    present = {f.category for f in config.FEEDS}
    for cat in config.CATEGORIES:
        if cat != "Inteligência Artificial":  # preenchida por reclassificação
            assert cat in present, f"sem feeds para {cat}"


def test_international_feeds_are_grouped_together():
    feeds = {f.name: f.category for f in config.FEEDS}
    assert feeds["BBC Brasil"] == "Internacional"
    assert feeds["Bloomberg Markets"] == "Internacional"
    assert feeds["TechCrunch"] == "Internacional"
    assert feeds["Google News - Brazil Politics"] == "Política"


def test_default_preferences():
    d = preferences.get_default_preferences()
    assert d["period"] == "Últimas 24h"
    assert d["refresh_option"] in config.REFRESH_INTERVALS
    assert isinstance(d["selected_category"], list)
    assert d["portfolio"]


def test_tags_and_sentiment():
    assert "Lula" in tags.extract_tags("Lula anuncia medida")
    assert isinstance(sentiment.score("bom resultado", "pt"), float)


def test_enrich():
    now = pd.Timestamp.now(tz="UTC")
    rows = [
        {"titulo": "Lula fala", "resumo": "", "data": now, "fonte": "x", "categoria": "Política",
         "link": "http://a", "lang": "pt"},
        {"titulo": "Dólar sobe", "resumo": "", "data": now, "fonte": "y", "categoria": "Economia",
         "link": "http://b", "lang": "pt"},
    ]
    df = rss_reader.enrich(pd.DataFrame(rows))
    assert list(df.columns) == rss_reader.COLS and len(df) == 2


def test_fetch_all_only_requested_categories():
    seen = []

    def fake(feed):
        seen.append(feed.category)
        return [], None

    with patch.object(rss_reader, "_fetch", fake):
        rss_reader.fetch_all(("Política",))
    assert seen and set(seen) == {"Política"}


def test_fetch_all_international_category():
    seen = []

    def fake(feed):
        seen.append(feed.category)
        return [], None

    with patch.object(rss_reader, "_fetch", fake):
        rss_reader.fetch_all(("Internacional",))
    assert seen and set(seen) == {"Internacional"}


def test_portfolio_has_default_tickers():
    for t in preferences.get_default_preferences()["portfolio"]:
        assert t in portfolio.B3_COMPANIES, t


def test_slugify():
    from src.utils import slugify

    assert slugify("Total de Notícias") == "total_de_noticias"
    assert slugify("Mercado Financeiro") == "mercado_financeiro"
    assert slugify("Inteligência Artificial") == "inteligencia_artificial"
    assert slugify("Política") == "politica"


def test_category_icons():
    assert "Total" in config.CATEGORY_ICONS
    for cat in config.CATEGORIES:
        assert cat in config.CATEGORY_ICONS


def test_overview_cards_click_filters_and_restores():
    import streamlit as st
    from streamlit.testing.v1 import AppTest

    st.cache_data.clear()
    now = pd.Timestamp.now(tz=config.TIMEZONE)
    sample = pd.DataFrame([
        {
            "titulo": "Notícia de Política", "resumo": "resumo pol", "fonte": "Fonte A",
            "categoria": "Política", "link": "http://a", "sentimento": "Neutro", "score": 0.0,
            "tags": ["Governo"], "data": now,
        },
        {
            "titulo": "Notícia de Economia", "resumo": "resumo eco", "fonte": "Fonte B",
            "categoria": "Economia", "link": "http://b", "sentimento": "Positivo", "score": 0.5,
            "tags": ["PIB"], "data": now,
        },
        {
            "titulo": "Notícia de Tecnologia", "resumo": "resumo tec", "fonte": "Fonte C",
            "categoria": "Tecnologia", "link": "http://c", "sentimento": "Positivo", "score": 0.5,
            "tags": ["Python"], "data": now,
        },
    ])
    with patch.object(rss_reader, "fetch_all", lambda *a, **k: (sample, [])):
        at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
        assert not at.exception

        # Sem filtro ativo: card "Total" deve ser primário (destaque visual)
        total_btn = at.button(key="kpi_cat_total")
        assert total_btn.proto.type == "primary"
        assert ":blue[" in total_btn.label
        assert "**3**" in total_btn.label
        pol_btn = at.button(key="kpi_cat_politica")
        assert pol_btn.proto.type == "secondary"
        assert ":gray[" in pol_btn.label
        assert "**1**" in pol_btn.label
        assert at.session_state["cat_filter"] == []

        # Listagem inicial deve conter todas as 3 notícias
        md_vals = [m.value for m in at.markdown]
        assert any("Notícia de Política" in m for m in md_vals)
        assert any("Notícia de Economia" in m for m in md_vals)
        assert any("Notícia de Tecnologia" in m for m in md_vals)

        # Clica no card de Política
        pol_btn.click().run()
        assert not at.exception
        assert at.session_state["cat_filter"] == ["Política"]
        assert at.button(key="kpi_cat_politica").proto.type == "primary"
        assert ":blue[" in at.button(key="kpi_cat_politica").label
        assert at.button(key="kpi_cat_total").proto.type == "secondary"
        assert ":gray[" in at.button(key="kpi_cat_total").label

        # Contadores nos cards permanecem sincronizados com o total da base
        assert "**3**" in at.button(key="kpi_cat_total").label
        assert "**1**" in at.button(key="kpi_cat_politica").label

        # Listagem exibida deve conter apenas a notícia da categoria Política
        md_vals = [m.value for m in at.markdown]
        assert any("Notícia de Política" in m for m in md_vals)
        assert not any("Notícia de Economia" in m for m in md_vals)
        assert not any("Notícia de Tecnologia" in m for m in md_vals)

        # Clica no card de Total para restaurar todos
        at.button(key="kpi_cat_total").click().run()
        assert not at.exception
        assert at.session_state["cat_filter"] == []
        assert at.button(key="kpi_cat_total").proto.type == "primary"
        assert ":blue[" in at.button(key="kpi_cat_total").label
        assert at.button(key="kpi_cat_politica").proto.type == "secondary"

        # Listagem volta a exibir todas as notícias
        md_vals = [m.value for m in at.markdown]
        assert any("Notícia de Política" in m for m in md_vals)
        assert any("Notícia de Economia" in m for m in md_vals)
        assert any("Notícia de Tecnologia" in m for m in md_vals)


def test_overview_filtering_in_memory_no_refetch():
    from unittest.mock import MagicMock
    import streamlit as st
    from streamlit.testing.v1 import AppTest

    st.cache_data.clear()
    now = pd.Timestamp.now(tz=config.TIMEZONE)
    sample = pd.DataFrame([
        {
            "titulo": "Notícia de Política", "resumo": "resumo pol", "fonte": "Fonte A",
            "categoria": "Política", "link": "http://a", "sentimento": "Neutro", "score": 0.0,
            "tags": ["Governo"], "data": now,
        },
        {
            "titulo": "Notícia de Economia", "resumo": "resumo eco", "fonte": "Fonte B",
            "categoria": "Economia", "link": "http://b", "sentimento": "Positivo", "score": 0.5,
            "tags": ["PIB"], "data": now,
        },
    ])
    mock_fetch = MagicMock(return_value=(sample, []))
    with patch.object(rss_reader, "fetch_all", mock_fetch):
        at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
        assert not at.exception
        # Chamado apenas uma vez na inicialização
        assert mock_fetch.call_count == 1
        assert "news_data" in at.session_state

        # Alternar filtros pelos cards da Visão Geral deve ser puramente em memória (sem nova busca)
        at.button(key="kpi_cat_politica").click().run()
        assert not at.exception
        assert mock_fetch.call_count == 1

        at.button(key="kpi_cat_economia").click().run()
        assert not at.exception
        assert mock_fetch.call_count == 1

        at.button(key="kpi_cat_total").click().run()
        assert not at.exception
        assert mock_fetch.call_count == 1

        # Apenas na atualização manual (botão 🔄) uma nova busca deve ocorrer
        at.button(key="reload_page_btn").click().run()
        assert not at.exception
        assert mock_fetch.call_count == 2


def test_app_runs_without_exceptions():
    from streamlit.testing.v1 import AppTest

    sample = pd.DataFrame([{
        "titulo": "Lula fala sobre economia", "resumo": "resumo", "fonte": "Teste",
        "categoria": "Política", "link": "http://a", "sentimento": "Neutro", "score": 0.0,
        "tags": ["Lula"], "data": pd.Timestamp.now(tz=config.TIMEZONE),
    }])
    with patch.object(rss_reader, "fetch_all", lambda *a, **k: (sample, [])):
        at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
    assert not at.exception, [e.value for e in at.exception]
