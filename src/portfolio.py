"""Gerenciamento de portfólio de investimentos B3."""
import re
import unicodedata

import pandas as pd
import streamlit as st

# Tickers cuja base (sem dígitos) coincide com palavras comuns do português;
# nesses casos exige-se o ticker completo (com dígito) para evitar falsos positivos.
AMBIGUOUS_TICKER_BASES = {"VALE3", "AZUL4", "EVEN3"}

# Mapeamento de tickers B3 para nomes de empresa e palavras-chave relacionadas
# Preparado para futura substituição/enriquecimento via API (BRAPI, Status Invest, Fundamentus).
B3_COMPANIES = {
    "PETR4": {"name": "Petrobras PN", "sector": "Energia",
              "keywords": ["petrobras", "petróleo", "refino", "pré-sal"]},
    "PETR3": {"name": "Petrobras ON", "sector": "Energia",
              "keywords": ["petrobras", "petróleo", "refino", "pré-sal"]},
    "VALE3": {"name": "Vale S.A.", "sector": "Mineração",
              "keywords": ["mineração", "minério de ferro", "níquel", "cobre", "fertilizantes"]},
    "ITUB4": {"name": "Itaú Unibanco PN", "sector": "Financeiro",
              "keywords": ["itaú", "itau", "unibanco"]},
    "ITUB3": {"name": "Itaú Unibanco ON", "sector": "Financeiro",
              "keywords": ["itaú", "itau", "unibanco"]},
    "BBAS3": {"name": "Banco do Brasil ON", "sector": "Financeiro",
              "keywords": ["banco do brasil", "bndes"]},
    "BBDC4": {"name": "Bradesco PN", "sector": "Financeiro", "keywords": ["bradesco"]},
    "BBDC3": {"name": "Bradesco ON", "sector": "Financeiro", "keywords": ["bradesco"]},
    "SANB11": {"name": "Santander Brasil Unit", "sector": "Financeiro", "keywords": ["santander"]},
    "BPAC11": {"name": "BTG Pactual Unit", "sector": "Financeiro", "keywords": ["btg", "btg pactual"]},
    "WEGE3": {"name": "Weg ON", "sector": "Industrial",
              "keywords": ["weg", "motores", "equipamentos elétricos"]},
    "B3SA3": {"name": "B3 ON", "sector": "Financeiro",
              "keywords": ["b3", "bolsa", "bmfbovespa", "mercado de capitais"]},
    "TAEE11": {"name": "Taesa Unit", "sector": "Energia",
               "keywords": ["taesa", "transmissão", "energia elétrica", "linhas de transmissão"]},
    "MXRF11": {"name": "Maxi Renda FII", "sector": "Fundos Imobiliários",
               "keywords": ["maxi renda", "fundo imobiliário", "fii"]},
    "XPML11": {"name": "XP Malls FII", "sector": "Fundos Imobiliários",
               "keywords": ["xp malls", "shopping", "varejo", "fii"]},
    "HGLG11": {"name": "CSHG Logística FII", "sector": "Fundos Imobiliários",
               "keywords": ["hglg", "logística", "galpão", "fii"]},
    "KNRI11": {"name": "Kinea Renda Imobiliária FII", "sector": "Fundos Imobiliários",
               "keywords": ["kinea", "fundo imobiliário", "fii"]},
    "VISC11": {"name": "Vinci Shopping Centers FII", "sector": "Fundos Imobiliários",
               "keywords": ["vinci", "shopping", "fii"]},
    "ABEV3": {"name": "Ambev ON", "sector": "Bebidas", "keywords": ["ambev", "cerveja", "bebidas"]},
    "MGLU3": {"name": "Magazine Luiza ON", "sector": "Varejo",
              "keywords": ["magazine luiza", "magalu", "varejo", "e-commerce"]},
    "RENT3": {"name": "Localiza ON", "sector": "Locação de Veículos",
              "keywords": ["localiza", "aluguel de carros", "frota"]},
    "LREN3": {"name": "Lojas Renner ON", "sector": "Varejo", "keywords": ["renner", "varejo", "moda"]},
    "SUZB3": {"name": "Suzano ON", "sector": "Papel e Celulose",
              "keywords": ["suzano", "celulose", "papel"]},
    "JBSS3": {"name": "JBS ON", "sector": "Alimentos", "keywords": ["jbs", "carne", "frigorífico"]},
    "RADL3": {"name": "Raia Drogasil ON", "sector": "Saúde", "keywords": ["raia drogasil", "farmácia", "drogaria"]},
    "RAIL3": {"name": "Rumo ON", "sector": "Logística", "keywords": ["rumo", "ferrovia", "logística"]},
    "CSNA3": {"name": "CSN ON", "sector": "Siderurgia", "keywords": ["csn", "siderurgia", "aço", "mineração"]},
    "GGBR4": {"name": "Gerdau PN", "sector": "Siderurgia", "keywords": ["gerdau", "siderurgia", "aço"]},
    "USIM5": {"name": "Usiminas PNA", "sector": "Siderurgia", "keywords": ["usiminas", "siderurgia", "aço"]},
    "CIEL3": {"name": "Cielo ON", "sector": "Meios de Pagamento", "keywords": ["cielo", "cartão", "pagamentos"]},
    "EQTL3": {"name": "Equatorial Energia ON", "sector": "Energia",
              "keywords": ["equatorial", "energia elétrica", "distribuição"]},
    "ENGI11": {"name": "Energisa Unit", "sector": "Energia",
               "keywords": ["energisa", "energia elétrica", "distribuição"]},
    "CPLE6": {"name": "Copel PNB", "sector": "Energia", "keywords": ["copel", "energia elétrica"]},
    "ELET3": {"name": "Eletrobras ON", "sector": "Energia", "keywords": ["eletrobras", "energia elétrica"]},
    "ELET6": {"name": "Eletrobras PNB", "sector": "Energia", "keywords": ["eletrobras", "energia elétrica"]},
    "BRFS3": {"name": "BRF ON", "sector": "Alimentos", "keywords": ["brf", "sadia", "perdigão", "alimentos"]},
    "CCRO3": {"name": "CCR ON", "sector": "Infraestrutura", "keywords": ["ccr", "rodovias", "infraestrutura", "concessão"]},
    "EMBR3": {"name": "Embraer ON", "sector": "Aviação", "keywords": ["embraer", "aeronaves", "aviação"]},
    "AZUL4": {"name": "Azul PN", "sector": "Aviação", "keywords": ["azul linhas aéreas", "companhia aérea"]},
    "GOLL4": {"name": "Gol PN", "sector": "Aviação", "keywords": ["gol linhas aéreas", "companhia aérea"]},
    "VIVT3": {"name": "Telefônica Brasil ON", "sector": "Telecomunicações",
              "keywords": ["telefônica brasil", "telefônica", "telecom"]},
    "TIMS3": {"name": "TIM ON", "sector": "Telecomunicações", "keywords": ["tim brasil", "telecom"]},
    "SBSP3": {"name": "Sabesp ON", "sector": "Saneamento", "keywords": ["sabesp", "saneamento", "água"]},
    "KLBN11": {"name": "Klabin Unit", "sector": "Papel e Celulose", "keywords": ["klabin", "celulose", "papel"]},
    "CYRE3": {"name": "Cyrela ON", "sector": "Construção Civil", "keywords": ["cyrela"]},
    "MRVE3": {"name": "MRV ON", "sector": "Construção Civil", "keywords": ["mrv"]},
    "EZTC3": {"name": "Eztec ON", "sector": "Construção Civil", "keywords": ["eztec"]},
    "BRAP4": {"name": "Bradespar PN", "sector": "Holding", "keywords": ["bradespar", "holding"]},
    "CSAN3": {"name": "Cosan ON", "sector": "Energia", "keywords": ["cosan", "combustíveis", "açúcar", "etanol"]},
    "UGPA3": {"name": "Ultrapar ON", "sector": "Energia", "keywords": ["ultrapar", "ipiranga", "combustíveis"]},
    "PRIO3": {"name": "PetroRio ON", "sector": "Energia", "keywords": ["petrorio", "petróleo", "óleo e gás"]},
    "VBBR3": {"name": "Vibra Energia ON", "sector": "Energia", "keywords": ["vibra", "br distribuidora", "combustíveis"]},
    "CURY3": {"name": "Cury Construtora ON", "sector": "Construção Civil", "keywords": ["cury"]},
    "DIRR3": {"name": "Direcional Engenharia ON", "sector": "Construção Civil", "keywords": ["direcional engenharia"]},
    "EVEN3": {"name": "Even Construtora ON", "sector": "Construção Civil", "keywords": ["even construtora"]},
    "TEND3": {"name": "Construtora Tenda ON", "sector": "Construção Civil", "keywords": ["construtora tenda"]},
    "PLPL3": {"name": "Plano&Plano ON", "sector": "Construção Civil", "keywords": ["plano&plano"]},
    "SMFT3": {"name": "Smart Fit ON", "sector": "Saúde e Bem-Estar", "keywords": ["smart fit", "academia", "fitness"]},
    "HAPV3": {"name": "Hapvida ON", "sector": "Saúde", "keywords": ["hapvida", "plano de saúde", "saúde"]},
    "RDOR3": {"name": "Rede D'Or São Luiz ON", "sector": "Saúde", "keywords": ["rede d'or", "hospital", "saúde"]},
    "ASAI3": {"name": "Assaí Atacadista ON", "sector": "Varejo", "keywords": ["assaí", "atacadista", "varejo"]},
    "CRFB3": {"name": "Carrefour Brasil ON", "sector": "Varejo", "keywords": ["carrefour", "supermercado", "varejo"]},
    "NTCO3": {"name": "Natura &Co ON", "sector": "Cosméticos", "keywords": ["natura", "cosméticos", "avon"]},
}

