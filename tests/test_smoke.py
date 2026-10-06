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


def test_portfolio_has_default_tickers():
    for t in preferences.get_default_preferences()["portfolio"]:
        assert t in portfolio.B3_COMPANIES, t


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
