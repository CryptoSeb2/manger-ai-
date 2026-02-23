from dataclasses import dataclass
from datetime import datetime, timedelta, date
from typing import List

import requests
from textblob import TextBlob

from config import (
    NEWS_API_KEY,
    NEWS_ENDPOINT,
    NEWS_LOOKBACK_HOURS,
    NEWS_KEYWORDS,
    FMP_API_KEY,
    FMP_ECON_CALENDAR_ENDPOINT,
    MAJOR_EVENT_KEYWORDS,
)


@dataclass
class NewsSignal:
    sentiment: float          # -1 .. +1
    has_major_event: bool
    headlines: List[str]
    events: List[str]


def _fetch_headlines(keywords: List[str]) -> List[str]:
    if not NEWS_API_KEY:
        return []

    q = " OR ".join(keywords)
    to_time = datetime.utcnow()
    from_time = to_time - timedelta(hours=NEWS_LOOKBACK_HOURS)

    params = {
        "q": q,
        "from": from_time.isoformat(timespec="seconds") + "Z",
        "to": to_time.isoformat(timespec="seconds") + "Z",
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 50,
        "apiKey": NEWS_API_KEY,
    }

    try:
        resp = requests.get(NEWS_ENDPOINT, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        articles = data.get("articles", [])
        titles = [a.get("title", "") or "" for a in articles]
        return titles
    except Exception as e:
        print(f"[news] Error fetching headlines: {e}")
        return []


def _sentiment_score(headlines: List[str]) -> float:
    if not headlines:
        return 0.0
    scores: List[float] = []
    for h in headlines:
        h = h.strip()
        if not h:
            continue
        try:
            s = TextBlob(h).sentiment.polarity  # -1..+1
            scores.append(s)
        except Exception:
            continue
    if not scores:
        return 0.0
    return float(sum(scores) / len(scores))


def _fetch_fmp_events(day: date) -> List[str]:
    if not FMP_API_KEY:
        return []

    day_str = day.isoformat()
    params = {
        "from": day_str,
        "to": day_str,
        "apikey": FMP_API_KEY,
    }

    try:
        resp = requests.get(FMP_ECON_CALENDAR_ENDPOINT, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        events = [str(item.get("event", "")) for item in data]
        return events
    except Exception as e:
        print(f"[news] Error fetching FMP economic calendar: {e}")
        return []


def _detect_major_event_from_events(events: List[str]) -> bool:
    text = " ".join(events).lower()
    return any(k.lower() in text for k in MAJOR_EVENT_KEYWORDS)


def _detect_major_event_from_headlines(headlines: List[str]) -> bool:
    text = " ".join(headlines).lower()
    return any(k.lower() in text for k in MAJOR_EVENT_KEYWORDS)


def fetch_news_signal(asset: str) -> NewsSignal:
    """
    Combine NewsAPI headlines + FMP economic calendar into a single signal.
    """
    keywords = NEWS_KEYWORDS.get(asset.lower(), [])
    headlines = _fetch_headlines(keywords)
    sentiment = _sentiment_score(headlines)

    today = datetime.utcnow().date()
    events = _fetch_fmp_events(today)

    has_major = _detect_major_event_from_events(events) or _detect_major_event_from_headlines(headlines)

    return NewsSignal(
        sentiment=sentiment,
        has_major_event=has_major,
        headlines=headlines,
        events=events,
    )