RELEVANCE_KEYWORDS = {
    "high": [
        "ticker", "ativo", "empresa", "subsidiária", "ceo", "presidente",
        "resultados", "trimestral", "dividendo", "earnings", "ipo",
        "fusão", "aquisição", "oferta", "recall", "sinistro", "guidance", "fato relevante"
    ],
    "medium": [
        "setor", "commodity", "mercado", "bolsa", "ações", "investimento",
        "taxa de juros", "câmbio", "inflação", "pib", "economia"
    ]
}


def _normalize_text(text: str) -> str:
    """Remove acentos e normaliza caixa para comparação tolerante a erros."""
    text = (text or "").lower().strip()
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c))


@st.cache_data(ttl=86400)
def get_asset_catalog() -> list[dict]:
    """Catálogo de ativos B3 disponível para busca. Hoje local; ponto único de troca por API (BRAPI etc.)."""
    return [
        {"ticker": ticker, "company": data["name"], "sector": data.get("sector", "")}
        for ticker, data in B3_COMPANIES.items()
    ]


def search_assets(query: str, limit: int = 8) -> list[dict]:
    """Busca tolerante a acentos/caixa por ticker, nome da empresa, setor ou palavras-chave."""
    if not query or len(query.strip()) < 2:
        return []

    norm_query = _normalize_text(query)
    catalog = get_asset_catalog()
    results = []

    for asset in catalog:
        ticker = asset["ticker"]
        data = B3_COMPANIES.get(ticker, {})
        norm_ticker = _normalize_text(ticker)
        norm_ticker_base = norm_ticker.rstrip("0123456789")
        norm_name = _normalize_text(data.get("name", ""))
        norm_sector = _normalize_text(data.get("sector", ""))
        norm_keywords = [_normalize_text(k) for k in data.get("keywords", [])]

        score = 0
        if norm_query == norm_ticker or norm_query == norm_ticker_base:
            score = 100
        elif norm_ticker.startswith(norm_query):
            score = 90
        elif norm_query in norm_ticker:
            score = 80
        elif norm_name.startswith(norm_query):
            score = 70
        elif norm_query in norm_name:
            score = 60
        elif any(norm_query in kw or kw in norm_query for kw in norm_keywords):
            score = 40
        elif norm_query in norm_sector:
            score = 30

        if score > 0:
            results.append({"ticker": ticker, "company": data.get("name", ""),
                             "sector": data.get("sector", ""), "score": score})

    results.sort(key=lambda x: (-x["score"], x["ticker"]))
    return results[:limit]


