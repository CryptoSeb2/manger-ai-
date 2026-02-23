"""Market phase: generate marketing copy, taglines, and social posts."""
from pathlib import Path
from .. import config
from ..manus_client import create_task, is_configured


def market_phase(
    business_name: str,
    idea: str,
    slug: str,
    use_manus: bool = True,
) -> dict:
    """
    Generate marketing assets: tagline, short blurb, 3 social posts.
    Optionally delegates to Manus for richer copy.
    """
    out_dir = config.OUTPUT_DIR / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    tagline = f"{business_name} — {idea[:60]}{'...' if len(idea) > 60 else ''}"
    blurb = (
        f"{business_name} helps you get results fast. {idea}\n\n"
        "Sign up or get in touch to get started."
    )
    posts = [
        f"Introducing {business_name}. {idea[:100]}...",
        f"New: {business_name}. Built to make your workflow simpler. Try it today.",
        f"Launch: {business_name}. {idea[:80]}...",
    ]
    if use_manus and is_configured():
        task = create_task(
            f"Write marketing copy for this business. Business name: {business_name}. Description: {idea}. "
            "Provide: 1) One punchy tagline (under 15 words), 2) One short paragraph for a landing page, "
            "3) Three tweet-length social posts (each under 280 chars) for launch."
        )
        if "error" not in task:
            # We still save our defaults; user can get full copy from Manus task
            manus_url = task.get("task_url")
        else:
            manus_url = None
    else:
        manus_url = None
    marketing = {
        "tagline": tagline,
        "blurb": blurb,
        "social_posts": posts,
        "manus_task_url": manus_url,
    }
    # Write to file
    marketing_file = out_dir / "marketing_copy.txt"
    lines = [
        f"# {business_name} — Marketing copy",
        "",
        "## Tagline",
        tagline,
        "",
        "## Landing blurb",
        blurb,
        "",
        "## Social posts",
    ]
    for i, p in enumerate(posts, 1):
        lines.append(f"{i}. {p}")
    if manus_url:
        lines.extend(["", "## Full copy from Manus", manus_url])
    marketing_file.write_text("\n".join(lines), encoding="utf-8")
    return {"marketing": marketing, "marketing_file": str(marketing_file)}
