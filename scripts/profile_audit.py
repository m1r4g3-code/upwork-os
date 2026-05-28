"""
profile_audit.py -- Ramshaw-level Upwork profile audit tool.

Reads current profile state from brain, applies algorithm research +
mentor frameworks (Ramshaw, Hormozi, Belfort), and outputs specific
actionable recommendations with exact text to use.

NOT vague advice -- exact strings to put in your title, overview, skills.

Usage:
  python scripts/profile_audit.py              # full audit
  python scripts/profile_audit.py --section title    # audit one section
  python scripts/profile_audit.py --json       # JSON output for Claude
"""

import sys
import json
import re
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
BRAIN = ROOT / "hephzibah-brain-temp"
PROFILE_NODE = BRAIN / "upwork" / "identity" / "profile.md"
NICHE_NODE = BRAIN / "upwork" / "identity" / "niche.md"
IDENTITY_NODE = BRAIN / "me" / "identity.md"
OUTPUTS = ROOT / "outputs" / "roasts"
OUTPUTS.mkdir(parents=True, exist_ok=True)

# ─── Profile data Emmanuel should maintain ───────────────────────────────────
# This is the ground truth we audit against.
# Claude updates this when Emmanuel updates his profile.

PROFILE_STATE = {
    "title": "",
    "overview_first_two_sentences": "",
    "skills": [],
    "portfolio_count": 0,
    "profile_completion_pct": 0,
    "has_photo": False,
    "hourly_rate": 0,
    "rising_talent": False,
    "top_rated": False,
    "jss": None,
    "reviews_count": 0,
    "availability": "full-time",
}

# ─── Ramshaw's title formula ──────────────────────────────────────────────────
IDEAL_TITLE_STRUCTURE = "Primary Skill | Secondary Skill | Outcome/Niche"
TITLE_EXAMPLE = "AI Workflow Engineer | n8n + Claude API | Automation for SaaS Teams"
TITLE_MAX_CHARS = 70

# ─── Algorithm-backed profile scoring weights ─────────────────────────────────
SECTION_WEIGHTS = {
    "jss": 30,
    "title": 20,
    "overview": 18,
    "portfolio": 15,
    "skills": 10,
    "completeness": 7,
}

# ─── AI slop phrases -- instant red flags in overview ─────────────────────────
AI_SLOP = [
    "i am passionate about",
    "i am dedicated",
    "i am a hard worker",
    "results-driven",
    "detail-oriented",
    "team player",
    "i love helping",
    "i specialize in",
    "i am experienced in",
    "with years of experience",
    "i am proficient",
    "i have a strong background",
    "i am committed to",
    "please feel free",
    "do not hesitate",
    "i look forward to",
    "i hope to hear",
    "leverage",
    "synergy",
    "holistic",
    "robust",
    "cutting-edge",
    "best-in-class",
]

# ─── High-demand skills for n8n/AI automation niche ──────────────────────────
CORE_SKILLS = [
    "n8n", "Workflow Automation", "AI Automation", "Claude API",
    "OpenAI API", "LangChain", "API Integration", "Webhook Integration",
    "Next.js", "React", "TypeScript", "Python", "PostgreSQL",
    "Supabase", "Make.com", "Zapier", "VAPI", "AI Agents",
]

ANTI_SKILLS = [
    "Data Entry", "Virtual Assistant", "General Admin",
    "Social Media Management", "Content Writing",
]