def normalize_portfolio(portfolio_input: str) -> list[str]:
    """Normaliza entrada de tickers e retorna lista validada."""
    if not portfolio_input or not isinstance(portfolio_input, str):
        return []
    
    # Suporta entrada separada por vírgula ou quebra de linha
    tickers = portfolio_input.replace("\n", ",").split(",")
    
    # Limpa, transforma em maiúsculo e valida
    normalized = []
    for ticker in tickers:
        cleaned = ticker.strip().upper()
        # Valida formato básico: deve ter 4-6 caracteres e terminar em 3-4 dígitos
        if cleaned and len(cleaned) >= 4:
            normalized.append(cleaned)
    
    # Remove duplicatas preservando ordem
    seen = set()
    result = []
    for ticker in normalized:
        if ticker not in seen:
            seen.add(ticker)
            result.append(ticker)
    
    return result


def add_to_portfolio(portfolio_list: list[str], ticker: str) -> list[str]:
    """Adiciona um ticker à carteira, evitando duplicatas."""
    ticker = ticker.strip().upper()
    if ticker and ticker not in portfolio_list:
        return portfolio_list + [ticker]
    return portfolio_list


def remove_from_portfolio(portfolio_list: list[str], ticker: str) -> list[str]:
    """Remove um ticker da carteira."""
    return [t for t in portfolio_list if t != ticker]


