"""Análise de sentimento: léxico PT-BR + TextBlob para inglês."""
import re

from textblob import TextBlob

POS = {"alta", "sobe", "avanço", "cresce", "crescimento", "lucro", "recorde", "aprova", "acordo", "melhora",
       "ganho", "valoriza", "otimismo", "positivo", "supera", "investimento", "lança"}
NEG = {"queda", "cai", "crise", "prejuízo", "perda", "rombo", "investigação", "preso", "denúncia", "escândalo",
       "inflação", "desaceleração", "recessão", "risco", "ataque", "vazamento", "demissões", "negativo", "multa"}


def score(text: str, lang: str = "pt") -> float:
    """Polaridade aproximada em [-1, 1]."""
    if lang == "en":
        return float(TextBlob(text).sentiment.polarity)
    low = text.lower()
    p = sum(len(re.findall(rf"\b{re.escape(w)}", low)) for w in POS)
    n = sum(len(re.findall(rf"\b{re.escape(w)}", low)) for w in NEG)
    return 0.0 if p + n == 0 else (p - n) / (p + n)


def label(value: float, threshold: float = 0.1) -> str:
    """Converte polaridade em rótulo."""
    return "Positivo" if value > threshold else "Negativo" if value < -threshold else "Neutro"
