#!/usr/bin/env python3
"""
Upwork OS — Google Maps Prospector

Searches Google Maps for businesses, extracts contact info from their websites,
writes personalized outreach emails (AI-powered if ANTHROPIC_API_KEY is set),
creates prospect nodes, and fires the outreach engine automatically.

Requirements:
    GOOGLE_MAPS_API_KEY in config.py
    Enable "Places API" at console.cloud.google.com (same project as Gmail)

Usage:
    python scripts/prospector.py --query "furniture stores Brooklyn NY" --limit 10
    python scripts/prospector.py --query "digital agencies Lagos" --limit 20 --auto
    python scripts/prospector.py --query "shopify stores New York" --niche ecommerce --limit 15
    python scripts/prospector.py --query "law firms Chicago" --limit 5 --dry-run
"""

import sys
import re
import json
import time
import argparse
import urllib.request
import urllib.parse
import urllib.error
import html
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

ROOT          = config.ROOT
BRAIN         = config.BRAIN
PROSPECTS_DIR = BRAIN / "outreach" / "prospects"
MAPS_KEY      = getattr(config, "GOOGLE_MAPS_API_KEY", "")
AI_KEY        = getattr(config, "ANTHROPIC_API_KEY", "")

PLACES_SEARCH_URL  = "https://maps.googleapis.com/maps/api/place/textsearch/json"
PLACES_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"


# ─── Google Places API ────────────────────────────────────────────────────────

