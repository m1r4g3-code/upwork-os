#!/usr/bin/env python3
"""
Upwork OS — Multi-Source Prospector (Playwright)

Sources:
  --source maps   Google Maps local businesses (quick wins, email extraction)
  --source dr     DesignRush agency directory (verified US agencies, high-budget)
  --source yc     Y Combinator company directory (funded US startups) [disabled]
  --source ph     ProductHunt recent launches (signal: just launched, no ops systems yet)
  --source tc     TechCrunch funding news (signal: just raised, scaling pain coming)

Signal-based outreach: each source carries a trigger event that drives the email angle.
Hunter.io integration (set HUNTER_API_KEY in config) upgrades email finding to
decision-maker level (CEO/founder/COO) instead of generic contact page scraping.

No API keys needed for scraping. Hunter.io key is optional but improves email quality.

Usage:
    python scripts/prospector.py --source dr --category social-media --limit 15 --auto
    python scripts/prospector.py --source ph --limit 10 --dry-run
    python scripts/prospector.py --source tc --limit 10 --auto
    python scripts/prospector.py --source maps --query "video production agency Chicago" --limit 10 --auto
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
HUNTER_KEY    = getattr(config, "HUNTER_API_KEY", "")


# ─── Shared Playwright helpers ────────────────────────────────────────────────

def _new_browser(pw, headless: bool = True):
    return pw.chromium.launch(
        headless=headless,
        args=["--no-sandbox", "--disable-dev-shm-usage",
              "--disable-blink-features=AutomationControlled"],
    )

def _new_context(browser):
    return browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
        viewport={"width": 1280, "height": 900},
        locale="en-US",
    )

def _dismiss_overlays(page) -> None:
    for selector in [
        'button[aria-label*="Accept all"]',
        'button[aria-label*="Accept"]',
        'button[jsname="b3VHJd"]',
        'form[action*="consent"] button',
        'button:has-text("Accept")',
        'button:has-text("I agree")',
        '[id*="cookie"] button',
    ]:
        try:
            if page.locator(selector).count() > 0:
                page.locator(selector).first.click(timeout=2000)
                page.wait_for_timeout(600)
                break
        except Exception:
            pass

def _extract_text(page, selectors: list) -> str:
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

def _extract_attr(page, selectors: list, attr: str) -> str:
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


# ─── Source 1: Google Maps ────────────────────────────────────────────────────

def _scrape_maps_detail(page, url: str) -> dict | None:
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(2000)
        _dismiss_overlays(page)
    except Exception as e:
        print(f"     [maps] Load error: {e}", file=sys.stderr)
        return None

    name = _extract_text(page, ["h1.DUwDvf", "h1[class*='fontDisplayLarge']", "h1"])
    if not name:
        return None

    website = _extract_attr(page, [
        'a[data-item-id="authority"]',
        'a[aria-label*="website" i]',
    ], "href")

    phone = _extract_text(page, [
        'button[data-item-id*="phone"] div.rogA2c',
        '[data-tooltip="Copy phone number"]',
    ])
    phone = re.sub(r"[^\d\s\-\+\(\)]", "", phone).strip()

    address = _extract_text(page, [
        'button[data-item-id="address"] div.rogA2c',
        '[data-tooltip="Copy address"]',
    ])

    category = _extract_text(page, ['button[jsaction*="category"]', 'span.DkEaL'])
    rating   = _extract_text(page, ['div.F7nice span[aria-hidden="true"]'])

    return {
        "name": name,
        "website": website,
        "formatted_phone_number": phone,
        "formatted_address": address,
        "category": category,
        "rating": rating,
        "source": "maps",
    }


def scrape_google_maps(query: str, limit: int = 10) -> list:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[prospector] Playwright not installed. Run: pip install playwright && playwright install chromium")
        sys.exit(1)

    results    = []
    place_urls = []
    search_url = "https://www.google.com/maps/search/" + urllib.parse.quote_plus(query)

    with sync_playwright() as pw:
        browser = _new_browser(pw)
        page    = _new_context(browser).new_page()
        page.set_extra_http_headers({"Accept-Language": "en-US,en;q=0.9"})

        print(f"[maps] {search_url}")
        try:
            page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(3000)
            _dismiss_overlays(page)
        except Exception as e:
            print(f"[maps] Load error: {e}", file=sys.stderr)
            browser.close()
            return []

        try:
            page.wait_for_selector('[role="feed"]', timeout=15000)
        except Exception:
            print("[maps] Results feed not found", file=sys.stderr)
            browser.close()
            return []

        seen = set()
        for _ in range(20):
            for link in page.locator('a[href*="/maps/place/"]').all():
                try:
                    href = link.get_attribute("href")
                    if href and "/maps/place/" in href:
                        clean = re.split(r'\?', href)[0]
                        if clean not in seen:
                            seen.add(clean)
                            place_urls.append(clean)
                except Exception:
                    pass
            if len(place_urls) >= limit:
                break
            try:
                page.locator('[role="feed"]').first.evaluate("el => el.scrollBy(0, 600)")
            except Exception:
                page.evaluate("window.scrollBy(0, 600)")
            page.wait_for_timeout(1500)

        place_urls = place_urls[:limit]
        print(f"[maps] {len(place_urls)} places collected. Fetching details...")

        for i, url in enumerate(place_urls, 1):
            label = url.split('/place/')[-1][:35]
            print(f"  [{i}/{len(place_urls)}] {label}...")
            detail = _scrape_maps_detail(page, url)
            if detail:
                results.append(detail)
            time.sleep(0.8)

        browser.close()

    return results


# ─── Source 2: DesignRush agency directory ────────────────────────────────────
# Replaces Clutch.co (blocked by Cloudflare). DesignRush listing pages include
# external agency website links directly — no profile page visits needed.

DESIGNRUSH_CATEGORIES = {
    "social-media":   "social-media-marketing",
    "content":        "content-marketing",
    "video":          "video-production",
    "digital":        "digital-marketing",
    "email":          "email-marketing",
    "ecommerce":      "ecommerce-development",
    "seo":            "search-engine-optimization",
    "branding":       "branding-agencies",
    "automation":     "web-development",
    "app-dev":        "mobile-app-development",
}


def scrape_designrush(category: str, limit: int = 10) -> list:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[prospector] Playwright not installed.")
        sys.exit(1)

    cat_slug = DESIGNRUSH_CATEGORIES.get(category, category)
    url      = f"https://www.designrush.com/agency/{cat_slug}"
    print(f"[dr] {url}")

    results = []

    with sync_playwright() as pw:
        browser = _new_browser(pw)
        context = _new_context(browser)
        page    = context.new_page()

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(3000)
            _dismiss_overlays(page)
        except Exception as e:
            print(f"[dr] Load error: {e}", file=sys.stderr)
            browser.close()
            return []

        # Scroll to load more agency cards
        for _ in range(4):
            page.evaluate("window.scrollBy(0, 2000)")
            page.wait_for_timeout(900)

        # Extract slug → website pairs directly from the listing page.
        # DesignRush cards include both the profile link (/agency/profile/slug)
        # and the agency's external website link — no profile visit needed.
        agencies = page.evaluate("""() => {
            const result = [];
            const seenSlugs = new Set();
            const profileLinks = Array.from(
                document.querySelectorAll('a[href*="/agency/profile/"]')
            );

            for (const profileLink of profileLinks) {
                const href = profileLink.href;
                const slug = href
                    .split('/agency/profile/')[1]
                    ?.split('#')[0]
                    ?.split('?')[0];
                if (!slug || seenSlugs.has(slug)) continue;
                seenSlugs.add(slug);

                // Walk up DOM to find the card that contains external links
                let card = profileLink.parentElement;
                let extUrl = '';
                for (let i = 0; i < 10; i++) {
                    if (!card) break;
                    const extLinks = Array.from(card.querySelectorAll('a[href^="http"]'))
                        .map(a => a.href)
                        .filter(h =>
                            !h.includes('designrush.com') &&
                            !h.includes('news.designrush')
                        );
                    if (extLinks.length > 0) {
                        extUrl = extLinks[0];
                        break;
                    }
                    card = card.parentElement;
                }
                result.push({slug, website: extUrl});
            }
            return result;
        }""")

        browser.close()

    # Remove sponsored-slot leaks: a URL shared by 2+ different agencies = injected ad link
    from collections import Counter
    _url_counts = Counter(ag["website"] for ag in agencies if ag.get("website"))
    agencies = [ag for ag in agencies if _url_counts.get(ag.get("website", ""), 0) < 2]

    # Build result list — strip UTM params from website URLs
    for ag in agencies[:limit]:
        slug    = ag["slug"]
        website = ag["website"]
        if not website:
            continue
        # Strip UTM params / referral junk
        website = website.split("?")[0].rstrip("/")
        name    = " ".join(w.capitalize() for w in slug.replace("-", " ").split())
        print(f"  {name} -> {website}")
        results.append({
            "name":                   name,
            "website":                website,
            "formatted_phone_number": "",
            "formatted_address":      "United States",
            "category":               category,
            "source":                 "dr",
        })

    print(f"[dr] {len(results)} agencies found")
    return results


# ─── Source 3: Y Combinator directory ────────────────────────────────────────

YC_INDUSTRIES = {
    "media":       "Media+%26+Entertainment",
    "saas":        "B2B+Software+%26+Services",
    "ecommerce":   "Consumer",
    "ai":          "Artificial+Intelligence",
    "marketing":   "Marketing",
    "video":       "Video",
    "content":     "Content+Creation",
}

# Recent active batches
YC_BATCHES = "batch=W25&batch=S25&batch=W24&batch=S24"


def scrape_yc(industry: str = "", limit: int = 10) -> list:
    """YC company directory — currently unavailable (Algolia API is IP-restricted).
    Use --source dr for agency prospects or --source maps for local businesses."""
    print("[yc] YC directory is unavailable — their Algolia API is IP-restricted to browser sessions.")
    print("[yc] Use --source dr for US agency prospects instead.")
    return []


# ─── Source 4: ProductHunt recent launches ────────────────────────────────────
# Signal: company just launched a product = no ops systems built yet, founder overwhelmed.
# Best targets: SaaS, AI tools, productivity apps. Skip: games, hardware, consumer.

PH_SKIP_TAGS = {"game", "gaming", "hardware", "crypto", "blockchain", "nft", "podcast",
                "book", "newsletter", "browser extension", "chrome extension", "font"}

PH_TARGET_TAGS = {"saas", "ai", "productivity", "developer tools", "no-code", "automation",
                  "marketing", "analytics", "crm", "b2b", "api", "workflow"}


def scrape_producthunt(limit: int = 10) -> list:
    """
    Uses ProductHunt RSS feed to get recent launches, then visits each product's
    website directly. No PH session needed, no bot detection.
    """
    import xml.etree.ElementTree as ET

    feed_url = "https://www.producthunt.com/feed"
    print(f"[ph] RSS: {feed_url}")

    NS_ATOM = "http://www.w3.org/2005/Atom"

    articles = []
    try:
        req = urllib.request.Request(feed_url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept":     "application/atom+xml, application/xml, */*",
        })
        with urllib.request.urlopen(req, timeout=15) as r:
            xml_bytes = r.read()
        root = ET.fromstring(xml_bytes)

        for entry in root.findall(f"{{{NS_ATOM}}}entry"):
            title_el = entry.find(f"{{{NS_ATOM}}}title")
            title    = (title_el.text or "").strip() if title_el is not None else ""

            # Atom link is an element with href attribute
            link_el  = entry.find(f"{{{NS_ATOM}}}link[@rel='alternate']")
            if link_el is None:
                link_el = entry.find(f"{{{NS_ATOM}}}link")
            link = (link_el.get("href") or "").strip() if link_el is not None else ""

            summary_el = entry.find(f"{{{NS_ATOM}}}summary")
            desc       = (summary_el.text or "").strip() if summary_el is not None else ""

            published_el = entry.find(f"{{{NS_ATOM}}}published")
            date         = (published_el.text or "")[:10] if published_el is not None else ""

            # PH Atom feed doesn't expose the product's external website directly.
            # We resolve it using DuckDuckGo instant answers on the product name.
            website = ""

            if title and link:
                articles.append({"name": title, "link": link, "website": website,
                                  "desc": re.sub(r'<[^>]+>', '', desc)[:200], "date": date})
    except Exception as e:
        print(f"[ph] Feed error: {e}", file=sys.stderr)
        return []

    if not articles:
        print("[ph] No articles from RSS feed.")
        return []

    print(f"[ph] {len(articles)} launches from RSS. Building prospect list...")

    today   = datetime.now().strftime("%Y-%m-%d")
    results = []
    count   = 0

    for p in articles:
        if count >= limit:
            break
        name    = p["name"].strip()
        website = p["website"].strip()
        tagline = p["desc"][:80]
        date    = p["date"][:10] or today

        if not name or len(name) < 3:
            continue

        # Skip bot/extension/crypto noise via name heuristics
        name_lower = name.lower()
        if any(skip in name_lower for skip in ("chrome extension", "browser extension",
               "nft", "token", "blockchain", "podcast", "newsletter issue")):
            continue

        # Website: use DuckDuckGo instant-answer to find the product's real website
        if not website:
            website = find_website_by_name(name, tagline)

        results.append({
            "name":    name,
            "website": website,
            "tagline": tagline,
            "votes":   0,
            "source":  "ph",
            "signal":  "product_launch",
            "signal_detail": f"Launched on ProductHunt, {date}",
            "formatted_phone_number": "",
            "formatted_address":      "United States",
            "category": "saas",
        })
        count += 1
        print(f"  {name} | {website or 'no website'}")

    print(f"[ph] {len(results)} qualifying launches")
    return results


# ─── Source 5: TechCrunch funding news ───────────────────────────────────────
# Signal: company just raised Series A/B = has money, operational scaling pain imminent.
# Best targets: SaaS, AI, media/content companies that raised $2M-$50M.

def scrape_techcrunch_funding(limit: int = 10) -> list:
    """
    Uses TechCrunch RSS feed + DuckDuckGo instant-answer to find company websites.
    No Playwright needed, no paywall issues.
    """
    import xml.etree.ElementTree as ET

    results      = []
    feed_urls    = [
        "https://techcrunch.com/tag/funding/feed/",
        "https://techcrunch.com/category/venture/feed/",
    ]

    articles = []
    for feed_url in feed_urls:
        print(f"[tc] RSS: {feed_url}")
        try:
            req = urllib.request.Request(feed_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as r:
                xml_bytes = r.read()
            root = ET.fromstring(xml_bytes)
            for item in root.findall(".//item"):
                title = (item.findtext("title") or "").strip()
                link  = (item.findtext("link") or "").strip()
                date  = (item.findtext("pubDate") or "")[:16]
                desc  = (item.findtext("description") or "").strip()
                if title and link:
                    articles.append({"title": title, "link": link, "date": date, "desc": desc})
        except Exception as e:
            print(f"[tc] RSS error: {e}", file=sys.stderr)

    if not articles:
        print("[tc] No articles from RSS. TechCrunch may have changed their feed URL.")
        return []

    print(f"[tc] {len(articles)} articles from RSS. Filtering for funding rounds...")

    # Filter and parse funding articles
    funding_articles = []
    seen_companies   = set()

    for art in articles:
        title       = art["title"]
        title_lower = title.lower()

        funding_keywords = ("raises", "raised", "funding", "series a", "series b",
                            "seed round", "million", "investment", "secures", "closes")
        if not any(k in title_lower for k in funding_keywords):
            continue

        # Amount extraction
        amount_m = 0
        amount_match = re.search(r'\$(\d+(?:\.\d+)?)\s*(m|million|b|billion)', title_lower)
        if amount_match:
            amount_m = float(amount_match.group(1))
            if amount_match.group(2) in ("b", "billion"):
                amount_m *= 1000
        if amount_m > 80:  # Skip mega-rounds
            continue

        # Company name extraction — strip "X-backed", "Former [X]", "How [N]" prefixes
        company = ""
        clean_title = re.sub(
            r'^(?:[A-Za-z\s]+-backed\s+|Former\s+[A-Za-z]+\s+|How\s+\d+\s+)',
            '', title
        ).strip()

        for pattern in [
            r'^([A-Z][A-Za-z0-9\s\.\-]{2,30}?)\s+(?:raises|raised|secures|closes|lands|gets)\b',
            r'^([A-Z][A-Za-z0-9\s\.\-]{2,30}?),\s+(?:a|an|the|which|that)\s+',
        ]:
            m = re.match(pattern, clean_title)
            if m:
                company = m.group(1).strip().rstrip(",")
                # Remove trailing corporate suffixes
                company = re.sub(r'\s+(?:Inc\.?|LLC|Ltd\.?|Corp\.?|Co\.?)$', '', company).strip()
                break

        if not company or len(company) < 3:
            continue
        # Skip titles that read as a sentence rather than a company name
        if any(w in company.lower() for w in (" the ", " a ", " an ", " to ", " and ")):
            continue
        if company in seen_companies:
            continue

        # Stage
        stage = "Venture"
        for s in ("Series B", "Series A", "Pre-Seed", "Seed", "Series C"):
            if s.lower() in title_lower:
                stage = s
                break
        if stage == "Series C":
            continue

        seen_companies.add(company)
        amount_str = f"${int(amount_m)}M" if amount_m else "undisclosed"
        funding_articles.append({**art, "company": company, "stage": stage,
                                  "amount_m": amount_m, "amount_str": amount_str})

    print(f"[tc] {len(funding_articles)} qualifying rounds. Opening articles for website links...")

    if not funding_articles:
        return []

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[prospector] Playwright not installed.")
        sys.exit(1)

    # TechCrunch articles are behind a paywall — use DuckDuckGo to find each company's website
    for art in funding_articles[:limit]:
        company    = art["company"]
        stage      = art["stage"]
        amount_str = art["amount_str"]
        date       = art["date"][:10]
        tagline    = art["title"][:100]

        # DDG lookup for the company's website
        website = find_website_by_name(company, f"startup {stage}")
        print(f"  {company} | {stage} {amount_str} | {website or 'no website'}")

        results.append({
            "name":    company,
            "website": website,
            "tagline": tagline,
            "source":  "tc",
            "signal":  "funding_raised",
            "signal_detail": f"Raised {amount_str} ({stage}), {date}",
            "stage":   stage,
            "amount":  amount_str,
            "formatted_phone_number": "",
            "formatted_address":      "United States",
            "category": "startup",
        })
        time.sleep(0.3)

    print(f"[tc] {len(results)} funded companies")
    return results


# ─── Website analysis ─────────────────────────────────────────────────────────

def _classify_site(html_lower: str, source: str, name: str) -> str:
    """Classify: agency | startup | ecommerce | local"""
    if source in ("clutch", "dr"):
        return "agency"
    if source == "yc":
        return "startup"
    agency_signals = (
        ("clients" in html_lower) +
        ("case study" in html_lower or "case studies" in html_lower) +
        ("agency" in name.lower() or "studio" in name.lower() or "agency" in html_lower) +
        ("portfolio" in html_lower and ("branding" in html_lower or "campaign" in html_lower)) +
        ("our team" in html_lower and "designers" in html_lower)
    )
    if "shopify" in html_lower or "woocommerce" in html_lower:
        return "ecommerce"
    if agency_signals >= 2:
        return "agency"
    return "local"


def _agency_observations(html_lower: str) -> list:
    obs = []
    has_portal   = any(x in html_lower for x in ("client login", "client portal", "client area", "dashboard", "login"))
    has_reports  = any(x in html_lower for x in ("databox", "looker", "tableau", "google data studio", "report builder"))
    has_schedule = any(x in html_lower for x in ("buffer", "hootsuite", "sprout social", "later.com", "publer", "metricool", "loomly"))
    has_crm      = any(x in html_lower for x in ("hubspot", "salesforce", "pipedrive", "zoho", "monday.com", "asana"))

    if not has_portal:
        obs.append("No client portal — clients are getting updates over email, which doesn't scale past 5 clients")
    if not has_reports:
        obs.append("No automated reporting visible — monthly reports probably eat 1-2 days of someone's time")
    if not has_schedule:
        obs.append("No content scheduling tool detected — posting manually or paying per platform is expensive at scale")
    if not has_crm:
        obs.append("No CRM visible — leads and client comms probably tracked in spreadsheets or email threads")

    service_count = sum(1 for s in ("seo", "social media", "video", "email marketing", "ppc", "content", "influencer", "branding") if s in html_lower)
    if service_count >= 4:
        obs.append(f"Offering {service_count}+ services — delivering all of these manually for multiple clients is a capacity trap")

    return obs


def _startup_observations(html_lower: str) -> list:
    obs = []
    has_automation = any(x in html_lower for x in ("zapier", "make.com", "n8n", "airtable", "notion automations", "retool"))
    has_onboarding = any(x in html_lower for x in ("onboarding", "get started", "setup wizard", "quick start"))
    has_analytics  = any(x in html_lower for x in ("amplitude", "mixpanel", "segment", "posthog", "hotjar"))

    if not has_automation:
        obs.append("No automation layer visible — ops are probably manual, which breaks when volume picks up")
    if not has_onboarding:
        obs.append("No visible onboarding flow — new users probably need hand-holding which doesn't scale")
    if not has_analytics:
        obs.append("No product analytics visible — hard to know where users drop off without instrumentation")
    if any(x in html_lower for x in ("waitlist", "beta", "early access", "launching soon")):
        obs.append("Still in early access — the automation foundation is cheapest to build now, before scale locks you in")

    return obs


def _local_observations(html_lower: str) -> list:
    obs = []
    has_chat   = any(x in html_lower for x in ("tawk.to", "intercom", "livechat", "freshchat", "crisp", "zendesk"))
    has_book   = any(x in html_lower for x in ("calendly", "acuity", "booksy", "cal.com", "bookingpress", "timely"))
    has_email  = any(x in html_lower for x in ("mailchimp", "klaviyo", "omnisend", "convertkit", "activecampaign"))
    has_review = any(x in html_lower for x in ("trustpilot", "yotpo", "judge.me", "stamped", "okendo", "loox"))

    if not has_chat:
        obs.append("No live chat — questions go unanswered outside business hours")
    if not has_book and any(w in html_lower for w in ("service", "appointment", "consult", "book", "schedule")):
        obs.append("No online booking — customers still have to call or email to book")
    if not has_email:
        obs.append("No email marketing visible — no automated follow-up after a visitor leaves")
    if not has_review and "shopify" in html_lower:
        obs.append("No review system — missing social proof that closes undecided buyers")

    return obs


def analyze_website_playwright(page, website: str, business_name: str,
                                source: str = "maps") -> dict:
    if not website:
        return {"tech_stack": [], "observations": [], "angle": "", "email": "",
                "biz_type": "local", "page_text": "", "founder_name": ""}

    if not website.startswith("http"):
        website = "https://" + website

    try:
        page.goto(website, wait_until="domcontentloaded", timeout=15000)
        page.wait_for_timeout(1500)
    except Exception:
        return {"tech_stack": [], "observations": [], "angle": "", "email": "",
                "biz_type": "local", "page_text": "", "founder_name": ""}

    html_text  = page.content()
    html_lower = html_text.lower()

    # Extract visible text for Claude analysis (strips HTML tags)
    visible_text = re.sub(r'<[^>]+>', ' ', html_text)
    visible_text = re.sub(r'\s+', ' ', visible_text).strip()[:4000]

    tech_stack = []
    if "shopify" in html_lower or "cdn.shopify" in html_lower:
        tech_stack.append("Shopify")
    if "wordpress" in html_lower or "wp-content" in html_lower:
        tech_stack.append("WordPress")
    if "webflow" in html_lower:
        tech_stack.append("Webflow")
    if "wix.com" in html_lower or "wixsite" in html_lower:
        tech_stack.append("Wix")
    if "squarespace" in html_lower:
        tech_stack.append("Squarespace")
    if "react" in html_lower or "next.js" in html_lower or "_next" in html_lower:
        tech_stack.append("React/Next.js")
    if "hubspot" in html_lower:
        tech_stack.append("HubSpot")

    biz_type     = _classify_site(html_lower, source, business_name)
    observations = {
        "agency":    lambda: _agency_observations(html_lower),
        "startup":   lambda: _startup_observations(html_lower),
        "ecommerce": lambda: _local_observations(html_lower),
        "local":     lambda: _local_observations(html_lower),
    }.get(biz_type, lambda: _local_observations(html_lower))()

    emails = _extract_emails_from_content(html_text)

    # Also try contact/about/team pages for email AND founder name
    founder_name = ""
    extra_pages  = ["/contact", "/contact-us", "/about", "/team", "/about-us"]
    base         = website.rstrip("/")
    for path in extra_pages:
        if emails and founder_name:
            break
        try:
            page.goto(base + path, wait_until="domcontentloaded", timeout=10000)
            page.wait_for_timeout(800)
            page_content = page.content()
            if not emails:
                emails = _extract_emails_from_content(page_content)
            # Try to extract founder/CEO name from team/about pages
            if not founder_name and path in ("/about", "/team", "/about-us"):
                text = re.sub(r'<[^>]+>', ' ', page_content)
                visible_text += " " + text[:1500]  # append to context for Claude
                # Heuristic: look for "CEO", "Founder", "Co-Founder" near a name
                founder_m = re.search(
                    r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s*[,\n|]?\s*(?:CEO|Founder|Co-Founder|Managing Director|President)',
                    page_content
                )
                if founder_m:
                    founder_name = founder_m.group(1).strip()
        except Exception:
            pass

    angle = observations[0] if observations else f"noticed something on {business_name}"

    return {
        "tech_stack":    tech_stack,
        "observations":  observations,
        "angle":         angle,
        "email":         emails[0] if emails else "",
        "biz_type":      biz_type,
        "page_text":     visible_text,
        "founder_name":  founder_name,
    }


def _extract_emails_from_content(html_text: str) -> list:
    skip_domains = {
        "example.com","sentry.io","wixpress.com","shopify.com","w3.org",
        "schema.org","googleapis.com","gstatic.com","facebook.com","twitter.com",
        "instagram.com","linkedin.com","apple.com","google.com","amazon.com",
        "microsoft.com","cloudflare.com","jquery.com","unpkg.com","github.com",
        "youtube.com","tiktok.com","pinterest.com","yelp.com","tripadvisor.com",
        "squarespace.com","webflow.io","template.index","myshopify.com",
        "clutch.co","ycombinator.com","typeform.com","mailchimp.com",
    }
    skip_prefixes = ("noreply","no-reply","donotreply","mailer-daemon","postmaster",
                     "abuse","spam","webmaster","info@wp","privacy@","press@",
                     "legal@","dmca@","support@sentry","careers@","jobs@")

    real_tlds = {
        "com","net","org","io","co","us","uk","ca","au","de","fr","nl","se","no",
        "shop","store","online","app","email","biz","info","pro","design","studio",
        "agency","media","digital","brand","style","fashion","nyc","la","miami","ai",
        "vc","tech","solutions","group","systems","services","consulting","marketing",
    }

    raw  = re.findall(r'mailto:([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})', html_text)
    raw += re.findall(r'\b([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})\b', html_text)

    seen, clean = set(), []
    for email in raw:
        email  = email.lower().strip(".")
        local, _, domain = email.partition("@")
        if "." not in domain:
            continue
        tld = domain.rsplit(".", 1)[-1]
        if tld in ("jpg","jpeg","png","gif","webp","svg","2x","ico","pdf","mp4","mov","zip","js","css","html","xml"):
            continue
        if tld not in real_tlds:
            continue
        if re.search(r'[0-9a-f]{8}-[0-9a-f]{4}-', local):
            continue
        if "/" in local or "\\" in local:
            continue
        if re.search(r'\.(jpg|png|gif|webp|svg|ico)$', local):
            continue
        if domain in skip_domains:
            continue
        if any(email.startswith(p) for p in skip_prefixes):
            continue
        if email not in seen:
            seen.add(email)
            clean.append(email)
    return clean[:3]


# ─── Decision-maker email finder (Hunter.io) ─────────────────────────────────

_DECISION_ROLES = {"ceo", "founder", "co-founder", "owner", "president",
                   "coo", "cto", "head", "director", "vp", "managing"}

def find_website_by_name(name: str, tagline: str = "") -> str:
    """
    Try DuckDuckGo instant-answer first, then domain guessing with HTTP probing.
    Works for well-known entities (DDG) and startups with predictable domains (guessing).
    """
    # 1. DuckDuckGo instant-answer (good for established companies)
    query = f"{name} company startup"
    url   = (f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}"
             f"&format=json&no_redirect=1&no_html=1&skip_disambig=1")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read())

        abstract_url = data.get("AbstractURL", "")
        if abstract_url and not any(s in abstract_url for s in
                                    ("producthunt.com", "twitter.com", "wikipedia",
                                     "facebook.com", "linkedin.com")):
            return abstract_url.split("?")[0].rstrip("/")

        official = data.get("OfficialWebsite", "")
        if official:
            return official.rstrip("/")
    except Exception:
        pass

    # 2. Domain guessing: common startup TLD patterns
    name_slug = re.sub(r'[^a-zA-Z0-9]', '', name).lower()
    if len(name_slug) < 3:
        return ""

    candidates = [
        f"https://{name_slug}.com",
        f"https://{name_slug}.ai",
        f"https://{name_slug}.io",
        f"https://get{name_slug}.com",
        f"https://try{name_slug}.com",
        f"https://{name_slug}.co",
        f"https://{name_slug}.app",
    ]
    for candidate in candidates:
        try:
            req = urllib.request.Request(
                candidate, method="HEAD",
                headers={"User-Agent": "Mozilla/5.0"},
            )
            resp = urllib.request.urlopen(req, timeout=3)
            if resp.status < 400:
                return candidate.rstrip("/")
        except Exception:
            pass

    return ""


def find_decision_maker_email(domain: str) -> dict:
    """
    Try Hunter.io domain search first (if HUNTER_API_KEY set).
    Returns: {"email": str, "name": str, "role": str, "confidence": int}
    Falls back to empty dict (caller falls back to website scraping).
    """
    if not HUNTER_KEY or not domain:
        return {}

    domain = re.sub(r'^https?://', '', domain).split('/')[0].strip()
    if not domain:
        return {}

    url = (f"https://api.hunter.io/v2/domain-search"
           f"?domain={urllib.parse.quote(domain)}"
           f"&limit=10&api_key={HUNTER_KEY}")
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            data = json.loads(r.read())
    except Exception as e:
        print(f"  [hunter] Error: {e}", file=sys.stderr)
        return {}

    emails = data.get("data", {}).get("emails", [])
    if not emails:
        return {}

    # Prefer decision-maker roles with high confidence
    best = None
    for e in emails:
        role        = (e.get("position") or "").lower()
        confidence  = e.get("confidence") or 0
        is_decision = any(r in role for r in _DECISION_ROLES)
        if is_decision and confidence >= 50:
            if best is None or confidence > best.get("confidence", 0):
                best = {
                    "email":      e.get("value", ""),
                    "name":       f"{e.get('first_name','')} {e.get('last_name','')}".strip(),
                    "role":       e.get("position", ""),
                    "confidence": confidence,
                }

    # If no decision-maker found, take highest-confidence email
    if not best and emails:
        e    = max(emails, key=lambda x: x.get("confidence", 0))
        best = {
            "email":      e.get("value", ""),
            "name":       f"{e.get('first_name','')} {e.get('last_name','')}".strip(),
            "role":       e.get("position", ""),
            "confidence": e.get("confidence", 0),
        }

    return best or {}


# ─── Email personalization ────────────────────────────────────────────────────

def _claude_analyze_and_write(
    business_name: str,
    website: str,
    page_text: str,
    signal: str,
    signal_detail: str,
    biz_type: str,
    tech_stack: list,
    founder_name: str = "",
) -> dict:
    """
    Claude reads the actual website content + the trigger signal and produces:
      - founder_name (if found on site)
      - specific_pain (one concrete observation from the site)
      - email_body (under 90 words, signed Emmanuel)
      - subject_line (3-5 words, signal-specific)
    Returns a dict with those keys. Falls back to empty if no AI key.
    """
    if not AI_KEY:
        return {}

    signal_context = {
        "product_launch": (
            f"TRIGGER: {business_name} just launched on ProductHunt ({signal_detail}). "
            f"They probably have no ops automation yet. The earlier you build it the cheaper."
        ),
        "funding_raised": (
            f"TRIGGER: {business_name} just raised money ({signal_detail}). "
            f"They have capital and are now under pressure to scale. "
            f"Manual ops become the first bottleneck at this stage."
        ),
        "website_gap": (
            f"TRIGGER: Website analysis revealed operational gaps. "
            f"Use the most specific one from the website content below."
        ),
    }.get(signal, "Use the most specific operational gap visible from the website.")

    tech_text    = ", ".join(tech_stack) if tech_stack else "unclear"
    founder_hint = f"Known founder/CEO name: {founder_name}." if founder_name else ""

    prompt = f"""You are reading the website of a company called {business_name}.
