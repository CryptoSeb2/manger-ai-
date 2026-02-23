"""
Trading bot configuration – quant-style futures paper trading.
Strategy: volume + math + news. Positions are in contracts (futures).
"""

# Futures symbols (Yahoo Finance: MGC=F micro gold, MNQ=F micro Nasdaq, etc.)
SYMBOLS = ["MGC=F", "MNQ=F"]

# Fixed contracts per symbol when BUY (overrides size-from-equity). None = use POSITION_SIZE_PCT / notional.
# 1 micro MGC, 3 micros MNQ
FIXED_CONTRACTS = {
    "MGC=F": 1,   # 1 micro gold
    "MNQ=F": 3,   # 3 micro Nasdaq
}

# Contract multiplier: notional per point. P&L per contract = (exit_price - entry_price) × multiplier
FUTURES_MULTIPLIERS = {
    "ES=F": 50,    # E-mini S&P 500
    "NQ=F": 20,    # E-mini Nasdaq-100
    "MGC=F": 10,   # Micro Gold (10 troy oz)
    "MNQ=F": 2,    # Micro E-mini Nasdaq-100
    "CL=F": 1000,  # Crude oil WTI
    "GC=F": 100,   # Gold
    "ZB=F": 1000,  # 30-Year T-Bond
    "ZN=F": 1000,  # 10-Year T-Note
    "ZC=F": 50,    # Corn
    "ZS=F": 50,    # Soybeans
    "ZW=F": 50,    # Wheat
}


def get_multiplier(symbol: str) -> float:
    """Contract multiplier for symbol. Notional per point = price × multiplier."""
    return FUTURES_MULTIPLIERS.get(symbol, 1.0)


# Paper trading starting equity (USD)
INITIAL_BALANCE = 100_000.0

# --- Volume-based ---
# Volume must be at least this many times the N-day average to confirm a move
VOLUME_AVG_DAYS = 20
VOLUME_MIN_RATIO = 1.0  # e.g. 1.2 = require 20% above average volume
# On-Balance Volume (OBV) trend: period for OBV moving average
OBV_MA_PERIOD = 10

# --- Math-based ---
# Rate of change (momentum): period in days. Positive ROC = upward momentum
ROC_PERIOD = 10
# ROC thresholds: BUY when ROC >= this, SELL when ROC <= this (e.g. 0 = crossover)
ROC_BUY_MIN = 0.0
ROC_SELL_MAX = 0.0
# Bollinger Bands: period and std-dev multiplier (volatility)
BB_PERIOD = 20
BB_STD = 2.0
# Optional: only buy when price is above lower band (avoid oversold chase)
REQUIRE_ABOVE_LOWER_BAND = True

# RSI (Relative Strength Index): overbought/oversold filter
USE_RSI = True
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70   # Don't buy when RSI > this; SELL when RSI > this (take profit)
RSI_OVERSOLD = 30     # Don't buy when RSI < this (falling knife); SELL when RSI < this

# MACD (Moving Average Convergence Divergence): trend confirmation
USE_MACD = True
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9      # Signal line period

# ADX (Average Directional Index): trend strength – only trade when trend is clear
USE_ADX = True
ADX_PERIOD = 14
ADX_MIN = 20         # Only BUY when ADX > this (avoids chop)

# ATR (Average True Range): volatility-based position sizing – smaller size when vol is high
USE_ATR_POSITION_SIZING = True
ATR_PERIOD = 14
ATR_SIZING_CAP = 1.5  # Max multiplier when vol is low (don't oversize)

# Money Flow Index (MFI): volume-weighted RSI (0–100). Overbought > 80, oversold < 20
USE_MFI = True
MFI_PERIOD = 14
MFI_OVERBOUGHT = 80
MFI_OVERSOLD = 20

# Stochastic Oscillator: %K and %D. Overbought > 80, oversold < 20
USE_STOCHASTIC = True
STOCH_K_PERIOD = 14
STOCH_D_PERIOD = 3
STOCH_OVERBOUGHT = 80
STOCH_OVERSOLD = 20

# Price Z-Score: how many std devs from mean. |z| > 2 = extreme (don't chase, take profit or cut loss)
USE_ZSCORE = True
ZSCORE_PERIOD = 20
ZSCORE_BUY_MAX = 2.0   # Don't buy when z > this (price too extended)
ZSCORE_SELL_EXTREME = 2.0  # SELL when |z| > this (take profit or cut loss)

# How much of equity to risk per trade (notional as % of total equity). Caps contract size.
POSITION_SIZE_PCT = 0.25
# Max contracts per symbol per trade (risk limit)
MAX_CONTRACTS_PER_TRADE = 2

# --- 1:4 Risk–Reward (math-based exit) ---
USE_SL_TP = True
# Per-symbol SL/TP in ticks (risk_ticks, reward_ticks). If set, overrides ATR-based SL/TP.
# MGC: 100 ticks risk → 400 ticks reward (1:4). MNQ: 50 ticks risk → 200 ticks reward (1:4).
SL_TP_TICKS = {
    "MGC=F": (100, 400),   # 100 ticks SL, 400 ticks TP
    "MNQ=F": (50, 200),    # 50 ticks SL, 200 ticks TP
}
# Tick size (minimum price move) per symbol. CME: MGC 0.25, MNQ 0.25.
TICK_SIZES = {
    "MGC=F": 0.25,
    "MNQ=F": 0.25,
}
# Fallback when symbol not in SL_TP_TICKS: use ATR-based distance.
RISK_REWARD_RATIO = 4
STOP_LOSS_ATR_MULT = 2.0

# How often to check and potentially trade (minutes)
CHECK_INTERVAL_MINUTES = 60

# Timeframe for fetching price history
HISTORY_DAYS = 90

# --- News ---
USE_NEWS = True
# How many recent news items to consider for sentiment
NEWS_LOOKBACK_ITEMS = 10
# BUY only when news sentiment >= this (-1 to 1). Set to -1 to effectively ignore.
NEWS_SENTIMENT_BUY_MIN = -0.3
# SELL more likely when news sentiment <= this (strong negative)
NEWS_SENTIMENT_SELL_MAX = -0.5