def _places_request(url: str, params: dict) -> dict:
    params["key"] = MAPS_KEY
    full_url = url + "?" + urllib.parse.urlencode(params)
    try:
        req = urllib.request.Request(full_url, headers={"User-Agent": "UpworkOS/1.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"[prospector] Places API error: {e}", file=sys.stderr)
        return {}


def search_places(query: str, limit: int = 10) -> list[dict]:
    """Text search Google Maps. Returns list of place dicts."""
    results = []
    params  = {"query": query, "type": "establishment"}
    seen    = set()

    while len(results) < limit:
        data = _places_request(PLACES_SEARCH_URL, params)
        if not data or data.get("status") not in ("OK", "ZERO_RESULTS"):
            print(f"[prospector] Places API status: {data.get('status', 'ERROR')}", file=sys.stderr)
            break

        for place in data.get("results", []):
            if len(results) >= limit:
                break
            pid = place.get("place_id")
            if pid in seen:
                continue
            seen.add(pid)
            results.append(place)

        next_token = data.get("next_page_token")
        if not next_token or len(results) >= limit:
            break
        time.sleep(2)  # Google requires 2s before using next_page_token
        params = {"pagetoken": next_token}

    return results


def get_place_details(place_id: str) -> dict:
    """Get full details for a place including website, phone, formatted_address."""
    data = _places_request(PLACES_DETAILS_URL, {
        "place_id": place_id,
        "fields":   "name,formatted_address,website,formatted_phone_number,rating,user_ratings_total,business_status",
    })
    return data.get("result", {})


# ─── Website contact extraction ───────────────────────────────────────────────

def _fetch_url(url: str, timeout: int = 10) -> str:
    """Fetch URL content. Returns HTML string or empty string on failure."""
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            charset = r.headers.get_content_charset() or "utf-8"
            return raw.decode(charset, errors="ignore")
    except Exception:
        return ""


def extract_emails_from_html(html_text: str) -> list[str]:
    """Extract email addresses from HTML content."""
    # mailto: links
    mailto = re.findall(r'mailto:([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})', html_text)
    # Plain text emails
    plain  = re.findall(r'\b([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})\b', html_text)

    all_emails = []
    skip_domains = {"example.com", "sentry.io", "wixpress.com", "shopify.com",
                    "w3.org", "schema.org", "googleapis.com", "gstatic.com",
                    "facebook.com", "twitter.com", "instagram.com", "linkedin.com",
                    "apple.com", "google.com", "amazon.com", "microsoft.com",
                    "cloudflare.com", "jquery.com", "unpkg.com", "emailprotected"}

    seen = set()
    for email in mailto + plain:
        email = email.lower().strip(".")
        domain = email.split("@")[-1]
        if domain in skip_domains or any(s in email for s in ("noreply", "no-reply", "donotreply", "support@", "abuse@")):
            continue
        if email not in seen:
            seen.add(email)
            all_emails.append(email)

    return all_emails[:3]  # Top 3 most relevant


def find_contact_email(website: str) -> str:
    """Visit a website and its /contact page to find a real email."""
    if not website:
        return ""

    # Normalize URL
    if not website.startswith("http"):
        website = "https://" + website

    # Try homepage first
    homepage = _fetch_url(website)
    emails   = extract_emails_from_html(homepage)
    if emails:
        return emails[0]

    # Try /contact page
    base = website.rstrip("/")
    for path in ("/contact", "/contact-us", "/contact.html", "/about", "/about-us"):
        contact_html = _fetch_url(base + path)
        if contact_html:
            emails = extract_emails_from_html(contact_html)
            if emails:
                return emails[0]

    return ""


def analyze_website(website: str, business_name: str) -> dict:
    """
    Analyze website to extract personalization context.
    Returns dict with: tech_stack, observations, angle.
    """
    if not website:
        return {"tech_stack": [], "observations": [], "angle": ""}

    if not website.startswith("http"):
        website = "https://" + website

    html_text = _fetch_url(website)
    if not html_text:
        return {"tech_stack": [], "observations": [], "angle": ""}

    html_lower = html_text.lower()
    observations = []
    tech_stack   = []

    # Tech detection
    if "shopify" in html_lower:
        tech_stack.append("Shopify")
    if "wordpress" in html_lower or "wp-content" in html_lower:
        tech_stack.append("WordPress")
    if "wix" in html_lower:
        tech_stack.append("Wix")
    if "squarespace" in html_lower:
        tech_stack.append("Squarespace")
    if "webflow" in html_lower:
        tech_stack.append("Webflow")

    # Missing systems — quick pattern checks
    has_chat     = any(x in html_lower for x in ("tawk.to", "intercom", "livechat", "freshchat", "zendesk", "crisp"))
    has_booking  = any(x in html_lower for x in ("calendly", "acuity", "booksy", "cal.com", "bookingpress", "timely"))
    has_email_mkt= any(x in html_lower for x in ("mailchimp", "klaviyo", "omnisend", "convertkit", "activecampaign"))
    has_reviews  = any(x in html_lower for x in ("trustpilot", "yotpo", "judge.me", "stamped", "okendo"))

    if not has_chat:
        observations.append("No live chat — customer questions go unanswered after hours")
    if not has_booking and "service" in html_lower:
        observations.append("No online booking — customers have to call or email to schedule")
    if not has_email_mkt:
        observations.append("No email marketing visible — no automated follow-up on visitors who don't buy")
    if not has_reviews and "shopify" in html_lower:
        observations.append("No review system — missing social proof that drives conversions")

    # Sold out / $0 pricing check (Shopify stores)
    if "shopify" in html_lower:
        if "sold out" in html_lower:
            observations.append("Sold-out products visible on homepage — first impression looks closed")
        if "$0.00" in html_text or "price: 0" in html_lower:
            observations.append("$0.00 pricing on products — looks broken to buyers")

    # Build top angle from first observation
    angle = observations[0] if observations else f"Quick thing I noticed on {business_name}'s site"

    return {
        "tech_stack":    tech_stack,
        "observations":  observations,
        "angle":         angle,
    }


# ─── Email personalization ────────────────────────────────────────────────────

def _ai_write_email(business_name: str, website: str, role: str,
                    tech_stack: list, observations: list) -> str:
    """Use Claude API to write a personalized outreach email. Requires ANTHROPIC_API_KEY."""
    if not AI_KEY:
        return ""

    obs_text  = "\n".join(f"- {o}" for o in observations[:3]) if observations else "- No specific issues found"
    tech_text = ", ".join(tech_stack) if tech_stack else "unknown"

    prompt = f"""Write a cold outreach email from Emmanuel (a web/automation specialist) to the owner of {business_name}.

Website: {website}
Tech stack detected: {tech_text}
Issues found on their site:
{obs_text}

Rules:
- 80-100 words max
- First line starts with THEIR situation, not "I"
- One specific observation from their site
- One clear ask (call or reply)
- Direct, slightly senior tone — no corporate speak
- NO: "I am passionate about", "leverage", "synergy", "I would be delighted"
- Sign off as: Emmanuel
- Do NOT include a subject line — body only"""

    try:
        payload = json.dumps({
            "model":      "claude-haiku-4-5-20251001",
            "max_tokens": 300,
            "messages":   [{"role": "user", "content": prompt}],
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
            resp = json.loads(r.read())
            return resp["content"][0]["text"].strip()
    except Exception as e:
        print(f"[prospector] AI email error: {e}", file=sys.stderr)
        return ""


def build_email_body(business_name: str, owner_name: str, website: str,
                     tech_stack: list, observations: list) -> str:
    """Build personalized email — AI if key available, template otherwise."""

    # Try AI first
    ai_body = _ai_write_email(business_name, website, owner_name, tech_stack, observations)
    if ai_body:
        return ai_body

    # Template fallback
    greeting = f"Hey," if not owner_name else f"Hey {owner_name.split()[0].title()},"
    angle    = observations[0] if observations else f"a few things on {business_name}'s site worth a quick look"
    tech_note = f" (I can see you're on {tech_stack[0]})" if tech_stack else ""

    return (
        f"{greeting}\n\n"
        f"{angle}{tech_note}.\n\n"
        f"I help businesses like yours fix the gaps that cost sales — "
        f"whether that's the site, the automation, or both. Usually takes less than a week to see results.\n\n"
        f"Worth a quick call?\n\n"
        f"Emmanuel"
    ).strip()


def build_subject(business_name: str, observations: list) -> str:
    """Build subject line from top observation."""
    if observations:
        obs = observations[0]
        if len(obs) < 55:
            return obs
    return f"Quick thing on {business_name}"


# ─── Prospect node creation ───────────────────────────────────────────────────

def _slugify(text: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", text.lower().strip())
    return text[:40].strip("-")


def create_prospect_node(business: dict, email: str, subject: str, body: str) -> Path:
    """Write a prospect node to outreach/prospects/ and return the path."""
    PROSPECTS_DIR.mkdir(parents=True, exist_ok=True)

    name    = business.get("name", "")
    website = business.get("website", "")
    phone   = business.get("formatted_phone_number", "")
    address = business.get("formatted_address", "")
    rating  = business.get("rating", "")
    niche   = business.get("_niche", "")

    slug = _slugify(name)
    path = PROSPECTS_DIR / f"{slug}.md"

    # Don't overwrite existing nodes
    if path.exists():
        counter = 2
        while path.exists():
            path = PROSPECTS_DIR / f"{slug}-{counter}.md"
            counter += 1

    obs_text = "\n".join(f"- {o}" for o in business.get("_observations", []))
    tech_text = ", ".join(business.get("_tech_stack", [])) or "unknown"

    content = f"""---
name: {name}
company: {name}
role: Owner
email: {email}
phone: {phone}
website: {website}
address: {address}
rating: {rating}
niche: {niche}
status: prospect
outreach_sent_on:
referred_by: Google Maps prospector
platform: cold
sensitivity: private
---

## Context
Found via Google Maps search. {niche.title() + " business." if niche else ""}
Website: {website}
Tech stack: {tech_text}
Rating: {rating} stars (if available)

## Outreach Notes
{body}

## Site Observations
{obs_text if obs_text else "- No specific issues detected"}

## Conversation Log
{datetime.now().strftime("%Y-%m-%d")} — Prospect created via Google Maps prospector. Email not yet sent.
"""

    path.write_text(content, encoding="utf-8")
    return path


# ─── Main pipeline ────────────────────────────────────────────────────────────

def prospect(query: str, limit: int = 10, niche: str = "",
             auto_send: bool = False, dry_run: bool = False) -> None:
    """Full pipeline: search → extract → personalize → create node → send."""
    from scripts.notify import send as tg_send

    if not MAPS_KEY:
        print("[prospector] GOOGLE_MAPS_API_KEY not set in config.py", file=sys.stderr)
        print("Enable Places API at console.cloud.google.com and add the key.", file=sys.stderr)
        sys.exit(1)

    print(f"[prospector] Searching: '{query}' (limit {limit})...")
    places = search_places(query, limit=limit)
    print(f"[prospector] Found {len(places)} places.")

    created    = []
    skipped    = []
    no_email   = []

    for i, place in enumerate(places, 1):
        place_id = place.get("place_id", "")
        name     = place.get("name", "Unknown")
        print(f"  [{i}/{len(places)}] {name}...")

        # Get full details
        details  = get_place_details(place_id)
        website  = details.get("website", "")
        phone    = details.get("formatted_phone_number", "")
        status   = details.get("business_status", "OPERATIONAL")

        if status != "OPERATIONAL":
            skipped.append(name + " (closed)")
            continue

        # Find email from website
        email = find_contact_email(website) if website else ""
        if not email:
            no_email.append(name)
            print(f"     No email found — skipping")
            continue

        # Analyze website
        analysis = analyze_website(website, name)
        analysis["_niche"] = niche

        # Build email
        body    = build_email_body(name, "", website, analysis["tech_stack"], analysis["observations"])
        subject = build_subject(name, analysis["observations"])

        # Merge analysis into details for node creation
        details["_tech_stack"]    = analysis["tech_stack"]
        details["_observations"]  = analysis["observations"]
        details["_niche"]         = niche

        if dry_run:
            print(f"\n[DRY RUN] {name} <{email}>")
            print(f"  Subject: {subject}")
            print(f"  Body preview: {body[:120]}...")
            created.append(name)
            continue

        # Create prospect node
        node_path = create_prospect_node(details, email, subject, body)
        created.append(name)
        print(f"     Node: {node_path.name}")

        # Auto-send if requested
        if auto_send:
            import scripts.outreach as outreach_mod
            text = node_path.read_text(encoding="utf-8")
            meta = outreach_mod._parse_frontmatter(text)
            prospect_dict = {
                "path":    str(node_path),
                "slug":    node_path.stem,
                "meta":    meta,
                "context": outreach_mod._read_section(text, "Context"),
                "notes":   outreach_mod._read_section(text, "Outreach Notes"),
            }
            outreach_mod.auto_send(prospect_dict, dry_run=False)

        time.sleep(0.5)  # Rate limit courtesy

    # Summary
    print(f"\n[prospector] Done.")
    print(f"  Created: {len(created)} nodes")
    print(f"  No email: {len(no_email)} — {', '.join(no_email[:5])}")
    print(f"  Skipped:  {len(skipped)}")

    # Telegram summary
    if not dry_run:
        summary = (
            f"🗺 <b>Prospector done:</b> '{query}'\n\n"
            f"✅ {len(created)} prospect nodes created\n"
            f"📧 {len(created)} emails {'sent' if auto_send else 'queued'}\n"
            f"❌ {len(no_email)} had no email\n"
            f"⏭️ {len(skipped)} skipped (closed)"
        )
        tg_send(summary)


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Upwork OS — Google Maps Prospector")
    parser.add_argument("--query",  required=True, help="Search query, e.g. 'furniture stores Brooklyn NY'")
    parser.add_argument("--limit",  type=int, default=10, help="Max prospects to find (default: 10)")
    parser.add_argument("--niche",  default="", help="Niche tag for prospect nodes, e.g. ecommerce")
    parser.add_argument("--auto",   action="store_true", help="Auto-send emails immediately after creating nodes")
    parser.add_argument("--dry-run",action="store_true", help="Preview only — no nodes created, no emails sent")
    args = parser.parse_args()

    prospect(
        query     = args.query,
        limit     = args.limit,
        niche     = args.niche,
        auto_send = args.auto,
        dry_run   = args.dry_run,
    )


if __name__ == "__main__":
    main()
