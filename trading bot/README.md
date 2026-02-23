# Quant Futures Bot (Paper Trading)

A **quant-style paper trading** bot for **futures**. Strategy: **volume** + **math** (momentum, volatility) + **news**. Positions are in **contracts**; P&L = (exit − entry) × contract multiplier. No real money—simulated only.

## What it does

- Trades **futures** (ES=F, NQ=F, CL=F, GC=F, etc.) via Yahoo Finance. Positions are **contracts** (integers).
- **P&L:** Realized when you close: `contracts × (exit_price − entry_price) × multiplier`. Equity = cash + unrealized P&L on open positions.
- **Volume:** Volume vs average (confirmation), **OBV** for trend (accumulation vs distribution).
- **Math:** **ROC**, **Bollinger**, **RSI**, **MACD**, **ADX**, **MFI**, **Stochastic**, **Z-Score**, **ATR** (position sizing).
- **News:** Keyword sentiment; BUY only when above threshold; SELL on strong negative.
- **BUY** only when math-based strategy passes (volume + OBV + ROC + Bollinger + RSI/MFI/Stochastic + MACD + ADX + Z-Score + news).
- **Exit** by **1:4 risk–reward**: every trade has a stop loss (SL) and take profit (TP). Risk distance = `STOP_LOSS_ATR_MULT × ATR`; reward = `RISK_REWARD_RATIO × risk` (default 1:4). Exit also on strategy SELL signal.
- No broker connection; no real orders.

## Setup

1. **Install Python** (3.10+ recommended).

2. **Go to the bot folder and install dependencies:**

   ```bash
   cd "trading bot"
   pip install -r requirements.txt
   ```

## How to use

**Run once** (single check and possible trades):

```bash
python main.py
```

**Run in a loop** (check every 60 minutes; interval is set in `config.py`):

```bash
python main.py --loop
```

Stop the loop with `Ctrl+C`.

**See average trades per month (backtest on last year of data):**

```bash
python backtest.py
```

This runs the same math-based strategy and 1:4 SL/TP on historical data (news off) and prints total trades and average trades per month/year.

## Configuration

Edit **`config.py`** to change:

| Setting | Meaning |
|--------|--------|
| `SYMBOLS` | Futures symbols (e.g. `["ES=F", "NQ=F", "CL=F", "GC=F"]`) |
| `FUTURES_MULTIPLIERS` | Dict: symbol → contract multiplier (ES=F: 50, NQ=F: 20, CL=F: 1000, GC=F: 100, etc.) |
| `INITIAL_BALANCE` | Starting equity in USD (e.g. 100_000) |
| `POSITION_SIZE_PCT` | % of equity to risk per trade (notional); caps contract size |
| `MAX_CONTRACTS_PER_TRADE` | Max contracts per symbol per trade (risk limit) |
| **1:4 Risk–Reward** | |
| `USE_SL_TP` | Use stop loss and take profit for every trade (default True) |
| `RISK_REWARD_RATIO` | Reward = this × risk (default 4 = 1:4 R:R) |
| `STOP_LOSS_ATR_MULT` | Risk distance = this × ATR (e.g. 2 = SL 2× ATR below entry) |
| **Volume** | |
| `VOLUME_AVG_DAYS` | Days for average volume (default 20) |
| `VOLUME_MIN_RATIO` | Volume must be ≥ this × average (e.g. 1.0 or 1.2) |
| `OBV_MA_PERIOD` | Period for OBV moving average (default 10) |
| **Math** | |
| `ROC_PERIOD` | Days for Rate of Change / momentum (default 10) |
| `ROC_BUY_MIN` / `ROC_SELL_MAX` | ROC thresholds (default 0) |
| `BB_PERIOD` / `BB_STD` | Bollinger Bands period and std-dev (20, 2.0) |
| `REQUIRE_ABOVE_LOWER_BAND` | Only buy when price above lower band (default True) |
| `USE_RSI` | Filter by RSI: don't buy overbought (>70) or oversold (<30) (default True) |
| `RSI_PERIOD` / `RSI_OVERBOUGHT` / `RSI_OVERSOLD` | RSI settings (14, 70, 30) |
| `USE_MACD` | Require MACD above signal for BUY, below for SELL (default True) |
| `MACD_FAST` / `MACD_SLOW` / `MACD_SIGNAL` | MACD periods (12, 26, 9) |
| `USE_ADX` | Only BUY when ADX > ADX_MIN (strong trend; avoids chop) (default True) |
| `ADX_PERIOD` / `ADX_MIN` | ADX period and minimum (14, 20) |
| `USE_ATR_POSITION_SIZING` | Reduce position size when ATR (volatility) is high (default True) |
| `ATR_PERIOD` / `ATR_SIZING_CAP` | ATR period and max size multiplier (14, 1.5) |
| `USE_MFI` | Money Flow Index: volume-weighted momentum; overbought > 80, oversold < 20 (default True) |
| `MFI_PERIOD` / `MFI_OVERBOUGHT` / `MFI_OVERSOLD` | MFI settings (14, 80, 20) |
| `USE_STOCHASTIC` | Stochastic oscillator: overbought > 80, oversold < 20 (default True) |
| `STOCH_K_PERIOD` / `STOCH_D_PERIOD` / `STOCH_OVERBOUGHT` / `STOCH_OVERSOLD` | Stochastic (14, 3, 80, 20) |
| `USE_ZSCORE` | Price Z-Score: don't buy when z > 2 (extended); SELL when \|z\| > 2 (default True) |
| `ZSCORE_PERIOD` / `ZSCORE_BUY_MAX` / `ZSCORE_SELL_EXTREME` | Z-Score period and thresholds (20, 2.0, 2.0) |
| `CHECK_INTERVAL_MINUTES` | Minutes between checks when using `--loop` |
| **News** | |
| `USE_NEWS` | Whether to factor news sentiment into BUY/SELL (default True) |
| `NEWS_LOOKBACK_ITEMS` | Number of recent news items to score (default 10) |
| `NEWS_SENTIMENT_BUY_MIN` | BUY only when sentiment ≥ this (-1 to 1; e.g. -0.3) |
| `NEWS_SENTIMENT_SELL_MAX` | Strong negative (≤ this) adds to SELL signal (e.g. -0.5) |

## Important

- **Paper only:** No broker; no real money. For live futures you'd need a broker API (e.g. Interactive Brokers, TDA).
- **Multipliers:** P&L per contract = (exit − entry) × multiplier (ES=$50/pt, NQ=$20/pt, CL=$1000/pt, etc.). Add new symbols to `FUTURES_MULTIPLIERS` in `config.py`.
- **No guarantees:** For learning and testing only. Past results do not guarantee future performance.
- **Data:** Yahoo Finance; futures symbols (e.g. ES=F) are typically front-month. Roll/continuous series not built-in.

## Project layout

```
trading bot/
  config.py       # Settings (symbols, balance, volume + math + news params)
  data.py         # Fetches prices and volume (yfinance)
  news.py         # Fetches news and keyword-based sentiment (yfinance)
  strategy.py     # Volume + math + news (OBV, ROC, Bollinger, RSI, MACD, ADX, MFI, Stochastic, Z-Score, sentiment)
  paper_trader.py # Futures: contracts, entry prices, P&L (realized + unrealized)
  main.py         # Entry point: python main.py [--loop]
  backtest.py     # Backtest: python backtest.py (average trades per month)
  requirements.txt
  README.md
  MATH_EXPLAINED.md
```
