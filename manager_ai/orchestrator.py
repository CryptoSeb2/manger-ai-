"""
Manager AI orchestrator: run only the tools you select (Cursor, Manus, Market, Publish, Social).
Uses Cursor (prompts), Manus (API), and optional social posting (Twitter etc.).
"""
from pathlib import Path
from .config import OUTPUT_DIR
from .phases import ideate, build_phase, market_phase, publish_phase, social_phase
from .manus_client import is_configured

# Tools we support. User picks which to run; we run many at once.
AVAILABLE_TOOLS = ["cursor", "manus", "market", "publish", "social"]


def run(
    idea: str = "",
    stack: str = "web",
    use_manus: bool = True,
    output_dir: None | Path = None,
    instruction: str | None = None,
    tools: list[str] | None = None,
    post_social: bool = False,
    other_tools: str | None = None,
) -> dict:
    """
    Run only the selected tools. If tools is None or empty, run all.
    tools: e.g. ["cursor", "manus", "market", "publish", "social"]
    post_social: when True and "social" in tools, actually post to Twitter if configured.
    other_tools: comma-separated names (included in context; no runtime integration).
    """
    out = output_dir or OUTPUT_DIR
    out.mkdir(parents=True, exist_ok=True)
    selected = [t.strip().lower() for t in (tools or AVAILABLE_TOOLS) if t and t.strip()]
    if not selected:
        selected = list(AVAILABLE_TOOLS)
    # Normalize: allow "social_media" -> "social", "build" -> "cursor"
    tool_map = {"social_media": "social", "build": "cursor", "marketing": "market", "landing": "publish"}
    selected = [tool_map.get(t, t) for t in selected]
    selected = [t for t in selected if t in AVAILABLE_TOOLS]
    if not selected:
        selected = list(AVAILABLE_TOOLS)

    from . import config as cfg
    orig_out, orig_cursor = cfg.OUTPUT_DIR, cfg.CURSOR_PROMPTS_DIR
    cfg.OUTPUT_DIR = out
    cfg.CURSOR_PROMPTS_DIR = out / "cursor_prompts"
    try:
        return _run_impl(
            idea=idea,
            stack=stack,
            use_manus=use_manus,
            out=out,
            instruction=instruction or "",
            tools=selected,
            post_social=post_social,
            other_tools=(other_tools or "").strip() or None,
        )
    finally:
        cfg.OUTPUT_DIR, cfg.CURSOR_PROMPTS_DIR = orig_out, orig_cursor


def _run_impl(
    idea: str,
    stack: str,
    use_manus: bool,
    out: Path,
    instruction: str = "",
    tools: list[str] | None = None,
    post_social: bool = False,
    other_tools: str | None = None,
) -> dict:
    tools = tools or list(AVAILABLE_TOOLS)
    # Always need name/slug/idea for any phase
    if instruction.strip():
        idea_text = instruction.strip()
        name = " ".join(idea_text.split()[:4]) + ("..." if len(idea_text.split()) > 4 else "")
        slug = "".join(c if c.isalnum() or c in "-_" else "_" for c in name.strip().lower()).strip("_") or "project"
        ideate_result = {"name": name, "idea": idea_text, "slug": slug, "manus_task_url": None}
    else:
        ideate_result = ideate(idea=idea, use_manus=use_manus and "manus" in tools)
    name = ideate_result["name"]
    slug = ideate_result["slug"]
    idea_text = ideate_result["idea"]

    build_result = {"cursor_prompt_path": "", "cursor_prompt_preview": "", "manus_task_url": None, "command_paths": [], "command_count": 0}
    market_result = {"marketing": {"tagline": "", "blurb": "", "social_posts": [], "manus_task_url": None}, "marketing_file": ""}
    publish_result = {"landing_page_path": "", "publish_instructions_path": "", "deploy_hint": ""}
    social_result = {"platform_copy": {}, "social_file": "", "posted": [], "posting_configured": False}

    if "cursor" in tools:
        build_result = build_phase(
            business_name=name,
            idea=idea_text,
            slug=slug,
            stack=stack,
            create_manus_task=use_manus and "manus" in tools and is_configured(),
            instruction=instruction.strip() or None,
            other_tools=other_tools,
        )

    if "market" in tools:
        market_result = market_phase(
            business_name=name,
            idea=idea_text,
            slug=slug,
            use_manus=use_manus and "manus" in tools,
        )
    marketing = market_result["marketing"]

    if "publish" in tools:
        publish_result = publish_phase(
            business_name=name,
            idea=idea_text,
            slug=slug,
            tagline=marketing.get("tagline", ""),
            blurb=marketing.get("blurb", ""),
        )

    if "social" in tools:
        social_result = social_phase(
            business_name=name,
            idea=idea_text,
            slug=slug,
            tagline=marketing.get("tagline", ""),
            blurb=marketing.get("blurb", ""),
            social_posts=marketing.get("social_posts"),
            post_to_twitter=post_social,
        )

    next_steps = []
    if build_result.get("cursor_prompt_path"):
        next_steps.append(f"1. Cursor: {build_result['cursor_prompt_path']}")
    if market_result.get("marketing_file"):
        next_steps.append(f"2. Marketing: {market_result['marketing_file']}")
    if publish_result.get("landing_page_path"):
        next_steps.append(f"3. Publish: {publish_result['landing_page_path']}")
    if social_result.get("social_file"):
        next_steps.append(f"4. Social: {social_result['social_file']}")

    return {
        "business": {"name": name, "slug": slug, "idea": idea_text},
        "ideate": ideate_result,
        "build": build_result,
        "market": market_result,
        "publish": publish_result,
        "social": social_result,
        "tools_used": tools,
        "other_tools": other_tools,
        "next_steps": next_steps,
    }
