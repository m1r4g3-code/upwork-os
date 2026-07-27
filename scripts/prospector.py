#!/usr/bin/env python3
"""
Upwork OS — Google Maps Prospector (Playwright)

Searches Google Maps autonomously using Playwright (no API key needed).
For each business found: visits their website, extracts email, analyzes
what's broken or missing, writes a personalized outreach email, creates
a prospect node, and fires the outreach engine.

Fully autonomous — no human input required during run.

Usage:
    python scripts/prospector.py --query "furniture stores Brooklyn NY" --limit 10
    python scripts/prospector.py --query "digital agencies Lagos" --limit 20 --auto
    python scripts/prospector.py --query "shopify stores New York" --niche ecommerce --limit 15 --auto
    python scripts/prospector.py --query "law firms Chicago" --limit 5 --dry-run
"""

import sys
import re
import json
import time
import argparse
import urllib.parse
import urllib.request
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

ROOT          = config.ROOT
BRAIN         = config.BRAIN
PROSPECTS_DIR = BRAIN / "outreach" / "prospects"
AI_KEY        = getattr(config, "ANTHROPIC_API_KEY", "")


# ─── Google Maps scraper (Playwright) ────────────────────────────────────────

def _dismiss_overlays(page) -> None:
    """Dismiss cookie consent / GDPR banners if present."""
    for selector in [
        'button[aria-label*="Accept all"]',
        'button[aria-label*="Accept"]',
        'button[jsname="b3VHJd"]',  # Google consent button
        'form[action*="consent"] button',
    ]:
        try:
            if page.locator(selector).count() > 0:
                page.locator(selector).first.click(timeout=2000)
                page.wait_for_timeout(800)
                break
        except Exception:
            pass


def _extract_text(page, selectors: list[str]) -> str:
    """Try multiple selectors, return first non-empty text found."""
    for sel in selectors:
        try:
            el = page.locator(sel).first
            if el.count() > 0:
                text = el.text_content(timeout=2000)
                if text and text.strip():
                    return text.strip()
        except Exception:
            pass
    return ""


def _extract_attr(page, selectors: list[str], attr: str) -> str:
    """Try multiple selectors, return first non-empty attribute value found."""
    for sel in selectors:
        try:
            el = page.locator(sel).first
            if el.count() > 0:
                val = el.get_attribute(attr, timeout=2000)
                if val and val.strip():
                    return val.strip()
        except Exception:
            pass
    return ""


def scrape_business_detail(page, url: str) -> dict | None:
    """Extract business details from a Google Maps place page."""
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(2000)
        _dismiss_overlays(page)
    except Exception as e:
        print(f"     [maps] Failed to load: {e}", file=sys.stderr)
        return None

    # Business name
    name = _extract_text(page, [
        "h1.DUwDvf", "h1[class*='fontDisplayLarge']", "h1",
    ])
    if not name:
        return None

    # Website — Google Maps renders a "website" button
    website = _extract_attr(page, [
        'a[data-item-id="authority"]',
        'a[aria-label*="website" i]',
        'a[href*="http"]:not([href*="google"]):not([href*="maps"])',
    ], "href")

    # Phone — various representations
    phone = _extract_text(page, [
        'button[data-item-id*="phone"] div.rogA2c',
        '[data-tooltip="Copy phone number"]',
        'span[aria-label*="phone" i]',
        'button[aria-label*="phone" i]',
    ])
    # Clean phone — keep only digits, spaces, dashes, parens, +
    phone = re.sub(r"[^\d\s\-\+\(\)]", "", phone).strip()

    # Address
    address = _extract_text(page, [
        'button[data-item-id="address"] div.rogA2c',
        '[data-tooltip="Copy address"]',
        'span[aria-label*="address" i]',
        'button[aria-label*="address" i]',
    ])

    # Category / business type
    category = _extract_text(page, [
        'button[jsaction*="category"]',
        'span.DkEaL',
        '[class*="fontBodyMedium"] span:first-child',
    ])

    # Rating
    rating = _extract_text(page, [
        'div.F7nice span[aria-hidden="true"]',
        'span.ceNzKf',
    ])

    return {
        "name":                    name,
        "website":                 website,
        "formatted_phone_number":  phone,
        "formatted_address":       address,
        "category":                category,
        "rating":                  rating,
        "source_url":              url,
    }


