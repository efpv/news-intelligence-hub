"""Trending topics: assuntos, empresas e pessoas."""
import re
from collections import Counter

import pandas as pd

from .tags import COMPANY_TAGS

PEOPLE = {"Lula": r"\blula\b", "Bolsonaro": r"\bbolsonaro\b", "Haddad": r"\bhaddad\b", "Galípolo": r"gal[íi]polo",
          "Campos Neto": r"campos neto", "Alexandre de Moraes": r"moraes", "Hugo Motta": r"hugo motta",
          "Alcolumbre": r"alcolumbre", "Sam Altman": r"altman", "Elon Musk": r"\bmusk\b",
          "Satya Nadella": r"nadella", "Zuckerberg": r"zuckerberg", "Jensen Huang": r"jensen huang",
          "Sundar Pichai": r"pichai"}


def top_tags(df: pd.DataFrame, n: int = 10, only: set[str] | None = None) -> pd.DataFrame:
    """Contagem das tags mais frequentes."""
    c = Counter(t for ts in df["tags"] for t in ts if only is None or t in only)
    return pd.DataFrame(c.most_common(n), columns=["Tema", "Menções"])


def top_companies(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Empresas mais citadas."""
    return top_tags(df, n, COMPANY_TAGS)


def top_people(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Pessoas mais citadas (lista de nomes monitorados)."""
    text = (df["titulo"] + " " + df["resumo"]).str.lower()
    c = Counter({p: int(text.str.contains(rx, flags=re.I, regex=True).sum()) for p, rx in PEOPLE.items()})
    return pd.DataFrame([kv for kv in c.most_common(n) if kv[1]], columns=["Pessoa", "Menções"])
