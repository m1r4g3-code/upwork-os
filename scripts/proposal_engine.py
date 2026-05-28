#!/usr/bin/env python3
"""
proposal_engine.py -- Job brief preparation and draft validation tool.

Claude Code writes the actual proposals. This script handles the mechanical parts:
  --prep   Mechanically extract budget, stack, red flags from a job description
  --check  Rule-based voice check on a written draft

The full /write-proposal workflow:
  1. Run:  python scripts/proposal_engine.py --prep --job "..."
  2. Claude Code reads the brief and runs its reasoning passes
  3. Claude Code writes the draft
  4. Run:  python scripts/proposal_engine.py --check "draft text"
  5. Claude Code revises if score < 7
  6. Claude Code saves to outputs/proposals/ using its Write tool

Usage:
    python scripts/proposal_engine.py --prep --job "paste job description"
    python scripts/proposal_engine.py --prep --file sources/jobs/2026-05-28-slug.json
    python scripts/proposal_engine.py --prep --stdin
    python scripts/proposal_engine.py --check "proposal draft text here"
    python scripts/proposal_engine.py --check --file path/to/draft.txt
"""

import sys
import json
import re
from pathlib import Path
from datetime import date

ROOT = Path(__file__).parent.parent


# ---------------------------------------------------------------------------
# Red flag / green flag patterns
# ---------------------------------------------------------------------------

RED_FLAG_PATTERNS = [
    (r'\bASAP\b|\bimmediately\b|\burgent\b', "urgency pressure"),
    (r'\bper\s+task\b|\bper\s+post\b|\bper\s+article\b', "per-unit pricing (race to bottom)"),
    (r'\btrial\s+(period|first|project)\b|\btest\s+task\b', "trial/test work request"),
    (r'\$\s*[1-9]\b|\$\s*[1-4][0-9]\s', "very low budget signal"),
    (r'\bother\s+duties\b|\bas\s+needed\b|\bongoing\b.*\btask', "scope ambiguity (ongoing/as needed)"),
    (r'\bunverified\b|\bno\s+payment\b|\bpayment\s+method\s+not', "payment not verified"),
    (r'\bmust\s+be\s+available\b|\bdaily\s+updates\b|\bconstant\s+communication\b', "micromanager signals"),
    (r'\b0\s+reviews?\b|\bno\s+reviews?\b|\bnew\s+client\b.*\b0\s+spent\b', "no client history"),
    (r'\bdiscounted?\s+rate\b|\bbest\s+price\b|\blowest\s+bid\b', "commodity mindset"),
]

GREEN_FLAG_PATTERNS = [
    (r'\bverified\s+payment\b|\bpayment\s+verified\b', "payment verified"),
    (r'\$[0-9,]{4,}\b|\bhigh\s+budget\b|\bpremium\b', "reasonable or high budget signal"),
    (r'\blong[- ]term\b|\bongoing\s+work\b|\bretainer\b', "long-term relationship potential"),
    (r'\bspecific\s+deliverable\b|\bdefined\s+scope\b', "clear scope"),
    (r'\b4\.[5-9]\s+stars?\b|\b5\s+stars?\b', "high client rating"),
    (r'\b\$[0-9,]+k?\s+spent\b|\bhired\s+\d+\s+times?\b', "established client spend history"),
    (r'\bn8n\b|\bclaude\b|\bautomation\b|\bworkflow\b', "tech stack alignment"),
]

STACK_KEYWORDS = [
    "n8n", "make.com", "zapier", "claude", "openai", "gpt", "anthropic",
    "supabase", "postgres", "mysql", "mongodb", "redis",
    "typescript", "javascript", "python", "react", "next.js", "nextjs", "node.js",
    "tailwind", "fastapi", "django", "flask",
    "stripe", "twilio", "vapi", "sendgrid", "hubspot", "airtable", "notion",
    "slack", "gmail", "google sheets", "google drive", "ga4",
    "playwright", "selenium", "puppeteer",
    "docker", "aws", "gcp", "vercel", "railway", "render",
    "rest api", "graphql", "webhook", "api integration",
    "whatsapp", "telegram", "discord",
]

