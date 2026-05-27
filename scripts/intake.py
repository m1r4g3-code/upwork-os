"""
intake.py — Job intake processor.

Takes raw job text (pasted from Upwork) + manual client stats,
structures it as JSON, runs qualify.py, and creates a job card in the brain.

This is the PRIMARY workflow for /job-qualify when scraping isn't available.

Usage:
  python scripts/intake.py                          # interactive mode
  python scripts/intake.py --file sources/jobs/x.txt  # process text file
  python scripts/intake.py --json sources/jobs/x.json # already structured

Output:
  1. sources/jobs/YYYY-MM-DD-<slug>.json  (raw data — immutable)
  2. hephzibah-brain-temp/upwork/jobs/archive/YYYY-MM-DD-<slug>.md  (job card)
  3. Prints score + bid/skip decision
"""

import sys
import json
import re
import subprocess
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
SOURCES = ROOT / "sources" / "jobs"
SOURCES.mkdir(parents=True, exist_ok=True)
BRAIN = ROOT / "hephzibah-brain-temp"
JOBS_ARCHIVE = BRAIN / "upwork" / "jobs" / "archive"
JOBS_ARCHIVE.mkdir(parents=True, exist_ok=True)
TEMPLATE = BRAIN / "upwork" / "jobs" / "_template.md"


def slugify(text: str, date: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'\s+', '-', text.strip())
    text = text[:40].rstrip('-')
    return f"{date}-{text}"


def gather_job_data_interactive() -> dict:
    print("\nUPWORK JOB INTAKE")
    print("Paste the job info. Press Enter after each field.\n")

    data = {"job": {}, "client": {}}

    data["job"]["title"] = input("Job title: ").strip()
    data["job"]["url"] = input("Job URL (or press Enter to skip): ").strip()

    print("Job description (paste, then type END on a new line):")
    lines = []
    while True:
        line = input()
        if line.strip().upper() == "END":
            break
        lines.append(line)
    data["job"]["description"] = "\n".join(lines)

    jtype = input("Job type — fixed or hourly? [f/h]: ").strip().lower()
    if jtype == "h":
        data["job"]["job_type"] = "hourly"
        rate = input("Hourly rate range (e.g. 25-75): ").strip()
        nums = re.findall(r'\d+', rate)
        if nums:
            data["job"]["hourly_rate_min"] = int(nums[0])
            data["job"]["hourly_rate_max"] = int(nums[1]) if len(nums) > 1 else int(nums[0])
    else:
        data["job"]["job_type"] = "fixed"
        budget = input("Budget range (e.g. 500-2000): ").strip()
        nums = re.findall(r'\d+', budget)
        if nums:
            data["job"]["budget_min"] = int(nums[0])
            data["job"]["budget_max"] = int(nums[1]) if len(nums) > 1 else int(nums[0])

    data["job"]["days_posted"] = int(input("Days since posted [0]: ").strip() or "0")
    data["job"]["proposals_count"] = int(input("Competing proposals [0]: ").strip() or "0")

    print("\nCLIENT INFO (from the job sidebar):")
    data["client"]["username"] = input("Client username/name: ").strip()
    data["client"]["country"] = input("Country: ").strip()

    pay_verified = input("Payment verified? [y/n]: ").strip().lower()
    data["client"]["payment_verified"] = pay_verified == "y"

    spend = input("Total spent on Upwork (e.g. 5000, or 0): ").strip()
    data["client"]["total_spend_usd"] = float(re.sub(r'[,$]', '', spend) or "0")

    hire_rate = input("Hire rate % (e.g. 45): ").strip()
    data["client"]["hire_rate_pct"] = float(hire_rate or "0")

    avg_hourly = input("Avg hourly paid to freelancers (0 if unknown): ").strip()
    data["client"]["avg_hourly_paid"] = float(avg_hourly or "0")

    avg_review = input("Client review score 1-5 (0 if no reviews): ").strip()
    data["client"]["avg_review_score"] = float(avg_review or "0")

    active = input("Active contracts [0]: ").strip()
    data["client"]["active_contracts"] = int(active or "0")

    total_hires = input("Total hires [0]: ").strip()
    data["client"]["total_hires"] = int(total_hires or "0")

    jobs_posted = input("Jobs posted [0]: ").strip()
    data["client"]["jobs_posted"] = int(jobs_posted or "0")

    return data


