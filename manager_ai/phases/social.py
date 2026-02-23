"""
Social phase: generate platform-specific posts (Twitter, LinkedIn, Facebook, Instagram)
and optionally post to Twitter (X) when API keys are set.
"""
from pathlib import Path
from .. import config
from ..social_client import (
    PLATFORMS,
    share_url_twitter,
    share_url_linkedin,
    share_url_facebook,
    post_tweet,
    is_posting_configured,
)


def _truncate(s: str, n: int) -> str:
    return (s[: n - 3] + "...") if len(s) > n else s


def social_phase(
    business_name: str,
    idea: str,
    slug: str,
    tagline: str = "",
    blurb: str = "",
    social_posts: list[str] | None = None,
    post_to_twitter: bool = False,
) -> dict:
    """
    Generate platform-specific copy and share URLs; optionally post to Twitter.
    social_posts: optional list of pre-written posts (e.g. from market phase); else we generate from idea/tagline.
    """
    out_dir = config.OUTPUT_DIR / slug
    out_dir.mkdir(parents=True, exist_ok=True)

    posts = social_posts or [
        f"Introducing {business_name}. {_truncate(idea, 100)}",
        f"New: {business_name}. Built to make your workflow simpler. Try it today.",
        f"Launch: {business_name}. {_truncate(idea, 80)}",
    ]
    # Ensure tweet-length for Twitter
    twitter_posts = [_truncate(p, 280) for p in posts]

    # Per-platform copy (same content adapted by length / style)
    platform_copy = {
        "twitter": [{"text": t, "share_url": share_url_twitter(t)} for t in twitter_posts],
        "linkedin": [
            {"text": f"{tagline or business_name}\n\n{blurb or idea[:300]}", "share_url": share_url_linkedin("")}
        ],
        "facebook": [
            {"text": f"{business_name}\n\n{blurb or idea[:200]}", "share_url": share_url_facebook(quote=tagline or business_name)}
        ],
        "instagram": [
            {"text": f"{tagline or business_name}\n\n{blurb or idea[:200]}\n\n#launch #startup", "share_url": "https://www.instagram.com/"}
        ],
    }

    # Optional: actually post to Twitter
    posted = []
    if post_to_twitter and is_posting_configured() and twitter_posts:
        for i, text in enumerate(twitter_posts[:3]):  # max 3 tweets per run
            r = post_tweet(text)
            if r.get("ok"):
                posted.append({"platform": "twitter", "text": text, "id": r.get("id", "")})
            else:
                posted.append({"platform": "twitter", "text": text, "error": r.get("error", "Unknown error")})

    # Write files
    social_file = out_dir / "social_posts.md"
    lines = [
        f"# {business_name} — Social posts",
        "",
        "## Twitter (X)",
    ]
    for i, p in enumerate(platform_copy["twitter"], 1):
        lines.append(f"{i}. {p['text']}")
        lines.append(f"   [Post on Twitter]({p['share_url']})")
        lines.append("")
    lines.extend(["## LinkedIn", "1. " + platform_copy["linkedin"][0]["text"][:200] + "...", f"   [Share on LinkedIn]({platform_copy['linkedin'][0]['share_url']})", ""])
    lines.extend(["## Facebook", "1. " + platform_copy["facebook"][0]["text"][:200] + "...", f"   [Share on Facebook]({platform_copy['facebook'][0]['share_url']})", ""])
    lines.extend(["## Instagram", "1. (Caption) " + platform_copy["instagram"][0]["text"][:150] + "...", ""])
    if posted:
        lines.extend(["## Posted (this run)", ""])
        for p in posted:
            if "error" in p:
                lines.append(f"- Twitter: error — {p['error']}")
            else:
                lines.append(f"- Twitter: posted (id {p.get('id', '')})")
    social_file.write_text("\n".join(lines), encoding="utf-8")

    return {
        "platform_copy": platform_copy,
        "social_file": str(social_file),
        "posted": posted,
        "posting_configured": is_posting_configured(),
    }