BUDGET_PATTERNS = [
    (r'\$([0-9,]+)\s*(?:to|-)\s*\$([0-9,]+)', "range"),
    (r'\$([0-9,]+)\+', "minimum"),
    (r'\$([0-9,]+)', "fixed"),
    (r'([0-9]+)\s*(?:to|-)\s*([0-9]+)\s*(?:dollars?|usd)', "range-text"),
]


def _parse_budget(text: str) -> str:
    """Try to extract a budget figure from job text."""
    for pattern, kind in BUDGET_PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            groups = [g.replace(",", "") for g in m.groups() if g]
            amounts = [int(g) for g in groups if g.isdigit() or g.replace(",", "").isdigit()]
            if amounts:
                avg = sum(amounts) // len(amounts)
                tier = (
                    "premium ($10k+)" if avg >= 10000 else
                    "high ($2k-10k)" if avg >= 2000 else
                    "medium ($500-2k)" if avg >= 500 else
                    "low (under $500)"
                )
                raw = m.group(0).strip()
                return f"{raw} -- {tier}"
    return "not specified"


def _detect_stack(text: str) -> list:
    text_lower = text.lower()
    found = []
    for kw in STACK_KEYWORDS:
        if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
            found.append(kw)
    return found


def _scan_flags(text: str, patterns: list) -> list:
    found = []
    for pattern, label in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            found.append(label)
    return found


def _detect_job_type(text: str) -> str:
    text_lower = text.lower()
    if re.search(r'\bhourly\b|\bper\s+hour\b|\b/hr\b|\bhr\b', text_lower):
        return "hourly"
    if re.search(r'\bfixed\b|\bflat\s+fee\b|\bproject\s+price\b', text_lower):
        return "fixed price"
    return "unknown"


def cmd_prep(job_text: str) -> None:
    """Mechanical job analysis -- no API needed."""
    word_count = len(job_text.split())
    budget = _parse_budget(job_text)
    stack = _detect_stack(job_text)
    red_flags = _scan_flags(job_text, RED_FLAG_PATTERNS)
    green_flags = _scan_flags(job_text, GREEN_FLAG_PATTERNS)
    job_type = _detect_job_type(job_text)

    # Try to infer title from first line
    first_line = job_text.strip().split("\n")[0].strip()[:80]

    lines = []
    lines.append("=" * 60)
    lines.append("JOB BRIEF -- Mechanical Pre-Analysis")
    lines.append(f"Date: {date.today().isoformat()}")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"First line: {first_line}")
    lines.append(f"Job text word count: {word_count} words")
    lines.append(f"Job type: {job_type}")
    lines.append(f"Budget detected: {budget}")
    lines.append("")
    lines.append(f"Stack / tools mentioned ({len(stack)}):")
    if stack:
        lines.append("  " + ", ".join(stack))
    else:
        lines.append("  none detected")
    lines.append("")
    lines.append(f"Red flags ({len(red_flags)}):")
    for f in red_flags:
        lines.append(f"  [!] {f}")
    if not red_flags:
        lines.append("  none detected")
    lines.append("")
    lines.append(f"Green flags ({len(green_flags)}):")
    for f in green_flags:
        lines.append(f"  [+] {f}")
    if not green_flags:
        lines.append("  none detected")
    lines.append("")
    lines.append("-" * 60)
    lines.append("FULL JOB TEXT (for Claude Code intel analysis):")
    lines.append("-" * 60)
    lines.append("")
    lines.append(job_text.strip())
    lines.append("")
    lines.append("=" * 60)
    lines.append("Ready. Claude Code runs intel -> psychology -> strategy -> draft.")
    lines.append("=" * 60)

    print("\n".join(lines))


# ---------------------------------------------------------------------------
# Voice rule check -- no API, pure regex
# ---------------------------------------------------------------------------

BANNED = [
    "passionate about", "would be delighted", " leverage ", "synergy",
    "robust solution", "holistic", "as per your requirements",
    "hope to hear from you", "well-versed", "excited to work",
    "excited about", "innovative", "cutting-edge", "seamlessly",
    "streamline", "at the forefront", "extensive experience",
    "i am well", "looking forward to hearing", "i would love to"
]


