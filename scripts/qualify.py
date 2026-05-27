"""
qualify.py — Deterministic job scoring engine.

Rules-based scoring. No LLM needed. Fast.
Claude calls this, then interprets the output strategically.

Usage:
  python scripts/qualify.py <json-file>              # score a job
  python scripts/qualify.py --client <json-file>     # score a client
  python scripts/qualify.py --calibrate <slug> <score>  # log calibration data
"""

import json
import sys
import re
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

RED_FLAG_PHRASES = [
    "trial task", "test first", "unpaid test", "free sample",
    "per task", "pay per task", "pay per piece",
    "must be available immediately", "available 24/7",
    "i need someone who can do everything",
    "as needed", "various tasks", "and other duties",
    "asap", "urgent urgent",
]

GREEN_FLAG_PHRASES = [
    "long-term", "ongoing relationship", "potential for more work",
    "milestone", "clear scope", "specific deliverable",
]

HARD_DISQUALIFIERS = [
    "trial task", "test first for free", "unpaid test", "per task payment",
]


def score_job_quality(data: dict) -> tuple[int, list[str]]:
    score = 50
    reasons = []
    desc = (data.get("description") or "").lower()
    title = (data.get("title") or "").lower()
    budget_min = data.get("budget_min", 0) or 0
    budget_max = data.get("budget_max", 0) or 0
    budget = (budget_min + budget_max) / 2 if budget_max else budget_min
    job_type = data.get("job_type", "").lower()
    days_posted = data.get("days_posted", 0) or 0
    proposals_count = data.get("proposals_count", 0) or 0

    # Clear deliverable signals
    if any(w in desc for w in ["deliverable", "milestone", "phase", "specific"]):
        score += 5
        reasons.append("+5: clear deliverable language")

    # Tech stack named
    tech_terms = ["n8n", "claude", "openai", "react", "next.js", "postgresql",
                  "typescript", "python", "api", "webhook", "zapier", "make.com"]
    tech_found = [t for t in tech_terms if t in desc or t in title]
    if len(tech_found) >= 2:
        score += 8
        reasons.append(f"+8: specific tech stack named ({', '.join(tech_found[:3])})")
    elif len(tech_found) == 1:
        score += 4
        reasons.append(f"+4: some tech specified ({tech_found[0]})")

    # Budget realism check
    if job_type == "fixed":
        complexity_words = ["system", "platform", "full", "complete", "integration", "dashboard", "app"]
        is_complex = any(w in desc or w in title for w in complexity_words)
        if is_complex and budget < 300:
            score -= 20
            reasons.append(f"-20: budget ${budget:.0f} too low for complex scope")
        elif budget >= 2000:
            score += 10
            reasons.append(f"+10: strong budget (${budget:.0f})")
        elif budget >= 500:
            score += 5
            reasons.append(f"+5: reasonable budget (${budget:.0f})")
    elif job_type == "hourly":
        rate_min = data.get("hourly_rate_min", 0) or 0
        rate_max = data.get("hourly_rate_max", 0) or 0
        rate = (rate_min + rate_max) / 2 if rate_max else rate_min
        if rate >= 50:
            score += 10
            reasons.append(f"+10: strong hourly rate (${rate:.0f}/hr)")
        elif rate >= 25:
            score += 4
        elif rate > 0 and rate < 15:
            score -= 15
            reasons.append(f"-15: low hourly rate (${rate:.0f}/hr)")

    # Vague scope signals
    vague_terms = ["various tasks", "as needed", "and other", "ongoing", "miscellaneous"]
    vague_found = [v for v in vague_terms if v in desc]
    if vague_found:
        score -= 15
        reasons.append(f"-15: vague scope signals ({', '.join(vague_found[:2])})")

    # Simple/easy misrepresentation
    if any(w in title or w in desc[:200] for w in ["simple", "easy", "quick fix", "small task"]):
        if any(w in desc for w in ["integration", "system", "platform", "full", "dashboard"]):
            score -= 10
            reasons.append("-10: 'simple' claim + complex scope = mismatch")

    # Age of posting
    if days_posted > 14:
        score -= 10
        reasons.append(f"-10: old posting ({days_posted} days)")
    elif days_posted > 7:
        score -= 5

    # Competition
    if proposals_count > 50:
        score -= 8
        reasons.append(f"-8: high competition ({proposals_count} proposals)")
    elif proposals_count > 20:
        score -= 3

    return max(0, min(100, score)), reasons


