"""
scraper.py -- Upwork job and client scraper.

Primary flow: tries HTTP with your Chrome session cookies.
Fallback (Cloudflare blocks): opens job in Chrome, watches clipboard,
auto-detects when you Ctrl+A → Ctrl+C, parses the text automatically.

FIRST-TIME SETUP (run once):
  python scripts/scraper.py --setup

USAGE:
  python scripts/scraper.py <upwork-job-url>
  python scripts/scraper.py --client <upwork-username>
"""

import sys
import json
import re
import os
import time
import webbrowser
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
SOURCES_JOBS = ROOT / "sources" / "jobs"
SOURCES_JOBS.mkdir(parents=True, exist_ok=True)
SESSION_FILE = ROOT / "data" / "upwork_session.json"
COOKIE_DROP  = ROOT / "data" / "upwork_cookies.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}


# ---------------------------------------------------------------------------
# Session setup
# ---------------------------------------------------------------------------

def setup_session() -> None:
    print()
    print("+------------------------------------------+")
    print("|  Upwork Session Setup                    |")
    print("+------------------------------------------+")
    print()

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
    except Exception as e:
        print(f"rookiepy unavailable: {e}")

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
    except Exception as e:
        print(f"browser_cookie3 unavailable: {e}")

    _manual_cookie_setup()


def _manual_cookie_setup() -> None:
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

    while not COOKIE_DROP.exists():
        time.sleep(2)
        sys.stdout.write(".")
        sys.stdout.flush()

    print()
    print("File detected. Processing...")

    with open(COOKIE_DROP) as f:
        raw = json.load(f)

    upwork_cookies = [
        {"name": c.get("name",""), "value": c.get("value",""),
         "domain": c.get("domain",".upwork.com"), "path": c.get("path","/")}
        for c in raw
        if "upwork" in c.get("domain","").lower() and c.get("name") and c.get("value")
    ]

    if not upwork_cookies:
        print("ERROR: No Upwork cookies found in the exported file.")
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
    if not SESSION_FILE.exists():
        print("No session found. Run first:")
        print("  python scripts/scraper.py --setup")
        sys.exit(1)

    with open(SESSION_FILE) as f:
        raw = json.load(f)

    return {c["name"]: c["value"] for c in raw}


# ---------------------------------------------------------------------------
# HTTP fetch (attempt 1 — fast when it works)
# ---------------------------------------------------------------------------

def fetch_url(url: str) -> str | None:
    """Returns HTML string or None if Cloudflare blocks."""
    try:
        import requests
    except ImportError:
        return None

    cookies = load_session()
    xsrf = cookies.get("XSRF-TOKEN", "")
    headers = {**HEADERS, "X-XSRF-TOKEN": xsrf, "Referer": "https://www.upwork.com/"}

    print(f"  Trying HTTP scrape...")
    try:
        session = requests.Session()
        session.headers.update(headers)
        r = session.get(url, cookies=cookies, timeout=20, allow_redirects=True)

        if r.status_code == 403 and "/jobs/~" in url:
            job_id = re.search(r"~([a-zA-Z0-9]+)", url)
            if job_id:
                alt = f"https://www.upwork.com/freelance-jobs/apply/~{job_id.group(1)}/"
                r = session.get(alt, cookies=cookies, timeout=20, allow_redirects=True)

        if r.status_code in (401, 403):
            print("  HTTP blocked by Cloudflare — switching to clipboard mode.")
            return None

        if "login" in r.url or "signin" in r.url:
            print("  Session expired — switching to clipboard mode.")
            return None

        if r.status_code != 200:
            print(f"  HTTP {r.status_code} — switching to clipboard mode.")
            return None

        if "Just a moment" in r.text[:3000] or "Challenge" in r.text[:1000]:
            print("  Cloudflare challenge detected — switching to clipboard mode.")
            return None

        return r.text

    except Exception as e:
        print(f"  HTTP error ({e}) — switching to clipboard mode.")
        return None


# ---------------------------------------------------------------------------
# Clipboard fallback (attempt 2 — always works)
# ---------------------------------------------------------------------------

