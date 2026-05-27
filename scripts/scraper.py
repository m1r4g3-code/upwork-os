"""
scraper.py — Upwork job and client scraper (Playwright).

Scrapes job pages and client profiles into structured JSON for qualify.py.

IMPORTANT: Requires Upwork login session. Run setup first:
  python scripts/scraper.py --setup

Usage:
  python scripts/scraper.py <upwork-job-url>           # scrape job
  python scripts/scraper.py --client <username>        # scrape client profile
  python scripts/scraper.py --manual                   # manual paste mode (fallback)
  python scripts/scraper.py --setup                    # save session cookies

Output: sources/jobs/YYYY-MM-DD-<slug>.json
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


def slug_from_url(url: str) -> str:
    """Extract a slug from a Upwork job URL."""
    match = re.search(r'~([a-zA-Z0-9]+)', url)
    if match:
        return match.group(1)[:12]
    return datetime.now().strftime("%H%M%S")


def manual_input_mode() -> dict:
    """Fallback: prompt for manual job data entry."""
    print("MANUAL JOB ENTRY MODE")
    print("(Scraper unavailable — enter job details manually)")
    print()

    data = {"job": {}, "client": {}}
    data["job"]["title"] = input("Job title: ").strip()
    data["job"]["url"] = input("Job URL: ").strip()
    data["job"]["description"] = input("Paste job description (press Enter twice when done):\n")
    # Read until double newline
    lines = []
    while True:
        line = input()
        if line == "" and lines and lines[-1] == "":
            break
        lines.append(line)
    data["job"]["description"] = "\n".join(lines[:-1])

    budget_input = input("Budget (e.g. '$500-1000 fixed' or '$25-50/hr'): ").strip()
    if "/hr" in budget_input.lower():
        data["job"]["job_type"] = "hourly"
        nums = re.findall(r'\d+', budget_input)
        if nums:
            data["job"]["hourly_rate_min"] = int(nums[0])
            data["job"]["hourly_rate_max"] = int(nums[1]) if len(nums) > 1 else int(nums[0])
    else:
        data["job"]["job_type"] = "fixed"
        nums = re.findall(r'\d+', budget_input)
        if nums:
            data["job"]["budget_min"] = int(nums[0])
            data["job"]["budget_max"] = int(nums[1]) if len(nums) > 1 else int(nums[0])

    data["job"]["days_posted"] = int(input("Days since posted (0 = today): ") or "0")
    data["job"]["proposals_count"] = int(input("Number of competing proposals (0 if unknown): ") or "0")

    print("\nCLIENT INFO:")
    data["client"]["username"] = input("Client username: ").strip()
    data["client"]["country"] = input("Client country: ").strip()

    spend_input = input("Total client spend (e.g. '$5,000' or '0'): ").strip()
    spend_clean = re.sub(r'[,$]', '', spend_input)
    data["client"]["total_spend_usd"] = float(spend_clean) if spend_clean.replace('.', '').isdigit() else 0

    data["client"]["hire_rate_pct"] = float(input("Hire rate % (0-100): ") or "0")
    data["client"]["avg_hourly_paid"] = float(input("Avg hourly rate paid to freelancers: ") or "0")
    data["client"]["avg_review_score"] = float(input("Client's avg review score (1-5): ") or "0")
    data["client"]["payment_verified"] = input("Payment verified? (y/n): ").strip().lower() == "y"
    data["client"]["active_contracts"] = int(input("Active contracts: ") or "0")
    data["client"]["total_hires"] = int(input("Total hires: ") or "0")
    data["client"]["jobs_posted"] = int(input("Total jobs posted: ") or "0")

    return data


def scrape_with_playwright(url: str, mode: str = "job") -> dict:
    """
    Playwright-based scraper. Requires:
    1. pip install playwright
    2. playwright install chromium
    3. Active Upwork session saved via --setup
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("ERROR: playwright not installed. Run: pip install playwright && playwright install chromium", file=sys.stderr)
        print("Falling back to manual mode...", file=sys.stderr)
        return manual_input_mode()

    if not SESSION_FILE.exists():
        print("ERROR: No Upwork session found. Run: python scripts/scraper.py --setup", file=sys.stderr)
        print("Falling back to manual mode...", file=sys.stderr)
        return manual_input_mode()

    data = {"job": {}, "client": {}}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()

        # Load saved session
        try:
            with open(SESSION_FILE) as f:
                cookies = json.load(f)
            context.add_cookies(cookies)
        except Exception as e:
            print(f"WARNING: Could not load session: {e}", file=sys.stderr)

        page = context.new_page()

        if mode == "job":
            page.goto(url, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(2000)

            # Extract job data
            try:
                data["job"]["title"] = page.title().replace(" | Upwork", "").strip()
                data["job"]["url"] = url

                desc_el = page.query_selector('[data-test="Description"], .Description, [class*="description"]')
                if desc_el:
                    data["job"]["description"] = desc_el.inner_text()

                budget_el = page.query_selector('[data-test="BudgetAmount"], [class*="budget"]')
                if budget_el:
                    budget_text = budget_el.inner_text()
                    if "/hr" in budget_text.lower():
                        data["job"]["job_type"] = "hourly"
                        nums = re.findall(r'\d+', budget_text)
                        if nums:
                            data["job"]["hourly_rate_min"] = int(nums[0])
                            data["job"]["hourly_rate_max"] = int(nums[1]) if len(nums) > 1 else int(nums[0])
                    else:
                        data["job"]["job_type"] = "fixed"
                        nums = re.findall(r'[\d,]+', budget_text)
                        if nums:
                            data["job"]["budget_min"] = int(nums[0].replace(",", ""))
                            data["job"]["budget_max"] = int(nums[1].replace(",", "")) if len(nums) > 1 else data["job"]["budget_min"]

                proposals_el = page.query_selector('[data-test="ProposalsCount"], [class*="proposal"]')
                if proposals_el:
                    nums = re.findall(r'\d+', proposals_el.inner_text())
                    if nums:
                        data["job"]["proposals_count"] = int(nums[0])

            except Exception as e:
                print(f"WARNING: Partial scrape: {e}", file=sys.stderr)

        elif mode == "client":
            profile_url = f"https://www.upwork.com/companies/{url}" if not url.startswith("http") else url
            page.goto(profile_url, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(2000)
            data["client"]["username"] = url
            # Client profile scraping is Upwork-version-dependent
            # Fallback: manual entry for client data
            print("NOTE: Client profile scraping requires manual verification. Switching to manual for client data.", file=sys.stderr)

        browser.close()

    return data


def setup_session() -> None:
    """Interactive session setup — opens browser for manual login."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("ERROR: playwright not installed. Run: pip install playwright && playwright install chromium")
        sys.exit(1)

    print("Opening Upwork in browser. Log in, then press Enter here.")
    print("Your session cookies will be saved for future scraping.")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://www.upwork.com/login")

        input("\nLog into Upwork in the browser window, then press Enter here...")

        cookies = context.cookies()
        SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SESSION_FILE, "w") as f:
            json.dump(cookies, f)

        browser.close()
        print(f"Session saved to {SESSION_FILE}")
        print("You can now run the scraper.")


def save_output(data: dict, slug: str) -> Path:
    """Save scraped data to sources/jobs/."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"{date_str}-{slug}.json"
    output_path = SOURCES_JOBS / filename
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Saved: {output_path}")
    return output_path


if __name__ == "__main__":
    args = sys.argv[1:]

    if not args or "--help" in args:
        print(__doc__)
        sys.exit(0)

    if "--setup" in args:
        setup_session()
        sys.exit(0)

    if "--manual" in args:
        data = manual_input_mode()
        slug = "manual-" + datetime.now().strftime("%H%M%S")
        output = save_output(data, slug)
        print(f"\nSaved to: {output}")
        print("Now run: python scripts/qualify.py " + str(output))
        sys.exit(0)

    if "--client" in args and len(args) >= 2:
        username = args[args.index("--client") + 1]
        data = scrape_with_playwright(username, mode="client")
        output = save_output(data, f"client-{username}")
        print(f"\nRun: python scripts/qualify.py --client {output}")
        sys.exit(0)

    url = args[0]
    if not url.startswith("http"):
        print(f"ERROR: Expected a URL. Got: {url}", file=sys.stderr)
        print("For manual entry: python scripts/scraper.py --manual", file=sys.stderr)
        sys.exit(1)

    slug = slug_from_url(url)
    data = scrape_with_playwright(url)
    data["job"]["url"] = url
    output = save_output(data, slug)
    print(f"\nNext step: python scripts/qualify.py {output}")
