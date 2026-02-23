import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

from config import LOOKBACK_DAYS, INTRADAY_INTERVAL


def fetch_intraday(symbol: str) -> pd.DataFrame:
    """
    Fetch recent intraday OHLCV data for a symbol using yfinance.
    """
    end = datetime.utcnow()
    start = end - timedelta(days=LOOKBACK_DAYS)
    df = yf.download(
        symbol,
        start=start,
        end=end,
        interval=INTRADAY_INTERVAL,
        auto_adjust=False,
        progress=False,
    )
    if df.empty:
        raise ValueError(f"No data downloaded for {symbol}")

    # Ensure we have a timezone on the index
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    return df

