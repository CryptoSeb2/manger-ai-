# Institutional Activity Detector — Guide

This indicator uses **every practical proxy available in TradingView** (no order flow or exchange data) to detect when **big banks and institutions** are likely moving the market.

---

## What It Detects (6 Types + Composite)

| Signal | What it means |
|--------|----------------|
| **SWEEP LOW / LONG** | Price wicked below support (liquidity grab) then closed back up → possible reversal long. |
| **SWEEP HIGH / SHORT** | Price wicked above resistance then closed back down → possible reversal short. |
| **BUY PRESSURE** | Big volume bar with close > open (buying) and pressure above recent average. |
| **SELL PRESSURE** | Big volume bar with close < open (selling) and pressure above recent average. |
| **VWAP REVERT LONG/SHORT** | Price was extended away from VWAP, now back inside deviation band (institutions often mean-revert to VWAP). |
| **RANGE EXP** | Bar range ≥ 2× ATR with volume — possible institutional breakout/impulse. |
| **ABSORPTION** | High volume but very small range (narrow candle) — possible absorption at a level. |
| **BANKS ACTIVE** | Two or more of the above on the same bar during a key session (composite). |

---

## What’s on the Chart

- **Red / green lines** — Liquidity levels (support/resistance): rolling, session, or ORB.
- **Yellow line** — VWAP; faint bands = VWAP ± 1 ATR (deviation).
- **Purple background** — Key session times (NY, London, 10am fix, optional afternoon).
- **Labels** — NY OPEN, LONDON, 10AM FIX at session start; SWEEP LOW/HIGH, BUY/SELL PRESSURE, VWAP REVERT, RANGE EXP, ABSORPTION, BANKS ACTIVE when conditions hit.
- **Arrows** — Green up = sweep low; red down = sweep high; purple diamond = BANKS ACTIVE.

---

## Inputs (What You Can Tune)

- **Levels:** Rolling (last N bars), Session (today H/L), or ORB (8:00–8:15 AM).
- **Sweeps:** Min wick size (% of ATR), require close back inside.
- **Volume:** MA length, “surge” multiplier; pressure lookback for extreme buy/sell bar.
- **VWAP:** Show bands, “extended” distance (ATR), signal when price returns to VWAP.
- **Times:** Which sessions to highlight (NY, London, 10am fix, afternoon); label session opens.
- **Range expansion:** Bar range ≥ ATR × multiplier.
- **Absorption:** “Narrow” range (ATR ×) + “high” volume (MA ×).
- **Composite:** Min number of signals (2–5) to show BANKS ACTIVE.

---

## How to Use It

1. Add **Institutional_Activity_Detector** to your chart (5m or 15m works well).
2. Use **key times** (NY, London, Fix) as when institutions are most active.
3. **Sweeps** = trade the reversal (long below support, short above resistance) with a stop beyond the wick.
4. **BUY/SELL PRESSURE** = confirm direction with volume; don’t fade strong one-sided pressure unless you see a sweep.
5. **VWAP REVERT** = consider longs when price comes back to VWAP from below, shorts from above.
6. **RANGE EXP** = possible start of a trend move; look for continuation or pullback to VWAP/levels.
7. **ABSORPTION** = possible accumulation/distribution; next bar direction often matters.
8. **BANKS ACTIVE** = multiple signals in one bar; good time to watch for entries that align with your plan.

---

## Alerts

You can set TradingView alerts on:

- **Sweep Low** — Institutional-style long setup.
- **Sweep High** — Institutional-style short setup.
- **Banks Active** — Multiple institutional signals on one bar.
- **Buy Pressure** / **Sell Pressure** — Extreme volume pressure.

---

## Limitations

- No real order flow, dark pool, or CME footprint — only price, volume, and time.
- “Institutional” here means **patterns that tend to appear when big players are active** (sweeps, VWAP, volume, key times), not proof of who traded.
- Best used with your **daily predictor** and **risk rules** (stops, targets, size).

Use this to **see** when the market is behaving in an institutional way; combine with **Bank_Move_Strategy** to backtest sweep-only entries, or trade manually using the full set of signals.