def create_job_card(data: dict, scores: dict, slug: str) -> Path:
    """Write a job card markdown file to the brain."""
    job = data.get("job", {})
    client = data.get("client", {})
    date_str = datetime.now().date().isoformat()
    card_path = JOBS_ARCHIVE / f"{slug}.md"

    decision = scores.get("decision", "SKIP")
    composite = scores.get("scores", {}).get("composite", 0)
    jq = scores.get("scores", {}).get("job_quality", 0)
    cq = scores.get("scores", {}).get("client_quality", 0)
    fit = scores.get("scores", {}).get("fit_score", 0)
    urgency = scores.get("scores", {}).get("urgency", 0)
    competition = scores.get("scores", {}).get("competition", 0)
    disqualifiers = scores.get("hard_disqualifiers", [])
    client_red_flags = scores.get("client_red_flags", [])
    all_red_flags = disqualifiers + client_red_flags

    budget_str = ""
    if job.get("job_type") == "hourly":
        lo = job.get("hourly_rate_min", 0)
        hi = job.get("hourly_rate_max", 0)
        budget_str = f"${lo}–${hi}/hr" if hi else f"${lo}/hr"
    else:
        lo = job.get("budget_min", 0)
        hi = job.get("budget_max", 0)
        budget_str = f"${lo:,}–${hi:,}" if hi and hi != lo else f"${lo:,}"

    frontmatter = f"""---
sensitivity: private
entity_type: job
name: "{job.get('title', '')}"
url: "{job.get('url', '')}"
posted: "{date_str}"
evaluated: "{date_str}"
scores:
  job_quality: {jq}
  client_quality: {cq}
  fit_score: {fit}
  urgency: {urgency}
  competition: {competition}
composite_score: {composite}
decision: "{decision.lower()}"
decision_rationale: ""
bid_amount: ""
budget_posted: "{budget_str}"
client_spend: "${client.get('total_spend_usd', 0):,.0f}"
client_hire_rate: "{client.get('hire_rate_pct', 0):.0f}%"
client_country: "{client.get('country', '')}"
client_username: "{client.get('username', '')}"
client_avg_review: {client.get('avg_review_score', 0)}
red_flags: {json.dumps(all_red_flags)}
green_flags: []
jss_risk: "{'high' if all_red_flags else 'low'}"
status: "{'evaluated' if decision != 'bid' else 'proposal-sent'}"
proposal_file: ""
connects_spent: 0
forced_bid: false
---"""

    desc_preview = job.get("description", "")[:300].replace("\n", " ")
    if len(job.get("description", "")) > 300:
        desc_preview += "..."

    body = f"""
# {job.get('title', 'Untitled Job')}

**URL:** {job.get('url', '—')}
**Client:** {client.get('username', '—')} | {client.get('country', '—')} | ${client.get('total_spend_usd', 0):,.0f} spent | {client.get('hire_rate_pct', 0):.0f}% hire rate | {client.get('avg_review_score', 0)}★
**Budget:** {budget_str} | {job.get('job_type', '—')}
**Competing proposals:** {job.get('proposals_count', 0)}

---

## Job Description (Summary)

{desc_preview}

---

## Score Breakdown

| Factor | Score | Rationale |
|---|---|---|
| Job quality | {jq} | |
| Client quality | {cq} | |
| Fit score | {fit} | |
| Urgency | {urgency}/10 | |
| Competition | {competition}/10 | |
| **Composite** | **{composite}** | |

---

## Red Flags

{chr(10).join(f'- {f}' for f in all_red_flags) if all_red_flags else 'None'}

## Green Flags

[Add after review]

---

## Decision: {decision}

**Rationale:** [Fill in after reviewing scores above]

**Positioning angle (if bid):** [How to frame the proposal]

---

## Proposal Notes

[Key points to hit — diagnosis frame, proof to use, question to ask]
"""

    card_path.write_text(frontmatter + body, encoding="utf-8")
    return card_path


def run_qualify(json_path: Path) -> dict:
    result = subprocess.run(
        ["python", "scripts/qualify.py", str(json_path)],
        cwd=ROOT, capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"qualify.py error: {result.stderr}", file=sys.stderr)
        return {}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {}


def print_summary(scores: dict, card_path: Path) -> None:
    composite = scores.get("scores", {}).get("composite", 0)
    decision = scores.get("decision", "SKIP")
    disq = scores.get("hard_disqualifiers", [])
    red = scores.get("client_red_flags", [])

    bar = "=" * 52
    print(f"\n{bar}")
    print(f"COMPOSITE SCORE: {composite}/100   DECISION: {decision}")
    print(bar)

    s = scores.get("scores", {})
    print(f"  Job quality:    {s.get('job_quality', 0)}/100")
    print(f"  Client quality: {s.get('client_quality', 0)}/100")
    print(f"  Fit score:      {s.get('fit_score', 0)}/100")
    print(f"  Urgency:        {s.get('urgency', 0)}/10")
    print(f"  Competition:    {s.get('competition', 0)}/10")

    if disq or red:
        print(f"\nRED FLAGS / DISQUALIFIERS:")
        for f in disq + red:
            print(f"  ! {f}")

    print(f"\nJob card saved: {card_path.name}")
    print(f"Location: {card_path.relative_to(ROOT)}")

    if decision == "BID":
        print(f"\nNEXT: run /write-proposal {card_path.name}")
    elif decision == "WATCHLIST":
        print(f"\nNEXT: monitor — re-evaluate if niche fit strengthens")
    else:
        print(f"\nSKIP. Connects saved.")
    print()


if __name__ == "__main__":
    args = sys.argv[1:]
    date_str = datetime.now().strftime("%Y-%m-%d")

    if "--file" in args:
        idx = args.index("--file") + 1
        text = Path(args[idx]).read_text(encoding="utf-8")
        data = {"job": {"description": text, "title": "Pasted Job", "job_type": "fixed"}, "client": {}}
        print("Loaded from file. Fill in remaining details:")
        data["job"]["title"] = input("Job title: ").strip() or "Pasted Job"
    elif "--json" in args:
        idx = args.index("--json") + 1
        with open(args[idx]) as f:
            data = json.load(f)
    else:
        data = gather_job_data_interactive()

    slug = slugify(data["job"].get("title", "job"), date_str)
    json_path = SOURCES / f"{slug}.json"
    with open(json_path, "w") as f:
        json.dump(data, f, indent=2)

    scores = run_qualify(json_path)
    if not scores:
        print(f"Scoring failed. Raw data saved to {json_path}")
        sys.exit(1)

    card_path = create_job_card(data, scores, slug)
    print_summary(scores, card_path)
