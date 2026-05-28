#!/usr/bin/env python3
"""
call_prep.py -- Pre-call brief generator for Hephzibah Upwork OS

Generates a structured preparation sheet before a discovery call.
Reads job card data (or prompts interactively) and outputs:
  - What we know (hard facts)
  - Research gaps to fill before the call
  - Ordered question stack by call phase
  - Red flags to listen for
  - Close script (exact words)

Saved to: outputs/intel/YYYY-MM-DD-call-prep-SLUG.md

Usage:
  python scripts/call_prep.py                                    # interactive
  python scripts/call_prep.py --project "CRM Sync" --client "Alex" --type crm --complexity complex
  python scripts/call_prep.py --project "AI Pipeline" --client "Sarah" --type pipeline --context "saas"
"""

import argparse
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent.parent
OUTPUTS_DIR = ROOT / "outputs" / "intel"

# ---------------------------------------------------------------------------
# Question bank — (question_text, applicable_types)
# "all" = every project type
# ---------------------------------------------------------------------------

QUESTIONS = {
    "current_state": [
        ("How are you handling this right now?", "all"),
        ("Walk me through the current workflow step by step.", "all"),
        ("How much time does this take your team weekly?", "all"),
        ("What tools are you using for this currently?", "all"),
        ("How many people touch this process today?", "all"),
    ],
    "problem_depth": [
        ("What made you decide now was the time to fix this?", "all"),
        ("Have you tried to solve this before? What happened?", "all"),
        ("When this breaks or slows down -- what is the downstream effect on the business?", "all"),
        ("What would fixed actually look like in your day-to-day?", "all"),
        ("What is the single biggest pain point with how you do this today?", "all"),
    ],
    "stakes": [
        ("What breaks if this is not solved by your target date?", "all"),
        ("Is there a specific launch or event driving the timeline?", "all"),
        ("What does this problem cost you right now -- time, revenue, or both?", "all"),
        ("Who else in the business is affected when this is not working?", "all"),
    ],
    "technical": [
        ("What is your expected volume at launch -- and 6 months out?", "automation|pipeline|agent|integration"),
        ("What other systems does this need to connect to?", "automation|pipeline|integration|crm|agent"),
        ("Who on your team owns this after delivery?", "all"),
        ("Any data sensitivity or compliance requirements I should know about?", "all"),
        ("Have you documented the current process or is it mostly in peoples heads?", "automation|pipeline|crm|scraper"),
        ("What is your tolerance for downtime on this?", "pipeline|agent|fullstack|integration"),
        ("What is the tech stack you are working with?", "fullstack|agent|pipeline"),
    ],
    "decision": [
        ("Who else is involved in this decision besides yourself?", "all"),
        ("Have you spoken to other freelancers about this?", "all"),
        ("Is there a budget range you are working within?", "all"),
        ("If the Scope of Work looks right -- what does starting look like on your end?", "all"),
        ("What is your timeline from decision to actual start?", "all"),
    ],
}

PHASE_LABELS = {
    "current_state": "CURRENT STATE",
    "problem_depth": "PROBLEM DEPTH",
    "stakes":        "STAKES & URGENCY",
    "technical":     "TECHNICAL QUALIFICATION",
    "decision":      "DECISION PROCESS",
}

# ---------------------------------------------------------------------------
# Red flags to listen for during the call
# ---------------------------------------------------------------------------

CALL_RED_FLAGS = [
    ("'We just need something quick'",
     "Scope undefined. Ask: 'What does quick mean -- what is the actual deadline?'"),
    ("'Budget is tight but lots of future work'",
     "Speculation. Price this project as if it is the only one."),
    ("Multiple decision makers with no clear lead",
     "Committee = slow or no close. Ask: 'Who has final sign-off?'"),
    ("Hired 3+ freelancers for the same problem",
     "Unclear scope or difficult client. Ask: 'What happened with the previous freelancers?'"),
    ("Cannot describe the current workflow",
     "They do not know their own process. SOW will move. Price for scope risk."),
    ("'Can you start today or tomorrow?'",
     "No planning = chaos project. State your actual start date calmly."),
    ("Pushes back on upfront payment before you mention it",
     "Payment risk. Hold the line: 40% upfront is non-negotiable. If they resist, walk."),
    ("Vague when asked to define success",
     "No acceptance criteria = JSS risk. Push until they give a concrete definition."),
    ("'We will handle the testing'",
     "They will not. You carry the JSS risk. Testing is part of your delivery."),
    ("Drops in and out of technical detail with no consistency",
     "They may not understand what they are asking for. SOW checkpoints become critical."),
]