Website: {website}
Tech stack detected: {tech_text}
{founder_hint}

WEBSITE CONTENT (first 4000 chars of visible text):
---
{page_text[:4000]}
---

{signal_context}

Emmanuel builds AI automation systems using n8n, Make, Claude API, and similar tools.
He builds things like: automated reporting pipelines, user onboarding flows, CRM automation,
content publishing systems, Slack/email alert systems, data sync between tools.
His case study: built a content automation pipeline that reached 1.3M views.

Your job: produce three things.

1. FOUNDER_NAME: The founder or CEO's first name if you can see it in the website content. If not visible, output blank.

2. SPECIFIC_PAIN: The single most concrete operational problem visible from this company's website or the trigger event. Not generic ("they need automation") — specific ("they're manually posting to 3 platforms daily with no scheduling tool" or "raised $17M but their onboarding page is a static FAQ with no automation"). One sentence, under 20 words.

3. EMAIL: A cold outreach email from Emmanuel. Rules:
- Under 90 words total (including sign-off)
- Open with the SPECIFIC_PAIN or the trigger event — not "I" not "Hi I saw your website"
- First line should make them go "how does he know that?"
- Name exactly one tool Emmanuel would use (n8n, Klaviyo, Make, Claude API)
- Give a rough timeline (1-2 weeks, 2-3 weeks)
- End with a binary yes/no question
- No em dashes. No "passionate about". No "leverage". No "streamline". No "seamless".
- Sign off: Emmanuel

