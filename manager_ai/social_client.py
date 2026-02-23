"""
Social media: generate platform-specific copy, share URLs, and optionally post to Twitter (X).
Add API keys in .env to enable posting; otherwise we only generate copy and share links.
"""
import urllib.parse
from . import config


# Platform names we support for copy + share links (and posting where implemented)
PLATFORMS = ["twitter", "linkedin", "facebook", "instagram"]


def share_url_twitter(text: str) -> str:
    """URL to open Twitter compose with pre-filled text (user posts manually)."""
    return "https://twitter.com/intent/tweet?" + urllib.parse.urlencode({"text": text})


def share_url_linkedin(comment: str, url: str = "") -> str:
    """LinkedIn share URL. Does not pre-fill text; user pastes. Optional url to share."""
    if url:
        return "https://www.linkedin.com/sharing/share-offsite/?" + urllib.parse.urlencode({"url": url})
    return "https://www.linkedin.com/feed/"


def share_url_facebook(url: str = "", quote: str = "") -> str:
    """Facebook share URL. quote = pre-filled text if supported."""
    base = "https://www.facebook.com/sharer/sharer.php"
    if url:
        return base + "?" + urllib.parse.urlencode({"u": url})
    if quote:
        return base + "?" + urllib.parse.urlencode({"quote": quote})
    return base


def post_tweet(text: str) -> dict:
    """
    Post a tweet via Twitter API v2 (OAuth 1.0a).
    Returns {"ok": True, "id": "..."} or {"ok": False, "error": "..."}.
    """
    if not config.social_twitter_configured():
        return {"ok": False, "error": "Twitter API keys not set in .env"}
    try:
        import requests
        from requests_oauthlib import OAuth1
    except ImportError:
        return {"ok": False, "error": "Install requests and requests_oauthlib: pip install requests requests-oauthlib"}

    auth = OAuth1(
        config.TWITTER_API_KEY,
        config.TWITTER_API_SECRET,
        config.TWITTER_ACCESS_TOKEN,
        config.TWITTER_ACCESS_SECRET,
    )
    url = "https://api.twitter.com/2/tweets"
    payload = {"text": text[:280]}
    resp = requests.post(url, json=payload, auth=auth, timeout=15)
    if resp.status_code in (200, 201):
        data = resp.json()
        return {"ok": True, "id": data.get("data", {}).get("id", "")}
    try:
        err = resp.json()
        msg = err.get("detail", str(err))
    except Exception:
        msg = resp.text or resp.reason
    return {"ok": False, "error": f"Twitter API {resp.status_code}: {msg}"}


def is_posting_configured() -> bool:
    """True if at least one platform can post (e.g. Twitter keys set)."""
    return config.social_twitter_configured()
