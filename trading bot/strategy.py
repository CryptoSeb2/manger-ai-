"""
Trading strategy based on volume + math + news.

Uses:
- Volume: volume vs average (confirmation), On-Balance Volume (OBV) trend
- Math: ROC, Bollinger, RSI, MACD, ADX, MFI (volume-weighted momentum), Stochastic, Z-Score
- News: keyword-based sentiment
"""

import pandas as pd
from config import (
    VOLUME_AVG_DAYS,
    VOLUME_MIN_RATIO,
    OBV_MA_PERIOD,
    ROC_PERIOD,
    ROC_BUY_MIN,
    ROC_SELL_MAX,
    BB_PERIOD,
    BB_STD,
    REQUIRE_ABOVE_LOWER_BAND,
    USE_RSI,
    RSI_PERIOD,
    RSI_OVERBOUGHT,
    RSI_OVERSOLD,
    USE_MACD,
    MACD_FAST,
    MACD_SLOW,
    MACD_SIGNAL,
    USE_ADX,
    ADX_PERIOD,
    ADX_MIN,
    USE_MFI,
    MFI_PERIOD,
    MFI_OVERBOUGHT,
    MFI_OVERSOLD,
    USE_STOCHASTIC,
    STOCH_K_PERIOD,
    STOCH_D_PERIOD,
    STOCH_OVERBOUGHT,
    STOCH_OVERSOLD,
    USE_ZSCORE,
    ZSCORE_PERIOD,
    ZSCORE_BUY_MAX,
    ZSCORE_SELL_EXTREME,
)
from data import get_prices
from news import news_allows_buy, news_suggests_sell


def _obv(df: pd.DataFrame) -> pd.Series:
    """On-Balance Volume: cumulative +volume on up closes, -volume on down closes."""
    close = df["Close"]
    volume = df["Volume"]
    direction = (close > close.shift(1)).astype(int).replace(0, -1)
    obv = (volume * direction).cumsum()
    return obv


def _bollinger_bands(close: pd.Series, period: int, num_std: float):
    """Lower, middle, upper Bollinger Bands."""
    middle = close.rolling(period).mean()
    std = close.rolling(period).std()
    upper = middle + num_std * std
    lower = middle - num_std * std
    return lower, middle, upper


def _rsi(close: pd.Series, period: int) -> pd.Series:
    """Relative Strength Index (0–100)."""
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss.replace(0, pd.NA)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)


def _macd(close: pd.Series, fast: int, slow: int, signal: int):
    """MACD line, signal line. Returns (macd_line, signal_line) as Series."""
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    return macd_line, signal_line


def _adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int) -> pd.Series:
    """Average Directional Index: trend strength (0–100). >20 = trending."""
    plus_dm = high.diff()
    minus_dm = -low.diff()
    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0.0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0.0)
    tr = pd.concat([
        high - low,
        (high - close.shift(1)).abs(),
        (low - close.shift(1)).abs(),
    ], axis=1).max(axis=1)
    atr = tr.rolling(period).mean().replace(0, pd.NA)
    plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(period).mean() / atr)
    di_sum = (plus_di + minus_di).replace(0, pd.NA)
    dx = 100 * (plus_di - minus_di).abs() / di_sum
    adx = dx.rolling(period).mean()
    return adx


def _mfi(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, period: int) -> pd.Series:
    """Money Flow Index (0–100). Volume-weighted momentum; overbought > 80, oversold < 20."""
    typical = (high + low + close) / 3
    raw_money_flow = typical * volume
    up = typical > typical.shift(1)
    down = typical < typical.shift(1)
    pos_flow = raw_money_flow.where(up, 0.0).rolling(period).sum()
    neg_flow = raw_money_flow.where(down, 0.0).rolling(period).sum()
    mf_ratio = pos_flow / neg_flow.replace(0, pd.NA)
    mfi = 100 - (100 / (1 + mf_ratio))
    return mfi.fillna(50)


def _stochastic(high: pd.Series, low: pd.Series, close: pd.Series, k_period: int, d_period: int):
    """Stochastic %K and %D (0–100). Overbought > 80, oversold < 20."""
    lowest_low = low.rolling(k_period).min()
    highest_high = high.rolling(k_period).max()
    k = 100 * (close - lowest_low) / (highest_high - lowest_low).replace(0, pd.NA)
    k = k.fillna(50)
    d = k.rolling(d_period).mean()
    return k, d


def _zscore(close: pd.Series, period: int) -> pd.Series:
    """Z-Score: (price - mean) / std. |z| > 2 = extreme."""
    mean = close.rolling(period).mean()
    std = close.rolling(period).std().replace(0, pd.NA)
    z = (close - mean) / std
    return z


def _lookback() -> int:
    """Minimum bars needed for all indicators."""
    return max(
        VOLUME_AVG_DAYS, OBV_MA_PERIOD, ROC_PERIOD, BB_PERIOD,
        RSI_PERIOD + 2 if USE_RSI else 0,
        MACD_SLOW + MACD_SIGNAL + 2 if USE_MACD else 0,
        ADX_PERIOD + 2 if USE_ADX else 0,
        MFI_PERIOD + 2 if USE_MFI else 0,
        STOCH_K_PERIOD + STOCH_D_PERIOD + 2 if USE_STOCHASTIC else 0,
        ZSCORE_PERIOD + 2 if USE_ZSCORE else 0,
    ) + 2


