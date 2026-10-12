"""Utilitários: logging e limpeza de texto."""
import logging
import re
import unicodedata

from bs4 import BeautifulSoup


def get_logger(name: str) -> logging.Logger:
    """Retorna logger com formato estruturado."""
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    return logging.getLogger(name)


def clean_html(raw: str, limit: int = 400) -> str:
    """Remove HTML e trunca o texto."""
    text = BeautifulSoup(raw or "", "html.parser").get_text(" ")
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= limit else text[:limit].rsplit(" ", 1)[0] + "…"


def slugify(text: str) -> str:
    """Converte texto para slug ASCII seguro para chaves e identificadores."""
    nfkd = unicodedata.normalize("NFKD", text)
    ascii_text = nfkd.encode("ASCII", "ignore").decode("utf-8")
    return re.sub(r"[^a-zA-Z0-9_]", "_", ascii_text.lower()).strip("_")

