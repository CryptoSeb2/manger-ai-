"""
Backtest the strategy on historical data to estimate average number of trades.
Uses same math-based signals and 1:4 SL/TP (tick-based for MGC/MNQ). News disabled (no history).
Run: python backtest.py
"""

import pandas as pd

from config import SYMBOLS, SL_TP_TICKS, TICK_SIZES, USE_SL_TP, ATR_PERIOD, RISK_REWARD_RATIO, STOP_LOSS_ATR_MULT
from data import get_prices, get_atr
from strategy import get_signals_from_df, _lookback


def _atr_from_df(df: pd.DataFrame, period: int = 14) -> float | None:
    """ATR at last bar of df (for ATR-based SL/TP fallback)."""
    if df is None or len(df) < period + 2:
        return None
    high = df["High"]
    low = df["Low"]
    close = df["Close"]
    prev = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev).abs(),
        (low - prev).abs(),
    ], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()
    val = atr.iloc[-1]
    if pd.isna(val) or val <= 0:
        return None
    return float(val)


def _sl_tp_prices(symbol: str, entry_price: float, df_sub: pd.DataFrame) -> tuple[float, float]:
    """Compute SL and TP prices for a long at entry_price. Uses ticks if configured else ATR."""
    if symbol in SL_TP_TICKS and symbol in TICK_SIZES:
        risk_ticks, reward_ticks = SL_TP_TICKS[symbol]
        tick = TICK_SIZES[symbol]
        sl = entry_price - risk_ticks * tick
        tp = entry_price + reward_ticks * tick
        return sl, tp
    atr = _atr_from_df(df_sub, period=ATR_PERIOD)
    if atr is not None and atr > 0:
        risk = STOP_LOSS_ATR_MULT * atr
        reward = RISK_REWARD_RATIO * risk
        return entry_price - risk, entry_price + reward
    return entry_price - 0.01, entry_price + 0.01 * RISK_REWARD_RATIO


def run_backtest(days: int = 365) -> dict:
    """
    Run backtest for each symbol. Returns dict: symbol -> list of (entry_date, exit_date, entry_price, exit_price, reason).
    """
    lookback = _lookback()
    all_trades = {}

    for symbol in SYMBOLS:
        df = get_prices(symbol, days=days)
        if df is None or len(df) < lookback:
            all_trades[symbol] = []
            continue

        position = None  # (entry_price, sl_price, tp_price, entry_date)
        trades = []

        for i in range(lookback, len(df)):
            row = df.iloc[i]
            high, low, close = float(row["High"]), float(row["Low"]), float(row["Close"])
            date = df.index[i]
            df_sub = df.iloc[: i + 1]

            signal = get_signals_from_df(symbol, df_sub, use_news=False)

            if position is None:
                if signal == "BUY":
                    entry_price = close
                    if USE_SL_TP:
                        sl_price, tp_price = _sl_tp_prices(symbol, entry_price, df_sub)
                    else:
                        sl_price, tp_price = entry_price - 0.01, entry_price + 0.01
                    position = (entry_price, sl_price, tp_price, date)
            else:
                entry_price, sl_price, tp_price, entry_date = position
                exit_price = None
                reason = None
                if USE_SL_TP and low <= sl_price:
                    exit_price = sl_price
                    reason = "SL"
                elif USE_SL_TP and high >= tp_price:
                    exit_price = tp_price
                    reason = "TP"
                elif signal == "SELL":
                    exit_price = close
                    reason = "SIGNAL"
                if exit_price is not None:
                    trades.append((entry_date, date, entry_price, exit_price, reason))
                    position = None

        all_trades[symbol] = trades

    return all_trades


def main():
    print("Backtesting strategy (math + 1:4 SL/TP, news OFF)...")
    print("Fetching data...")
    all_trades = run_backtest(days=365)

    total = 0
    for symbol in SYMBOLS:
        trades = all_trades.get(symbol, [])
        total += len(trades)
        print(f"  {symbol}: {len(trades)} trades")

    print()
    print(f"  Total trades (all symbols): {total}")
    # Backtest is ~1 year (365 days) of data
    months_in_backtest = 12
    if total > 0:
        avg_per_month = total / months_in_backtest
        print(f"  Over last ~{months_in_backtest} months of data")
        print(f"  Average trades per month: ~{avg_per_month:.1f}")
        print(f"  Average trades per year: ~{total:.1f}")
    else:
        print("  Average trades per month: 0 (no trades in backtest)")
    print()
    print("Note: Backtest uses price/volume only (no news). Live trading may differ.")


if __name__ == "__main__":
    main()