4. SUBJECT: A 3-5 word email subject line. Signal-specific. Not generic.
   Good: "Post-$17M ops automation" / "Onboarding gap at Meridian" / "Content pipeline post-launch"
   Bad: "Partnership opportunity" / "Quick question" / "Automation for your business"

Output format (use these exact labels, nothing else):
FOUNDER_NAME: [name or blank]
SPECIFIC_PAIN: [one sentence]
SUBJECT: [3-5 words]
EMAIL:
[the full email body]"""

    try:
        payload = json.dumps({
            "model":      "claude-haiku-4-5-20251001",
            "max_tokens": 500,
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
        with urllib.request.urlopen(req, timeout=25) as r:
            text = json.loads(r.read())["content"][0]["text"].strip()

        # Parse structured output
        result         = {}
        fn_m           = re.search(r'FOUNDER_NAME:\s*(.+)', text)
        pain_m         = re.search(r'SPECIFIC_PAIN:\s*(.+)', text)
        subject_m      = re.search(r'SUBJECT:\s*(.+)', text)
        email_m        = re.search(r'EMAIL:\s*\n([\s\S]+)', text)

        result["founder_name"]  = fn_m.group(1).strip() if fn_m else ""
        result["specific_pain"] = pain_m.group(1).strip() if pain_m else ""
        result["subject"]       = subject_m.group(1).strip() if subject_m else ""
        result["email_body"]    = email_m.group(1).strip() if email_m else ""

        # Clean blank founder name
        if result["founder_name"].lower() in ("blank", "none", "unknown", "n/a", ""):
            result["founder_name"] = ""

        return result

    except Exception as e:
        print(f"[prospector] Claude analysis error: {e}", file=sys.stderr)
        return {}


_claude_cache: dict = {}  # cache per website to avoid double calls in same run


def _get_claude_analysis(business_name: str, website: str, page_text: str,
                         signal: str, signal_detail: str, biz_type: str,
                         tech_stack: list, founder_name: str) -> dict:
    """Run Claude analysis once per prospect, cache the result."""
    key = website or business_name
    if key not in _claude_cache:
        _claude_cache[key] = _claude_analyze_and_write(
            business_name=business_name, website=website, page_text=page_text,
            signal=signal, signal_detail=signal_detail, biz_type=biz_type,
            tech_stack=tech_stack, founder_name=founder_name,
        )
    return _claude_cache[key]


def build_email_body(business_name: str, website: str, biz_type: str,
                     tech_stack: list, observations: list,
                     signal: str = "website_gap",
                     signal_detail: str = "",
                     contact_name: str = "",
                     page_text: str = "",
                     founder_name: str = "") -> str:

    # Claude is the brain — it reads the website and writes the email
    analysis = _get_claude_analysis(
        business_name, website, page_text, signal, signal_detail,
        biz_type, tech_stack, founder_name or contact_name,
    )
    if analysis.get("email_body"):
        return analysis["email_body"]

    # Fallback (no API key or Claude error) — signal-aware static templates
    greeting = f"Hey {contact_name or founder_name}," if (contact_name or founder_name) else "Hey,"
    angle    = observations[0] if observations else "noticed something on your site"

    if signal == "funding_raised" and signal_detail:
        amount_m = re.search(r'\$[\d\.]+[MB]', signal_detail)
        amount   = amount_m.group(0) if amount_m else "recent round"
        return (
            f"{greeting}\n\nSaw {business_name} raised {amount}. "
            f"At that growth rate, manual ops become the first bottleneck. "
            f"I build automation systems for post-funding teams — onboarding flows, "
            f"reporting pipelines, CRM syncs. n8n or Make, 2-3 week build.\n\n"
            f"Worth a quick call?\n\nEmmanuel"
        ).strip()

    if signal == "product_launch":
        return (
            f"{greeting}\n\nSaw {business_name} launched recently. "
            f"The ops automation layer is cheapest to build now, before scale locks you in. "
            f"User onboarding sequences, Slack alerts, tool syncs. n8n, 2-3 weeks.\n\n"
            f"Worth a quick call?\n\nEmmanuel"
        ).strip()

    if biz_type == "agency":
        return (
            f"Hey,\n\n{angle}.\n\n"
            f"I build automated reporting for agencies — GA, Meta, ad platforms formatted "
            f"per client and emailed automatically, built in n8n. "
            f"Usually 15-20 hours/week recovered. 1-2 week build.\n\n"
            f"Worth a quick call?\n\nEmmanuel"
        ).strip()

    if biz_type == "startup":
        return (
            f"Hey,\n\n{angle}.\n\n"
            f"I build internal automation for early-stage teams — onboarding sequences, "
            f"Slack alerts, data syncs between tools. Usually n8n, 2-3 week project.\n\n"
            f"Worth a quick call?\n\nEmmanuel"
        ).strip()

    return (
        f"Hey,\n\n{angle}.\n\n"
        f"I do automation work — Klaviyo sequences, booking integrations, "
        f"reporting pipelines. Usually 1-2 weeks depending on scope.\n\n"
        f"Worth a quick call?\n\nEmmanuel"
    ).strip()


def build_subject(business_name: str, observations: list, biz_type: str,
                  signal: str = "website_gap", signal_detail: str = "",
                  page_text: str = "", tech_stack: list = None,
                  founder_name: str = "") -> str:
    # Claude writes the subject line too
    analysis = _get_claude_analysis(
        business_name, "", page_text, signal, signal_detail,
        biz_type, tech_stack or [], founder_name,
    )
    if analysis.get("subject"):
        return analysis["subject"]

    # Fallback subject lines
    if signal == "funding_raised":
        amount_m = re.search(r'\$[\d\.]+[MB]', signal_detail)
        amount   = amount_m.group(0) if amount_m else "raise"
        return f"Post-{amount} ops automation"

    if signal == "product_launch":
        return "Automation layer post-launch"

    if observations:
        obs = observations[0]
        if len(obs) < 55:
            return obs

    if biz_type == "agency":
        obs = observations[0] if observations else ""
        if "report" in obs.lower():
            return f"Reporting automation for {business_name}"
        if "crm" in obs.lower():
            return f"CRM setup for {business_name}"
        return "Agency ops gap"

    return f"Quick thing on {business_name}"


# ─── Prospect node creation ───────────────────────────────────────────────────

def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower().strip())[:40].strip("-")


def create_prospect_node(business: dict, email: str,
                         body: str, analysis: dict, niche: str = "") -> Path:
    PROSPECTS_DIR.mkdir(parents=True, exist_ok=True)

    name          = business.get("name", "")
    website       = business.get("website", "")
    phone         = business.get("formatted_phone_number", "")
    address       = business.get("formatted_address", "")
    source        = business.get("source", "maps")
    biz_type      = analysis.get("biz_type", "local")
    category      = business.get("category", niche)
    min_proj      = business.get("min_project", "")
    tagline       = business.get("tagline", "")
    batch         = business.get("batch", "")
    contact_name  = business.get("_contact_name", "")
    contact_role  = business.get("_contact_role", "")
    signal        = business.get("signal", "website_gap")
    signal_detail = business.get("signal_detail", "")

    slug = _slugify(name)
    path = PROSPECTS_DIR / f"{slug}.md"
    if path.exists():
        i = 2
        while path.exists():
            path = PROSPECTS_DIR / f"{slug}-{i}.md"
            i += 1

    obs_text  = "\n".join(f"- {o}" for o in analysis.get("observations", []))
    tech_text = ", ".join(analysis.get("tech_stack", [])) or "unknown"

    source_note = {
        "dr":  f"Found on DesignRush ({category} agencies).",
        "yc":  f"YC company ({batch}). Tagline: {tagline}",
        "maps": f"Found via Google Maps search.",
        "ph":  f"ProductHunt launch. {signal_detail}",
        "tc":  f"TechCrunch funding news. {signal_detail}",
    }.get(source, "Found via prospector.")

    contact_line = f"\nContact: {contact_name} ({contact_role})" if contact_name else ""

    content = f"""---
