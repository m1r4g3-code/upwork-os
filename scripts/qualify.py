"""
qualify.py -- Deterministic job scoring engine.

Rules-based scoring. No LLM needed. Fast.
Claude calls this, then interprets the output strategically.

Usage:
  python scripts/qualify.py <json-file>              # score a job
  python scripts/qualify.py --client <json-file>     # score a client
  python scripts/qualify.py --calibrate <slug> <score>  # log calibration data
"""

import json
import re
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

PROFILE_FILE = ROOT / "hephzibah-brain-temp" / "upwork" / "identity" / "profile.md"

# Soft red flag phrases -- applied as penalties in score_job_quality
RED_FLAG_PHRASES = [
    "trial task", "test first", "unpaid test", "free sample",
    "per task", "pay per task", "pay per piece",
    "must be available immediately", "available 24/7",
    "i need someone who can do everything",
    "as needed", "various tasks", "and other duties",
    "asap", "urgent urgent",
]

# Green flag phrases -- applied as bonuses in score_job_quality
GREEN_FLAG_PHRASES = [
    "long-term", "ongoing relationship", "potential for more work",
    "milestone", "clear scope", "specific deliverable",
]

# Phrases that hard-disqualify a job (checked in check_hard_disqualifiers)
HARD_DISQUALIFIERS = [
    "trial task", "test first for free", "unpaid test", "per task payment",
]

# Substrings in client_red_flags that escalate to a forced SKIP
_SKIP_FLAG_SUBSTRINGS = [
    "SKIP",
    "window shopper",
    "0% hire rate",
]


def _has_skip_red_flag(client_red_flags: list[str]) -> bool:
    """Return True if any client red flag is severe enough to force a SKIP."""
    return any(
        any(sub in flag for sub in _SKIP_FLAG_SUBSTRINGS)
        for flag in client_red_flags
    )


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

    # Soft red flag phrases (5pt penalty each, cap at 3 hits)
    soft_red_hits = [p for p in RED_FLAG_PHRASES if p in desc][:3]
    if soft_red_hits:
        penalty = len(soft_red_hits) * 5
        score -= penalty
        reasons.append(f"-{penalty}: soft red flag phrases ({', '.join(soft_red_hits[:2])})")

    # Green flag phrases (4pt bonus each, cap at 2 hits)
    green_hits = [p for p in GREEN_FLAG_PHRASES if p in desc][:2]
    if green_hits:
        bonus = len(green_hits) * 4
        score += bonus
        reasons.append(f"+{bonus}: positive engagement signals ({', '.join(green_hits)})")

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

    payment_verified = data.get("payment_verified", False)  # conservative default
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
        red_flags.append(f"Very low hire rate ({hire_rate:.0f}%) -- window shopper signal")
    elif hire_rate == 0 and jobs_posted >= 5:
        score -= 25
        red_flags.append("0% hire rate with multiple posted jobs -- window shopper")

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
        reasons.append(f"+10: excellent review score ({avg_review:.1f}stars)")
    elif avg_review >= 4.5:
        score += 5
    elif avg_review > 0 and avg_review < 4.0:
        score -= 20
        red_flags.append(f"Low review score ({avg_review:.1f}stars) -- multiple bad experiences")
    elif avg_review > 0 and avg_review < 3.5:
        score -= 35
        red_flags.append(f"Very low review score ({avg_review:.1f}stars) -- SKIP")

    # Active contracts (distraction risk)
    if active_contracts >= 10:
        score -= 15
        red_flags.append(f"Too many active contracts ({active_contracts}) -- won't have bandwidth")
    elif active_contracts >= 6:
        score -= 5

    return max(0, min(100, score)), reasons, red_flags


