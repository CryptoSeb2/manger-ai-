"""Generate Cursor-ready prompts and project scaffolds for the Build phase."""
from pathlib import Path
from . import config


def cursor_prompt_build(business_name: str, idea: str, stack: str = "web") -> str:
    """Generate a prompt you can paste into Cursor to build the product."""
    return f"""Build a complete, production-ready product for this business:

**Business name:** {business_name}
**Idea:** {idea}
**Stack preference:** {stack}

In Cursor, please:
1. Create a new project folder or use this workspace.
2. Scaffold the app (frontend + backend if needed) with a modern stack.
3. Implement core features: landing page, signup/contact, and at least one main value feature.
4. Add a simple deploy config (e.g. Vercel, Netlify, or Docker) and a README with run/deploy instructions.
5. Keep code clean, typed where applicable, and secure (no secrets in repo).
"""


def cursor_prompt_from_instruction(instruction: str, stack: str = "web", other_tools: str | None = None) -> str:
    """Generate a Cursor prompt from a freeform user instruction (manage anything)."""
    tools_line = f"\n**Tools to use if relevant:** {other_tools}\n" if other_tools else ""
    return f"""You are being managed by Manager AI. Execute this goal in full:

**Goal / instruction:**
{instruction}
{tools_line}
**Stack preference:** {stack}

Do the following in order:
1. Understand the goal and break it into concrete tasks if needed.
2. Create or use this workspace — scaffold the project if nothing exists yet.
3. Implement each part of the goal (features, refactors, pages, deploy, etc.).
4. Add a README with run/deploy instructions and keep code clean and secure.

Reply when done and say what you built or changed. If the goal is large, work through it step by step; the user can run Manager AI again for "next steps" or follow-up commands.
"""


def cursor_commands_from_instruction(instruction: str, stack: str = "web") -> list[str]:
    """Break a freeform instruction into a sequence of Cursor commands the user can run one by one."""
    # Generate a sensible sequence so the manager "keeps giving" commands
    return [
        f"**Command 1 — Setup & scope**\nIn this workspace, scope the project for this goal and scaffold if needed.\n\nGoal: {instruction}\n\nStack: {stack}. Create the project structure and list the next 2–3 concrete tasks you will do.",
        f"**Command 2 — Core work**\nContinue from the previous setup. Implement the main part of the goal.\n\nGoal: {instruction}\n\nImplement the core features or changes. Keep code clean and add a brief README.",
        f"**Command 3 — Polish & deploy**\nFinish the goal: add landing/marketing if relevant, deploy config (e.g. Vercel/Netlify), and any final polish.\n\nGoal: {instruction}\n\nEnsure the project runs and can be deployed.",
    ]


def cursor_prompt_fix_or_extend(instruction: str) -> str:
    """Generic Cursor prompt for fixes or new features."""
    return f"""In this codebase, do the following and apply the changes: {instruction}"""


def write_cursor_prompt(business_slug: str, prompt: str, filename: str = "build_in_cursor.md") -> Path:
    """Write a Cursor prompt to a file for easy copy-paste."""
    config.CURSOR_PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
    biz_dir = config.CURSOR_PROMPTS_DIR / business_slug
    biz_dir.mkdir(parents=True, exist_ok=True)
    path = biz_dir / filename
    path.write_text(prompt, encoding="utf-8")
    return path


def write_cursor_commands(business_slug: str, commands: list[str]) -> list[Path]:
    """Write a sequence of Cursor command files (command_1.md, command_2.md, ...). Returns paths."""
    config.CURSOR_PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
    biz_dir = config.CURSOR_PROMPTS_DIR / business_slug
    biz_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for i, cmd in enumerate(commands, 1):
        path = biz_dir / f"command_{i}.md"
        path.write_text(cmd, encoding="utf-8")
        paths.append(path)
    # Also write one combined file for easy copy-paste of all commands
    combined = "\n\n---\n\n".join(f"## Command {i}\n\n{c}" for i, c in enumerate(commands, 1))
    combined_path = biz_dir / "all_commands.md"
    combined_path.write_text(combined, encoding="utf-8")
    return paths + [combined_path]