def read_node(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def extract_profile_data() -> dict:
    """Try to extract profile state from brain nodes."""
    profile_text = read_node(PROFILE_NODE).lower()
    identity_text = read_node(IDENTITY_NODE).lower()

    data = {}

    # JSS
    jss_match = re.search(r'jss[^\|]*\|\s*([0-9.]+|--)', profile_text)
    data["jss"] = None if not jss_match or "--" in jss_match.group(1) else float(jss_match.group(1))

    # Reviews
    reviews_match = re.search(r'reviews[^\|]*\|\s*([0-9]+)', profile_text)
    data["reviews_count"] = int(reviews_match.group(1)) if reviews_match else 0

    # Portfolio
    portfolio_match = re.search(r'portfolio pieces[^\|]*\|\s*([0-9]+)', profile_text)
    data["portfolio_count"] = int(portfolio_match.group(1)) if portfolio_match else 0

    # Rate
    rate_match = re.search(r'hourly rate set[^\|]*\|\s*\$?([0-9]+)', profile_text)
    data["hourly_rate"] = int(rate_match.group(1)) if rate_match else 0

    # Profile completion
    comp_match = re.search(r'profile completion[^\|]*\|\s*([0-9]+)', profile_text)
    data["profile_completion_pct"] = int(comp_match.group(1)) if comp_match else 0

    # Top Rated
    data["top_rated"] = "top rated" in profile_text and "no" not in profile_text[profile_text.find("top rated"):profile_text.find("top rated")+20]
    data["rising_talent"] = "rising talent" in profile_text

    return data


def audit_jss(profile: dict) -> dict:
    jss = profile.get("jss")
    score = 0
    issues = []
    recommendations = []

    if jss is None:
        score = 0
        issues.append("JSS not yet established (new account)")
        recommendations.append(
            "PRIORITY: First 3 contracts define your trajectory. "
            "Choose clear-scope, fixed-budget jobs with verified-payment clients. "
            "Aim for 5-star public review + private NPS 9+. "
            "Never let contracts sit idle -- proactively ask clients to close."
        )
    elif jss < 80:
        score = 2
        issues.append(f"JSS {jss}% -- severely limits search visibility")
        recommendations.append("Focus entirely on closing existing contracts cleanly before bidding new work.")
    elif jss < 90:
        score = 5
        issues.append(f"JSS {jss}% -- below Top Rated threshold (90%)")
        recommendations.append("Review all open contracts. Close idle ones. Ask recent clients for reviews.")
    elif jss >= 90:
        score = 10
        recommendations.append(f"JSS {jss}% -- Top Rated territory. Maintain by never ending contracts yourself.")

    return {"score": score, "max": 10, "issues": issues, "recommendations": recommendations}


def audit_title(profile: dict) -> dict:
    title = profile.get("title", "")
    score = 5
    issues = []
    recommendations = []

    if not title:
        score = 0
        issues.append("No title set")
    else:
        if len(title) < 40:
            score -= 2
            issues.append(f"Title too short ({len(title)} chars) -- use all 70 characters")
        if title.lower() in ["software developer", "web developer", "freelancer", "full stack developer"]:
            score -= 3
            issues.append("Generic title -- will not rank for any specific search")
        if "|" not in title and "+" not in title:
            score -= 1
            issues.append("No pipe/separator structure -- harder for algorithm to parse skills")
        if "n8n" not in title.lower() and "automation" not in title.lower() and "ai" not in title.lower():
            score -= 2
            issues.append("Missing primary niche keywords (n8n, automation, AI) -- algorithm can't match you to relevant jobs")

    recommendations.append(
        f"Ideal title format: {IDEAL_TITLE_STRUCTURE}\n"
        f"  Example: \"{TITLE_EXAMPLE}\"\n"
        f"  Max {TITLE_MAX_CHARS} chars. Use all of them. Put most important keyword first."
    )
    return {"score": max(0, min(10, score)), "max": 10, "issues": issues, "recommendations": recommendations}


def audit_overview(profile: dict) -> dict:
    overview = profile.get("overview", "")
    score = 5
    issues = []
    recommendations = []

    if not overview:
        score = 0
        issues.append("No overview set")
    else:
        ov_lower = overview.lower()
        # First word check
        sentences = [s.strip() for s in overview.split(".") if s.strip()]
        if sentences and sentences[0].lower().startswith("i "):
            score -= 2
            issues.append("Overview starts with 'I' -- start with the client's outcome instead")

        # AI slop check
        found_slop = [p for p in AI_SLOP if p in ov_lower]
        if found_slop:
            score -= 2
            issues.append(f"AI slop detected: {', '.join(found_slop[:3])}")

        # Length check
        words = len(overview.split())
        if words > 300:
            score -= 1
            issues.append(f"Overview {words} words -- clients don't read past 300. Cut it.")

        # Specificity check
        if not re.search(r'\d+', overview):
            score -= 1
            issues.append("No specific numbers in overview -- vague claims carry no weight")

        if "?" not in overview and words > 50:
            score -= 0.5

    recommendations.append(
        "Ramshaw overview formula:\n"
        "  Line 1: Client outcome statement (NOT about you)\n"
        "    Example: 'Most SaaS ops teams are still running on spreadsheets and manual Slack pings -- I build the systems that replace that.'\n"
        "  Line 2: Specific proof (1 result, 1 number)\n"
        "    Example: 'Built an intake-to-CRM pipeline that cut a 4-hour/day manual process to 20 minutes.'\n"
        "  Line 3 onward: Stack + niche + who you work with\n"
        "  NEVER: 'I am passionate about', 'I specialize in', 'years of experience', 'results-driven'"
    )
    return {"score": max(0, min(10, score)), "max": 10, "issues": issues, "recommendations": recommendations}


def audit_skills(profile: dict) -> dict:
    skills = profile.get("skills", [])
    score = 5
    issues = []
    recommendations = []

    if not skills:
        score = 0
        issues.append("No skills set")
    else:
        skills_lower = [s.lower() for s in skills]

        # Anti-skills check
        anti_found = [s for s in ANTI_SKILLS if s.lower() in skills_lower]
        if anti_found:
            score -= 2
            issues.append(f"Off-niche skills dilute algorithmic relevance: {', '.join(anti_found)}")

        # Count check
        if len(skills) > 20:
            score -= 1
            issues.append(f"{len(skills)} skills listed -- over 20 weakens algorithmic relevance. Use all 20 slots but keep them coherent.")
        elif len(skills) < 10:
            score -= 2
            issues.append(f"Only {len(skills)} skills listed -- use all 20 slots with tightly focused niche skills")

        # Core skill check
        core_found = [s for s in CORE_SKILLS if s.lower() in skills_lower]
        if len(core_found) < 5:
            score += 0
            missing = [s for s in CORE_SKILLS[:8] if s.lower() not in skills_lower]
            issues.append(f"Missing key niche skills: {', '.join(missing[:5])}")
        else:
            score += 3

    recommendations.append(
        "Ideal 20-skill list for your niche (use all 20 slots):\n"
        "  Tier 1 -- Core (must be first): n8n, AI Automation, Workflow Automation, API Integration, Claude API\n"
        "  Tier 2 -- Technical: OpenAI API, Make.com, Python, TypeScript, Next.js, React, Webhook Integration\n"
        "  Tier 3 -- Supporting: Supabase, PostgreSQL, LangChain, AI Agents, VAPI, Zapier, Playwright\n"
        "  DO NOT include: Data Entry, Virtual Assistant, General Admin, Content Writing"
    )
    return {"score": max(0, min(10, score)), "max": 10, "issues": issues, "recommendations": recommendations}


def audit_portfolio(profile: dict) -> dict:
    count = profile.get("portfolio_count", 0)
    score = 0
    issues = []
    recommendations = []

    if count == 0:
        score = 0
        issues.append("No portfolio items -- profile cannot compete without proof")
    elif count == 1:
        score = 3
        issues.append("Only 1 portfolio item -- minimum 3 before serious bidding")
    elif count < 3:
        score = 5
        issues.append(f"{count} portfolio items -- add 1 more before heavy bidding")
    elif count >= 3:
        score = 8

    recommendations.append(
        "Portfolio items to build right now (from your GitHub):\n\n"
        "1. n8n-Aigent-app -- Loom video walkthrough (60-90 sec) showing the webhook -> AI agent -> response flow\n"
        "   Title: 'Webhook-Driven AI Agent Workflow Manager'\n"
        "   Description: Show 1 specific flow. Name the outcome. Screenshot the n8n canvas.\n\n"
        "2. Distill -- Screen recording feeding a URL, showing the structured JSON output\n"
        "   Title: 'URL -> Structured JSON for AI Pipelines and RAG Systems'\n"
        "   Use case: 'Feed any webpage into your n8n workflow as clean structured data'\n\n"
        "3. Case study placeholder for the German clinic work\n"
        "   Title: 'AI Workflow System for Medical Admin Team'\n"
        "   Note: Cannot claim this as an Upwork job. Frame as: 'Prior client engagement -- 4 production workflows built in 4 days'\n"
        "   Show the outcome, not the client. Use metrics if you have them.\n\n"
        "Each portfolio item MUST include:\n"
        "  - SAR format: Situation (stakes) -> Action (what you built) -> Result (specific outcome)\n"
        "  - At least 1 screenshot OR Loom walkthrough\n"
        "  - Tech stack listed"
    )
    return {"score": score, "max": 10, "issues": issues, "recommendations": recommendations}


def audit_rate(profile: dict) -> dict:
    rate = profile.get("hourly_rate", 0)
    score = 5
    issues = []
    recommendations = []

    if rate == 0:
        score = 0
        issues.append("No hourly rate set")
    elif rate < 25:
        score = 2
        issues.append(f"${rate}/hr signals low-quality positioning. Clients who pay $10/hr are your worst JSS risk.")
    elif rate < 40:
        score = 5
        issues.append(f"${rate}/hr is acceptable for new account but leave room to grow")
    elif rate <= 75:
        score = 8
    else:
        score = 10

    recommendations.append(
        "Rate strategy for new account:\n"
        "  Starting rate: $35-$45/hr (competitive, not desperate)\n"
        "  After first 2 reviews: $50-$65/hr\n"
        "  After Top Rated: $75-$100/hr\n"
        "  Target ceiling: $100-$150/hr (n8n + AI agents, architecture-level work)\n\n"
        "Ramshaw principle: Never anchor below $35/hr. Clients who budget $10/hr "
        "will also give you 3-star reviews and fight over scope. They cost JSS, not just time.\n\n"
        "For fixed-price: price projects at what 8 hours of $50/hr work looks like minimum."
    )
    return {"score": score, "max": 10, "issues": issues, "recommendations": recommendations}


def audit_completeness(profile: dict) -> dict:
    pct = profile.get("profile_completion_pct", 0)
    has_photo = profile.get("has_photo", False)
    score = 0
    issues = []
    recommendations = []

    if pct < 100:
        issues.append(f"Profile completion: {pct}% -- must be 100% for Rising Talent eligibility and full algorithm indexing")
        score = int(pct / 10)
    else:
        score = 8

    if not has_photo:
        score -= 2
        issues.append("No professional photo -- non-negotiable for Rising Talent and client trust")

    recommendations.append(
        "100% profile checklist:\n"
        "  [[OK]] Professional photo (not a logo, not blurry, face clearly visible)\n"
        "  [ ] Title -- 70 characters, pipe structure\n"
        "  [ ] Overview -- client-outcome first, 150-300 words, no AI slop\n"
        "  [ ] Skills -- all 20 slots filled, coherent niche\n"
        "  [ ] Portfolio -- minimum 3 items\n"
        "  [ ] Hourly rate set\n"
        "  [ ] Education (Miva Open University -- list it)\n"
        "  [ ] Employment history (freelance work -- list the German clinic engagement as: 'AI Workflow Consultant, Independent, 2025-present')\n"
        "  [ ] Languages (English)\n"
        "  [ ] Availability set to actively looking"
    )
    return {"score": max(0, min(10, score)), "max": 10, "issues": issues, "recommendations": recommendations}


def run_full_audit(profile_override: dict = None) -> dict:
    profile = profile_override or extract_profile_data()

    sections = {
        "jss": audit_jss(profile),
        "title": audit_title(profile),
        "overview": audit_overview(profile),
        "portfolio": audit_portfolio(profile),
        "skills": audit_skills(profile),
        "rate": audit_rate(profile),
        "completeness": audit_completeness(profile),
    }

    # Weighted overall score
    weight_map = {"jss": 30, "title": 20, "overview": 18, "portfolio": 15, "skills": 10, "rate": 4, "completeness": 3}
    total_weight = sum(weight_map.values())
    weighted_sum = sum(sections[k]["score"] * weight_map.get(k, 5) for k in sections)
    overall = round(weighted_sum / total_weight)

    return {
        "overall_score": overall,
        "overall_max": 10,
        "grade": _grade(overall),
        "sections": sections,
        "audited_at": datetime.now().isoformat(),
    }


def _grade(score: int) -> str:
    if score >= 9: return "ELITE -- submit 40+ proposals/month"
    if score >= 7: return "COMPETITIVE -- ready to bid actively"
    if score >= 5: return "FUNCTIONAL -- fix priority issues first"
    if score >= 3: return "WEAK -- algorithm will suppress you"
    return "NOT READY -- fix before bidding anything"


def print_audit(audit: dict) -> None:
    bar = "=" * 58
    overall = audit["overall_score"]
    grade = audit["grade"]

    print(f"\n{bar}")
    print(f"UPWORK PROFILE AUDIT -- {datetime.now().strftime('%Y-%m-%d')}")
    print(f"OVERALL: {overall}/10 -- {grade}")
    print(bar)

    weight_map = {"jss": 30, "title": 20, "overview": 18, "portfolio": 15, "skills": 10, "rate": 4, "completeness": 3}

    for section, data in audit["sections"].items():
        weight = weight_map.get(section, 5)
        score = data["score"]
        bar_fill = "#" * score + "." * (10 - score)
        print(f"\n[{section.upper()}] {score}/10  {bar_fill}  (weight: {weight}%)")

        if data["issues"]:
            for issue in data["issues"]:
                print(f"  ! {issue}")

        for rec in data["recommendations"]:
            print(f"\n  RECOMMENDATION:")
            for line in rec.split("\n"):
                print(f"    {line}")

    print(f"\n{bar}")
    print(f"PRIORITY ACTION ORDER (by algorithm impact):")
    # Sort sections by weight * (10 - score) to find highest-impact gaps
    gaps = sorted(
        [(section, weight_map.get(section, 5) * (10 - data["score"])) for section, data in audit["sections"].items()],
        key=lambda x: x[1], reverse=True
    )
    for i, (section, gap) in enumerate(gaps[:5], 1):
        if gap > 0:
            print(f"  {i}. Fix {section.upper()} (impact score: {gap})")
    print()


def save_output(audit: dict) -> Path:
    date_str = datetime.now().strftime("%Y-%m-%d")
    output_path = OUTPUTS / f"{date_str}-profile-audit.md"

    overall = audit["overall_score"]
    grade = audit["grade"]

    lines = [
        f"# Profile Audit -- {date_str}",
        f"**Date:** {date_str}",
        f"**Command:** /profile-audit",
        f"**Status:** final",
        f"**Overall Score:** {overall}/10 -- {grade}",
        "",
        "---",
        "",
        "## Section Scores",
        "",
        "| Section | Score | Weight |",
        "|---|---|---|",
    ]

    weight_map = {"jss": 30, "title": 20, "overview": 18, "portfolio": 15, "skills": 10, "rate": 4, "completeness": 3}
    for section, data in audit["sections"].items():
        w = weight_map.get(section, 5)
        lines.append(f"| {section.upper()} | {data['score']}/10 | {w}% |")

    lines += ["", "---", ""]

    for section, data in audit["sections"].items():
        lines.append(f"## {section.upper()}")
        lines.append("")
        if data["issues"]:
            lines.append("**Issues:**")
            for issue in data["issues"]:
                lines.append(f"- {issue}")
            lines.append("")
        if data["recommendations"]:
            lines.append("**Recommendations:**")
            for rec in data["recommendations"]:
                lines.append(rec)
            lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


if __name__ == "__main__":
    args = sys.argv[1:]
    output_json = "--json" in args

    # Allow profile override via JSON arg
    profile_override = None
    if "--profile" in args:
        idx = args.index("--profile") + 1
        try:
            profile_override = json.loads(args[idx])
        except (json.JSONDecodeError, IndexError):
            print("ERROR: --profile expects a JSON string", file=sys.stderr)
            sys.exit(1)

    section_filter = None
    if "--section" in args:
        idx = args.index("--section") + 1
        section_filter = args[idx] if idx < len(args) else None

    audit = run_full_audit(profile_override)

    if section_filter and section_filter in audit["sections"]:
        filtered = {
            "overall_score": audit["sections"][section_filter]["score"],
            "overall_max": 10,
            "grade": "",
            "sections": {section_filter: audit["sections"][section_filter]},
            "audited_at": audit["audited_at"],
        }
        audit = filtered

    if output_json:
        print(json.dumps(audit, indent=2))
    else:
        print_audit(audit)
        output_path = save_output(audit)
        print(f"Saved to: {output_path.relative_to(ROOT)}")
