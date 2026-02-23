# Math in the Trading Bot – Explained

This document explains every mathematical concept and formula used in the bot.

---

## 1. Volume

### Volume ratio

- **What:** Current day's volume divided by the **average volume** over the last N days (e.g. 20).
- **Formula:**  
  `volume_ratio = today_volume / average(volume, last N days)`
- **Use:** The bot only acts when `volume_ratio >= VOLUME_MIN_RATIO` (e.g. 1.0). That means "today's volume is at least as big as the recent average," so moves are backed by volume.

### On-Balance Volume (OBV)

- **What:** A cumulative line that adds volume on "up" days and subtracts it on "down" days.
- **Rule:**
  - If today's close **>** yesterday's close → add today's volume to OBV.
  - If today's close **<** yesterday's close → subtract today's volume from OBV.
- **Formula (per day):**  
  `direction = +1 if close > prev_close else -1`  
  `OBV = cumulative_sum(volume × direction)`
- **Use:** OBV is compared to its own moving average (e.g. 10-day). **OBV > OBV_MA** → accumulation (bullish). **OBV < OBV_MA** → distribution (bearish). The bot uses this to confirm trend.

---

## 2. Rate of Change (ROC)

- **What:** How much price changed over the last N days, as a fraction.
- **Formula:**  
  `ROC = (close_now - close_N_days_ago) / close_N_days_ago`
- **Example:** If price was 100 and is now 105, ROC = 0.05 (5% up).
- **Use:** **ROC ≥ 0** → upward momentum (can allow BUY). **ROC ≤ 0** → downward momentum (can trigger SELL). Thresholds are set by `ROC_BUY_MIN` and `ROC_SELL_MAX`.

---

## 3. Bollinger Bands

- **What:** A middle line (moving average) and two bands that widen when volatility is high.
- **Formulas:**  
  `middle = average(close, last N days)`  
  `std = standard_deviation(close, last N days)`  
  `upper = middle + k × std`  
  `lower = middle - k × std`  
  (N and k are e.g. 20 and 2.)
- **Use:** The bot can require **price > lower band** before BUY (`REQUIRE_ABOVE_LOWER_BAND`), so it doesn't buy when price is far below the recent average (oversold / high volatility).

---

## 4. RSI (Relative Strength Index)

- **What:** An oscillator 0–100 that measures how much of the recent move was "up" vs "down."
- **Steps:**
  1. For each day: `change = close - prev_close`
  2. `gain = change` when change > 0, else 0  
     `loss = -change` when change < 0, else 0
  3. Over the last N days (e.g. 14):  
     `avg_gain = average(gains)`  
     `avg_loss = average(losses)`
  4. `RS = avg_gain / avg_loss`  
     `RSI = 100 - 100/(1 + RS)`
- **Use:** **RSI > 70** → overbought (don't buy; can sell). **RSI < 30** → oversold (don't buy falling knife; can sell). The bot only buys when RSI is between 30 and 70.

---

## 5. MACD (Moving Average Convergence Divergence)

- **What:** Two lines: "MACD line" (difference of two EMAs) and "signal line" (EMA of that difference).
- **Formulas:**  
  `EMA_fast = exponential_average(close, span=12)`  
  `EMA_slow = exponential_average(close, span=26)`  
  `MACD_line = EMA_fast - EMA_slow`  
  `signal_line = exponential_average(MACD_line, span=9)`
- **Use:** **MACD line > signal line** → short-term trend is bullish (allow BUY). **MACD line < signal line** → bearish (trigger SELL). So the math is "fast trend minus slow trend," smoothed again.

---

## 6. ADX (Average Directional Index)

- **What:** Measures **strength of trend** (0–100), not direction. Above ~20–25 means "trending"; below means "choppy."
- **Steps:**

  1. **True Range (TR)** – biggest of:
     - today's high − today's low  
     - |today's high − yesterday's close|  
     - |today's low − yesterday's close|  
     `TR = max(high - low, |high - prev_close|, |low - prev_close|)`

  2. **Directional movement**
     - `+DM = today_high - yesterday_high` (only if positive and > −DM; else 0)
     - `-DM = yesterday_low - today_low` (only if positive and > +DM; else 0)

  3. **Smoothed over N days (e.g. 14):**
     - `ATR = average(TR)`
     - `+DI = 100 × average(+DM) / ATR`
     - `-DI = 100 × average(-DM) / ATR`

  4. **Directional Index and ADX:**
     - `DX = 100 × |+DI - -DI| / (+DI + -DI)`
     - `ADX = average(DX)` over the same N days

