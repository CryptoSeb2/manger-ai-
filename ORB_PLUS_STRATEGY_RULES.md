# ORB+ Strategy — Rules & How to Use

A simple, rule-based strategy: **8:00 AM opening range breakout** + **trend filter** + **volume**, with clear stop and target.

---

## What It Is

- **ORB:** 8:00–8:15 AM Eastern (one 15-minute candle). High and low of that candle = the range.
- **Entry:** Long when price breaks **above** ORB high; short when price breaks **below** ORB low.
- **Filters:** Volume above average; long only above trend EMA, short only below (optional).
- **Stop:** Opposite side of ORB (or ATR-based).
- **Target:** 2× your risk (2R), or trail after 1R (optional).

---

## How to Run It

### Option A: Backtest in TradingView

1. Open **TradingView** → chart **15m** (e.g. NQ=F, GC=F).
2. Pine Editor → paste **ORB_Plus_Strategy.pine** → Add to chart.
3. Strategy appears on chart; open **Strategy Tester** to see equity, win rate, drawdown.
4. Tweak inputs (ORB bars, EMA length, stop type, target R, trailing).

### Option B: Trade It Manually (with your predictor)

1. **Before session:** Run `python3 predict_daily.py` in `daily_predictor` folder. Note **Bias** for Gold and NQ.
2. **Filter by bias (recommended):**
   - **Bullish** → Only take **long** breakouts (ignore short).
   - **Bearish** → Only take **short** breakouts (ignore long).
   - **Range / Event** → Reduce size (e.g. half) or skip.
3. **On chart (15m):** Add the **ORB+ Strategy** or your **Volume Math** indicator with ORB (8am). Wait for ORB to form (8:00–8:15).
4. **Entry:**
   - **Long:** First 15m close **above** ORB high, with volume above average. Optional: price above 50 EMA.
   - **Short:** First 15m close **below** ORB low, with volume above average. Optional: price below 50 EMA.
5. **Stop:** Below ORB low (long) or above ORB high (short). Or 1.5× ATR from entry.
6. **Target:** 2× the distance from entry to stop (2R). Or move stop to breakeven at 1R and trail.

---

## Default Settings (in the Pine strategy)

| Setting        | Default | Meaning                          |
|----------------|--------|----------------------------------|
| ORB            | 8am, 1 bar | First 15 min = one 15m candle |
| Volume filter  | ON, 20-period MA | Require vol ≥ MA(20)      |
| Trend filter   | ON, 50 EMA | Long above EMA, short below   |
| Stop           | ORB    | Stop at opposite side of range   |
| Target         | 2R     | Take profit at 2× risk           |
| Trailing       | OFF    | Optional trail after 1R          |

---

## Best Practices

- Use on **15m chart** so the 8:00–8:15 range is exactly one candle (wick to wick).
- **One long and one short per day** (strategy does this automatically).
- Prefer **NQ** and **Gold (GC/MGC)**; same logic works on other liquid futures/index.
- Combine with your **daily predictor**: only take longs when bias is Bullish, shorts when Bearish, to improve win rate and avoid fighting the day’s bias.

---

## Quick Checklist (manual trade)

- [ ] Ran predictor → Bias = Bullish / Bearish / Range / Event  
- [ ] 15m chart, ORB (8:00–8:15) drawn  
- [ ] Price broke **above** ORB high (long) or **below** ORB low (short)  
- [ ] Volume bar above average  
- [ ] (Optional) Long above 50 EMA, short below 50 EMA  
- [ ] Entry at close of breakout bar (or next bar)  
- [ ] Stop: opposite ORB or 1.5× ATR  
- [ ] Target: 2R or trail after 1R  

This is the full ORB+ strategy you can backtest and trade with your predictor.
