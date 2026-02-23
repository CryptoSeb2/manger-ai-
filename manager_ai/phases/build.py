"""Build phase: generate Cursor prompts and optional Manus task for implementation."""
from pathlib import Path
from ..cursor_prompts import (
    cursor_prompt_build,
    cursor_prompt_from_instruction,
    cursor_commands_from_instruction,
    write_cursor_prompt,
    write_cursor_commands,
)
from ..manus_client import create_task, is_configured


def build_phase(
    business_name: str,
    idea: str,
    slug: str,
    stack: str = "web",
    create_manus_task: bool = True,
    instruction: str | None = None,
    other_tools: str | None = None,
) -> dict:
    """
    Produce Cursor-ready build instructions and optionally a Manus task.
    If instruction is provided, also generates a sequence of commands for Cursor.
    Returns paths to generated prompt file(s), command list, and optional Manus task URL.
    """
    use_instruction = instruction and instruction.strip()
    if use_instruction:
        prompt = cursor_prompt_from_instruction(instruction.strip(), stack, other_tools=other_tools)
        path = write_cursor_prompt(slug, prompt, "build_in_cursor.md")
        commands = cursor_commands_from_instruction(instruction.strip(), stack)
        command_paths = write_cursor_commands(slug, commands)
        command_count = len(commands)
    else:
        prompt = cursor_prompt_build(business_name, idea, stack)
        path = write_cursor_prompt(slug, prompt, "build_in_cursor.md")
        command_paths = []
        command_count = 0

    result = {
        "cursor_prompt_path": str(path),
        "cursor_prompt_preview": prompt[:400] + "..." if len(prompt) > 400 else prompt,
        "manus_task_url": None,
        "command_paths": [str(p) for p in command_paths],
        "command_count": command_count,
    }

    task_desc = (
        f"Goal: {instruction}. Stack: {stack}. Break into step-by-step implementation plan for an IDE."
        if use_instruction
        else f"Business: {business_name}. Idea: {idea}. Stack: {stack}. List concrete steps (tech stack, pages, APIs, deploy)."
    )
    if create_manus_task and is_configured():
        task = create_task(
            f"Break down into step-by-step implementation plan for a developer using an IDE: {task_desc}"
        )
        if "error" not in task:
            result["manus_task_url"] = task.get("task_url")
    return result
