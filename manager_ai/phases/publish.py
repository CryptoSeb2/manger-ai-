"""Publish phase: generate a static landing page and deploy instructions."""
from pathlib import Path
from .. import config


def publish_phase(
    business_name: str,
    idea: str,
    slug: str,
    tagline: str = "",
    blurb: str = "",
) -> dict:
    """
    Generate a static landing page (HTML) and a PUBLISH.md with deploy steps.
    """
    out_dir = config.OUTPUT_DIR / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    tagline = tagline or f"{business_name} — {idea[:60]}"
    blurb = blurb or idea
    html = _landing_page_html(business_name, tagline, blurb)
    index_path = out_dir / "index.html"
    index_path.write_text(html, encoding="utf-8")
    publish_md = _publish_md(slug, business_name)
    publish_path = out_dir / "PUBLISH.md"
    publish_path.write_text(publish_md, encoding="utf-8")
    return {
        "landing_page_path": str(index_path),
        "publish_instructions_path": str(publish_path),
        "deploy_hint": "Upload the folder to Vercel/Netlify or any static host, or use the same folder in Cursor to deploy.",
    }


def _landing_page_html(name: str, tagline: str, blurb: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{name}</title>
  <style>
    :root {{ font-family: system-ui, sans-serif; line-height: 1.6; color: #1a1a1a; }}
    body {{ max-width: 640px; margin: 0 auto; padding: 2rem; }}
    h1 {{ font-size: 1.75rem; margin-bottom: 0.5rem; }}
    .tagline {{ color: #555; font-size: 1.1rem; margin-bottom: 1.5rem; }}
    .cta {{ display: inline-block; background: #1a1a1a; color: #fff; padding: 0.75rem 1.5rem; text-decoration: none; border-radius: 8px; margin-top: 1rem; }}
    .cta:hover {{ opacity: 0.9; }}
  </style>
</head>
<body>
  <h1>{name}</h1>
  <p class="tagline">{tagline}</p>
  <p>{blurb}</p>
  <a class="cta" href="#contact">Get started</a>
  <section id="contact" style="margin-top: 2rem;">
    <h2>Contact</h2>
    <p>Reach out to get early access or ask questions.</p>
  </section>
</body>
</html>
"""


def _publish_md(slug: str, business_name: str) -> str:
    return f"""# Publish {business_name} online

## Option 1: Vercel (recommended)
1. Push this folder to a GitHub repo.
2. Go to [vercel.com](https://vercel.com) → Import project → select the repo.
3. Root directory: `{slug}` (or the folder containing `index.html`). Deploy.

## Option 2: Netlify
1. Drag the folder containing `index.html` to [app.netlify.com/drop](https://app.netlify.com/drop), or connect a Git repo.

## Option 3: GitHub Pages
1. Create a repo, push this folder. In Settings → Pages, set source to main branch and root (or /docs if you put files in docs/).

## Option 4: Use Cursor to build a full app
Use the Cursor prompt in `manager_ai_output/cursor_prompts/{slug}/build_in_cursor.md` to build a full app, then deploy that project to Vercel/Netlify.
"""
