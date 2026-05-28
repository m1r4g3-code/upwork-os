"""
scraper.py -- Upwork job and client scraper.

Reads cookies from your existing Chrome session (no new browser, no bot detection).
Uses plain HTTP requests — indistinguishable from normal browsing.

FIRST-TIME SETUP (run once):
  python scripts/scraper.py --setup

USAGE:
  python scripts/scraper.py <upwork-job-url>
  python scripts/scraper.py --client <upwork-username>

OUTPUT:
  sources/jobs/YYYY-MM-DD-<slug>.json
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

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
}


# ---------------------------------------------------------------------------
# Session: extract from Chrome (no new browser needed)
# ---------------------------------------------------------------------------

COOKIE_DROP = ROOT / "data" / "upwork_cookies.json"


def setup_session() -> None:
    """
    Set up Upwork session from Chrome cookies.

    Tries automatic extraction first (rookiepy / browser_cookie3).
    Falls back to watching for a manually exported cookie file.
    """
    print()
    print("+------------------------------------------+")
    print("|  Upwork Session Setup                    |")
    print("+------------------------------------------+")
    print()

    # --- Try rookiepy (handles Chrome 127+ Application-Bound Encryption) ---
    try:
        import rookiepy
        print("Trying rookiepy cookie extraction...")
        raw = rookiepy.chrome([".upwork.com"])
        cookies = [{"name": c["name"], "value": c["value"],
                    "domain": c["host_key"], "path": c["path"]}
                   for c in raw if "upwork" in c.get("host_key", "")]
        if cookies:
            _save_cookies(cookies)
            return
        print("No Upwork cookies via rookiepy.")
    except Exception as e:
        print(f"rookiepy unavailable: {e}")

    # --- Try browser_cookie3 ---
    try:
        import browser_cookie3
        print("Trying browser_cookie3 extraction...")
        raw = browser_cookie3.chrome(domain_name=".upwork.com")
        cookies = [{"name": c.name, "value": c.value,
                    "domain": c.domain, "path": getattr(c, "path", "/")}
                   for c in raw]
        if cookies:
            _save_cookies(cookies)
            return
        print("No Upwork cookies via browser_cookie3.")
    except Exception as e:
        print(f"browser_cookie3 unavailable: {e}")

    # --- Manual export fallback ---
    _manual_cookie_setup()


def _manual_cookie_setup() -> None:
    """Watch for manually exported cookie file."""
    print()
    print("Automatic extraction failed (Chrome 127+ encryption).")
    print("One-time manual export needed -- takes 2 minutes:")
    print()
    print("  1. Open Chrome and go to: https://www.upwork.com")
    print("     (make sure you are logged in)")
    print()
    print("  2. Install this free extension:")
    print("     https://chromewebstore.google.com/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm")
    print()
    print("  3. Click the Cookie Editor icon in Chrome toolbar")
    print("     -> Click 'Export' (top right)")
    print("     -> Choose 'Export as JSON'")
    print()
    print(f"  4. Save the file to:")
    print(f"     {COOKIE_DROP}")
    print()
    print("Waiting for the file to appear... (Ctrl+C to cancel)")
    print()

    import time
    while not COOKIE_DROP.exists():
        time.sleep(2)
        sys.stdout.write(".")
        sys.stdout.flush()

    print()
    print("File detected. Processing...")

    with open(COOKIE_DROP) as f:
        raw = json.load(f)

    # Cookie Editor exports as list of objects with 'name', 'value', 'domain' etc.
    upwork_cookies = [
        {
            "name":   c.get("name", ""),
            "value":  c.get("value", ""),
            "domain": c.get("domain", ".upwork.com"),
            "path":   c.get("path", "/"),
        }
        for c in raw
        if "upwork" in c.get("domain", "").lower()
           and c.get("name") and c.get("value")
    ]

    if not upwork_cookies:
        print("ERROR: No Upwork cookies found in the exported file.")
        print("Make sure you exported from upwork.com, not another site.")
        sys.exit(1)

    _save_cookies(upwork_cookies)


def _save_cookies(cookies: list) -> None:
    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SESSION_FILE, "w") as f:
        json.dump(cookies, f, indent=2)
    print(f"Saved {len(cookies)} Upwork cookies -> {SESSION_FILE}")
    print()
    print("Scraper ready. Test it:")
    print("  python scripts/scraper.py <upwork-job-url>")


def load_session() -> dict:
    """Load saved cookies as a requests-compatible dict. Warn if CF cookie is stale."""
    import time

    if not SESSION_FILE.exists():
        print("No session found. Run first:")
        print("  python scripts/scraper.py --setup")
        sys.exit(1)

    with open(SESSION_FILE) as f:
        raw = json.load(f)

    cookies = {c["name"]: c["value"] for c in raw}

    # Check Cloudflare cookie freshness — __cf_bm expires in ~30 min
    cf_cookie = next((c for c in raw if c["name"] == "__cf_bm"), None)
    if cf_cookie:
        expiry = cf_cookie.get("expirationDate", 0)
        if expiry and expiry < time.time():
            print()
            print("  WARNING: Cloudflare session cookie (__cf_bm) has expired.")
            print("  Upwork will reject the request. Re-export cookies now:")
            print()
            print("  1. Open Chrome -> go to upwork.com (stay logged in)")
            print("  2. Click Cookie Editor icon -> Export -> Export as JSON")
            print(f"  3. Save to: {COOKIE_DROP}")
            print("  4. Re-run: python scripts/scraper.py --setup")
            print("  5. Then run the scraper again immediately (within 25 min)")
            print()
            sys.exit(1)

    return cookies


# ---------------------------------------------------------------------------
# HTTP fetch (no browser, no Cloudflare)
# ---------------------------------------------------------------------------

def fetch_url(url: str) -> str:
    try:
        import requests
    except ImportError:
        print("ERROR: requests not installed. Run: pip install requests")
        sys.exit(1)

    cookies = load_session()

    # Build headers including XSRF token (required by Upwork)
    xsrf = cookies.get("XSRF-TOKEN", "")
    headers = {**HEADERS, "X-XSRF-TOKEN": xsrf, "Referer": "https://www.upwork.com/"}

    print(f"Fetching: {url}")
    session = requests.Session()
    session.headers.update(headers)

    # Attempt 1: direct URL
    r = session.get(url, cookies=cookies, timeout=20, allow_redirects=True)

    # Upwork sometimes serves the job under /freelance-jobs/apply/ path
    if r.status_code == 403 and "/jobs/~" in url:
        job_id = re.search(r"~([a-zA-Z0-9]+)", url)
        if job_id:
            alt = f"https://www.upwork.com/freelance-jobs/apply/~{job_id.group(1)}/"
            print(f"  Retrying alternate URL: {alt}")
            r = session.get(alt, cookies=cookies, timeout=20, allow_redirects=True)

    if r.status_code in (401, 403):
        print()
        print(f"HTTP {r.status_code} — session may have expired (Cloudflare cookies are short-lived).")
        print("Re-export cookies from Chrome and run: python scripts/scraper.py --setup")
        sys.exit(1)

    if "login" in r.url or "signin" in r.url:
        print("Redirected to login — session expired.")
        print("Re-export cookies and run: python scripts/scraper.py --setup")
        sys.exit(1)

    if r.status_code != 200:
        print(f"HTTP {r.status_code} — {url}")
        sys.exit(1)

    return r.text


# ---------------------------------------------------------------------------
# Parse: try Next.js __NEXT_DATA__ first, fall back to regex on body text
# ---------------------------------------------------------------------------

def extract_next_data(html: str) -> dict | None:
    """Upwork is Next.js — job data is embedded as JSON in __NEXT_DATA__."""
    m = re.search(
        r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>',
        html, re.DOTALL
    )
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except Exception:
        return None


def job_from_next_data(nd: dict) -> dict:
    """Walk the Next.js props tree to find job + client fields."""
    job = {}
    client = {}

    # Try common key paths Upwork uses
    def dig(obj, *keys):
        for k in keys:
            if isinstance(obj, dict):
                obj = obj.get(k)
            else:
                return None
        return obj

    props = nd.get("props", {}).get("pageProps", {})

    # Job object — Upwork nests it differently per page variant
    job_obj = (
        dig(props, "job")
        or dig(props, "jobData", "job")
        or dig(props, "initialData", "job")
        or dig(props, "data", "job")
    )

    if job_obj:
        job["title"]         = job_obj.get("title") or job_obj.get("op_title")
        job["description"]   = job_obj.get("description") or job_obj.get("op_description")
        job["job_type"]      = "hourly" if job_obj.get("jobType") in ("hourly", "HOURLY") else "fixed"
        job["skills"]        = [s.get("name") or s.get("prefLabel") for s in
                                 (job_obj.get("skills") or job_obj.get("op_required_skills") or [])
                                 if isinstance(s, dict)]

        # Budget
        budget = job_obj.get("budget") or {}
        if isinstance(budget, dict):
            job["budget_min"] = budget.get("min") or budget.get("amount")
            job["budget_max"] = budget.get("max") or budget.get("amount")
        elif isinstance(budget, (int, float)):
            job["budget_min"] = job["budget_max"] = budget

        hourly = job_obj.get("hourlyBudget") or job_obj.get("op_hourly_rate") or {}
        if isinstance(hourly, dict):
            job["hourly_rate_min"] = hourly.get("min") or hourly.get("minRate")
            job["hourly_rate_max"] = hourly.get("max") or hourly.get("maxRate")
        elif isinstance(hourly, (int, float)):
            job["hourly_rate_min"] = job["hourly_rate_max"] = hourly

        job["proposals_count"] = (
            job_obj.get("proposalsTier")
            or job_obj.get("applicants")
            or job_obj.get("proposals_count")
        )

    # Client object
    client_obj = (
        dig(props, "client")
        or dig(props, "jobData", "client")
        or dig(props, "initialData", "client")
    )
    if client_obj:
        client["country"]         = client_obj.get("location", {}).get("country") or client_obj.get("country")
        client["total_spend_usd"] = client_obj.get("totalSpent") or client_obj.get("total_spent")
        client["hire_rate_pct"]   = client_obj.get("hireRate") or client_obj.get("hire_rate")
        client["avg_review_score"]= client_obj.get("avgReviewScore") or client_obj.get("avg_review_score")
        client["payment_verified"]= client_obj.get("paymentVerified") or client_obj.get("payment_verified")
        client["total_hires"]     = client_obj.get("hires") or client_obj.get("total_hires")
        client["jobs_posted"]     = client_obj.get("jobs") or client_obj.get("jobs_posted")

    return {"job": {k: v for k, v in job.items() if v is not None},
            "client": {k: v for k, v in client.items() if v is not None}}


# ---------------------------------------------------------------------------
# Regex fallback on visible text
# ---------------------------------------------------------------------------

def _parse_spend(text: str) -> float:
    text = text.strip().replace(",", "")
    m = re.search(r"\$?([\d.]+)([KkMm]?)", text)
    if not m:
        return 0.0
    val = float(m.group(1))
    suf = m.group(2).upper()
    return val * (1000 if suf == "K" else 1_000_000 if suf == "M" else 1)


def parse_job_text(html: str, url: str) -> dict:
    """Regex extraction from page text as fallback."""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text("\n")
    except ImportError:
        text = re.sub(r"<[^>]+>", " ", html)

    full = "\n".join(l.strip() for l in text.splitlines() if l.strip())
    job = {"url": url}
    client = {}

    # Title
    skip = ("upwork", "find jobs", "log in", "sign up", "back to", "jobs >")
    for line in full.splitlines()[:40]:
        if len(line) > 20 and not any(line.lower().startswith(s) for s in skip):
            job["title"] = line
            break

    # Budget
    hourly_m = re.search(r"\$\s*([\d,.]+)\s*[-–]\s*\$([\d,.]+)\s*/\s*hr", full, re.I) \
            or re.search(r"\$\s*([\d,.]+)\s*/\s*hr", full, re.I)
    fixed_m  = re.search(r"\$\s*([\d,]+)\s*[-–]\s*\$\s*([\d,]+)\s+[Ff]ix", full) \
            or re.search(r"[Ff]ixed.{0,30}\$\s*([\d,]+)", full) \
            or re.search(r"\$\s*([\d,]+)\s+[Ff]ixed", full)

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

    prop_m = re.search(r"(\d+)\s+(?:to\s+\d+\s+)?[Pp]roposals?", full) \
          or re.search(r"Less than (\d+)", full, re.I)
    if prop_m:
        job["proposals_count"] = int(prop_m.group(1))

    posted_m = re.search(r"[Pp]osted\s+(just now|\d+\s+(?:minute|hour|day|week|month)s?\s+ago)", full)
    if posted_m:
        job["posted_text"] = posted_m.group(1)
        pt = posted_m.group(1).lower()
        job["days_posted"] = (
            0 if ("minute" in pt or "hour" in pt or "just" in pt)
            else int(re.search(r"(\d+)", pt).group(1)) * (
                7 if "week" in pt else 30 if "month" in pt else 1
            )
        )

    desc_m = re.search(
        r"(?:Description|About the project|Job Details)[:\n]+(.{200,}?)"
        r"(?:\n(?:Skills|Budget|Client|Expertise|Posted|Proposals))",
        full, re.I | re.DOTALL
    )
    if desc_m:
        job["description"] = desc_m.group(1).strip()

    client["payment_verified"] = bool(re.search(r"[Pp]ayment\s+[Vv]erified", full))

    country_m = re.search(r"(?:Location|From)[:\s]+([A-Z][a-zA-Z\s,]+?)(?:\n|$)", full)
    if country_m:
        client["country"] = country_m.group(1).strip()

    spent_m = re.search(r"(?:Total\s+[Ss]pent|Spent)[:\s]+(\$?[\d,.]+[KkMm]?)", full)
    if spent_m:
        client["total_spend_usd"] = _parse_spend(spent_m.group(1))

    hire_m = re.search(r"(\d+)%?\s+[Hh]ire\s+[Rr]ate", full) \
          or re.search(r"[Hh]ire\s+[Rr]ate[:\s]+(\d+)%", full)
    if hire_m:
        client["hire_rate_pct"] = float(hire_m.group(1))

    rating_m = re.search(r"([\d.]+)\s+of\s+5", full)
    if rating_m:
        client["avg_review_score"] = float(rating_m.group(1))

    jobs_m = re.search(r"(\d+)\s+[Jj]obs?\s+[Pp]osted", full)
    if jobs_m:
        client["jobs_posted"] = int(jobs_m.group(1))

    hires_m = re.search(r"(\d+)\s+[Hh]ires?(?:\s|$)", full)
    if hires_m:
        client["total_hires"] = int(hires_m.group(1))

    return {"job": job, "client": client}


# ---------------------------------------------------------------------------
# Main parse logic
# ---------------------------------------------------------------------------

def scrape_job(url: str) -> dict:
    html = fetch_url(url)

    # Try Next.js data first (clean structured JSON)
    nd = extract_next_data(html)
    if nd:
        data = job_from_next_data(nd)
        data["job"]["url"] = url
        if data["job"].get("title"):
            print("  [Next.js data found]")
            return data

    # Fallback: regex on visible text
    print("  [Fallback: regex parse]")
    return parse_job_text(html, url)


def scrape_client(username: str) -> dict:
    url = f"https://www.upwork.com/companies/{username}"
    html = fetch_url(url)
    nd = extract_next_data(html)
    if nd:
        data = job_from_next_data(nd)
        data["client"]["username"] = username
        if data["client"]:
            return data
    return parse_job_text(html, url)


# ---------------------------------------------------------------------------
# Slug + save + print summary
# ---------------------------------------------------------------------------

def slug_from_url(url: str) -> str:
    m = re.search(r"~([a-zA-Z0-9]+)", url)
    return m.group(1)[:12] if m else datetime.now().strftime("%H%M%S")


def save_output(data: dict, slug: str) -> Path:
    date_str = datetime.now().strftime("%Y-%m-%d")
    out = SOURCES_JOBS / f"{date_str}-{slug}.json"
    with open(out, "w") as f:
        json.dump(data, f, indent=2)
    return out


def print_summary(data: dict) -> None:
    job    = data.get("job", {})
    client = data.get("client", {})
    print()
    print(f"  Title:    {job.get('title', 'not found')}")
    btype = job.get("job_type", "?")
    if btype == "hourly":
        budget_str = f"${job.get('hourly_rate_min','?')}-${job.get('hourly_rate_max','?')}/hr"
    elif btype == "fixed":
        budget_str = f"${job.get('budget_min','?')}-${job.get('budget_max','?')}"
    else:
        budget_str = "unknown"
    print(f"  Budget:   {budget_str} ({btype})")
    print(f"  Proposals:{job.get('proposals_count', '?')}")
    print(f"  Client:   {client.get('country','?')} | "
          f"${client.get('total_spend_usd', 0):,.0f} spent | "
          f"{client.get('hire_rate_pct','?')}% hire | "
          f"payment {'OK' if client.get('payment_verified') else 'NOT verified'}")


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
        data = scrape_client(username)
        out  = save_output(data, f"client-{username}")
        print_summary(data)
        print(f"\n  Saved:    {out}")
        print(f"  Next:     python scripts/qualify.py --client {out}")
        sys.exit(0)

    url = args[0]
    if not url.startswith("http"):
        print(f"Expected a URL. Got: {url}")
        sys.exit(1)

    slug = slug_from_url(url)
    data = scrape_job(url)
    out  = save_output(data, slug)
    print_summary(data)
    print(f"\n  Saved:    {out}")
    print(f"  Next:     python scripts/qualify.py {out}")
