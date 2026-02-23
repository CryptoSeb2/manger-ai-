from datetime import date

from config import SYMBOLS
from data_market import fetch_intraday
from data_news import fetch_news_signal
from features import daily_features, classify_day


def predict_for_symbol(name: str, ticker: str):
    print(f"\n=== {name.upper()} ({ticker}) ===")
    df = fetch_intraday(ticker)
    feats = daily_features(df)
    news = fetch_news_signal(name)

    summary = classify_day(
        feats,
        news_sentiment=news.sentiment,
        has_major_event=news.has_major_event,
    )

    last_trade_date = feats["today_date"]
    calendar_today = date.today()
    if last_trade_date < calendar_today:
        print(f"Date: {last_trade_date} (last trading day — market closed today/weekend)")
    else:
        print(f"Date: {last_trade_date}")
    print(f"Bias: {summary['bias']}")
    print(f"Trend slope: {summary['trend_slope']:.4f}")
    print(f"ATR hourly: {summary['atr_hourly']:.2f}")
    print(f"Vol ratio (ATR / yesterday range): {summary['vol_ratio']:.2f}")
    print(f"Return z-score: {summary['ret_zscore']:.2f}")
    print(f"Up-day freq (last 30d): {summary['up_freq']:.2f}")
    print(f"News sentiment: {news.sentiment:.2f}, major_event={news.has_major_event}")
    if news.headlines:
        print("Sample headlines:")
        for h in news.headlines[:3]:
            print("  -", h)
    if news.events:
        print("Today’s econ events (FMP):")
        for ev in news.events[:3]:
            print("  -", ev)


if __name__ == "__main__":
    for name, ticker in SYMBOLS.items():
        predict_for_symbol(name, ticker)

