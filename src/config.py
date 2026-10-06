"""Configuração central: feeds, categorias e parâmetros."""
from dataclasses import dataclass

TIMEZONE = "America/Sao_Paulo"
REFRESH_SECONDS = 600  # padrão: coleta automática a cada 10 minutos
CACHE_TTL = 300  # cache mais curto para permitir atualizações frequentes
REQUEST_TIMEOUT = 8
MAX_ITEMS_PER_FEED = 30
USER_AGENT = "Mozilla/5.0 (NewsIntelligenceHub/1.0)"
CATEGORIES = ["Política", "Economia", "Mercado Financeiro", "Tecnologia", "Inteligência Artificial"]
COLORS = {"primary": "#58A6FF", "pos": "#3FB950", "neg": "#F85149", "ai": "#A371F7", "neu": "#D29922"}

# Opções de intervalo de atualização automática (em minutos)
REFRESH_INTERVALS = {
    "1 minuto": 60,
    "5 minutos": 300,
    "10 minutos": 600,
    "30 minutos": 1800,
    "1 hora": 3600,
    "Desativar": None
}


@dataclass(frozen=True)
class Feed:
    name: str
    category: str
    url: str
    lang: str = "pt"


# ATENÇÃO: valide as URLs após o deploy; portais mudam seus endpoints RSS.
FEEDS: list[Feed] = [
# ==========================================
# POLÍTICA
# ==========================================
Feed("G1 Política", "Política", "https://g1.globo.com/rss/g1/politica/"),
Feed("Folha - Poder", "Política", "https://feeds.folha.uol.com.br/poder/rss091.xml"),
Feed("Agência Brasil Política", "Política", "https://agenciabrasil.ebc.com.br/rss/politica/feed.xml"),
Feed("Agência Senado", "Política", "https://www12.senado.leg.br/noticias/rss"),
Feed("Agência Câmara", "Política", "https://www.camara.leg.br/noticias/rss/ultimas-noticias"),
Feed("Poder360", "Política", "https://www.poder360.com.br/feed/"),
Feed("Google News - Política Brasil", "Política",
     "https://news.google.com/rss/search?q=pol%C3%ADtica+Brasil+governo+Congresso+STF&hl=pt-BR&gl=BR&ceid=BR:pt-419"),
Feed("Google News - Brazil Politics", "Política",
     "https://news.google.com/rss/search?q=Brazil+politics+OR+Lula+OR+Brazil+Congress&hl=en-US&gl=US&ceid=US:en", "en"),

# ==========================================
# ECONOMIA & MACROECONOMIA (NACIONAL)
# ==========================================
Feed("Agência Brasil Economia", "Economia", "https://agenciabrasil.ebc.com.br/rss/economia/feed.xml"),
Feed("Valor Econômico", "Economia", "https://pox.globo.com/rss/valor/"),
Feed("Neofeed", "Economia", "https://neofeed.com.br/feed/"),
Feed("Capital Reset", "Economia", "https://www.capitalreset.com/feed/"),
Feed("Google News - Economia Brasil", "Economia",
     "https://news.google.com/rss/search?q=Brazilian+economy+OR+Brazil+inflation+OR+Brazil+GDP&hl=en-US&gl=US&ceid=US:en", "en"),

# ==========================================
# MERCADO FINANCEIRO & INVESTIMENTOS (NACIONAL)
# ==========================================
Feed("InfoMoney", "Mercado Financeiro", "https://www.infomoney.com.br/feed/"),
Feed("Money Times", "Mercado Financeiro", "https://www.moneytimes.com.br/feed/"),
Feed("Investing Brasil", "Mercado Financeiro", "https://br.investing.com/rss/news.rss"),
Feed("Suno Notícias", "Mercado Financeiro", "https://www.suno.com.br/noticias/feed/"),
Feed("Fiis.com.br", "Mercado Financeiro", "https://fiis.com.br/noticias/feed/"),
Feed("Clube FII", "Mercado Financeiro", "https://www.clubefii.com.br/noticias/rss"),
Feed("B3 News", "Mercado Financeiro",
     "https://news.google.com/rss/search?q=B3+bolsa+de+valores&hl=pt-BR&gl=BR&ceid=BR:pt-419"),
Feed("Tickers da carteira", "Mercado Financeiro",
     "https://news.google.com/rss/search?q=BBDC4+OR+BBAS3+OR+ITSA4+OR+PETR4+OR+CURY3+OR+CMIG4+OR+TAEE11+OR+BBSE3+OR+SAPR4+OR+KLBN4+OR+COGN3+OR+BHIA3+OR+PRIO3+OR+GARE11+OR+VGHF11+OR+MXRF11+OR+KISU11+OR+TRXF11&hl=pt-BR&gl=BR&ceid=BR:pt-419"),

# ==========================================
# ECONOMIA & MERCADO FINANCEIRO (INTERNACIONAL)
# ==========================================
Feed("Bloomberg Markets", "Mercado Financeiro", "https://feeds.bloomberg.com/markets/news.rss", "en"),
Feed("CNBC Business", "Mercado Financeiro", "https://www.cnbc.com/id/100003114/device/rss/rss.html", "en"),
Feed("CNBC Finance", "Mercado Financeiro", "https://www.cnbc.com/id/10000664/device/rss/rss.html", "en"),
Feed("MarketWatch Top Stories", "Mercado Financeiro", "https://feeds.content.dowjones.io/public/rss/mw_topstories", "en"),
Feed("MarketWatch Real-time", "Mercado Financeiro", "https://feeds.content.dowjones.io/public/rss/mw_realtimeheadlines", "en"),
Feed("Investing.com Global", "Mercado Financeiro", "https://www.investing.com/rss/news.rss", "en"),
Feed("Seeking Alpha - Market Pulse", "Mercado Financeiro", "https://seekingalpha.com/market_currents.xml", "en"),
Feed("Wall Street Journal - Business", "Economia", "https://feeds.content.dowjones.io/public/rss/WSJcomUSBusiness", "en"),
Feed("Financial Times - Global Economy", "Economia", "https://www.ft.com/global-economy?format=rss", "en"),
Feed("Financial Times - Markets", "Mercado Financeiro", "https://www.ft.com/markets?format=rss", "en"),
Feed("The Economist - Finance", "Economia", "https://www.economist.com/finance-and-economics/rss.xml", "en"),
Feed("Federal Reserve Press Releases", "Economia", "https://www.federalreserve.gov/feeds/press_all.xml", "en"),
Feed("European Central Bank (ECB)", "Economia", "https://www.ecb.europa.eu/rss/press.html", "en"),
Feed("CB Insights Research", "Mercado Financeiro", "https://www.cbinsights.com/research/feed/", "en"),
Feed("Fortune Finance", "Economia", "https://fortune.com/feed/fortune-feeds/?id=3230629", "en"),
Feed("Google News - Reuters Finance", "Mercado Financeiro",
     "https://news.google.com/rss/search?q=site%3Areuters.com+markets+OR+finance+OR+economy&hl=en-US&gl=US&ceid=US:en", "en"),
Feed("Google News - Latin America Markets", "Mercado Financeiro",
     "https://news.google.com/rss/search?q=Latin+America+markets+OR+LatAm+economy&hl=en-US&gl=US&ceid=US:en", "en"),
Feed("Google News - Fed & US Rates", "Economia",
     "https://news.google.com/rss/search?q=Federal+Reserve+OR+interest+rates+OR+US+inflation&hl=en-US&gl=US&ceid=US:en", "en"),
Feed("Google News - Commodities Global", "Mercado Financeiro",
     "https://news.google.com/rss/search?q=Brent+crude+OR+Gold+price+OR+Iron+ore&hl=en-US&gl=US&ceid=US:en", "en"),

# ==========================================
# CRIPTOMOEDAS (INTERNACIONAL)
# ==========================================
Feed("CoinDesk", "Mercado Financeiro", "https://www.coindesk.com/arc/outboundfeeds/rss/", "en"),
Feed("Cointelegraph", "Mercado Financeiro", "https://cointelegraph.com/rss", "en"),
Feed("Decrypt", "Mercado Financeiro", "https://decrypt.co/feed", "en"),
Feed("The Block", "Mercado Financeiro", "https://www.theblock.co/rss.xml", "en"),
Feed("Blockworks", "Mercado Financeiro", "https://blockworks.co/feed", "en"),
Feed("Google News - Cryptocurrency", "Mercado Financeiro",
     "https://news.google.com/rss/search?q=cryptocurrency+OR+bitcoin+OR+ethereum&hl=en-US&gl=US&ceid=US:en", "en"),

# ==========================================
# TECNOLOGIA, SOFTWARE & IA
# ==========================================
Feed("Canaltech", "Tecnologia", "https://canaltech.com.br/rss/"),
Feed("Tecnoblog", "Tecnologia", "https://tecnoblog.net/feed/"),
Feed("Olhar Digital", "Tecnologia", "https://olhardigital.com.br/feed/"),
Feed("Hardware.com.br", "Tecnologia", "https://www.hardware.com.br/rss/"),
Feed("TechCrunch", "Tecnologia", "https://techcrunch.com/feed/", "en"),
Feed("The Verge", "Tecnologia", "https://www.theverge.com/rss/index.xml", "en"),
Feed("Wired", "Tecnologia", "https://www.wired.com/feed/rss", "en"),
Feed("Ars Technica", "Tecnologia", "https://feeds.arstechnica.com/arstechnica/index", "en"),
Feed("Tom's Hardware", "Tecnologia", "https://www.tomshardware.com/feeds/all", "en"),
Feed("9to5Mac", "Tecnologia", "https://9to5mac.com/feed/", "en"),
Feed("MIT Technology Review", "Tecnologia", "https://www.technologyreview.com/feed/", "en"),
Feed("Dev.to", "Desenvolvimento", "https://dev.to/feed", "en"),

# ==========================================
# INTERNACIONAL & NOTÍCIAS GERAIS
# ==========================================
Feed("BBC Brasil", "Internacional", "https://feeds.bbci.co.uk/portuguese/rss.xml"),
Feed("DW Brasil", "Internacional", "https://rss.dw.com/xml/rss-br-all"),
]
