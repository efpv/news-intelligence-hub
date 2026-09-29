"""Resumo executivo — interface pronta para provedores de IA (V2)."""
from typing import Protocol

import pandas as pd


class Summarizer(Protocol):
    def summarize(self, df: pd.DataFrame) -> str: ...


class LocalSummarizer:
    """Baseline sem LLM: contagem por categoria e últimas manchetes."""

    def summarize(self, df: pd.DataFrame) -> str:
        if df.empty:
            return "Sem notícias no período selecionado."
        cats = ", ".join(f"{k} ({v})" for k, v in df["categoria"].value_counts().head(4).items())
        neg = (df["sentimento"] == "Negativo").mean() * 100
        heads = "\n".join(f"- {t}" for t in df.head(5)["titulo"])
        return (f"**Principais eventos do período** — {len(df)} notícias, com destaque para {cats}. "
                f"Tom negativo em {neg:.0f}% das matérias.\n\n**Últimas manchetes:**\n{heads}")


class LLMSummarizer:
    """TODO V2: OpenAI / Azure OpenAI / Gemini com chaves em st.secrets."""

    def summarize(self, df: pd.DataFrame) -> str:
        raise NotImplementedError("Implemente a chamada ao provedor de LLM.")


def get_summarizer(provider: str = "local") -> Summarizer:
    """Factory de provedores."""
    return {"local": LocalSummarizer}.get(provider, LocalSummarizer)()