def score_fit(job_data: dict) -> tuple[int, list[str]]:
    """Score how well this job fits Emmanuel's stack and niche."""
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

    # Niche match (all-industry -- any operational/automation vertical)
    niche_terms = ["medical", "clinic", "healthcare", "saas", "agency", "marketing",
                   "e-commerce", "ecommerce", "logistics", "finance", "real estate",
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
        matched = next(h for h in high_urgency if h in desc)
        reasons.append(f"High urgency: '{matched}'")
    elif any(l in desc for l in low_urgency):
        score = 2
        matched = next(l for l in low_urgency if l in desc)
        reasons.append(f"Low urgency: '{matched}'")

    return score, reasons


def score_competition(data: dict) -> tuple[int, list[str]]:
    proposals = data.get("proposals_count", 0) or 0
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

    # Conservative default: False (unknown payment status = treat as unverified)
    if not client_data.get("payment_verified", False):
        if client_data.get("total_spend_usd", 0) == 0:
            disqualifiers.append("Payment not verified AND zero spend history")

    hire_rate = client_data.get("hire_rate_pct", 0)
    jobs_posted = client_data.get("jobs_posted", 0)
    if hire_rate == 0 and jobs_posted >= 10:
        disqualifiers.append(f"0% hire rate with {jobs_posted} posted jobs")

    avg_review = client_data.get("avg_review_score", 0)
    if avg_review > 0 and avg_review < 3.5:
        disqualifiers.append(f"Average review score {avg_review:.1f} -- too low")

    return disqualifiers


def composite_score(jq: int, cq: int, fit: int, urgency: int, competition: int) -> int:
    return int(
        jq * 0.30 +
        cq * 0.30 +
        fit * 0.25 +
        (urgency / 10 * 100) * 0.08 +
        (competition / 10 * 100) * 0.07
    )


def make_decision(score: int, disqualifiers: list[str], client_red_flags: list[str], fit_score: int) -> str:
    """
    BID / WATCHLIST / SKIP.

    Aligns with CLAUDE.md spec:
      < 65                        -> SKIP
      65-79, fit >= 70            -> BID (strong niche alignment)
      65-79, fit < 70             -> WATCHLIST
      80+                         -> BID
      Any disqualifier or skip-level red flag -> SKIP regardless of score
    """
    if disqualifiers or _has_skip_red_flag(client_red_flags):
        return "SKIP"
    if score < 65:
        return "SKIP"
    if score < 80:
        return "BID" if fit_score >= 70 else "WATCHLIST"
    return "BID"


def load_profile() -> dict:
    """Read profile.md YAML frontmatter. Returns empty dict if file missing."""
    if not PROFILE_FILE.exists():
        return {}
    text = PROFILE_FILE.read_text(encoding="utf-8")
    # Extract content between first --- and second ---
    m = re.search(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}
    block = m.group(1)

    profile = {}

    def _get(key, default=None):
        km = re.search(rf'^{key}\s*:\s*(.+)$', block, re.MULTILINE)
        return km.group(1).strip().strip('"') if km else default

    profile["account_owner"] = _get("account_owner", "unknown")
    profile["badge"] = _get("badge", "none")
    profile["rate_usd"] = float(_get("rate_usd") or 0)
    profile["total_reviews"] = int(_get("total_reviews") or 0)
    jss_raw = _get("jss", "null")
    profile["jss"] = None if jss_raw in ("null", "~", "") else float(jss_raw)
    profile["title"] = _get("title", "")

    # Parse list fields
    def _get_list(key):
        km = re.search(rf'^{key}\s*:\s*\n((?:  - .+\n?)+)', block, re.MULTILINE)
        if not km:
            return []
        return [re.sub(r'^  - ', '', l).strip().strip('"') for l in km.group(1).splitlines() if l.strip()]

    profile["overview_keywords"] = _get_list("overview_keywords")
    profile["skills_listed"] = _get_list("skills_listed")

    # Portfolio categories
    cat_matches = re.findall(r'category:\s*"?([^"\n]+)"?', block)
    profile["portfolio_categories"] = [c.strip() for c in cat_matches if c.strip() != "none"]

    return profile


def score_profile_fit(job_data: dict, client_data: dict, profile: dict) -> tuple[int, list[str], list[str]]:
    """
    Score how well the current profile backs up a proposal for this job.
    Simulates what the client sees when they click through after reading the proposal.

    Returns (score 0-100, reasons, warnings)
    """
    if not profile:
        return 50, ["Profile data not found — using neutral score"], ["Update hephzibah-brain-temp/upwork/identity/profile.md"]

    score = 0
    reasons = []
    warnings = []

    desc = (job_data.get("description") or "").lower()
    title = (job_data.get("title") or "").lower()
    job_text = desc + " " + title

    # 1. JSS / Badge (0-25 pts) ─────────────────────────────────────────────
    badge = profile.get("badge", "none")
    jss = profile.get("jss")
    if jss and jss >= 90:
        score += 25
        reasons.append("+25: JSS 90+ — algorithm-visible credibility")
    elif badge == "top_rated_plus":
        score += 24
        reasons.append("+24: Top Rated Plus badge")
    elif badge == "top_rated":
        score += 20
        reasons.append("+20: Top Rated badge")
    elif badge == "rising_talent":
        score += 12
        reasons.append("+12: Rising Talent badge — partial credibility signal")
        warnings.append("Rising Talent: experienced clients may filter for JSS. Proposal must work harder.")
    else:
        score += 4
        reasons.append("+4: No badge, no JSS — profile credibility is low")
        warnings.append("No badge or JSS: sophisticated clients often skip new accounts.")

    # 2. Profile title keyword match (0-25 pts) ─────────────────────────────
    profile_title = profile.get("title", "").lower()
    job_keywords = re.findall(r'\b\w{4,}\b', title + " " + " ".join(
        re.findall(r'\b(n8n|claude|openai|automation|workflow|ai|agent|react|python|'
                   r'typescript|nextjs|airtable|zapier|make|crm|chatbot|rag)\b', job_text)
    ))
    title_hits = [kw for kw in set(job_keywords) if kw in profile_title]
    if len(title_hits) >= 3:
        score += 25
        reasons.append(f"+25: profile title matches job keywords ({', '.join(title_hits[:4])})")
    elif len(title_hits) == 2:
        score += 18
        reasons.append(f"+18: profile title partially matches ({', '.join(title_hits)})")
    elif len(title_hits) == 1:
        score += 10
        reasons.append(f"+10: one keyword match in title ({title_hits[0]})")
    else:
        score += 0
        warnings.append("Profile title has no keyword overlap with this job — client may not recognise the fit.")

    # 3. Portfolio relevance (0-25 pts) ─────────────────────────────────────
    portfolio_cats = profile.get("portfolio_categories", [])
    job_categories = []
    if any(w in job_text for w in ["automation", "workflow", "n8n", "agent", "crm", "chatbot"]):
        job_categories.append("automation")
    if any(w in job_text for w in ["social media", "instagram", "content", "canva", "ugc"]):
        job_categories.append("social-media")
    if any(w in job_text for w in ["web", "react", "next.js", "dashboard", "portal", "frontend"]):
        job_categories.append("web-dev")
    if any(w in job_text for w in ["email", "newsletter", "mailchimp"]):
        job_categories.append("email-marketing")

    portfolio_hits = [c for c in job_categories if c in portfolio_cats]
    matching_item_count = sum(1 for c in portfolio_cats if c in job_categories)
    if matching_item_count >= 4:
        score += 25
        reasons.append(f"+25: portfolio has {matching_item_count} relevant items ({', '.join(set(portfolio_hits))})")
    elif matching_item_count >= 2:
        score += 18
        reasons.append(f"+18: portfolio has {matching_item_count} relevant items ({', '.join(set(portfolio_hits))})")
    elif matching_item_count == 1:
        score += 10
        reasons.append(f"+10: portfolio has 1 relevant item ({portfolio_hits[0]})")
    elif portfolio_cats:
        score += 5
        reasons.append("+5: portfolio exists but not directly relevant to this job")
        warnings.append("Portfolio items don't match this job category — client will see misalignment.")
    else:
        score += 0
        warnings.append("No portfolio items yet — this is the biggest profile gap. Client asked for examples.")

    # 4. Rate alignment vs client avg paid (0-15 pts) ───────────────────────
    client_avg = client_data.get("avg_hourly_paid", 0) or 0
    profile_rate = profile.get("rate_usd", 0)
    if client_avg > 0 and profile_rate > 0:
        ratio = profile_rate / client_avg
        if ratio <= 1.3:
            score += 15
            reasons.append(f"+15: rate ${profile_rate}/hr close to client avg ${client_avg:.0f}/hr")
        elif ratio <= 2.0:
            score += 8
            reasons.append(f"+8: rate ${profile_rate}/hr above client avg ${client_avg:.0f}/hr but acceptable")
        else:
            score += 3
            reasons.append(f"+3: rate ${profile_rate}/hr significantly above client avg ${client_avg:.0f}/hr")
            warnings.append(f"Rate gap: your ${profile_rate}/hr vs client avg ${client_avg:.0f}/hr. Proposal must justify the premium.")
    else:
        score += 8  # neutral if no data

    # 5. Overview / skills relevance (0-10 pts) ─────────────────────────────
    overview_kws = [kw.lower() for kw in profile.get("overview_keywords", [])]
    skills = [s.lower() for s in profile.get("skills_listed", [])]
    profile_terms = set(overview_kws + skills)
    job_term_hits = [t for t in profile_terms if t in job_text]
    if len(job_term_hits) >= 4:
        score += 10
        reasons.append(f"+10: overview/skills strongly aligned ({', '.join(list(job_term_hits)[:4])})")
    elif len(job_term_hits) >= 2:
        score += 6
        reasons.append(f"+6: overview/skills partially aligned ({', '.join(list(job_term_hits)[:3])})")
    elif len(job_term_hits) == 1:
        score += 3
    else:
        warnings.append("Profile overview/skills have no overlap with job terms.")

    score = max(0, min(100, score))

    # Overall profile warning
    if score < 40:
        warnings.append("PROFILE TOO WEAK for this job — connects risk is high. Build portfolio first.")
    elif score < 55:
        warnings.append("Profile has gaps. Proposal must compensate. Consider whether connects are worth it.")

    return score, reasons, warnings


def qualify_job(filepath: str) -> dict:
    with open(filepath) as f:
        data = json.load(f)

    job_data = data.get("job", data)
    client_data = data.get("client", {})

    profile = load_profile()

    jq, jq_reasons = score_job_quality(job_data)
    cq, cq_reasons, client_red_flags = score_client_quality(client_data)
    fit, fit_reasons = score_fit(job_data)
    urgency, urgency_reasons = score_urgency(job_data)
    competition, competition_reasons = score_competition(job_data)
    pf, pf_reasons, pf_warnings = score_profile_fit(job_data, client_data, profile)
    disqualifiers = check_hard_disqualifiers(job_data, client_data)
    composite = composite_score(jq, cq, fit, urgency, competition)
    dec = make_decision(composite, disqualifiers, client_red_flags, fit)

    # Downgrade BID to WATCHLIST if profile is too weak to back up the proposal
    if dec == "BID" and pf < 40:
        dec = "WATCHLIST"
        dec_note = "Downgraded BID → WATCHLIST: profile fit too weak to justify connects spend."
    elif dec == "BID" and pf < 65:
        dec_note = "BID with caution: profile has gaps — proposal must work harder than usual."
    else:
        dec_note = ""

    return {
        "title": job_data.get("title", "Unknown"),
        "url": job_data.get("url", ""),
        "scores": {
            "job_quality": jq,
            "client_quality": cq,
            "fit_score": fit,
            "urgency": urgency,
            "competition": competition,
            "composite": composite,
            "profile_fit": pf,
        },
        "decision": dec,
        "decision_note": dec_note,
        "profile": {
            "account": profile.get("account_owner", "unknown"),
            "badge": profile.get("badge", "none"),
            "jss": profile.get("jss"),
            "rate_usd": profile.get("rate_usd"),
            "portfolio_items": len(profile.get("portfolio_categories", [])),
        },
        "hard_disqualifiers": disqualifiers,
        "client_red_flags": client_red_flags,
        "profile_warnings": pf_warnings,
        "score_reasons": {
            "job_quality": jq_reasons,
            "client_quality": cq_reasons,
            "fit": fit_reasons,
            "urgency": urgency_reasons,
            "competition": competition_reasons,
            "profile_fit": pf_reasons,
        },
        "evaluated_at": datetime.now().isoformat(),
    }


def qualify_client(filepath: str) -> dict:
    with open(filepath) as f:
        data = json.load(f)

    score, reasons, red_flags = score_client_quality(data)
    return {
        "username": data.get("username", "unknown"),
        "quality_score": score,
        "reasons": reasons,
        "red_flags": red_flags,
        "recommendation": "HIRE" if score >= 65 and not red_flags else "AVOID" if score < 50 else "CAUTION",
        "evaluated_at": datetime.now().isoformat(),
    }


def log_calibration(slug: str, emmanuel_score: int) -> None:
    cal_file = DATA_DIR / "calibration_log.jsonl"
    entry = {
        "date": datetime.now().date().isoformat(),
        "slug": slug,
        "emmanuel_score": emmanuel_score,
    }
    with open(cal_file, "a") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"Calibration logged: {slug} -> {emmanuel_score}")


if __name__ == "__main__":
    args = sys.argv[1:]

    if not args:
        print(__doc__)
        sys.exit(1)

    if args[0] == "--client" and len(args) >= 2:
        print(json.dumps(qualify_client(args[1]), indent=2))
    elif args[0] == "--calibrate" and len(args) >= 3:
        log_calibration(args[1], int(args[2]))
    else:
        print(json.dumps(qualify_job(args[0]), indent=2))