- **Use:** The bot only **BUY** when **ADX > 20** (or your `ADX_MIN`), so it avoids trading in weak/choppy trends.

---

## 7. Money Flow Index (MFI)

- **What:** Like RSI, but uses **volume-weighted** price moves. Scale 0–100; overbought > 80, oversold < 20.
- **Steps:**
  1. **Typical price:**  
     `typical = (high + low + close) / 3`
  2. **Raw money flow:**  
     `raw_mf = typical × volume`
  3. Over the last N days (e.g. 14):
     - On "up" days (typical > yesterday): add `raw_mf` to **positive flow**
     - On "down" days: add `raw_mf` to **negative flow**
  4. `money_ratio = positive_flow / negative_flow`  
     `MFI = 100 - 100/(1 + money_ratio)`
- **Use:** Same idea as RSI: only buy when MFI is between 20 and 80; sell when MFI ≥ 80 or ≤ 20. The extra math is "weight by volume."

---

## 8. Stochastic Oscillator

- **What:** Where the current close sits inside the last N days' high–low range. Output 0–100.
- **Formulas (over last N days, e.g. 14):**  
  `lowest_low = min(low)`  
  `highest_high = max(high)`  
  `%K = 100 × (close - lowest_low) / (highest_high - lowest_low)`  
  `%D = average(%K, last 3 days)` (smoothing)
- **Use:** **%K > 80** → price near top of range (overbought). **%K < 20** → near bottom (oversold). The bot only buys when Stochastic is between 20 and 80; sells when ≥ 80 or ≤ 20.

---

## 9. Price Z-Score

- **What:** How many **standard deviations** the current price is from its recent average.
- **Formula (over last N days, e.g. 20):**  
  `mean = average(close)`  
  `std = standard_deviation(close)`  
  `z = (close_now - mean) / std`
- **Use:** **z > 2** → price far above mean (don't chase). **|z| > 2** → extreme (take profit or cut loss). So the math is standard "normalized distance from average."

---

## 10. ATR (Average True Range) and Position Sizing

- **What:** ATR measures **volatility** as the average of "true range" over N days. True Range is the same as in ADX: max of (high−low, |high−prev_close|, |low−prev_close|).
- **Formula:**  
  `TR = max(high - low, |high - prev_close|, |low - prev_close|)`  
  `ATR = average(TR, last N days)`
- **Use in sizing:**  
  `ratio = ATR_average_long_term / ATR_current`  
  - When **volatility is high**, ATR_current is large → ratio < 1 → position size is **reduced**.  
  - When **volatility is low**, ratio can be > 1; the bot caps it at `ATR_SIZING_CAP` (e.g. 1.5) so you don't oversize.  
  So: **same formula (ATR), used to scale risk** by reducing size when the market is wild.

---

## 11. News Sentiment (Not Pure Math)

- **What:** Headlines are scored with **keyword lists**: positive words (e.g. "surge," "beat," "growth") and negative words (e.g. "fall," "miss," "fraud").
- **Formula:**  
  `score = (positive_count - negative_count) / total_keywords`  
  then normalized to about **-1 to +1**.
- **Use:** BUY only when sentiment ≥ your threshold; SELL when sentiment is very negative (e.g. ≤ -0.5). So the "math" is counting and normalizing.

---

## Summary Table

| Name        | Main idea                         | Formula (concept)                          |
|------------|------------------------------------|--------------------------------------------|
| Volume ratio | Today vs average volume           | `vol / mean(vol)`                          |
| OBV        | Cumulative ± volume by direction   | `cumsum(vol × sign(close - prev_close))`   |
| ROC        | Percent change over N days        | `(close - close_N) / close_N`              |
| Bollinger  | Mean ± k × std                     | `mid ± k*std(close)`                       |
| RSI        | Gain vs loss over N days          | `100 - 100/(1 + avg_gain/avg_loss)`       |
| MACD       | Fast EMA − slow EMA, then signal   | `EMA12 - EMA26`, signal = EMA9 of that    |
| ADX        | Trend strength from +DM, −DM, TR  | DX smoothed → ADX                         |
| MFI        | Volume-weighted RSI               | Same as RSI with `typical×volume`          |
| Stochastic | Close in N-day range              | `100*(close - low_N)/(high_N - low_N)`    |
| Z-Score    | Distance from mean in std units   | `(close - mean) / std`                     |
| ATR        | Average true range                | `mean(TR)`; TR = max(high-low, …)         |

All of these are standard in technical analysis; the bot just combines them with your volume and news rules to decide BUY / SELL / HOLD.
