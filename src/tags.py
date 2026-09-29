"""Identificação automática de tags por palavras-chave."""
import re

TAG_RULES: dict[str, dict[str, str]] = {
    "Política": {"Lula": r"\blula\b", "Bolsonaro": r"\bbolsonaro\b", "STF": r"\bstf\b|supremo tribunal",
                 "Congresso": r"\bcongresso\b", "Senado": r"\bsenado\b",
                 "Câmara": r"c[âa]mara dos deputados|\bc[âa]mara\b",
                 "Eleições": r"elei[çc][õo]es|eleitoral", "TSE": r"\btse\b"},
    "Economia": {"Inflação": r"infla[çc][ãa]o|\bipca\b", "PIB": r"\bpib\b",
                 "BancoCentral": r"banco central|\bbacen\b|\bcopom\b",
                 "Selic": r"\bselic\b", "Juros": r"\bjuros\b"},
    "Mercado": {"Ibovespa": r"ibovespa|\bibov\b", "Dólar": r"\bd[óo]lar\b", "Petrobras": r"petrobras|\bpetr[34]\b",
                "Vale": r"\bvale\b|\bvale3\b", "B3": r"\bb3\b", "Dividendos": r"dividendos?|proventos"},
    "Tecnologia": {"Microsoft": r"microsoft", "Google": r"\bgoogle\b", "Amazon": r"\bamazon\b|\baws\b",
                   "Meta": r"\bmeta\b|facebook|instagram|whatsapp", "Apple": r"\bapple\b|iphone",
                   "Oracle": r"\boracle\b", "Salesforce": r"salesforce"},
    "IA": {"OpenAI": r"openai", "ChatGPT": r"chatgpt", "Copilot": r"copilot", "Gemini": r"\bgemini\b",
           "Claude": r"\bclaude\b|anthropic", "AzureAI": r"azure (ai|openai)",
           "MachineLearning": r"machine learning|aprendizado de m[áa]quina",
           "DataScience": r"data science|ci[êe]ncia de dados", "NVIDIA": r"nvidia",
           "IA": r"intelig[êe]ncia artificial|\bia\b|\bai\b|artificial intelligence"},
}
_COMPILED = {t: re.compile(p, re.I) for g in TAG_RULES.values() for t, p in g.items()}
AI_TAGS = set(TAG_RULES["IA"])
COMPANY_TAGS = set(TAG_RULES["Tecnologia"]) | {"OpenAI", "NVIDIA", "Petrobras", "Vale"}


def extract_tags(text: str) -> list[str]:
    """Retorna tags encontradas no texto."""
    return [t for t, rx in _COMPILED.items() if rx.search(text)]


def is_ai(tags: list[str]) -> bool:
    """Indica se as tags caracterizam conteúdo de IA."""
    return bool(AI_TAGS.intersection(tags))