def export_portfolio_csv(portfolio_list: list[str]) -> bytes:
    """Gera CSV (ticker, empresa, setor) para backup/reimportação da carteira."""
    rows = [{"ticker": t, "empresa": B3_COMPANIES.get(t, {}).get("name", ""),
             "setor": B3_COMPANIES.get(t, {}).get("sector", "")} for t in portfolio_list]
    df = pd.DataFrame(rows, columns=["ticker", "empresa", "setor"])
    return df.to_csv(index=False).encode("utf-8-sig")


def import_portfolio_csv(uploaded_file) -> list[str]:
    """Lê um CSV exportado previamente e retorna a lista de tickers normalizada."""
    df = pd.read_csv(uploaded_file)
    ticker_col = next((c for c in df.columns if c.strip().lower() == "ticker"), df.columns[0])
    tickers = [str(t).strip().upper() for t in df[ticker_col].dropna()]

    seen = set()
    result = []
    for ticker in tickers:
        if ticker and ticker not in seen:
            seen.add(ticker)
            result.append(ticker)
    return result


def _contains_word(text: str, word: str) -> bool:
    """Verifica presença de `word` em `text` respeitando limites de palavra (evita casamentos parciais)."""
    return re.search(r"\b" + re.escape(word) + r"\b", text) is not None


def classify_relevance(title: str, summary: str, portfolio: list[str]) -> dict[str, any]:
    """Classifica a relevância de uma notícia para a carteira do usuário."""
    text = (title + " " + summary).lower()
    
    relevance_score = 0
    matched_tickers = []
    matched_companies = []
    
    # Verifica tickers e empresas mencionadas
    for ticker in portfolio:
        company_data = B3_COMPANIES.get(ticker, {})
        keywords = company_data.get("keywords", [])
        company_name = company_data.get("name", ticker)
        base = ticker[:-1]  # Ex: PETR4 -> PETR

        # Verifica ticker direto (com dígito sempre; base isolada só se não for ambígua)
        ticker_matched = _contains_word(text, ticker.lower())
        if not ticker_matched and ticker not in AMBIGUOUS_TICKER_BASES:
            ticker_matched = _contains_word(text, base.lower())

        if ticker_matched:
            relevance_score += 50
            matched_tickers.append(ticker)
            matched_companies.append(company_name)

        # Verifica palavras-chave da empresa (tickers fora do catálogo não têm keywords)
        for keyword in keywords:
            if _contains_word(text, keyword.lower()):
                relevance_score += 30
                if company_name not in matched_companies:
                    matched_companies.append(company_name)
                if ticker not in matched_tickers:
                    matched_tickers.append(ticker)
                break  # Conta apenas uma vez por empresa
    
    # Verifica palavras-chave de alta relevância geral
    high_relevance_words = ["resultados", "dividendo", "earnings", "fusão", "aquisição"]
    for word in high_relevance_words:
        if matched_tickers and _contains_word(text, word):  # Só conta se houver menção de empresa
            relevance_score += 20
            break
    
    # Classifica relevância por score
    if relevance_score >= 60:
        relevance_level = "Alta"
        badge = "🟢"
    elif relevance_score >= 30:
        relevance_level = "Média"
        badge = "🟡"
    else:
        relevance_level = "Baixa"
        badge = "⚪"
    
    return {
        "relevance_level": relevance_level,
        "badge": badge,
        "score": relevance_score,
        "matched_tickers": matched_tickers,
        "matched_companies": matched_companies,
        "is_relevant": len(matched_tickers) > 0
    }


