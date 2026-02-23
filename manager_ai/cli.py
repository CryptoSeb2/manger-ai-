#!/usr/bin/env python3
"""Manager AI CLI: create businesses, generate Cursor prompts, market copy, and publish assets."""
import argparse
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from .orchestrator import run
from .config import OUTPUT_DIR
from .manus_client import is_configured

console = Console()


def main():
    p = argparse.ArgumentParser(
        description="Manager AI: use Cursor + Manus to create, market, and publish businesses."
    )
    p.add_argument(
        "idea",
        nargs="?",
        default="",
        help="Business idea (one sentence). If omitted, a default or Manus-suggested idea is used.",
    )
    p.add_argument(
        "--stack",
        default="web",
        help="Tech stack hint for Cursor (default: web)",
    )
    p.add_argument(
        "--no-manus",
        action="store_true",
        help="Do not call Manus API (use defaults only)",
    )
    p.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_DIR,
        help=f"Output directory (default: {OUTPUT_DIR})",
    )
    args = p.parse_args()
    console.print(Panel("[bold]Manager AI[/bold] — Ideate → Build (Cursor) → Market → Publish", style="blue"))
    if not is_configured():
        console.print("[yellow]Tip: Set MANUS_API_KEY in .env to use Manus for ideas and task decomposition.[/yellow]\n")
    result = run(
        idea=args.idea,
        stack=args.stack,
        use_manus=not args.no_manus,
        output_dir=args.output_dir if args.output_dir != OUTPUT_DIR else None,
    )
    biz = result["business"]
    console.print(f"\n[green]Business:[/green] {biz['name']} ({biz['slug']})")
    console.print(f"[green]Idea:[/green] {biz['idea'][:200]}{'...' if len(biz['idea']) > 200 else ''}\n")
    console.print("[bold]Next steps:[/bold]")
    for step in result["next_steps"]:
        console.print(f"  • {step}")
    if result.get("build", {}).get("manus_task_url"):
        console.print(f"\n[dim]Manus build plan:[/dim] {result['build']['manus_task_url']}")
    if result.get("market", {}).get("marketing", {}).get("manus_task_url"):
        console.print(f"[dim]Manus marketing copy:[/dim] {result['market']['marketing']['manus_task_url']}")
    console.print(f"\n[dim]All outputs under: {args.output_dir}[/dim]")


if __name__ == "__main__":
    main()