# ---------------------------------------------------------------------------
# Opening line templates by context type
# ---------------------------------------------------------------------------

OPENING_LINES = {
    "has_research": (
        "I was looking at your [site/product] before the call -- I noticed [SPECIFIC FINDING]. "
        "Is that [assumption] accurate, or am I reading it wrong?"
    ),
    "no_research": (
        "I read through your post in detail. Before I recommend anything, "
        "I want to make sure I have the full picture. Can I ask you a few questions first?"
    ),
    "enterprise": (
        "I have done a few builds similar to what you are describing. "
        "Some of my recommendations will depend on details I do not have yet -- "
        "specifically your volume and who owns this after delivery. "
        "Can I lead with a few questions?"
    ),
    "returning": (
        "Good to speak with you. I have reviewed everything you sent. "
        "A couple of things came up that I want to make sure I understand correctly before I finalize the SOW."
    ),
}

# ---------------------------------------------------------------------------
# Research checklist items
# ---------------------------------------------------------------------------

RESEARCH_GAPS = [
    "[ ] Visit their website -- find ONE specific thing tied to their project",
    "[ ] Find their first name (check reviews section -- freelancers address clients by name)",
    "[ ] Google the company name -- check LinkedIn, AppSumo, Product Hunt for market/size signals",
    "[ ] Review their Upwork job history -- what have they hired for before?",
    "[ ] Infer their tech stack from what they mentioned in the post",
    "[ ] Identify who else is likely involved (solo founder vs team with a boss?)",
]

CLOSE_SCRIPT = """\
CLOSE SCRIPT
------------
"Based on what you have told me -- [1-sentence summary of their real problem] --
I have a clear picture of what this needs.

Here is what I would suggest: I will put together a Scope of Work by [tomorrow / Friday].
It will show you exactly what is included, what is not, the milestone structure,
and the investment -- split into stages so there is no risk on either side.

Does that work?"

If yes  -> "Good. You will have it by [date]. I will send it to [Upwork / email]."
If "need to talk to others first" -> "Of course. When will you have alignment? I will
  time the SOW to land before that conversation."

DO NOT:
  - Ask "Would you like to hire me?"
  - Say "Let me know if you want to move forward."
  - Mention the rate again unprompted -- the SOW handles that.
  - End the call without a specific date and delivery method for the SOW.\
"""

POST_CALL = """\
POST-CALL ACTIONS (do immediately -- memory degrades)
------------------------------------------------------
[ ] Write down every number mentioned: volume, team size, timeline, current cost, budget
[ ] One sentence: what is the REAL problem (not the stated one)?
[ ] Run /quote with confirmed project type + complexity
[ ] Send SOW within 24 hours -- strike while warm
[ ] Create client node: hephzibah-brain-temp/upwork/clients/active/SLUG.md if proceeding
[ ] Log Fathom transcript -> Claude -> extract key numbers + their exact problem language\
"""


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def select_questions(proj_type: str, n: int = 8) -> list:
    selected = []
    phase_order = ["current_state", "problem_depth", "stakes", "technical", "decision"]
    for phase in phase_order:
        for q, types in QUESTIONS[phase]:
            if types == "all" or proj_type in types:
                selected.append((phase, q))
                if len(selected) >= n:
                    return selected
    return selected


def fmt_questions(questions: list) -> str:
    lines = []
    current_phase = None
    i = 1
    for phase, q in questions:
        if phase != current_phase:
            lines.append(f"\n  [{PHASE_LABELS.get(phase, phase)}]")
            current_phase = phase
        lines.append(f"  {i}. {q}")
        i += 1
    return "\n".join(lines)


def fmt_red_flags() -> str:
    lines = []
    for signal, risk in CALL_RED_FLAGS:
        lines.append(f"  {signal}")
        lines.append(f"    -> {risk}")
        lines.append("")
    return "\n".join(lines)


def fmt_research_gaps() -> str:
    return "\n".join(f"  {item}" for item in RESEARCH_GAPS)


def pick_opening(has_research: bool, complexity: str) -> str:
    if complexity == "enterprise":
        return OPENING_LINES["enterprise"]
    if has_research:
        return OPENING_LINES["has_research"]
    return OPENING_LINES["no_research"]


