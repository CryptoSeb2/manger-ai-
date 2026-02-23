"""Ideate phase: generate or validate business ideas. Can delegate to Manus."""
from pathlib import Path
from ..config import OUTPUT_DIR
from ..manus_client import create_task, is_configured


def _slug(name: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in name.strip().lower()).strip("_") or "business"


def ideate(
    idea: str = "",
    use_manus: bool = True,
) -> dict:
    """
    Ideate a business. If idea is empty and use_manus, ask Manus to suggest one.
    Returns dict with name, idea, slug, manus_task_url (if used).
    """
    result = {"name": "", "idea": "", "slug": "", "manus_task_url": None}
    if idea.strip():
        # Use provided idea; derive a short name from first few words
        result["idea"] = idea.strip()
        result["name"] = " ".join(idea.split()[:4]) + ("..." if len(idea.split()) > 4 else "")
        result["slug"] = _slug(result["name"])
        return result
    if use_manus and is_configured():
        task = create_task(
            "Suggest one concrete, actionable online business idea I can build and publish in a few weeks. "
            "Reply with: 1) Business name, 2) One-paragraph description, 3) Target audience, 4) Main deliverable (product/service)."
        )
        if "error" in task:
            result["error"] = task["error"]
            result["idea"] = "SaaS dashboard for small teams"
            result["name"] = "Team Dashboard SaaS"
            result["slug"] = _slug(result["name"])
            return result
        result["manus_task_url"] = task.get("task_url")
        result["idea"] = f"See Manus task for full idea: {result['manus_task_url']}"
        result["name"] = task.get("task_title", "New Business")
        result["slug"] = _slug(result["name"])
        return result
    # Default idea when no input and no Manus
    result["name"] = "Micro-SaaS Tool"
    result["idea"] = "A simple web app that solves one specific problem for a niche (e.g. form builder, booking widget, calculator)."
    result["slug"] = _slug(result["name"])
    return result
