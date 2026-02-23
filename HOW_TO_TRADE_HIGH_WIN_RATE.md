# How to Trade the High Win Rate Mean Reversion Indicator

## What This Indicator Does

It only gives **LONG** and **SHORT** signals when **all** of these are true:

1. **Market is in a range** (ADX below your setting, e.g. 25) — no signals in strong trends.
2. **Price is at support (for LONG) or resistance (for SHORT)** — within your “near S/R” % of the range.
3. **RSI reversal** — for LONG: RSI was oversold and crosses back above 30; for SHORT: RSI was overbought and crosses back below 70.
4. **Volume confirmation** — current bar volume ≥ your volume MA × multiplier (if enabled).

Optional: “LONG only in lower 1/3 of range, SHORT only in upper 1/3” keeps signals at the extremes.

---

## Exact Trading Rules

### When a LONG Signal Appears (green arrow + “LONG (mean reversion)” label)

1. **Confirm**
   - You are on a **range-bound** chart (price bouncing between the green Support and red Resistance lines).
   - The candle that triggered the signal **closed** (or you wait for close) so the signal is confirmed.

2. **Entry**
   - **Option A:** Enter on the **close** of the bar that shows the LONG signal.
   - **Option B:** Enter on a **limit order** at the **low of the signal bar** (or 1–2 ticks below) on the next bar.

3. **Stop loss**
   - Place stop **below the low of the signal bar** by **1–2 ATR** (e.g. 1.5 × ATR).  
   - The indicator can draw a “Long stop ref” line; use that as a **reference** and place your actual stop slightly below it, or use the signal bar’s low minus 1.5×ATR.

4. **Take profit**
   - **Target 1:** First resistance (the red line) — take part of the position.
   - **Target 2:** Middle of the range or the opposite side — move stop to breakeven and trail the rest, or exit the remainder at the red line.

5. **If price breaks below support (green line)**  
   - Treat the setup as failed. Exit or tighten stop; do not add.

---

### When a SHORT Signal Appears (red arrow + “SHORT (mean reversion)” label)

1. **Confirm**
   - Same as LONG: chart is range-bound; signal bar has closed (or you trade on close).

2. **Entry**
   - **Option A:** Enter on the **close** of the bar that shows the SHORT signal.
   - **Option B:** Enter **limit at the high of the signal bar** (or 1–2 ticks above) on the next bar.

3. **Stop loss**
   - Place stop **above the high of the signal bar** by **1–2 ATR** (e.g. 1.5 × ATR).  
   - Use the indicator’s “Short stop ref” line as reference; put your real stop just above it or at high + 1.5×ATR.

4. **Take profit**
   - **Target 1:** First support (the green line) — take part.
   - **Target 2:** Middle of range or other side — move stop to breakeven and trail, or close rest at the green line.

5. **If price breaks above resistance (red line)**  
   - Setup invalidated. Exit or tighten stop; do not add.

---

## Settings to Start With

- **Timeframe:** 5m or 15m (good balance; 1m is noisier).
- **Instruments:** Indices (e.g. NQ, ES), gold (GC/MGC), or liquid forex pairs that range often.
- **Indicator settings (defaults are fine):**
  - Support/Resistance lookback: **20**
  - Near S/R: **15%**
  - **LONG only in lower 1/3, SHORT only in upper 1/3:** ON
  - RSI: **14**, oversold **30**, overbought **70**
  - ADX max (range): **25**
  - Volume: require confirmation ON, multiplier **1.0**
  - Min bars between signals: **5**
  - ATR stop multiplier: **1.5** (for stop reference)

---

## Rules That Protect Your Win Rate

1. **Only take signals when you clearly see a range** — price oscillating between the green and red lines. If ADX is high or price is trending hard, ignore or disable the indicator for that chart.
2. **One signal at a time** — do not stack another LONG if you already have an open LONG from a previous signal (same for SHORT). Respect “min bars between signals.”
3. **Size small** — 1–2% risk per trade so a few losses don’t hurt. Mean reversion works over many trades.
4. **Session** — use on sessions with good volume (e.g. NY for NQ/ES, overlap for forex). Avoid the first 5–10 minutes after open if it’s too wild.
5. **If the range breaks** — e.g. price closes clearly above resistance or below support — stop trading that range and wait for a new one to form.

---

## Quick Checklist (LONG)

- [ ] LONG arrow + label on chart  
- [ ] Price in lower part of range (near green Support)  
- [ ] RSI crossed up from below 30  
- [ ] ADX &lt; 25 (range, not trend)  
- [ ] Volume bar decent (if requirement ON)  
- [ ] Entry: close of signal bar or limit at signal bar low  
- [ ] Stop: below signal bar low by ~1.5×ATR  
- [ ] Target: first the red Resistance line, then manage the rest  

Same logic in reverse for SHORT (price near red Resistance, RSI crossed down from 70, stop above bar, target green Support).

---

## Summary

- **Strategy:** Mean reversion only in ranges, at support/resistance, with RSI reversal and volume.
- **Entry:** On signal bar close or limit at signal bar extreme (low for LONG, high for SHORT).
- **Stop:** Beyond the signal bar by about 1.5×ATR.
- **Target:** Opposite level (support for SHORT, resistance for LONG); then trail or scale.
- **Win rate:** Aim for many small wins; cut losers quickly and avoid trading when the market is trending (ADX high) or the range has broken.
