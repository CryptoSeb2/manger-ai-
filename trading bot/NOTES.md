## Trading bot quick notes (for new agents)

If you're a new agent, read this first before helping.

### What this bot is

- **Type**: Quant-style **paper trading** bot for **futures** (no live orders yet).
- **Folder**: `trading bot/`
- **Core files**:
  - `config.py` – symbols, futures multipliers, risk settings.
  - `strategy.py` – volume + math + news entry/exit logic.
  - `paper_trader.py` – simulates futures positions in contracts.
  - `main.py` – runs the bot (`python main.py` or `python main.py --loop`).
  - `backtest.py` – estimates average trades per month (`python backtest.py`).
  - `MATH_EXPLAINED.md` – detailed math formulas.

### Instruments and sizing

- **Symbols traded now** (see `config.py` → `SYMBOLS`):
  - `MGC=F` – Micro Gold, trade **1 micro**.
  - `MNQ=F` – Micro E-mini Nasdaq-100, trade **3 micros**.
- **Sizing**:
  - Fixed contracts per symbol via `FIXED_CONTRACTS`:
    - `MGC=F`: 1 contract
    - `MNQ=F`: 3 contracts
  - P&L per contract = (exit_price − entry_price) × `FUTURES_MULTIPLIERS[symbol]`.

### Risk / reward and ticks

- The user wants **pure math-based execution** with **1:4 risk–reward**:
  - Each trade has a **stop loss (SL)** and **take profit (TP)**.
  - Reward distance = `RISK_REWARD_RATIO × risk` (default 4 → 1:4).
- Per-symbol tick SL/TP (see `SL_TP_TICKS` and `TICK_SIZES` in `config.py`):
  - `MGC=F`: **100 ticks SL**, **400 ticks TP**, tick size **0.25**.
  - `MNQ=F`: **50 ticks SL**, **200 ticks TP**, tick size **0.25**.
- For symbols not in `SL_TP_TICKS`, fallback is ATR-based SL/TP:
  - Risk distance = `STOP_LOSS_ATR_MULT × ATR`.
  - Reward distance = `RISK_REWARD_RATIO × risk`.

### Strategy (what must line up to BUY)

For a BUY, **all** of these must pass (see `strategy.py` → `get_signals_from_df` / `get_signals`):

- **Volume**:
  - Volume ≥ `VOLUME_MIN_RATIO ×` average volume (20-day).
  - OBV above its moving average (`OBV_MA_PERIOD`).
- **Momentum / price**:
  - ROC (10-day) ≥ `ROC_BUY_MIN` (default 0).
  - Price above lower Bollinger band if `REQUIRE_ABOVE_LOWER_BAND` is True.
- **Oscillators / trend filters**:
  - RSI between `RSI_OVERSOLD` (30) and `RSI_OVERBOUGHT` (70).
  - MACD line above signal line (bullish).
  - ADX > `ADX_MIN` (e.g. 20) for trend strength.
  - MFI between its overbought/oversold bounds.
  - Stochastic %K between its overbought/oversold bounds.
  - Z-Score ≤ `ZSCORE_BUY_MAX` (not too extended).
- **News** (if `USE_NEWS` is True):
  - `news_allows_buy(symbol)` (sentiment ≥ `NEWS_SENTIMENT_BUY_MIN`).

Exits are via:

- Hitting **SL** or **TP** (1:4 risk–reward, tick or ATR based), OR
- Strategy **SELL** signal (OBV down, ROC ≤ threshold, RSI/MFI/Stoch extreme, MACD bearish, Z-Score extreme, or strong negative news).

### Live trading status

- **Current state**: **paper trading only**. No broker or real orders.
- The user’s broker of interest: **Tradovate**.
- Next steps for live (future agent task, when user asks):
  1. Guide user to enable API access in Tradovate and obtain credentials safely (env vars / `.env`, NOT hard-coded).
  2. Add a `tradovate_client.py` module to:
     - Authenticate to Tradovate.
     - Place futures orders with attached SL/TP for MGC and MNQ.
  3. Extend `main.py` with a `--live` mode that:
     - Uses the same math signals and SL/TP levels.
     - Calls `tradovate_client` instead of `PaperTrader` for execution.
  4. Test first against **Tradovate demo/sim**, then (optionally) live.

### How to quickly get average trades

- Run the built-in backtest over ~1 year of data:

  ```bash
  cd "trading bot"
  python backtest.py
  ```

- This prints total trades and rough **average trades per month/year** (news OFF in backtest).

### What the user will likely ask next

- “Help me connect this to **Tradovate demo** and then live.”
- Expect to:
  - Read `config.py`, `strategy.py`, `paper_trader.py`, `main.py`.
  - Add a Tradovate execution layer.
  - Keep all existing math, tick, and 1:4 risk–reward rules intact.