def rule_check(text: str) -> dict:
    """Fast rule-based voice check -- no API needed."""
    issues = []
    words = text.split()
    word_count = len(words)

    # Word count
    in_range = 150 <= word_count <= 250
    if not in_range:
        issues.append(f"Word count {word_count} -- target is 150-250")

    # First word
    first_word = words[0].rstrip(".,!?\"'").lower() if words else ""
    if first_word == "i":
        issues.append("First word is 'I' -- must start with client's situation")

    # Hyphens in compound words (flag these)
    hyphen_compounds = re.findall(r'\b[a-zA-Z]+-[a-zA-Z]+\b', text)
    ok_prefixes = ("n8n", "co-", "pre-", "non-", "sub-", "self-", "re-", "mid-", "anti-", "bi-")
    bad_hyphens = [
        h for h in hyphen_compounds
        if not any(h.lower().startswith(p) for p in ok_prefixes)
    ]
    if bad_hyphens:
        issues.append(f"Hyphenated compounds (remove hyphens): {', '.join(bad_hyphens[:5])}")

    # Banned phrases
    text_lower = text.lower()
    found_banned = [b.strip() for b in BANNED if b in text_lower]
    if found_banned:
        issues.append(f"Banned phrases found: {', '.join(found_banned)}")

    # Em-dash / en-dash
    if "--" in text or "-" in text:
        issues.append("Contains em-dash or en-dash -- remove")

    # Closing question
    last_line = text.strip().split("\n")[-1].strip()
    if not last_line.endswith("?"):
        issues.append("Last line must end with a question mark")

    # Bullet points inside proposal
    if re.search(r'^\s*[-*+]\s', text, re.MULTILINE):
        issues.append("Contains bullet points -- proposal should be prose only")

    return {
        "word_count": word_count,
        "in_range": in_range,
        "bad_hyphens": bad_hyphens,
        "banned_phrases": found_banned,
        "issues": issues,
        "clean": len(issues) == 0
    }


def _bar(filled: int, total: int = 10) -> str:
    filled = max(0, min(total, filled))
    return "[" + "#" * filled + "." * (total - filled) + "]"


def cmd_check(text: str) -> None:
    """Print rule-based voice check results."""
    result = rule_check(text)

    wc = result["word_count"]
    in_range = result["in_range"]

    lines = []
    lines.append("")
    lines.append("VOICE RULE CHECK")
    lines.append("-" * 40)
    lines.append(f"Word count:  {wc}  ({'OK' if in_range else 'OUT OF RANGE -- 150-250 required'})")

    issues = result["issues"]
    if issues:
        lines.append("")
        lines.append(f"Issues found ({len(issues)}):")
        for issue in issues:
            lines.append(f"  [!] {issue}")
    else:
        lines.append("")
        lines.append("No rule violations found.")

    lines.append("")
    lines.append("Verdict: " + ("CLEAN -- ready for semantic review" if result["clean"] else "NEEDS REVISION"))
    lines.append("")

    print("\n".join(lines))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _load_job(args: list) -> str:
    if "--stdin" in args:
        print("Paste job description. Press Ctrl+Z then Enter (Windows) / Ctrl+D (Linux):")
        return sys.stdin.read().strip()
    if "--file" in args:
        idx = args.index("--file")
        fp = Path(args[idx + 1])
        if fp.suffix == ".json":
            data = json.loads(fp.read_text(encoding="utf-8"))
            return data.get("description", data.get("job_text", str(data)))
        return fp.read_text(encoding="utf-8")
    if "--job" in args:
        idx = args.index("--job")
        return args[idx + 1]
    return ""


def main():
    args = sys.argv[1:]

    if not args:
        print(__doc__)
        sys.exit(0)

    if "--prep" in args:
        job_text = _load_job(args)
        if not job_text.strip():
            print("ERROR: No job text. Use --job, --file, or --stdin")
            sys.exit(1)
        cmd_prep(job_text)

    elif "--check" in args:
        # Either inline text or --file
        idx = args.index("--check")
        if idx + 1 < len(args) and not args[idx + 1].startswith("--"):
            text = args[idx + 1]
        elif "--file" in args:
            fidx = args.index("--file")
            text = Path(args[fidx + 1]).read_text(encoding="utf-8")
        else:
            print("ERROR: --check requires draft text or --file path")
            sys.exit(1)
        cmd_check(text)

    else:
        print(__doc__)
        sys.exit(0)


if __name__ == "__main__":
    main()