def scrape_via_clipboard(url: str) -> dict:
    """
    Open the job in Chrome, watch clipboard for Ctrl+A + Ctrl+C,
    then parse the text automatically. Takes ~15 seconds.
    """
    try:
        import pyperclip
        old_clip = pyperclip.paste()
    except Exception:
        old_clip = ""
        pyperclip = None  # type: ignore

    print()
    print("  +----------------------------------------------------------+")
    print("  |  Opening job in Chrome. When it loads:                  |")
    print("  |    1. Press Ctrl+A  (select all)                        |")
    print("  |    2. Press Ctrl+C  (copy)                              |")
    print("  |  Auto-detects -- no Enter needed.                       |")
    print("  +----------------------------------------------------------+")
    print()

    webbrowser.open(url)
    time.sleep(3)  # give Chrome time to load

    if pyperclip is None:
        input("Press Enter after Ctrl+A + Ctrl+C... ")
        try:
            import pyperclip as pc
            text = pc.paste()
        except Exception:
            print("ERROR: pyperclip not installed. Run: pip install pyperclip")
            sys.exit(1)
    else:
        import pyperclip as pc
        print("  Watching clipboard...", end="", flush=True)
        for _ in range(120):  # wait up to 2 min
            time.sleep(1)
            current = pc.paste()
            if current != old_clip and len(current) > 500:
                print(f" got {len(current)} chars.")
                text = current
                break
            sys.stdout.write(".")
            sys.stdout.flush()
        else:
            print()
            print("  Timeout — no clipboard content detected.")
            sys.exit(1)

    print("  Parsing clipboard content...")
    return _parse_text(text, url)


# ---------------------------------------------------------------------------
# Parse: Next.js __NEXT_DATA__ (from HTTP) or plain text (from clipboard)
# ---------------------------------------------------------------------------

def extract_next_data(html: str) -> dict | None:
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except Exception:
        return None


def job_from_next_data(nd: dict) -> dict:
    job, client = {}, {}

    def dig(obj, *keys):
        for k in keys:
            if isinstance(obj, dict):
                obj = obj.get(k)
            else:
                return None
        return obj

    props = nd.get("props", {}).get("pageProps", {})

    job_obj = (
        dig(props, "job")
        or dig(props, "jobData", "job")
        or dig(props, "initialData", "job")
        or dig(props, "data", "job")
    )

    if job_obj:
        job["title"]       = job_obj.get("title") or job_obj.get("op_title")
        job["description"] = job_obj.get("description") or job_obj.get("op_description")
        job["job_type"]    = "hourly" if job_obj.get("jobType") in ("hourly","HOURLY") else "fixed"
        job["skills"]      = [s.get("name") or s.get("prefLabel")
                              for s in (job_obj.get("skills") or []) if isinstance(s, dict)]

        budget = job_obj.get("budget") or {}
        if isinstance(budget, dict):
            job["budget_min"] = budget.get("min") or budget.get("amount")
            job["budget_max"] = budget.get("max") or budget.get("amount")

        hourly = job_obj.get("hourlyBudget") or job_obj.get("op_hourly_rate") or {}
        if isinstance(hourly, dict):
            job["hourly_rate_min"] = hourly.get("min") or hourly.get("minRate")
            job["hourly_rate_max"] = hourly.get("max") or hourly.get("maxRate")

        job["proposals_count"] = (
            job_obj.get("proposalsTier") or job_obj.get("applicants") or job_obj.get("proposals_count")
        )

    client_obj = (
        dig(props, "client")
        or dig(props, "jobData", "client")
        or dig(props, "initialData", "client")
    )
    if client_obj:
        client["country"]          = client_obj.get("location", {}).get("country") or client_obj.get("country")
        client["total_spend_usd"]  = client_obj.get("totalSpent") or client_obj.get("total_spent")
        client["hire_rate_pct"]    = client_obj.get("hireRate") or client_obj.get("hire_rate")
        client["avg_review_score"] = client_obj.get("avgReviewScore") or client_obj.get("avg_review_score")
        client["payment_verified"] = client_obj.get("paymentVerified") or client_obj.get("payment_verified")
        client["total_hires"]      = client_obj.get("hires") or client_obj.get("total_hires")
        client["jobs_posted"]      = client_obj.get("jobs") or client_obj.get("jobs_posted")

    return {
        "job":    {k: v for k, v in job.items() if v is not None},
        "client": {k: v for k, v in client.items() if v is not None},
    }