def score_client_quality(data: dict) -> tuple[int, list[str], list[str]]:
    score = 50
    reasons = []
    red_flags = []

    payment_verified = data.get("payment_verified", False)
    total_spend = data.get("total_spend_usd", 0) or 0
    hire_rate = data.get("hire_rate_pct", 0) or 0
    avg_hourly_paid = data.get("avg_hourly_paid", 0) or 0
    avg_review = data.get("avg_review_score", 0) or 0
    active_contracts = data.get("active_contracts", 0) or 0
    total_hires = data.get("total_hires", 0) or 0
    jobs_posted = data.get("jobs_posted", 0) or 0

    # Payment verification (critical)
    if not payment_verified:
        score -= 40
        red_flags.append("Payment NOT verified")
    else:
        score += 15
        reasons.append("+15: payment verified")

    # Total spend
    if total_spend >= 10000:
        score += 15
        reasons.append(f"+15: strong spend history (${total_spend:,.0f})")
    elif total_spend >= 1000:
        score += 8
        reasons.append(f"+8: decent spend history (${total_spend:,.0f})")
    elif total_spend >= 100:
        score += 2
    elif total_spend == 0 and total_hires == 0:
        score -= 20
        red_flags.append("Zero spend history, no hires")

    # Hire rate
    if hire_rate >= 60:
        score += 10
        reasons.append(f"+10: high hire rate ({hire_rate:.0f}%)")
    elif hire_rate >= 30:
        score += 5
    elif hire_rate < 10 and jobs_posted >= 5:
        score -= 15
        red_flags.append(f"Very low hire rate ({hire_rate:.0f}%) — window shopper signal")
    elif hire_rate == 0 and jobs_posted >= 5:
        score -= 25
        red_flags.append("0% hire rate with multiple posted jobs — window shopper")

    # Average hourly paid
    if avg_hourly_paid >= 50:
        score += 10
        reasons.append(f"+10: pays premium rates (${avg_hourly_paid:.0f}/hr avg)")
    elif avg_hourly_paid >= 25:
        score += 5
    elif avg_hourly_paid > 0 and avg_hourly_paid < 10:
        score -= 15
        red_flags.append(f"Pays very low rates (${avg_hourly_paid:.0f}/hr avg)")

    # Review score
    if avg_review >= 4.8:
        score += 10
        reasons.append(f"+10: excellent review score ({avg_review:.1f}★)")
    elif avg_review >= 4.5:
        score += 5
    elif avg_review > 0 and avg_review < 4.0:
        score -= 20
        red_flags.append(f"Low review score ({avg_review:.1f}★) — multiple bad experiences")
    elif avg_review > 0 and avg_review < 3.5:
        score -= 35
        red_flags.append(f"Very low review score ({avg_review:.1f}★) — SKIP")

    # Active contracts (distraction risk)
    if active_contracts >= 10:
        score -= 15
        red_flags.append(f"Too many active contracts ({active_contracts}) — won't have bandwidth")
    elif active_contracts >= 6:
        score -= 5

    return max(0, min(100, score)), reasons, red_flags


