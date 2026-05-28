"""
scraper.py -- Upwork job and client scraper (Playwright).

Scrapes job pages and client profiles into structured JSON for qualify.py.

FIRST-TIME SETUP (run once, then forget):
  python scripts/scraper.py --setup

USAGE:
  python scripts/scraper.py <upwork-job-url>
  python scripts/scraper.py --client <upwork-username>

OUTPUT:
  sources/jobs/YYYY-MM-DD-<slug>.json  (then pipe to qualify.py)
"""

import sys
import json
import re
import os
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
SOURCES_JOBS = ROOT / "sources" / "jobs"
SOURCES_JOBS.mkdir(parents=True, exist_ok=True)
SESSION_FILE = ROOT / "data" / "upwork_session.json"


# ---------------------------------------------------------------------------
# Session setup
# ---------------------------------------------------------------------------

def setup_session() -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright not installed. Run:")
        print("  pip install playwright")
        print("  playwright install chromium")
        sys.exit(1)

    print()
    print("+------------------------------------------+")
    print("|  Upwork Session Setup (run once only)    |")
    print("+------------------------------------------+")
    print()
    print("A browser window will open. Log into Upwork normally.")
    print("Come back here and press Enter when you are fully logged in.")
    print()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://www.upwork.com/login")

        input(">> Logged in? Press Enter to save session and close browser...")

        cookies = context.cookies()
        SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SESSION_FILE, "w") as f:
            json.dump(cookies, f, indent=2)

        browser.close()

    print(f"Session saved to {SESSION_FILE}")
    print()
    print("You can now run the scraper on any Upwork job URL.")
    print("If you get logged-out errors later, just run --setup again.")


def _check_session() -> list:
    if not SESSION_FILE.exists():
        print("No Upwork session found.")
        print("Run first: python scripts/scraper.py --setup")
        sys.exit(1)
    with open(SESSION_FILE) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Text-based extraction (robust against Upwork frontend changes)
# ---------------------------------------------------------------------------

def _parse_spend(text: str) -> float:
    """Parse spend strings like '$5K', '$12,000', '$1.2M' into float."""
    text = text.strip().replace(",", "")
    m = re.search(r'\$?([\d.]+)([KkMm]?)', text)
    if not m:
        return 0.0
    val = float(m.group(1))
    suffix = m.group(2).upper()
    if suffix == "K":
        val *= 1000
    elif suffix == "M":
        val *= 1_000_000
    return val