def filter_by_portfolio(df: pd.DataFrame, portfolio: list[str]) -> pd.DataFrame:
    """Filtra notícias relevantes para a carteira."""
    if not portfolio:
        return df
    
    relevant_news = []
    for _, row in df.iterrows():
        classification = classify_relevance(row["titulo"], row["resumo"], portfolio)
        if classification["is_relevant"]:
            relevant_news.append(row)
    
    return pd.DataFrame(relevant_news) if relevant_news else df.iloc[0:0]


def get_portfolio_stats(df: pd.DataFrame, portfolio: list[str]) -> dict:
    """Extrai estatísticas da carteira."""
    if not portfolio:
        return {
            "total_relevant": 0,
            "most_cited": None,
            "sentiment_counts": {"Positivo": 0, "Neutro": 0, "Negativo": 0},
            "ticker_rankings": []
        }
    
    ticker_mentions = {}
    sentiment_counts = {"Positivo": 0, "Neutro": 0, "Negativo": 0}
    
    for _, row in df.iterrows():
        classification = classify_relevance(row["titulo"], row["resumo"], portfolio)
        
        if classification["is_relevant"]:
            # Contabiliza menções de tickers
            for ticker in classification["matched_tickers"]:
                ticker_mentions[ticker] = ticker_mentions.get(ticker, 0) + 1
            
            # Contabiliza sentimentos
            sentiment = row.get("sentimento", "Neutro")
            if sentiment in sentiment_counts:
                sentiment_counts[sentiment] += 1
    
    # Ranking de ativos citados
    ticker_ranking = sorted(ticker_mentions.items(), key=lambda x: x[1], reverse=True)
    
    return {
        "total_relevant": sum(sentiment_counts.values()),
        "most_cited": ticker_ranking[0][0] if ticker_ranking else None,
        "sentiment_counts": sentiment_counts,
        "ticker_rankings": ticker_ranking,
        "sentiment_positive_pct": (
            round(sentiment_counts["Positivo"] / sum(sentiment_counts.values()) * 100, 1)
            if sum(sentiment_counts.values()) > 0 else 0
        )
    }


def get_portfolio_news(df: pd.DataFrame, portfolio: list[str]) -> pd.DataFrame:
    """Retorna notícias relevantes para a carteira com classificação de relevância."""
    if not portfolio:
        return df.iloc[0:0]
    
    relevant_rows = []
    for _, row in df.iterrows():
        classification = classify_relevance(row["titulo"], row["resumo"], portfolio)
        if classification["is_relevant"]:
            row_copy = row.copy()
            row_copy["portfolio_relevance"] = classification["relevance_level"]
            row_copy["portfolio_badge"] = classification["badge"]
            row_copy["matched_tickers"] = ", ".join(classification["matched_tickers"])
            relevant_rows.append(row_copy)
    
    if not relevant_rows:
        return df.iloc[0:0]
    
    result = pd.DataFrame(relevant_rows)
    # Ordena por relevância (alta > média > baixa)
    relevance_order = {"Alta": 0, "Média": 1, "Baixa": 2}
    result["_order"] = result["portfolio_relevance"].map(relevance_order)
    result = result.sort_values("_order").drop("_order", axis=1)
    return result


def get_sentiment_by_asset(df: pd.DataFrame, portfolio: list[str]) -> pd.DataFrame:
    """Agrega contagem de sentimento por ativo monitorado."""
    if not portfolio:
        return pd.DataFrame(columns=["Ticker", "Positivo", "Neutro", "Negativo"])

    ticker_sentiment = {t: {"Positivo": 0, "Neutro": 0, "Negativo": 0} for t in portfolio}

    for _, row in df.iterrows():
        classification = classify_relevance(row["titulo"], row["resumo"], portfolio)
        sentiment = row.get("sentimento", "Neutro")
        for ticker in classification["matched_tickers"]:
            if sentiment in ticker_sentiment[ticker]:
                ticker_sentiment[ticker][sentiment] += 1

    rows = [{"Ticker": ticker, **counts} for ticker, counts in ticker_sentiment.items()
            if sum(counts.values()) > 0]

    return pd.DataFrame(rows) if rows else pd.DataFrame(columns=["Ticker", "Positivo", "Neutro", "Negativo"])
