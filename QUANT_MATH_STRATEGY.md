# Quant Math Strategy — The Math Behind It

This strategy packs in the **kinds of math** used in quant trading (e.g. Jane Street–style): probability, statistics, regression, multi-factor scoring, reversion speed, volatility regime, and optional confirmation.

---

## 1. Probability & Statistics

- **Z-Score:** `z = (price - mean) / σ` over the last N bars.
- **Role:** Measures how many standard deviations price is from its mean. |z| > 2 ≈ statistical extreme → mean reversion edge.
- **In the strategy:** Long when `z < -z_long`, short when `z > z_short`.

---

## 2. Linear Regression (Equilibrium + Drift)

- **Regression line:** `reg = ta.linreg(close, length, 0)` = “fair value” / equilibrium.
- **Slope (drift):** `slope = reg(0) - reg(1)` ≈ instantaneous trend (like drift in a stochastic model).
- **Role:** Equilibrium = level price tends to revert to; slope = trend filter (e.g. only long when drift is not strongly down).
- **In the strategy:** Optional “drift” filter: long when slope is rising or positive, short when slope is falling or negative.

---

## 3. Stochastic-Style: Normalized Deviation

- **Formula:** `dev_norm = (close - reg) / ATR`.
- **Role:** Same idea as “(price - equilibrium) / volatility” in stochastic models. ATR = volatility proxy (diffusion).
- **In the strategy:** Optional filter: long when price is below regression (dev_norm < 0), short when above.

---

## 4. Reversion Speed (Mean Reversion in Progress)

- **Idea:** In mean reversion, “deviation from mean” should start shrinking before we enter.
- **Formula:** `dev_from_mean = close - mean`, `delta_dev = dev_from_mean - dev_from_mean[1]`. For a long: we want price below mean and `delta_dev > 0` (deviation becoming less negative = moving toward mean).
- **Simpler version in script:** Z improving: for long `z < 0` and `z > z[1]` (oversold but less extreme).
- **In the strategy:** Optional “reversion speed” filter so we enter when the move is already starting to revert.

---

## 5. Momentum (Rate of Change)

- **ROC:** `(close - close[k]) / close[k] × 100`.
- **Role:** Momentum exhaustion — when ROC stops making new extremes and turns, often lines up with short-term reversals.
- **In the strategy:** Optional: long when ROC is turning up or positive, short when turning down or negative.

---

## 6. Multi-Factor Score (Linear Algebra)

- **Idea:** Combine several signals into one number: `score = w1×f1 + w2×f2 + w3×f3`.
- **Factors:**  
  - Long: f_z = -z (positive when oversold), f_dev = -dev_norm (positive when below reg), f_roc = 1 if momentum up else 0.  
  - Short: f_z = z, f_dev = dev_norm, f_roc = 1 if momentum down else 0.
- **In the strategy:** Optional threshold: only trade when `score_long ≥ score_min_long` or `score_short ≥ score_min_short`. Lets you tune “how strong” the combo must be.

---

## 7. Volatility Regime

- **Idea:** Only trade when volatility is in a “normal” band (not dead, not chaotic).
- **Formula:** `ATR / MA(ATR)` in [atr_min_mult, atr_max_mult] (e.g. 0.6–2.5).
- **In the strategy:** Optional filter so we skip very low or very high vol regimes.

---

## 8. Two-Bar Confirmation (Bayesian-Style)

- **Idea:** Reduce false positives by requiring a “confirming” bar after the first signal.
- **Rule:** Bar 1 had extreme z (e.g. z < -2). Bar 2: close > open and close > close[1] (bullish bar and higher close).
- **In the strategy:** Optional “Two-bar confirmation” — fewer but higher-quality signals.

---

## 9. Volume

- **Rule:** `volume ≥ MA(volume)`.
- **Role:** Simple “information” filter — only take the math signal when volume supports it.

---

## Risk

- Stop = entry ± **1.5 × ATR** (configurable).
- Target = **2 × R** (R = distance to stop).
- Max **3 long** and **3 short** per day (configurable).

---

## How to Use

1. Add **Quant Math Strategy** to the chart and run **Strategy Tester**.
2. Turn inputs on/off to see the effect of each math block (e.g. turn off score, then on; turn on two-bar confirmation).
3. Tune **weights** and **score_min** for long/short to optimize (or use TradingView’s optimizer on a few key inputs).

This gives you one strategy that uses **probability, statistics, regression, normalized deviation, reversion speed, momentum, multi-factor score, volatility regime, and optional confirmation** — all in one place.
