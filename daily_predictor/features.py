import pandas as pd

from config import TREND_EMA_FAST, TREND_EMA_SLOW, ATR_LEN, RANGE_VOL_MULT

RET_LOOKBACK = 30  # days for quant stats


def compute_atr(df: pd.DataFrame, length: int) -> pd.Series:
    high = df["High"]
    low = df["Low"]
    close = df["Close"]
    prev_close = close.shift(1)

    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(length).mean()


def daily_features(df: pd.DataFrame) -> dict:
    # Normalise columns in case yfinance returns a MultiIndex or lowercased names
    df = df.copy()
    if isinstance(df.columns, pd.MultiIndex):
        # If only one ticker level, drop that level so we get simple columns
        if len(df.columns.levels[0]) == 1:
            df.columns = df.columns.droplevel(0)
        elif len(df.columns.levels) > 1 and len(df.columns.levels[1]) == 1:
            df.columns = df.columns.droplevel(1)

    rename_map = {}
    for c in df.columns:
        lc = str(c).lower()
        if lc == "open":
            rename_map[c] = "Open"
        elif lc == "high":
            rename_map[c] = "High"
        elif lc == "low":
            rename_map[c] = "Low"
        elif lc == "close":
            rename_map[c] = "Close"
        elif lc in ("volume", "vol"):
            rename_map[c] = "Volume"
    if rename_map:
        df = df.rename(columns=rename_map)

    # Resample intraday to daily bars
    daily = df.resample("1D").agg({
        "Open": "first",
        "High": "max",
        "Low":  "min",
        "Close": "last",
        "Volume": "sum",
    }).dropna()

    if len(daily) < RET_LOOKBACK + 2:
        raise ValueError("Not enough daily history for quant stats")

    daily["ret"] = daily["Close"].pct_change()
    rets = daily["ret"].dropna()

    yesterday = daily.iloc[-2]
    today = daily.iloc[-1]

    y_range = yesterday.High - yesterday.Low
    gap = today.Open - yesterday.Close

    hist = rets.iloc[-RET_LOOKBACK-1:-1]
    mu_r = hist.mean()
    sigma_r = hist.std(ddof=1)
    skew_r = hist.skew()
    last_ret = rets.iloc[-1]
    ret_z = (last_ret - mu_r) / sigma_r if sigma_r > 0 else 0.0
    up_freq = (hist > 0).mean()

    close_intraday = df["Close"]
    ema_fast = close_intraday.ewm(span=TREND_EMA_FAST).mean()
    ema_slow = close_intraday.ewm(span=TREND_EMA_SLOW).mean()
    trend_slope = (ema_fast - ema_slow).iloc[-1]

    atr_hourly = compute_atr(df, ATR_LEN)
    atr_last = atr_hourly.iloc[-1]

    return {
        "today_date": today.name.date(),
        "today_open": today.Open,
        "yesterday_close": yesterday.Close,
        "yesterday_range": y_range,
        "gap": gap,
        "trend_slope": float(trend_slope),
        "atr_hourly": float(atr_last),
        "last_ret": float(last_ret),
        "ret_mean": float(mu_r),
        "ret_std": float(sigma_r),
        "ret_zscore": float(ret_z),
        "ret_skew": float(skew_r),
        "up_freq": float(up_freq),
    }


def classify_day(features: dict, news_sentiment: float, has_major_event: bool) -> dict:
    trend = features["trend_slope"]
    atr = features["atr_hourly"]
    y_range = features["yesterday_range"]
    ret_z = features["ret_zscore"]
    up_freq = features["up_freq"]
    skew_r = features["ret_skew"]

    vol_ratio = atr / y_range if y_range > 0 else 1.0

    # Base trend bias
    if trend > 0:
        bias = "Bullish"
    elif trend < 0:
        bias = "Bearish"
    else:
        bias = "Range"

    # Low volatility → likely range
    if vol_ratio < RANGE_VOL_MULT:
        bias = "Range"

    # Quant tilts
    if ret_z > 1.5 and skew_r < 0 and bias == "Bullish":
        bias = "Range"
    if ret_z < -1.5 and skew_r > 0 and bias == "Bearish":
        bias = "Range"

    if up_freq > 0.6 and bias == "Range":
        bias = "Bullish"
    if up_freq < 0.4 and bias == "Range":
        bias = "Bearish"

    # News sentiment tilt
    if news_sentiment > 0.2 and not has_major_event and bias == "Range":
        bias = "Bullish"
    if news_sentiment < -0.2 and not has_major_event and bias == "Range":
        bias = "Bearish"

    if has_major_event:
        bias = "Event/Risk"

    return {
        "bias": bias,
        "vol_ratio": float(vol_ratio),
        "trend_slope": float(trend),
        "atr_hourly": float(atr),
        "ret_zscore": float(ret_z),
        "ret_skew": float(skew_r),
        "up_freq": float(up_freq),
    }

