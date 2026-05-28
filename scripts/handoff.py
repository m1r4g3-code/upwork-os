#!/usr/bin/env python3
"""
handoff.py — Delivery brief + contract close generator for Hephzibah Upwork OS

Generates:
  1. Delivery brief (what was built, how to use it, unexpected extra, maintenance)
  2. Contract close message (ready to paste into Upwork chat)

Saved to: outputs/briefs/YYYY-MM-DD-handoff-SLUG.md

Usage:
  python scripts/handoff.py
  python scripts/handoff.py --project "CRM Sync" --client "Alex" --slug crm-sync
"""

import argparse
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent.parent
OUTPUTS_DIR = ROOT / "outputs" / "briefs"

CLOSE_MESSAGE_TEMPLATE = """\
Hey {client},

Everything's wrapped up on my end. {summary}

I've put together a delivery brief with everything you need — how it works, what to do if \
something breaks, and a couple of things I added that weren't in the original scope.

Could you close the contract when you get a chance?

Emmanuel"""

SILENT_FOLLOWUP_5 = """\
Hey {client}, just checking in — did you get a chance to look at {project}?
Let me know if anything needs adjusting. Happy to close this off once you confirm it's working."""

SILENT_FOLLOWUP_10 = """\
Hey {client}, everything's still ready on my end whenever you are.
Happy to do a quick walkthrough if that helps before we close."""


def prompt_list(label: str, hint: str = "") -> list[str]:
    """Collect multi-line input until empty line."""
    if hint:
        print(f"  ({hint})")
    items = []
    i = 1
    while True:
        val = input(f"  {i}. ").strip()
        if not val:
            break
        items.append(val)
        i += 1
    return items


def build_brief(client: str, project: str, stack: str,
                deliverables: list, instructions: list,
                break_fix: str, extra: str, maintenance: list) -> str:
    today = date.today().isoformat()
    summary = f"{project} is live and ready to use."

    lines = [
        f"# Delivery Brief — {project}",
        f"**Date:** {today}  |  **Client:** {client}  |  **Status:** delivered",
        "---",
        "",
        "## What Was Built",
        "",
    ]
    for i, d in enumerate(deliverables, 1):
        lines.append(f"{i}. {d}")
    if stack:
        lines += ["", f"**Stack:** {stack}"]
    lines.append("")

    if instructions:
        lines += ["## How to Use It", ""]
        for inst in instructions:
            lines.append(f"- {inst}")
        lines.append("")

    if break_fix:
        lines += ["## If Something Breaks", "", break_fix, ""]

    if extra:
        lines += [
            "## What I Added (Not in Scope)",
            "",
            extra,
            "",
            "> This wasn't in the brief. I added it because it prevents a problem",
            "> you would have hit within a week of going live.",
            "",
        ]

    if maintenance:
        lines += ["## Maintenance Notes", ""]
        for m in maintenance:
            lines.append(f"- {m}")
        lines.append("")

    close_msg = CLOSE_MESSAGE_TEMPLATE.format(client=client, summary=summary)
    followup_5 = SILENT_FOLLOWUP_5.format(client=client, project=project)
    followup_10 = SILENT_FOLLOWUP_10.format(client=client)

    lines += [
        "---",
        "",
        "## Contract Close Message",
        "",
        "*(Send in Upwork chat after client confirms delivery is working)*",
        "",
        "```",
        close_msg,
        "```",
        "",
        "---",
        "",
        "## Silent Client Follow-Ups",
        "",
        "**Day 5 (if no reply):**",
        "```",
        followup_5,
        "```",
        "",
        "**Day 10:**",
        "```",
        followup_10,
        "```",
        "",
        "> Day 21: stop. Do not chase further.",
    ]

    return "\n".join(lines)


def interactive():
    print("\n╔════════════════════════════════════╗")
    print("║  Hephzibah — Handoff Generator    ║")
    print("╚════════════════════════════════════╝\n")

    client  = input("Client first name: ").strip()
    project = input("Project name: ").strip()
    slug    = input("File slug (e.g. crm-sync): ").strip() or \
              project.lower().replace(" ", "-")
    stack   = input("Tech stack (e.g. n8n, Claude API, Airtable): ").strip()

    print("\n--- WHAT WAS BUILT ---")
    print("One deliverable per line. Plain English. No jargon. Empty line to finish.")
    deliverables = prompt_list("deliverables")

    print("\n--- HOW TO USE IT ---")
    print("The 3-5 things they need to know to operate this. Empty line to finish.")
    instructions = prompt_list("instructions")

    print("\n--- IF SOMETHING BREAKS ---")
    break_fix = input("  > ").strip()

    print("\n--- THE UNEXPECTED EXTRA ---")
    print("  One small thing you added that wasn't in scope (10 min, stays forever).")
    extra = input("  > ").strip()

    print("\n--- MAINTENANCE NOTES ---")
    print("  API key rotation, rate limits, monthly checks, etc. Empty line to finish.")
    maintenance = prompt_list("maintenance notes")

    content = build_brief(client, project, stack, deliverables,
                          instructions, break_fix, extra, maintenance)

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    out = OUTPUTS_DIR / f"{date.today().isoformat()}-handoff-{slug}.md"
    out.write_text(content, encoding="utf-8")

    print("\n" + "─" * 52)
    print(f"  Saved → {out}")
    print("─" * 52)
    print("\n--- CONTRACT CLOSE MESSAGE ---\n")
    print(CLOSE_MESSAGE_TEMPLATE.format(
        client=client,
        summary=f"{project} is live and ready to use.",
    ))
    print("\n" + "─" * 52)


def main():
    p = argparse.ArgumentParser(description="Hephzibah Handoff Generator")
    p.add_argument("--project", help="Project name")
    p.add_argument("--client",  help="Client first name")
    p.add_argument("--slug",    help="Output filename slug")
    args = p.parse_args()
    # Always interactive — handoffs need full detail to be useful
    interactive()


if __name__ == "__main__":
    main()