def score_fit(data: dict, job_data: dict) -> tuple[int, list[str]]:
    score = 50
    reasons = []
    desc = (job_data.get("description") or "").lower()
    title = (job_data.get("title") or "").lower()

    # Core stack match
    core_skills = ["n8n", "claude", "openai", "automation", "workflow", "ai", "agent",
                   "next.js", "nextjs", "react", "typescript", "python", "postgresql",
                   "api integration", "dashboard", "full-stack", "fullstack"]
    matches = [s for s in core_skills if s in desc or s in title]
    if len(matches) >= 3:
        score += 20
        reasons.append(f"+20: strong stack match ({', '.join(matches[:3])})")
    elif len(matches) >= 1:
        score += 10
        reasons.append(f"+10: partial stack match ({', '.join(matches[:2])})")
    else:
        score -= 10
        reasons.append("-10: no clear stack match")

    # Niche match (medical, SaaS, agency)
    niche_terms = ["medical", "clinic", "healthcare", "saas", "agency", "marketing",
                   "admin", "operations", "workflow", "process automation"]
    niche_matches = [n for n in niche_terms if n in desc or n in title]
    if niche_matches:
        score += 10
        reasons.append(f"+10: niche match ({niche_matches[0]})")

    # Budget signals premium positioning
    budget_min = job_data.get("budget_min", 0) or 0
    if budget_min >= 2000 or job_data.get("hourly_rate_min", 0) >= 50:
        score += 10
        reasons.append("+10: budget supports premium positioning")
    elif budget_min < 200 and budget_min > 0:
        score -= 15
        reasons.append("-15: budget signals commodity thinking")

    # Anti-fit: outside core skills
    anti_fit = ["mobile app", "ios", "android", "flutter", "devops", "kubernetes",
                "blockchain", "solidity", "hardware", "embedded", "wordpress plugin"]
    anti_matches = [a for a in anti_fit if a in desc or a in title]
    if anti_matches:
        score -= 20
        reasons.append(f"-20: outside core skills ({anti_matches[0]})")

    return max(0, min(100, score)), reasons


def score_urgency(data: dict) -> tuple[int, list[str]]:
    score = 5
    reasons = []
    desc = (data.get("description") or "").lower()

    high_urgency = ["previous freelancer", "mid-project", "deadline", "launch date",
                    "going live", "business critical", "production issue", "already behind"]
    low_urgency = ["no rush", "whenever", "thinking about", "exploring", "future project",
                   "planning to", "eventually"]

    if any(h in desc for h in high_urgency):
        score = 8
        matched = [h for h in high_urgency if h in desc][0]
        reasons.append(f"High urgency: '{matched}'")
    elif any(l in desc for l in low_urgency):
        score = 2
        matched = [l for l in low_urgency if l in desc][0]
        reasons.append(f"Low urgency: '{matched}'")

    return score, reasons


def score_competition(data: dict) -> tuple[int, list[str]]:
    proposals = data.get("proposals_count", 0) or 0
    days_posted = data.get("days_posted", 0) or 0
    reasons = []

    if proposals <= 5:
        score = 9
        reasons.append(f"Low competition ({proposals} proposals)")
    elif proposals <= 15:
        score = 7
        reasons.append(f"Moderate competition ({proposals} proposals)")
    elif proposals <= 30:
        score = 5
        reasons.append(f"Medium-high competition ({proposals} proposals)")
    elif proposals <= 50:
        score = 3
        reasons.append(f"High competition ({proposals} proposals)")
    else:
        score = 1
        reasons.append(f"Very high competition ({proposals} proposals)")

    return score, reasons


