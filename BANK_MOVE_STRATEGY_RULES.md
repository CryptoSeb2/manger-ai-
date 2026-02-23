# Bank Move Strategy — How It Works

This strategy tries to **copy how banks move the markets** by detecting **liquidity sweeps** (stop hunts) and signaling the reversal.

---

## The idea

- **Banks / institutions** often push price through obvious levels (recent highs/lows, session high/low, ORB) to trigger **retail stops**.
- After that **liquidity grab**, price often **reverses** in the opposite direction.
- The strategy **signals when that happens**: LONG after a sweep of the low, SHORT after a sweep of the high.

---

## What counts as a “bank move” (sweep)

1. **Liquidity level**  
   A level where stops are assumed (you choose):
   - **Rolling** = last N bars’ high/low (default 20).
   - **Session** = today’s high/low.
   - **ORB** = 8:00–8:15 AM NY range high/low.

2. **Sweep**  
   - **Sweep high (SHORT):** Price **wicks above** the level then **closes back below** (rejection).
   - **Sweep low (LONG):** Price **wicks below** the level then **closes back above** (rejection).

3. **Filters**  
   - **Time:** Only in selected sessions (e.g. NY 8–11 AM, London, 10 AM fix, afternoon).
   - **Volume:** Bar volume ≥ MA(volume).
   - **ATR:** ATR ≥ average (avoid dead markets).

---

## Default settings

| Setting | Default | Meaning |
|--------|--------|--------|
| Level source | Rolling | Use last 20-bar high/low as liquidity |
| Lookback | 20 | Bars for rolling high/low |
| Require close back inside | ON | Must close back inside range (rejection) |
| Key times | NY 8–11 AM | Only signal in this window |
| Volume filter | ON | Volume ≥ MA(20) |
| Stop | Beyond wick | Stop beyond the sweep wick |
| Target | 2R | Take profit at 2× risk |

---

## How to use

1. **TradingView:** Add **Bank_Move_Strategy.pine** to a chart (5m or 15m works well).
2. **Backtest:** Use Strategy Tester for win rate, drawdown, profit factor.
3. **Key times:** Turn on “Only signal during key session times” and choose NY, London, 10 AM fix, or afternoon.
4. **Levels:** Use **Rolling** for any market; use **Session** or **ORB (8am)** for a fixed daily range.

---

## When you get a signal

- **Green triangle (long):** Price swept below support (liquidity grab) then closed back up → possible bounce.
- **Red triangle (short):** Price swept above resistance then closed back down → possible drop.

Stop is placed beyond the sweep wick (or ATR-based); target is 2× that risk (2R) by default.

---

## Why “banks move the market”

This is a **retail narrative**: institutions are said to run stops at obvious levels, then reverse. The strategy does **not** see order flow or bank books; it only detects **price action** (wick beyond level + close back). So “bank move” here means: *a liquidity-sweep style move that often reverses* — useful as a label, not as proof of who traded.

Use it as a **reversal-after-sweep** strategy; tune levels and times to your instrument and session.