def build_brief(project: str, client: str, budget: str, proj_type: str,
                complexity: str, has_research: bool, research_note: str,
                post_notes: str) -> str:
    today = date.today().isoformat()
    questions = select_questions(proj_type, n=8)
    opening = pick_opening(has_research, complexity)

    lines = [
        f"# Pre-Call Brief -- {project}",
        f"**Date:** {today}  |  **Client:** {client}  |  **Command:** /prep-call",
        f"**Status:** prep",
        "---",
        "",
        "## What We Know",
        "",
        f"  Project:    {project}",
        f"  Client:     {client}",
        f"  Budget:     {budget or 'not posted'}",
        f"  Type:       {proj_type} / {complexity}",
    ]

    if research_note:
        lines += ["", f"  Research:   {research_note}"]
    if post_notes:
        lines += ["", "  Notes from post:", f"  {post_notes}"]

    lines += [
        "",
        "---",
        "",
        "## Research Gaps (fill before the call)",
        "",
        fmt_research_gaps(),
        "",
        "---",
        "",
        "## The Kill Shot (open with this)",
        "",
        "  One specific observation from their site or post. Not generic -- pointed.",
        "  Fill this in after 15 min of research.",
        "",
        f"  Opening line:",
        f'  "{opening}"',
        "",
        "---",
        "",
        "## Question Stack",
        "",
        "  Run in order. Never rush. Let silence do work.",
        "  After every answer: 'Tell me more about that.'",
        "",
        fmt_questions(questions),
        "",
        "---",
        "",
        "## Red Flags to Listen For",
        "",
        fmt_red_flags(),
        "",
        "---",
        "",
        CLOSE_SCRIPT,
        "",
        "---",
        "",
        POST_CALL,
        "",
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Interactive mode
# ---------------------------------------------------------------------------

def interactive():
    print("\n+====================================+")
    print("|   Hephzibah -- Call Prep           |")
    print("+====================================+\n")

    project = input("Project name / slug: ").strip() or "project"
    client  = input("Client first name: ").strip() or "Client"
    budget  = input("Budget posted (blank if unknown): ").strip()

    print(f"\nProject type: integration / automation / pipeline / agent / fullstack / scraper / crm / custom")
    proj_type  = input("> ").strip() or "automation"

    print("Complexity: simple / medium / complex / enterprise")
    complexity = input("> ").strip() or "medium"

    print("\nHave you researched their website or business before this call? [y/n]")
    has_research = input("> ").strip().lower() == "y"

    research_note = ""
    if has_research:
        research_note = input("One-line note on what you found: ").strip()

    print("\nKey notes from job post (specific things they mentioned):")
    post_notes = input("> ").strip()

    slug = project.lower().replace(" ", "-")
    content = build_brief(project, client, budget, proj_type, complexity,
                          has_research, research_note, post_notes)

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    out = OUTPUTS_DIR / f"{date.today().isoformat()}-call-prep-{slug}.md"
    out.write_text(content, encoding="utf-8")

    print("\n" + "-" * 52)
    print(content)
    print("-" * 52)
    print(f"\n  Saved -> {out}\n")


# ---------------------------------------------------------------------------
# CLI mode
# ---------------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(description="Hephzibah Pre-Call Brief Generator")
    p.add_argument("--project",    help="Project name")
    p.add_argument("--client",     help="Client first name")
    p.add_argument("--budget",     help="Budget posted by client")
    p.add_argument("--type",       dest="proj_type", default="automation",
                   choices=["integration", "automation", "pipeline", "agent",
                            "fullstack", "scraper", "crm", "custom"])
    p.add_argument("--complexity", default="medium",
                   choices=["simple", "medium", "complex", "enterprise"])
    p.add_argument("--context",    help="Research note (what you found on their site)")
    p.add_argument("--notes",      help="Key notes from the job post")
    p.add_argument("--slug",       default="project", help="Output filename slug")
    args = p.parse_args()

    if not args.project:
        interactive()
        return

    has_research = bool(args.context)
    content = build_brief(
        args.project,
        args.client or "Client",
        args.budget or "",
        args.proj_type,
        args.complexity,
        has_research,
        args.context or "",
        args.notes or "",
    )

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    out = OUTPUTS_DIR / f"{date.today().isoformat()}-call-prep-{args.slug}.md"
    out.write_text(content, encoding="utf-8")

    print(content)
    print(f"\n  Saved -> {out}\n")


if __name__ == "__main__":
    main()
