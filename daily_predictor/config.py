SYMBOLS = {
    "gold": "GC=F",   # or 'MGC=F' depending on data source
    "nq":   "NQ=F",   # Nasdaq futures
}

LOOKBACK_DAYS = 90
INTRADAY_INTERVAL = "60m"  # 1-hour bars

TREND_EMA_FAST = 20
TREND_EMA_SLOW = 50

ATR_LEN = 14
RANGE_VOL_MULT = 0.8  # below this → more range-like

# --- News & calendar APIs ---

# NewsAPI (https://newsapi.org/)
NEWS_API_KEY = "dded64f279a549a3899265a4c572e884"
NEWS_ENDPOINT = "https://newsapi.org/v2/everything"
NEWS_LOOKBACK_HOURS = 12

NEWS_KEYWORDS = {
    "gold": ["gold", "XAU", "inflation", "yields", "dollar"],
    "nq":   ["Nasdaq", "tech stocks", "NQ", "equities", "risk-on", "risk-off"],
}

# FinancialModelingPrep (https://financialmodelingprep.com/)
FMP_API_KEY = "pfhG50d9wsFnSPlwQ0SKGvFsnSMJGwtb"
FMP_ECON_CALENDAR_ENDPOINT = "https://financialmodelingprep.com/api/v3/economic_calendar"

MAJOR_EVENT_KEYWORDS = [
    "FOMC",
    "Fed Interest Rate Decision",
    "Fed Interest Rate",
    "CPI",
    "Core CPI",
    "PCE",
    "Nonfarm Payrolls",
    "Unemployment Rate",
    "GDP",
]

NEWS_BULLISH_THRESHOLD = 0.2
NEWS_BEARISH_THRESHOLD = -0.2

