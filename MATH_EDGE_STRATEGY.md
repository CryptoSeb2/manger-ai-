# Math Edge Strategy — Pure Math, No Narrative

This strategy uses **only mathematics** to trade: no ORB, no sweeps, no session times. Just statistics, regression, momentum, and volatility.

---

## The Math Used

| Concept | Formula / Idea | Role |
|--------|----------------|------|
| **Z-Score** | `(price - mean) / stddev` over last N bars | How many standard deviations price is from its mean. \|z\| > 2 ≈ statistical extreme → mean reversion. |
| **Linear regression** | `ta.linreg(close, length, 0)` | “Equilibrium” line; slope = trend direction. |
| **Slope** | `reg(0) - reg(1)` | Rising slope = bias up; falling = bias down. Used to confirm reversal. |
| **ROC (Rate of change)** | `(close - close[k]) / close[k] × 100` | Momentum. “ROC turning up” = exhaustion of down move. |
| **ATR** | Average True Range | Volatility. Filter: only trade when ATR is between 0.6× and 2.5× its average (avoid dead or chaotic markets). |
| **Volume** | `volume ≥ MA(volume)` | Optional confirmation. |

---

## Entry Logic (Mean Reversion)

- **Long:** Z-Score **< -2** (price ~2+ std below mean) **and** regression slope improving or positive **and** (optional) ROC turning up **and** ATR in range **and** volume ≥ MA.
- **Short:** Z-Score **> +2** **and** slope falling or negative **and** (optional) ROC turning down **and** same filters.

**Exit:** Stop = entry ± 1.5× ATR. Target = 2× that risk (2R).

---

## Why This Math?

- **Z-Score:** In normally distributed returns, ~95% of the time price is within 2 std of the mean. Beyond that, mean reversion has a statistical edge (over many trades).
- **Regression:** Gives a clean “fair value” line; trading deviation from it is a classic quant approach.
- **ROC exhaustion:** When momentum (ROC) stops making new extremes and turns, it often coincides with short-term reversals.
- **ATR filter:** Avoids very low volatility (no edge) and very high volatility (noise/whipsaw).

---

## Defaults

- Z lookback 20, thresholds ±2.
- Regression length 20; slope confirmation on.
- ROC length 5; ROC reversal on.
- ATR filter 0.6–2.5× MA(ATR).
- Volume filter on, MA(20).
- Stop 1.5× ATR, target 2R, max 3 long + 3 short per day.

---

## How to Use

1. Add **Math_Edge_Strategy** to a chart (any timeframe; 15m–1H common).
2. Run **Strategy Tester** to see win rate, profit factor, drawdown.
3. Tune: **z_long / z_short** (e.g. 2.5 = fewer, stronger extremes); **reg_len** (longer = smoother); **atr_min / atr_max** (tighter = fewer trades).

No sessions, no levels—just the numbers.
