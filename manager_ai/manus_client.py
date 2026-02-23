"""Manus API client for task creation and goal decomposition."""
import requests
from typing import Optional, Any
from .config import MANUS_API_KEY, MANUS_BASE_URL


def is_configured() -> bool:
    return bool(MANUS_API_KEY)


def create_task(
    prompt: str,
    task_mode: str = "agent",
    agent_profile: str = "manus-1.6",
    project_id: Optional[str] = None,
) -> dict[str, Any]:
    """Create a Manus AI task. Requires MANUS_API_KEY in .env."""
    if not MANUS_API_KEY:
        return {"error": "MANUS_API_KEY not set. Add it to .env to use Manus."}
    url = f"{MANUS_BASE_URL.rstrip('/')}/v1/tasks"
    payload = {
        "prompt": prompt,
        "taskMode": task_mode,
        "agentProfile": agent_profile,
    }
    if project_id:
        payload["projectId"] = project_id
    resp = requests.post(
        url,
        json=payload,
        headers={"Authorization": f"Bearer {MANUS_API_KEY}", "Content-Type": "application/json"},
        timeout=60,
    )
    if not resp.ok:
        return {"error": resp.text or f"HTTP {resp.status_code}"}
    return resp.json()


def decompose_goal(goal: str) -> dict[str, Any]:
    """Ask Manus to decompose a goal into steps (via a task)."""
    prompt = f"""Decompose this business goal into clear, actionable steps. List each step as a numbered item. Goal: {goal}"""
    return create_task(prompt, task_mode="agent")