def parse_job_page(text: str, url: str) -> dict:
    """
    Extract structured job data from Upwork job page visible text.
    Regex-based so it survives Upwork's frequent CSS class changes.
    """
    job = {"url": url}
    client = {}

    lines = [l.strip() for l in text.splitlines() if l.strip()]
    full = "\n".join(lines)

    # --- Title: first long-ish line that doesn't look like nav/header ---
    skip_starts = ("upwork", "find jobs", "log in", "sign up", "back to", "jobs >", "category")
    for line in lines[:30]:
        if len(line) > 15 and not any(line.lower().startswith(s) for s in skip_starts):
            job["title"] = line
            break

    # --- Budget / Rate ---
    hourly_m = re.search(
        r'\$\s*([\d,.]+)\s*[-–]\s*\$([\d,.]+)\s*/\s*hr', full, re.IGNORECASE
    ) or re.search(r'\$\s*([\d,.]+)\s*/\s*hr', full, re.IGNORECASE)

    fixed_m = re.search(
        r'\$\s*([\d,]+)\s*[-–]\s*\$\s*([\d,]+)\s+[Ff]ix', full
    ) or re.search(r'[Ff]ixed.{0,30}\$\s*([\d,]+)', full) or re.search(
        r'\$\s*([\d,]+)\s+[Ff]ixed', full
    )

    if hourly_m:
        job["job_type"] = "hourly"
        nums = [float(n.replace(",", "")) for n in hourly_m.groups() if n]
        job["hourly_rate_min"] = nums[0]
        job["hourly_rate_max"] = nums[1] if len(nums) > 1 else nums[0]
    elif fixed_m:
        job["job_type"] = "fixed"
        nums = [float(n.replace(",", "")) for n in fixed_m.groups() if n]
        job["budget_min"] = nums[0]
        job["budget_max"] = nums[1] if len(nums) > 1 else nums[0]
    else:
        job["job_type"] = "unknown"

    # --- Proposals count ---
    prop_m = re.search(r'(\d+)\s+(?:to\s+\d+\s+)?[Pp]roposals?', full) or \
             re.search(r'[Pp]roposals?\s*[:\-]?\s*(\d+)', full) or \
             re.search(r'Less than (\d+) bids?', full, re.IGNORECASE)
    if prop_m:
        job["proposals_count"] = int(prop_m.group(1))

    # --- Posted time ---
    posted_m = re.search(
        r'[Pp]osted\s+(just now|\d+\s+(?:minute|hour|day|week|month)s?\s+ago)', full
    )
    if posted_m:
        job["posted_text"] = posted_m.group(1)
        pt = posted_m.group(1).lower()
        if "minute" in pt or "just now" in pt:
            job["days_posted"] = 0
        elif "hour" in pt:
            job["days_posted"] = 0
        elif "day" in pt:
            n = re.search(r'(\d+)', pt)
            job["days_posted"] = int(n.group(1)) if n else 1
        elif "week" in pt:
            n = re.search(r'(\d+)', pt)
            job["days_posted"] = (int(n.group(1)) if n else 1) * 7
        elif "month" in pt:
            n = re.search(r'(\d+)', pt)
            job["days_posted"] = (int(n.group(1)) if n else 1) * 30

    # --- Skills ---
    skills = re.findall(r'(?:Skills?|Expertise)[:\s]+([^\n]+)', full, re.IGNORECASE)
    if skills:
        job["skills"] = [s.strip() for s in re.split(r'[,|]', skills[0]) if s.strip()]

    # --- Project length / experience ---
    duration_m = re.search(
        r'(\d+\s+to\s+\d+\s+months?|\d+\s+months?|Less than \d+ month|More than \d+ month'
        r'|\blong.?term\b|\bshort.?term\b)', full, re.IGNORECASE
    )
    if duration_m:
        job["duration"] = duration_m.group(1)

    # --- Description: largest contiguous block between known anchors ---
    desc_m = re.search(
        r'(?:Description|About the project|Job Details)[:\n]+(.{200,}?)(?:\n(?:Skills|Budget|Client|About the client|'
        r'Expertise|Project Type|Experience Level|Posted|Proposals))',
        full, re.IGNORECASE | re.DOTALL
    )
    if desc_m:
        job["description"] = desc_m.group(1).strip()
    else:
        # Fallback: longest paragraph
        paragraphs = [p.strip() for p in full.split("\n\n") if len(p.strip()) > 100]
        if paragraphs:
            job["description"] = max(paragraphs, key=len)

    # --- Client: Payment verified ---
    client["payment_verified"] = bool(re.search(r'[Pp]ayment\s+[Vv]erified', full))

    # --- Client: Country ---
    country_m = re.search(r'(?:Location|From)[:\s]+([A-Z][a-zA-Z\s,]+?)(?:\n|$)', full)
    if country_m:
        client["country"] = country_m.group(1).strip()

    # --- Client: Total spent ---
    spent_m = re.search(r'(?:Total\s+[Ss]pent|Spent)[:\s]+(\$?[\d,.]+[KkMm]?)', full) or \
              re.search(r'(\$[\d,.]+[KkMm]?)\s+total\s+spent', full, re.IGNORECASE)
    if spent_m:
        client["total_spend_usd"] = _parse_spend(spent_m.group(1))

    # --- Client: Hire rate ---
    hire_m = re.search(r'(\d+)%?\s+[Hh]ire\s+[Rr]ate', full) or \
             re.search(r'[Hh]ire\s+[Rr]ate[:\s]+(\d+)%', full)
    if hire_m:
        client["hire_rate_pct"] = float(hire_m.group(1))

    # --- Client: Rating ---
    rating_m = re.search(r'([\d.]+)\s+of\s+5', full) or \
               re.search(r'Rating[:\s]+([\d.]+)', full, re.IGNORECASE)
    if rating_m:
        client["avg_review_score"] = float(rating_m.group(1))

    # --- Client: Jobs posted ---
    posted_jobs_m = re.search(r'(\d+)\s+[Jj]obs?\s+[Pp]osted', full) or \
                    re.search(r'[Jj]obs?\s+[Pp]osted[:\s]+(\d+)', full)
    if posted_jobs_m:
        client["jobs_posted"] = int(posted_jobs_m.group(1))

    # --- Client: Total hires ---
    hires_m = re.search(r'(\d+)\s+[Hh]ires?(?:\s|$)', full) or \
              re.search(r'[Hh]ires?[:\s]+(\d+)', full)
    if hires_m:
        client["total_hires"] = int(hires_m.group(1))

    # --- Client: Active contracts ---
    active_m = re.search(r'(\d+)\s+[Aa]ctive?', full) or \
               re.search(r'[Aa]ctive[:\s]+(\d+)', full)
    if active_m:
        client["active_contracts"] = int(active_m.group(1))

    # --- Client: Avg hourly paid ---
    avg_m = re.search(r'[Aa]vg\.\s+[Hh]ourly\s+[Rr]ate\s+[Pp]aid[:\s]+\$([\d.]+)', full) or \
            re.search(r'\$([\d.]+)\s+[Aa]vg\.\s+[Hh]ourly', full)
    if avg_m:
        client["avg_hourly_paid"] = float(avg_m.group(1))

    return {"job": job, "client": client}