def check_hard_disqualifiers(job_data: dict, client_data: dict) -> list[str]:
    disqualifiers = []
    desc = (job_data.get("description") or "").lower()

    for phrase in HARD_DISQUALIFIERS:
        if phrase in desc:
            disqualifiers.append(f"Hard disqualifier in job description: '{phrase}'")

    if not client_data.get("payment_verified", True):
        if client_data.get("total_spend_usd", 0) == 0:
            disqualifiers.append("Payment not verified AND zero spend history")

    hire_rate = client_data.get("hire_rate_pct", 100)
    jobs_posted = client_data.get("jobs_posted", 0)
    if hire_rate == 0 and jobs_posted >= 10:
        disqualifiers.append(f"0% hire rate with {jobs_posted} posted jobs")

    avg_review = client_data.get("avg_review_score", 5.0)
    if avg_review > 0 and avg_review < 3.5:
        disqualifiers.append(f"Average review score {avg_review:.1f} — too low")

    return disqualifiers


def composite_score(jq: int, cq: int, fit: int, urgency: int, competition: int) -> int:
    return int(
        jq * 0.30 +
        cq * 0.30 +
        fit * 0.25 +
        (urgency / 10 * 100) * 0.08 +
        (competition / 10 * 100) * 0.07
    )


def decision(score: int, disqualifiers: list[str], red_flags: list[str]) -> str:
    if disqualifiers:
        return "SKIP"
    if score < 65:
        return "SKIP"
    if score < 80:
        return "WATCHLIST"
    return "BID"


def qualify_job(filepath: str) -> dict:
    with open(filepath) as f:
        data = json.load(f)

    job_data = data.get("job", data)
    client_data = data.get("client", {})

    jq, jq_reasons = score_job_quality(job_data)
    cq, cq_reasons, client_red_flags = score_client_quality(client_data)
    fit, fit_reasons = score_fit({}, job_data)
    urgency, urgency_reasons = score_urgency(job_data)
    competition, competition_reasons = score_competition(job_data)
    disqualifiers = check_hard_disqualifiers(job_data, client_data)
    composite = composite_score(jq, cq, fit, urgency, competition)
    dec = decision(composite, disqualifiers, client_red_flags)

    result = {
        "title": job_data.get("title", "Unknown"),
        "url": job_data.get("url", ""),
        "scores": {
            "job_quality": jq,
            "client_quality": cq,
            "fit_score": fit,
            "urgency": urgency,
            "competition": competition,
            "composite": composite,
        },
        "decision": dec,
        "hard_disqualifiers": disqualifiers,
        "client_red_flags": client_red_flags,
        "score_reasons": {
            "job_quality": jq_reasons,
            "client_quality": cq_reasons,
            "fit": fit_reasons,
            "urgency": urgency_reasons,
            "competition": competition_reasons,
        },
        "evaluated_at": datetime.now().isoformat(),
    }

    print(json.dumps(result, indent=2))
    return result


def qualify_client(filepath: str) -> dict:
    with open(filepath) as f:
        data = json.load(f)

    score, reasons, red_flags = score_client_quality(data)
    result = {
        "username": data.get("username", "unknown"),
        "quality_score": score,
        "reasons": reasons,
        "red_flags": red_flags,
        "recommendation": "HIRE" if score >= 65 and not red_flags else "AVOID" if score < 50 else "CAUTION",
        "evaluated_at": datetime.now().isoformat(),
    }
    print(json.dumps(result, indent=2))
    return result


def log_calibration(slug: str, emmanuel_score: int):
    cal_file = DATA_DIR / "calibration_log.jsonl"
    entry = {
        "date": datetime.now().date().isoformat(),
        "slug": slug,
        "emmanuel_score": emmanuel_score,
    }
    with open(cal_file, "a") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"Calibration logged: {slug} → {emmanuel_score}")


if __name__ == "__main__":
    args = sys.argv[1:]

    if not args:
        print("Usage: python scripts/qualify.py <json-file>")
        print("       python scripts/qualify.py --client <json-file>")
        print("       python scripts/qualify.py --calibrate <slug> <score>")
        sys.exit(1)

    if args[0] == "--client" and len(args) >= 2:
        qualify_client(args[1])
    elif args[0] == "--calibrate" and len(args) >= 3:
        log_calibration(args[1], int(args[2]))
    else:
        qualify_job(args[0])
