"""Fetch market data using Yahoo Finance."""

import yfinance as yf
import pandas as pd
from config import SYMBOLS, HISTORY_DAYS


def get_prices(symbol: str, days: int = HISTORY_DAYS) -> pd.DataFrame | None:
    """Get historical OHLCV data for a symbol."""
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=f"{days}d")
        if df.empty or len(df) < 2:
            return None
        return df
    except Exception:
        return None


def get_latest_price(symbol: str) -> float | None:
    """Get the latest close price for a symbol."""
    df = get_prices(symbol, days=5)
    if df is None or df.empty:
        return None
    return float(df["Close"].iloc[-1])


def get_atr(symbol: str, period: int = 14) -> float | None:
    """
    Current ATR (Average True Range) in price units.
    Used for stop loss / take profit distance (math-based risk).
    """
    df = get_prices(symbol, days=period + 20)
    if df is None or len(df) < period + 2:
        return None
    high = df["High"]
    low = df["Low"]
    close = df["Close"]
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()
    val = atr.iloc[-1]
    if pd.isna(val) or val <= 0:
        return None
    return float(val)


def get_atr_ratio(symbol: str, period: int = 14, ma_days: int = 20) -> float | None:
    """
    ATR (Average True Range) ratio for position sizing.
    Returns (ATR_ma / ATR_current) so high vol -> smaller ratio -> smaller position.
    None if not enough data.
    """
    df = get_prices(symbol, days=max(period, ma_days) + 10)
    if df is None or len(df) < period + ma_days:
        return None
    high = df["High"]
    low = df["Low"]
    close = df["Close"]
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()
    atr_current = atr.iloc[-1]
    atr_ma = atr.rolling(ma_days).mean().iloc[-1]
    if pd.isna(atr_current) or pd.isna(atr_ma) or atr_current <= 0:
        return None
    return float(atr_ma / atr_current)
