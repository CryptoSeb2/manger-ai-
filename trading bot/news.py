"""
Fetch news for a symbol and compute simple keyword-based sentiment.
Uses Yahoo Finance news (no API key required).
"""

import yfinance as yf
from config import USE_NEWS, NEWS_LOOKBACK_ITEMS, NEWS_SENTIMENT_BUY_MIN, NEWS_SENTIMENT_SELL_MAX

# Keyword-based sentiment (expand as needed)
POSITIVE_WORDS = {
    "surge", "soar", "gain", "rise", "rally", "beat", "growth", "record", "strong",
    "outperform", "upgrade", "breakthrough", "profit", "revenue", "expansion",
    "buy", "bullish", "recovery", "optimistic", "exceed", "raise", "higher",
    "success", "deal", "partnership", "approval", "launch", "hit", "high",
}
NEGATIVE_WORDS = {
    "fall", "drop", "plunge", "crash", "miss", "cut", "layoff", "fraud",
    "investigation", "downgrade", "warning", "loss", "decline", "weak",
    "sell", "bearish", "concern", "risk", "lawsuit", "recall", "breach",
    "default", "bankruptcy", "recession", "slump", "lower", "fail",
}


def _sentiment_score(text: str) -> float:
    """
    Score text from -1 (negative) to +1 (positive) using keyword counts.
    Returns 0 if no keywords or empty text.
    """
    if not text or not text.strip():
        return 0.0
    lower = text.lower()
    pos = sum(1 for w in POSITIVE_WORDS if w in lower)
    neg = sum(1 for w in NEGATIVE_WORDS if w in lower)
    total = pos + neg
    if total == 0:
        return 0.0
    return (pos - neg) / total


def get_news_sentiment(symbol: str) -> float | None:
    """
    Fetch recent news for symbol and return aggregate sentiment in [-1, 1].
    Returns None if news is disabled or fetch fails.
    """
    if not USE_NEWS:
        return None
    try:
        ticker = yf.Ticker(symbol)
        items = getattr(ticker, "news", None)
        if not items:
            return None
        items = items[:NEWS_LOOKBACK_ITEMS]
        scores = []
        for item in items:
            if isinstance(item, dict):
                title = item.get("title") or ""
                pub = item.get("publisher", "") or ""
            else:
                title = getattr(item, "title", None) or ""
                pub = getattr(item, "publisher", None) or ""
            text = f"{title} {pub}"
            s = _sentiment_score(text)
            scores.append(s)
        if not scores:
            return None
        return sum(scores) / len(scores)
    except Exception:
        return None


def news_allows_buy(symbol: str) -> bool:
    """True if news sentiment is above BUY threshold (or news disabled / unavailable)."""
    sent = get_news_sentiment(symbol)
    if sent is None:
        return True  # no news = don't block
    return sent >= NEWS_SENTIMENT_BUY_MIN


def news_suggests_sell(symbol: str) -> bool:
    """True if news sentiment is below SELL threshold (strong negative)."""
    sent = get_news_sentiment(symbol)
    if sent is None:
        return False
    return sent <= NEWS_SENTIMENT_SELL_MAX