name: {contact_name or name}
company: {name}
role: {contact_role or ("Founder" if biz_type == "startup" else "Owner")}
email: {email}
phone: {phone}
website: {website}
address: {address}
category: {category}
biz_type: {biz_type}
niche: {niche}
source: {source}
signal: {signal}
status: prospect
outreach_sent_on:
platform: cold
sensitivity: private
---

## Context
{source_note}{contact_line}
Website: {website}
Tech stack: {tech_text}
Type: {biz_type}
Trigger: {signal_detail}

## Outreach Notes
{body}

## Site Observations
{obs_text if obs_text else "- No specific issues detected"}

## Conversation Log
{datetime.now().strftime("%Y-%m-%d")} — Prospect created via {source} prospector.
"""
    path.write_text(content, encoding="utf-8")
    return path


# ─── Main pipeline ────────────────────────────────────────────────────────────

def run_prospector(source: str = "maps", query: str = "", category: str = "",
                   industry: str = "", limit: int = 10, niche: str = "",
                   auto: bool = False, dry_run: bool = False) -> None:
    from scripts.notify import send as tg_send

    hunter_active = bool(HUNTER_KEY)
    print(f"\n[prospector] Source: {source} | Limit: {limit} | Auto: {auto} | Dry: {dry_run}")
    if hunter_active:
        print(f"[prospector] Hunter.io: enabled (decision-maker email finding active)")
    else:
        print(f"[prospector] Hunter.io: disabled (set HUNTER_API_KEY in config for better emails)")

    # Phase 1: Fetch businesses from the right source
    if source == "maps":
        if not query:
            print("[prospector] --query required for --source maps")
            return
        businesses = scrape_google_maps(query, limit=limit)
    elif source == "dr":
        if not category:
            print(f"[prospector] --category required. Options: {', '.join(DESIGNRUSH_CATEGORIES)}")
            return
        businesses = scrape_designrush(category, limit=limit)
    elif source == "yc":
        businesses = scrape_yc(industry=industry, limit=limit)
    elif source == "ph":
        businesses = scrape_producthunt(limit=limit)
    elif source == "tc":
        businesses = scrape_techcrunch_funding(limit=limit)
    else:
        print(f"[prospector] Unknown source: {source}. Use maps | dr | yc | ph | tc")
        return

    if not businesses:
        print("[prospector] No businesses found.")
        return

    print(f"\n[prospector] Analyzing {len(businesses)} prospects...")

    created, no_email, skipped = [], [], []

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[prospector] Playwright not installed.", file=sys.stderr)
        sys.exit(1)

    with sync_playwright() as pw:
        browser = _new_browser(pw)
        page    = _new_context(browser).new_page()

        for i, biz in enumerate(businesses, 1):
            name          = biz.get("name", "?")
            website       = biz.get("website", "")
            src           = biz.get("source", source)
            signal        = biz.get("signal", "website_gap")
            signal_detail = biz.get("signal_detail", "")
            print(f"  [{i}/{len(businesses)}] {name}")

            if not website:
                print(f"     No website — skipping")
                skipped.append(name)
                continue

            # Phase 2: Analyze website + extract email
            analysis = analyze_website_playwright(page, website, name, source=src)
            biz_type = analysis.get("biz_type", "local")

            # Phase 2b: Try Hunter.io for decision-maker email
            contact_name = ""
            contact_role = ""
            email        = ""

            if hunter_active:
                domain = re.sub(r'^https?://', '', website).split('/')[0]
                hunter = find_decision_maker_email(domain)
                if hunter:
                    email        = hunter.get("email", "")
                    contact_name = hunter.get("name", "")
                    contact_role = hunter.get("role", "")
                    conf         = hunter.get("confidence", 0)
                    print(f"     Hunter: {email} ({contact_role}, {conf}% confidence)")

            # Fall back to website-scraped email
            if not email:
                email = analysis.get("email", "")

            if not email:
                print(f"     No email ({biz_type}) — skipping")
                no_email.append(name)
                continue

            obs_count    = len(analysis["observations"])
            page_text    = analysis.get("page_text", "")
            founder_name = analysis.get("founder_name", "") or contact_name

            print(f"     Email: {email} | Type: {biz_type} | Issues: {obs_count} | Signal: {signal}")
            if founder_name:
                print(f"     Founder: {founder_name}")

            # Phase 3: Claude reads the website and writes the email
            body    = build_email_body(
                name, website, biz_type,
                analysis["tech_stack"], analysis["observations"],
                signal=signal, signal_detail=signal_detail,
                contact_name=founder_name,
                page_text=page_text,
                founder_name=founder_name,
            )
            subject = build_subject(
                name, analysis["observations"], biz_type,
                signal=signal, signal_detail=signal_detail,
                page_text=page_text,
                tech_stack=analysis["tech_stack"],
                founder_name=founder_name,
            )

            # Enrich the biz dict with contact info for the prospect node
            biz["_contact_name"] = founder_name
            biz["_contact_role"] = contact_role

            if dry_run:
                print(f"\n     [DRY RUN] Subject: {subject}")
                print(f"     Body preview: {body[:120]}...")
                created.append(name)
                continue

            # Phase 4: Create prospect node
            node_path = create_prospect_node(biz, email, body, analysis, niche or category or industry)
            print(f"     Node: {node_path.name}")
            created.append(name)

            # Phase 5: Auto-send
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

    sent_count = len(created) if auto else 0
    print(f"\n[prospector] Done.")
    print(f"  Sent:     {sent_count}")
    print(f"  Created:  {len(created)} nodes")
    print(f"  No email: {len(no_email)}")
    print(f"  Skipped:  {len(skipped)} (no website)")

    if not dry_run:
        source_label = {"maps": "Maps", "dr": f"DesignRush/{category}", "yc": f"YC/{industry}",
                        "ph": "ProductHunt", "tc": "TechCrunch Funding"}.get(source, source)
        tg_send(
            f"🎯 <b>Prospector [{source_label}]</b>\n\n"
            f"✅ {len(created)} {'sent' if auto else 'nodes created'}\n"
            f"❌ {len(no_email)} no email found\n"
            f"⏭ {len(skipped)} no website"
        )


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Upwork OS — Multi-Source Prospector")
    parser.add_argument("--source",   default="maps", choices=["maps","dr","yc","ph","tc"],
                        help="Prospecting source: maps | dr | yc | ph (ProductHunt) | tc (TechCrunch funding)")
    parser.add_argument("--query",    default="", help="[maps] Search query")
    parser.add_argument("--category", default="", help=f"[dr] Category: {', '.join(DESIGNRUSH_CATEGORIES)}")
    parser.add_argument("--industry", default="", help=f"[yc] Industry: {', '.join(YC_INDUSTRIES)}")
    parser.add_argument("--limit",    type=int, default=10, help="Max prospects (default: 10)")
    parser.add_argument("--niche",    default="", help="Niche tag for prospect node")
    parser.add_argument("--auto",     action="store_true", help="Auto-send emails immediately")
    parser.add_argument("--dry-run",  action="store_true", help="Preview only — nothing sent or saved")
    args = parser.parse_args()

    run_prospector(
        source   = args.source,
        query    = args.query,
        category = args.category,
        industry = args.industry,
        limit    = args.limit,
        niche    = args.niche,
        auto     = args.auto,
        dry_run  = args.dry_run,
    )


if __name__ == "__main__":
    main()