def get_signals_from_df(symbol: str, df: pd.DataFrame, use_news: bool = True) -> str:
    """
    Same as get_signals but uses provided df (for backtest). use_news=False skips news checks.
    """
    lookback = _lookback()
    if df is None or len(df) < lookback:
        return "HOLD"

    close = df["Close"]
    volume = df["Volume"]
    high = df["High"]
    low = df["Low"]

    # --- Volume ---
    vol_avg = volume.rolling(VOLUME_AVG_DAYS).mean()
    vol_ratio = volume / vol_avg
    current_vol_ratio = vol_ratio.iloc[-1]
    if pd.isna(current_vol_ratio) or current_vol_ratio < VOLUME_MIN_RATIO:
        return "HOLD"

    obv = _obv(df)
    obv_ma = obv.rolling(OBV_MA_PERIOD).mean()
    obv_up = obv.iloc[-1] > obv_ma.iloc[-1]
    obv_down = obv.iloc[-1] < obv_ma.iloc[-1]

    # --- Math: momentum (ROC) ---
    roc = (close - close.shift(ROC_PERIOD)) / close.shift(ROC_PERIOD)
    current_roc = roc.iloc[-1]
    if pd.isna(current_roc):
        return "HOLD"

    # --- Math: Bollinger (volatility) ---
    lower_bb, _, upper_bb = _bollinger_bands(close, BB_PERIOD, BB_STD)
    above_lower = close.iloc[-1] > lower_bb.iloc[-1] if not pd.isna(lower_bb.iloc[-1]) else True

    # --- Math: RSI (overbought/oversold) ---
    rsi_ok_buy = True
    rsi_sell = False
    if USE_RSI:
        rsi = _rsi(close, RSI_PERIOD)
        current_rsi = rsi.iloc[-1]
        if not pd.isna(current_rsi):
            rsi_ok_buy = RSI_OVERSOLD < current_rsi < RSI_OVERBOUGHT  # don't buy at extremes
            rsi_sell = current_rsi >= RSI_OVERBOUGHT or current_rsi <= RSI_OVERSOLD

    # --- Math: MACD (trend confirmation) ---
    macd_ok_buy = True
    macd_sell = False
    if USE_MACD:
        macd_line, signal_line = _macd(close, MACD_FAST, MACD_SLOW, MACD_SIGNAL)
        curr_macd = macd_line.iloc[-1]
        curr_sig = signal_line.iloc[-1]
        prev_macd = macd_line.iloc[-2]
        prev_sig = signal_line.iloc[-2]
        if not (pd.isna(curr_macd) or pd.isna(curr_sig)):
            macd_ok_buy = curr_macd > curr_sig  # bullish: MACD above signal
            macd_sell = curr_macd < curr_sig  # bearish

    # --- Math: ADX (trend strength – avoid chop) ---
    adx_ok_buy = True
    if USE_ADX:
        adx = _adx(high, low, close, ADX_PERIOD)
        current_adx = adx.iloc[-1]
        if not pd.isna(current_adx):
            adx_ok_buy = current_adx > ADX_MIN

    # --- Math: MFI (volume-weighted momentum) ---
    mfi_ok_buy = True
    mfi_sell = False
    if USE_MFI:
        mfi = _mfi(high, low, close, volume, MFI_PERIOD)
        current_mfi = mfi.iloc[-1]
        if not pd.isna(current_mfi):
            mfi_ok_buy = MFI_OVERSOLD < current_mfi < MFI_OVERBOUGHT
            mfi_sell = current_mfi >= MFI_OVERBOUGHT or current_mfi <= MFI_OVERSOLD

    # --- Math: Stochastic (overbought/oversold) ---
    stoch_ok_buy = True
    stoch_sell = False
    if USE_STOCHASTIC:
        stoch_k, stoch_d = _stochastic(high, low, close, STOCH_K_PERIOD, STOCH_D_PERIOD)
        current_k = stoch_k.iloc[-1]
        if not pd.isna(current_k):
            stoch_ok_buy = STOCH_OVERSOLD < current_k < STOCH_OVERBOUGHT
            stoch_sell = current_k >= STOCH_OVERBOUGHT or current_k <= STOCH_OVERSOLD

    # --- Math: Z-Score (price extremes) ---
    zscore_ok_buy = True
    zscore_sell = False
    if USE_ZSCORE:
        z = _zscore(close, ZSCORE_PERIOD)
        current_z = z.iloc[-1]
        if not pd.isna(current_z):
            zscore_ok_buy = current_z <= ZSCORE_BUY_MAX  # don't chase extended price
            zscore_sell = abs(current_z) > ZSCORE_SELL_EXTREME  # take profit or cut loss

    # BUY: volume + OBV + momentum + Bollinger + RSI + MACD + ADX + MFI + Stochastic + Z-Score + news
    if (
        current_vol_ratio >= VOLUME_MIN_RATIO
        and obv_up
        and current_roc >= ROC_BUY_MIN
        and rsi_ok_buy
        and macd_ok_buy
        and adx_ok_buy
        and mfi_ok_buy
        and stoch_ok_buy
        and zscore_ok_buy
    ):
        if use_news and not news_allows_buy(symbol):
            return "HOLD"
        if REQUIRE_ABOVE_LOWER_BAND and not above_lower:
            return "HOLD"
        return "BUY"

    # SELL: volume and (OBV down or ROC negative or RSI/MFI/Stoch extreme or MACD bearish or Z-Score extreme or news)
    if current_vol_ratio >= VOLUME_MIN_RATIO and (
        obv_down
        or current_roc <= ROC_SELL_MAX
        or rsi_sell
        or macd_sell
        or mfi_sell
        or stoch_sell
        or zscore_sell
        or (use_news and news_suggests_sell(symbol))
    ):
        return "SELL"

    return "HOLD"


def get_signals(symbol: str) -> str:
    """Live signal: fetches data and returns BUY/SELL/HOLD."""
    df = get_prices(symbol)
    return get_signals_from_df(symbol, df, use_news=True)