def scrape_google_maps(query: str, limit: int = 10) -> list[dict]:
    """
    Search Google Maps for query, return list of business dicts.
    Fully headless — no user interaction required.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[prospector] Playwright not installed.", file=sys.stderr)
        print("Run: pip install playwright && playwright install chromium", file=sys.stderr)
        sys.exit(1)

    results   = []
    place_urls = []

    search_url = (
        "https://www.google.com/maps/search/"
        + urllib.parse.quote_plus(query)
    )

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage",
                  "--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 900},
            locale="en-US",
        )
        page = context.new_page()
        page.set_extra_http_headers({"Accept-Language": "en-US,en;q=0.9"})

        print(f"[maps] Loading: {search_url}")
        try:
            page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(3000)
            _dismiss_overlays(page)
        except Exception as e:
            print(f"[maps] Load error: {e}", file=sys.stderr)
            browser.close()
            return []

        # Wait for results feed
        try:
            page.wait_for_selector('[role="feed"], div[class*="Nv2PK"]', timeout=15000)
        except Exception:
            print("[maps] Results feed not found — Google may have changed layout", file=sys.stderr)
            browser.close()
            return []

        # Collect business place URLs by scrolling the results panel
        seen_urls = set()
        scroll_attempts = 0
        max_scrolls = 20

        while len(place_urls) < limit and scroll_attempts < max_scrolls:
            # Find all place links currently visible
            links = page.locator('a[href*="/maps/place/"]').all()
            for link in links:
                try:
                    href = link.get_attribute("href")
                    if href and "/maps/place/" in href and href not in seen_urls:
                        # Normalize — strip query params after the place CID
                        clean = re.split(r'\?', href)[0]
                        if clean not in seen_urls:
                            seen_urls.add(clean)
                            place_urls.append(clean)
                except Exception:
                    pass

            if len(place_urls) >= limit:
                break

            # Scroll the feed panel
            try:
                feed = page.locator('[role="feed"]').first
                feed.evaluate("el => el.scrollBy(0, 600)")
            except Exception:
                page.evaluate("window.scrollBy(0, 600)")
            page.wait_for_timeout(1500)
            scroll_attempts += 1

        place_urls = place_urls[:limit]
        print(f"[maps] Collected {len(place_urls)} place URLs. Fetching details...")

        # Visit each place URL and extract details
        for i, url in enumerate(place_urls, 1):
            print(f"  [{i}/{len(place_urls)}] {url.split('/place/')[-1][:40]}...")
            detail = scrape_business_detail(page, url)
            if detail:
                results.append(detail)
            time.sleep(0.8)

        browser.close()

    return results


# ─── Website analysis (Playwright) ───────────────────────────────────────────

def analyze_website_playwright(page, website: str, business_name: str) -> dict:
    """
    Visit the business website with Playwright and analyze what's missing.
    Returns: {tech_stack, observations, angle, email}
    """
    if not website:
        return {"tech_stack": [], "observations": [], "angle": "", "email": ""}

    if not website.startswith("http"):
        website = "https://" + website

    try:
        page.goto(website, wait_until="domcontentloaded", timeout=15000)
        page.wait_for_timeout(1500)
    except Exception:
        return {"tech_stack": [], "observations": [], "angle": "", "email": ""}

    html_text  = page.content()
    html_lower = html_text.lower()

    tech_stack   = []
    observations = []

    # Tech detection
    if "shopify" in html_lower or "cdn.shopify" in html_lower:
        tech_stack.append("Shopify")
    if "wordpress" in html_lower or "wp-content" in html_lower:
        tech_stack.append("WordPress")
    if "wix.com" in html_lower or "wixsite" in html_lower:
        tech_stack.append("Wix")
    if "squarespace" in html_lower:
        tech_stack.append("Squarespace")
    if "webflow" in html_lower:
        tech_stack.append("Webflow")

    # Missing systems
    has_chat   = any(x in html_lower for x in ("tawk.to","intercom","livechat","freshchat","crisp","zendesk"))
    has_book   = any(x in html_lower for x in ("calendly","acuity","booksy","cal.com","bookingpress","timely","appointlet"))
    has_email  = any(x in html_lower for x in ("mailchimp","klaviyo","omnisend","convertkit","activecampaign","drip"))
    has_review = any(x in html_lower for x in ("trustpilot","yotpo","judge.me","stamped","okendo","loox"))
    has_popup  = any(x in html_lower for x in ("privy","popup","poptin","optinmonster","sumo","sleeknote"))

    if not has_chat:
        observations.append("No live chat — customer questions go unanswered outside business hours")
    if not has_book and any(w in html_lower for w in ("service","appointment","consult","book","schedule")):
        observations.append("No online booking — customers have to call or email to schedule")
    if not has_email:
        observations.append("No email marketing visible — no automated follow-up on visitors who don't buy")
    if not has_review and "shopify" in html_lower:
        observations.append("No review system — missing social proof that converts browsers into buyers")
    if not has_popup and "shopify" in html_lower:
        observations.append("No email capture popup — visitor leaves and is gone forever")

    # Shopify-specific issues
    if "shopify" in html_lower:
        if "sold out" in html_lower:
            observations.append("Sold-out items visible on homepage — first impression looks closed for business")
        if "$0.00" in html_text or "price\":\"0" in html_lower:
            observations.append("$0.00 pricing visible — looks like a broken store to buyers")

    # WordPress issues
    if "wordpress" in html_lower:
        if "hello world" in html_lower:
            observations.append("Default WordPress placeholder content still visible — site looks unfinished")

    # Extract email from current page
    emails = _extract_emails_from_content(html_text)

    # Try contact page if no email found
    if not emails:
        base = website.rstrip("/")
        for path in ["/contact", "/contact-us", "/contact.html", "/about", "/about-us"]:
            try:
                page.goto(base + path, wait_until="domcontentloaded", timeout=10000)
                page.wait_for_timeout(800)
                emails = _extract_emails_from_content(page.content())
                if emails:
                    break
            except Exception:
                pass

    angle = observations[0] if observations else f"Quick thing I noticed on {business_name}"

    return {
        "tech_stack":   tech_stack,
        "observations": observations,
        "angle":        angle,
        "email":        emails[0] if emails else "",
    }


def _extract_emails_from_content(html_text: str) -> list[str]:
    """Extract real email addresses from HTML."""
    skip_domains = {
        "example.com","sentry.io","wixpress.com","shopify.com","w3.org",
        "schema.org","googleapis.com","gstatic.com","facebook.com","twitter.com",
        "instagram.com","linkedin.com","apple.com","google.com","amazon.com",
        "microsoft.com","cloudflare.com","jquery.com","unpkg.com","github.com",
        "youtube.com","tiktok.com","pinterest.com","yelp.com","tripadvisor.com",
    }
    skip_prefixes = ("noreply","no-reply","donotreply","mailer-daemon","postmaster",
                     "abuse","spam","webmaster","admin@","info@wp","privacy@")

    raw = re.findall(r'mailto:([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})', html_text)
    raw += re.findall(r'\b([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})\b', html_text)

    seen, clean = set(), []
    for email in raw:
        email = email.lower().strip(".")
        domain = email.split("@")[-1]
        if domain in skip_domains:
            continue
        if any(email.startswith(p) for p in skip_prefixes):
            continue
        if email not in seen:
            seen.add(email)
            clean.append(email)
    return clean[:3]


# ─── Email personalization ────────────────────────────────────────────────────

def _ai_write_email(business_name: str, website: str,
                    tech_stack: list, observations: list) -> str:
    """Claude Haiku writes a personalized email if ANTHROPIC_API_KEY is set."""
    if not AI_KEY:
        return ""

    obs_text  = "\n".join(f"- {o}" for o in observations[:3]) or "- No specific issues found"
    tech_text = ", ".join(tech_stack) or "unknown"

    prompt = (
        f"Write a cold outreach email from Emmanuel (web/automation specialist) "
        f"to the owner of {business_name}.\n\n"
        f"Website: {website}\nTech: {tech_text}\nSite issues:\n{obs_text}\n\n"
        f"Rules:\n"
        f"- 80-100 words max\n"
        f"- Open with THEIR situation, not 'I'\n"
        f"- One specific observation from their site\n"
        f"- One clear ask (call or reply)\n"
        f"- Direct, slightly senior tone — no corporate speak\n"
        f"- No 'passionate about', 'leverage', 'synergy', 'delighted'\n"
        f"- Sign off: Emmanuel\n"
        f"- Body only, no subject line"
    )

    try:
        payload = json.dumps({
            "model":    "claude-haiku-4-5-20251001",
            "max_tokens": 300,
            "messages": [{"role": "user", "content": prompt}],
        }).encode("utf-8")
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            headers={
                "x-api-key":         AI_KEY,
                "anthropic-version": "2023-06-01",
                "content-type":      "application/json",
            }
        )
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())["content"][0]["text"].strip()
    except Exception as e:
        print(f"[prospector] AI email error: {e}", file=sys.stderr)
        return ""


def build_email_body(business_name: str, website: str,
                     tech_stack: list, observations: list) -> str:
    ai = _ai_write_email(business_name, website, tech_stack, observations)
    if ai:
        return ai

    angle    = observations[0] if observations else f"a few things on the {business_name} site worth a look"
    tech_note= f" (I see you're on {tech_stack[0]})" if tech_stack else ""

    return (
        f"Hey,\n\n"
        f"{angle}{tech_note}.\n\n"
        f"I help businesses fix the gaps that cost sales — whether that's the site, "
        f"the automation, or both. Usually takes less than a week to see results.\n\n"
        f"Worth a quick call?\n\n"
        f"Emmanuel"
    ).strip()


def build_subject(business_name: str, observations: list) -> str:
    if observations and len(observations[0]) < 55:
        return observations[0]
    return f"Quick thing on {business_name}"


# ─── Prospect node creation ───────────────────────────────────────────────────

def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower().strip())[:40].strip("-")


def create_prospect_node(business: dict, email: str,
                         body: str, analysis: dict, niche: str = "") -> Path:
    PROSPECTS_DIR.mkdir(parents=True, exist_ok=True)

    name    = business.get("name", "")
    website = business.get("website", "")
    phone   = business.get("formatted_phone_number", "")
    address = business.get("formatted_address", "")
    rating  = business.get("rating", "")
    category= business.get("category", niche)

    slug = _slugify(name)
    path = PROSPECTS_DIR / f"{slug}.md"
    if path.exists():
        i = 2
        while path.exists():
            path = PROSPECTS_DIR / f"{slug}-{i}.md"
            i += 1

    obs_text  = "\n".join(f"- {o}" for o in analysis.get("observations", []))
    tech_text = ", ".join(analysis.get("tech_stack", [])) or "unknown"

    content = f"""---
