"""Coleta concorrente de RSS e enriquecimento (sentimento, tags, categoria)."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from time import mktime

import feedparser
import pandas as pd
import requests

from . import config, sentiment, tags
from .utils import clean_html, get_logger

log = get_logger(__name__)
COLS = ["titulo", "resumo", "data", "fonte", "categoria", "link", "sentimento", "score", "tags"]


def _fetch(feed: config.Feed) -> tuple[list[dict], str | None]:
    """Baixa um feed. Retorna (itens, erro amigável)."""
    try:
        r = requests.get(feed.url, timeout=config.REQUEST_TIMEOUT, headers={"User-Agent": config.USER_AGENT})
        r.raise_for_status()
    except requests.Timeout:
        return [], f"{feed.name}: tempo esgotado"
    except requests.RequestException as exc:
        log.warning("Falha em %s: %s", feed.name, exc)
        return [], f"{feed.name}: indisponível"
    parsed = feedparser.parse(r.content)
    if not parsed.entries:
        return [], f"{feed.name}: feed vazio ou inválido"
    items = []
    for e in parsed.entries[: config.MAX_ITEMS_PER_FEED]:
        title, link = e.get("title"), e.get("link")
        if not title or not link:  # dados incompletos
            continue
        ts = e.get("published_parsed") or e.get("updated_parsed")
        date = datetime.fromtimestamp(mktime(ts), tz=timezone.utc) if ts else datetime.now(timezone.utc)
        items.append({"titulo": clean_html(title, 200), "resumo": clean_html(e.get("summary", "")),
                      "data": date, "fonte": feed.name, "categoria": feed.category,
                      "link": link, "lang": feed.lang})
    return items, None


def enrich(df: pd.DataFrame) -> pd.DataFrame:
    """Adiciona sentimento, tags e reclassifica IA."""
    if df.empty:
        return pd.DataFrame(columns=COLS)
    text = df["titulo"] + ". " + df["resumo"]
    df["tags"] = text.map(tags.extract_tags)
    df["score"] = [sentiment.score(t, l) for t, l in zip(text, df["lang"])]
    df["sentimento"] = df["score"].map(sentiment.label)
    df.loc[df["tags"].map(tags.is_ai), "categoria"] = "Inteligência Artificial"
    df["data"] = pd.to_datetime(df["data"], utc=True).dt.tz_convert(config.TIMEZONE)
    return df.drop_duplicates("link").sort_values("data", ascending=False)[COLS].reset_index(drop=True)


def fetch_all() -> tuple[pd.DataFrame, list[str]]:
    """Coleta todos os feeds em paralelo."""
    with ThreadPoolExecutor(max_workers=8) as ex:
        results = list(ex.map(_fetch, config.FEEDS))
    rows = [i for items, _ in results for i in items]
    errors = [err for _, err in results if err]
    return enrich(pd.DataFrame(rows)), errors