def parse_client_page(text: str, username: str) -> dict:
    """Extract client stats from a client profile page."""
    client = {"username": username}
    full = "\n".join(l.strip() for l in text.splitlines() if l.strip())

    client["payment_verified"] = bool(re.search(r'[Pp]ayment\s+[Vv]erified', full))

    country_m = re.search(r'(?:Location|From)[:\s]+([A-Z][a-zA-Z\s,]+?)(?:\n|$)', full)
    if country_m:
        client["country"] = country_m.group(1).strip()

    spent_m = re.search(r'(?:Total\s+[Ss]pent|Spent)[:\s]+(\$?[\d,.]+[KkMm]?)', full)
    if spent_m:
        client["total_spend_usd"] = _parse_spend(spent_m.group(1))

    hire_m = re.search(r'(\d+)%?\s+[Hh]ire\s+[Rr]ate', full)
    if hire_m:
        client["hire_rate_pct"] = float(hire_m.group(1))

    rating_m = re.search(r'([\d.]+)\s+of\s+5', full)
    if rating_m:
        client["avg_review_score"] = float(rating_m.group(1))

    jobs_m = re.search(r'(\d+)\s+[Jj]obs?\s+[Pp]osted', full)
    if jobs_m:
        client["jobs_posted"] = int(jobs_m.group(1))

    hires_m = re.search(r'(\d+)\s+[Hh]ires?', full)
    if hires_m:
        client["total_hires"] = int(hires_m.group(1))

    avg_m = re.search(r'[Aa]vg\.\s+[Hh]ourly[^$]*\$([\d.]+)', full)
    if avg_m:
        client["avg_hourly_paid"] = float(avg_m.group(1))

    return {"job": {}, "client": client}


# ---------------------------------------------------------------------------
# Playwright fetch
# ---------------------------------------------------------------------------

def fetch_page_text(url: str) -> str:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright not installed. Run:")
        print("  pip install playwright")
        print("  playwright install chromium")
        sys.exit(1)

    cookies = _check_session()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        )
        context.add_cookies(cookies)
        page = context.new_page()

        print(f"Loading: {url}")
        try:
            page.goto(url, wait_until="networkidle", timeout=30000)
        except Exception:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)

        page.wait_for_timeout(2500)

        # Check if we got redirected to login (session expired)
        current_url = page.url
        if "login" in current_url or "signup" in current_url:
            browser.close()
            print()
            print("Session expired. Re-run setup:")
            print("  python scripts/scraper.py --setup")
            sys.exit(1)

        text = page.inner_text("body")
        browser.close()

    return text


# ---------------------------------------------------------------------------
# Slug + save
# ---------------------------------------------------------------------------

def slug_from_url(url: str) -> str:
    m = re.search(r'~([a-zA-Z0-9]+)', url)
    if m:
        return m.group(1)[:12]
    return datetime.now().strftime("%H%M%S")


def save_output(data: dict, slug: str) -> Path:
    date_str = datetime.now().strftime("%Y-%m-%d")
    out = SOURCES_JOBS / f"{date_str}-{slug}.json"
    with open(out, "w") as f:
        json.dump(data, f, indent=2)
    return out


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    args = sys.argv[1:]

    if not args or "--help" in args:
        print(__doc__)
        sys.exit(0)

    if "--setup" in args:
        setup_session()
        sys.exit(0)

    if "--client" in args:
        idx = args.index("--client")
        username = args[idx + 1] if idx + 1 < len(args) else None
        if not username:
            print("Usage: python scripts/scraper.py --client <username>")
            sys.exit(1)
        profile_url = f"https://www.upwork.com/companies/{username}"
        text = fetch_page_text(profile_url)
        data = parse_client_page(text, username)
        out = save_output(data, f"client-{username}")
        print(f"Saved: {out}")
        print(f"Next:  python scripts/qualify.py --client {out}")
        sys.exit(0)

    url = args[0]
    if not url.startswith("http"):
        print(f"Expected a URL. Got: {url}")
        print("Usage: python scripts/scraper.py <upwork-job-url>")
        sys.exit(1)

    slug = slug_from_url(url)
    text = fetch_page_text(url)
    data = parse_job_page(text, url)
    out = save_output(data, slug)

    # Print what was extracted for quick review
    job = data.get("job", {})
    client = data.get("client", {})
    print()
    print(f"  Title:    {job.get('title', 'not found')}")
    print(f"  Type:     {job.get('job_type', '?')}", end="  ")
    if job.get("job_type") == "hourly":
        print(f"${job.get('hourly_rate_min', '?')}-${job.get('hourly_rate_max', '?')}/hr")
    elif job.get("job_type") == "fixed":
        print(f"${job.get('budget_min', '?')}-${job.get('budget_max', '?')}")
    else:
        print()
    print(f"  Proposals:{job.get('proposals_count', '?')}")
    print(f"  Posted:   {job.get('posted_text', job.get('days_posted', '?'))}")
    print(f"  Client:   {client.get('country', '?')} | "
          f"${client.get('total_spend_usd', 0):,.0f} spent | "
          f"{client.get('hire_rate_pct', '?')}% hire rate | "
          f"payment {'verified' if client.get('payment_verified') else 'NOT verified'}")
    print()
    print(f"  Saved:    {out}")
    print(f"  Next:     python scripts/qualify.py {out}")
    print()
