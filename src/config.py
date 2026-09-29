"""Configuração central: feeds, categorias e parâmetros."""
from dataclasses import dataclass

TIMEZONE = "America/Sao_Paulo"
REFRESH_SECONDS = 3600  # coleta automática de hora em hora
CACHE_TTL = REFRESH_SECONDS
REQUEST_TIMEOUT = 8
MAX_ITEMS_PER_FEED = 30
USER_AGENT = "Mozilla/5.0 (NewsIntelligenceHub/1.0)"
CATEGORIES = ["Política", "Economia", "Mercado Financeiro", "Tecnologia", "Inteligência Artificial"]
COLORS = {"primary": "#58A6FF", "pos": "#3FB950", "neg": "#F85149", "ai": "#A371F7", "neu": "#D29922"}


@dataclass(frozen=True)
class Feed:
    name: str
    category: str
    url: str
    lang: str = "pt"


# ATENÇÃO: valide as URLs após o deploy; portais mudam seus endpoints RSS.
FEEDS: list[Feed] = [
    Feed("Poder360", "Política", "https://www.poder360.com.br/feed/"),
    Feed("Congresso em Foco", "Política", "https://congressoemfoco.uol.com.br/feed/"),
    Feed("Veja Política", "Política", "https://veja.abril.com.br/politica/feed/"),
    Feed("CartaCapital", "Política", "https://www.cartacapital.com.br/feed/"),
    Feed("Agência Brasil Política", "Política", "https://agenciabrasil.ebc.com.br/rss/politica/feed.xml"),
    Feed("Exame Economia", "Economia", "https://exame.com/economia/feed/"),
    Feed("CNN Economia", "Economia", "https://www.cnnbrasil.com.br/economia/feed/"),
    Feed("Agência Brasil Economia", "Economia", "https://agenciabrasil.ebc.com.br/rss/economia/feed.xml"),
    Feed("Valor Econômico", "Economia", "https://pox.globo.com/rss/valor/"),
    Feed("InfoMoney", "Mercado Financeiro", "https://www.infomoney.com.br/feed/"),
    Feed("Valor Investe", "Mercado Financeiro", "https://pox.globo.com/rss/valor-investe/"),
    Feed("Money Times", "Mercado Financeiro", "https://www.moneytimes.com.br/feed/"),
    Feed("Investing Brasil", "Mercado Financeiro", "https://br.investing.com/rss/news.rss"),
    Feed("B3 News", "Mercado Financeiro",
         "https://news.google.com/rss/search?q=B3+bolsa+de+valores&hl=pt-BR&gl=BR&ceid=BR:pt-419"),
    Feed("Canaltech", "Tecnologia", "https://canaltech.com.br/rss/"),
    Feed("Tecnoblog", "Tecnologia", "https://tecnoblog.net/feed/"),
    Feed("Olhar Digital", "Tecnologia", "https://olhardigital.com.br/feed/"),
    Feed("Hardware.com.br", "Tecnologia", "https://www.hardware.com.br/rss/"),
    Feed("TechCrunch", "Tecnologia", "https://techcrunch.com/feed/", "en"),
    Feed("The Verge", "Tecnologia", "https://www.theverge.com/rss/index.xml", "en"),
    Feed("Wired", "Tecnologia", "https://www.wired.com/feed/rss", "en"),
    Feed("Ars Technica", "Tecnologia", "https://feeds.arstechnica.com/arstechnica/index", "en"),
]