def _parse_spend(text: str) -> float:
    text = text.strip().replace(",", "")
    m = re.search(r"\$?([\d.]+)([KkMm]?)", text)
    if not m:
        return 0.0
    val, suf = float(m.group(1)), m.group(2).upper()
    return val * (1000 if suf == "K" else 1_000_000 if suf == "M" else 1)


def _parse_text(text: str, url: str) -> dict:
    """
    Parse copied page text (or HTML) into structured job dict.
    Works whether the input is raw page HTML or clipboard plain-text.
    """
    # If HTML, extract text first
    if "<html" in text[:200].lower() or "<!doctype" in text[:100].lower():
        try:
            from bs4 import BeautifulSoup
            text = BeautifulSoup(text, "html.parser").get_text("\n")
        except ImportError:
            text = re.sub(r"<[^>]+>", " ", text)

    full = "\n".join(l.strip() for l in text.splitlines() if l.strip())
    job    = {"url": url, "source": "clipboard"}
    client = {}

    # --- Title ---
    skip_words = ("upwork", "find jobs", "log in", "sign up", "back to",
                  "jobs >", "skills", "budget", "posted", "apply", "save")
    for line in full.splitlines()[:60]:
        clean = line.strip()
        if (len(clean) > 15 and len(clean) < 200
                and not any(clean.lower().startswith(s) for s in skip_words)
                and not clean.startswith("$")
                and not re.match(r"^\d", clean)):
            job["title"] = clean
            break

    # --- Budget ---
    hourly_m = (re.search(r"\$\s*([\d,.]+)\s*[-–]\s*\$\s*([\d,.]+)\s*/\s*hr", full, re.I)
                or re.search(r"\$\s*([\d,.]+)\s*/\s*hr", full, re.I))
    fixed_m  = (re.search(r"\$\s*([\d,]+)\s*[-–]\s*\$\s*([\d,]+)", full)
                or re.search(r"[Ff]ixed.{0,30}\$\s*([\d,]+)", full)
                or re.search(r"\$\s*([\d,]+)\s+[Ff]ixed", full))
    budget_m = re.search(r"[Bb]udget\s*\n\s*\$\s*([\d,]+)\s*[-–]?\s*\$?\s*([\d,]*)", full)

    if hourly_m:
        job["job_type"] = "hourly"
        nums = [float(n.replace(",","")) for n in hourly_m.groups() if n]
        job["hourly_rate_min"] = nums[0]
        job["hourly_rate_max"] = nums[1] if len(nums) > 1 else nums[0]
    elif fixed_m:
        job["job_type"] = "fixed"
        nums = [float(n.replace(",","")) for n in fixed_m.groups() if n]
        job["budget_min"] = nums[0]
        job["budget_max"] = nums[1] if len(nums) > 1 else nums[0]
    elif budget_m:
        job["job_type"] = "fixed"
        nums = [float(n.replace(",","")) for n in budget_m.groups() if n]
        job["budget_min"] = nums[0]
        job["budget_max"] = nums[1] if len(nums) > 1 else nums[0]
    else:
        job["job_type"] = "unknown"

    # --- Proposals ---
    prop_m = (re.search(r"(\d+)\s+to\s+(\d+)\s+[Pp]roposals?", full)
              or re.search(r"[Ll]ess than (\d+)\s+[Pp]roposals?", full)
              or re.search(r"[Pp]roposals?[:\s]+(\d+)", full))
    if prop_m:
        job["proposals_count"] = int(prop_m.group(1))

    # --- Posted ---
    posted_m = re.search(r"[Pp]osted\s+(just now|\d+\s+(?:minute|hour|day|week|month)s?\s+ago)", full)
    if posted_m:
        job["posted_text"] = posted_m.group(1)
        pt = posted_m.group(1).lower()
        job["days_posted"] = (
            0 if ("minute" in pt or "hour" in pt or "just" in pt)
            else int(re.search(r"(\d+)", pt).group(1)) * (7 if "week" in pt else 30 if "month" in pt else 1)
        )

    # --- Description ---
    desc_m = re.search(
        r"(?:[Dd]escription|[Aa]bout the project|[Jj]ob [Dd]etails)[:\n]+(.{100,}?)"
        r"(?:\n(?:[Ss]kills?|[Bb]udget|[Cc]lient|[Pp]roposals?|[Pp]osted|[Aa]ctivity))",
        full, re.DOTALL
    )
    if desc_m:
        job["description"] = desc_m.group(1).strip()

    # --- Skills ---
    skills_m = re.search(
        r"[Ss]kills? and [Ee]xpertise\n(.*?)(?:\n[A-Z][a-z]|\Z)",
        full, re.DOTALL
    )
    if skills_m:
        raw_skills = skills_m.group(1).strip().splitlines()
        job["skills"] = [s.strip() for s in raw_skills if s.strip() and len(s.strip()) < 60]

    # --- Client fields ---
    client["payment_verified"] = bool(re.search(r"[Pp]ayment\s+[Vv]erified", full))

    country_m = (re.search(r"[Cc]ountry[:\s]+([A-Z][a-zA-Z\s,]+?)(?:\n|$)", full)
                 or re.search(r"[Ll]ocation[:\s]+([A-Z][a-zA-Z\s,]+?)(?:\n|$)", full)
                 or re.search(r"[Mm]ember since.{0,60}\n([A-Z][a-zA-Z\s,]{2,40})(?:\n|$)", full))
    if country_m:
        client["country"] = country_m.group(1).strip()

    spent_m = (re.search(r"\$\s*([\d,]+[KkMm]?\+?)\s+[Ss]pent", full)
               or re.search(r"[Ss]pent[:\s]+\$?\s*([\d,]+[KkMm]?)", full)
               or re.search(r"(\$[\d,]+[KkMm]?\+?)\s*total spent", full, re.I))
    if spent_m:
        client["total_spend_usd"] = _parse_spend(spent_m.group(1))

    hire_m = (re.search(r"(\d+)%\s+[Hh]ire\s+[Rr]ate", full)
              or re.search(r"[Hh]ire\s+[Rr]ate[:\s]+(\d+)", full))
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

    # Store raw text for Claude to use in qualification
    job["_raw_text"] = full[:8000]

    return {
        "job":    {k: v for k, v in job.items() if v is not None},
        "client": {k: v for k, v in client.items() if v is not None},
    }