name: {name}
company: {name}
role: Owner
email: {email}
phone: {phone}
website: {website}
address: {address}
rating: {rating}
category: {category}
niche: {niche}
status: prospect
outreach_sent_on:
referred_by: Google Maps prospector
platform: cold
sensitivity: private
---

## Context
Found via Google Maps search. {category + " business." if category else ""}
Website: {website}
Tech stack: {tech_text}
Rating: {rating}

## Outreach Notes
{body}

## Site Observations
{obs_text if obs_text else "- No specific issues detected"}

## Conversation Log
{datetime.now().strftime("%Y-%m-%d")} — Prospect created via Google Maps prospector.
"""
    path.write_text(content, encoding="utf-8")
    return path


# ─── Main pipeline ────────────────────────────────────────────────────────────

def run_prospector(query: str, limit: int = 10, niche: str = "",
                   auto: bool = False, dry_run: bool = False) -> None:
    """Full pipeline: Maps → website → email → prospect node → send."""
    from scripts.notify import send as tg_send

    print(f"\n[prospector] Query: '{query}' | Limit: {limit} | Auto: {auto} | Dry: {dry_run}")

    # Phase 1: Scrape Google Maps
    businesses = scrape_google_maps(query, limit=limit)
    if not businesses:
        print("[prospector] No businesses found.")
        return

    print(f"\n[prospector] Analyzing {len(businesses)} businesses...")

    created, no_email, skipped = [], [], []

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[prospector] Playwright not installed.", file=sys.stderr)
        sys.exit(1)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 900},
        )
        page = context.new_page()

        for i, biz in enumerate(businesses, 1):
            name    = biz.get("name", "?")
            website = biz.get("website", "")
            print(f"  [{i}/{len(businesses)}] {name}")

            if not website:
                print(f"     No website — skipping")
                skipped.append(name)
                continue

            # Phase 2: Analyze website + extract email
            analysis = analyze_website_playwright(page, website, name)
            email    = analysis.get("email", "")

            if not email:
                print(f"     No email found — skipping")
                no_email.append(name)
                continue

            print(f"     Email: {email} | Issues: {len(analysis['observations'])}")

            # Phase 3: Write email
            body    = build_email_body(name, website, analysis["tech_stack"], analysis["observations"])
            subject = build_subject(name, analysis["observations"])

            if dry_run:
                print(f"\n     [DRY RUN] Subject: {subject}")
                print(f"     Body: {body[:100]}...")
                created.append(name)
                continue

            # Phase 4: Create prospect node
            node_path = create_prospect_node(biz, email, body, analysis, niche)
            print(f"     Node: {node_path.name}")
            created.append(name)

            # Phase 5: Auto-send if requested
            if auto:
                import scripts.outreach as out
                text         = node_path.read_text(encoding="utf-8", errors="ignore")
                meta         = out._parse_frontmatter(text)
                prospect_obj = {
                    "path":    str(node_path),
                    "slug":    node_path.stem,
                    "meta":    meta,
                    "context": out._read_section(text, "Context"),
                    "notes":   out._read_section(text, "Outreach Notes"),
                }
                out.auto_send(prospect_obj, dry_run=False)

            time.sleep(0.5)

        browser.close()

    # Summary
    sent_count = len(created) if auto else 0
    print(f"\n[prospector] Done.")
    print(f"  Sent:     {sent_count}")
    print(f"  Created:  {len(created)} nodes")
    print(f"  No email: {len(no_email)}")
    print(f"  Skipped:  {len(skipped)} (no website)")

    if not dry_run:
        tg_send(
            f"🗺 <b>Prospector:</b> '{query}'\n\n"
            f"✅ {len(created)} {'sent' if auto else 'nodes created'}\n"
            f"❌ {len(no_email)} had no email\n"
            f"⏭️ {len(skipped)} had no website"
        )


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Upwork OS — Google Maps Prospector")
    parser.add_argument("--query",   required=True, help="Search e.g. 'furniture stores Brooklyn NY'")
    parser.add_argument("--limit",   type=int, default=10, help="Max businesses (default: 10)")
    parser.add_argument("--niche",   default="", help="Niche tag, e.g. ecommerce")
    parser.add_argument("--auto",    action="store_true", help="Auto-send emails immediately")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, nothing sent or saved")
    args = parser.parse_args()

    run_prospector(
        query   = args.query,
        limit   = args.limit,
        niche   = args.niche,
        auto    = args.auto,
        dry_run = args.dry_run,
    )


if __name__ == "__main__":
    main()