# ---------------------------------------------------------------------------
# Main scrape function
# ---------------------------------------------------------------------------

def scrape_job(url: str) -> dict:
    """Try HTTP first; fall back to clipboard if Cloudflare blocks."""
    # Attempt 1: HTTP
    html = fetch_url(url)
    if html:
        nd = extract_next_data(html)
        if nd:
            data = job_from_next_data(nd)
            data["job"]["url"] = url
            if data["job"].get("title"):
                print("  [Next.js data — OK]")
                return data
        print("  [Regex parse from HTTP]")
        data = _parse_text(html, url)
        if data["job"].get("title"):
            return data

    # Attempt 2: Clipboard
    return scrape_via_clipboard(url)


def scrape_client(username: str) -> dict:
    url  = f"https://www.upwork.com/companies/{username}"
    html = fetch_url(url)
    if html:
        nd = extract_next_data(html)
        if nd:
            data = job_from_next_data(nd)
            data.setdefault("client", {})["username"] = username
            if data["client"]:
                return data
        return _parse_text(html, url)
    return scrape_via_clipboard(url)


# ---------------------------------------------------------------------------
# Slug, save, print summary
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
        bstr = f"${job.get('hourly_rate_min','?')}-${job.get('hourly_rate_max','?')}/hr"
    elif btype == "fixed":
        bstr = f"${job.get('budget_min','?')}-${job.get('budget_max','?')}"
    else:
        bstr = "unknown"
    print(f"  Budget:   {bstr} ({btype})")
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
        print(f"\n  Saved: {out}")
        sys.exit(0)

    url = args[0]
    if not url.startswith("http"):
        print(f"Expected a URL. Got: {url}")
        sys.exit(1)

    slug = slug_from_url(url)
    data = scrape_job(url)
    out  = save_output(data, slug)
    print_summary(data)
    print(f"\n  Saved: {out}")
    print(f"  Next:  python scripts/qualify.py {out}")
