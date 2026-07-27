#!/usr/bin/env python3
"""
Upwork OS — Multi-Source Prospector (Playwright)

Sources:
  --source maps   Google Maps local businesses (quick wins, email extraction)
  --source dr     DesignRush agency directory (verified US agencies, high-budget)
  --source yc     Y Combinator company directory (funded US startups)

No API keys needed. Playwright controls the browser autonomously.

Usage:
    python scripts/prospector.py --source dr --category social-media --limit 15 --auto
    python scripts/prospector.py --source dr --category video --limit 10 --dry-run
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
        return {"tech_stack": [], "observations": [], "angle": "", "email": "", "biz_type": "local"}

    if not website.startswith("http"):
        website = "https://" + website

    try:
        page.goto(website, wait_until="domcontentloaded", timeout=15000)
        page.wait_for_timeout(1500)
    except Exception:
        return {"tech_stack": [], "observations": [], "angle": "", "email": "", "biz_type": "local"}

    html_text  = page.content()
    html_lower = html_text.lower()

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

    if not emails:
        base = website.rstrip("/")
        for path in ["/contact", "/contact-us", "/about", "/team", "/contact.html"]:
            try:
                page.goto(base + path, wait_until="domcontentloaded", timeout=10000)
                page.wait_for_timeout(800)
                emails = _extract_emails_from_content(page.content())
                if emails:
                    break
            except Exception:
                pass

    angle = observations[0] if observations else f"noticed something on {business_name}"

    return {
        "tech_stack":   tech_stack,
        "observations": observations,
        "angle":        angle,
        "email":        emails[0] if emails else "",
        "biz_type":     biz_type,
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


# ─── Email personalization ────────────────────────────────────────────────────

def _ai_write_email(business_name: str, website: str, biz_type: str,
                    tech_stack: list, observations: list) -> str:
    if not AI_KEY:
        return ""

    type_context = {
        "agency":    "a content/social media/digital marketing agency in the US",
        "startup":   "a funded US startup",
        "ecommerce": "an e-commerce brand (Shopify or similar)",
        "local":     "a local business",
    }.get(biz_type, "a business")

    obs_text  = "\n".join(f"- {o}" for o in observations[:3]) or "- No specific issues identified"
    tech_text = ", ".join(tech_stack) or "unclear"

    deliverable_hint = {
        "agency":    "automated client reporting (Google Analytics, Meta Ads, etc. formatted and emailed per client), content scheduling pipelines, or approval workflow automation built in n8n or Zapier",
        "startup":   "internal automation (user onboarding sequences, Slack alerts, data syncs between tools) built in n8n — typically a 2-3 week build",
        "ecommerce": "Shopify conversion stack: live chat (Tidio or Gorgias), Klaviyo abandoned cart sequences, automated review requests — usually 1-week setup",
        "local":     "website upgrades or automation: live chat, online booking, email follow-up sequences — specific tools, not vague 'fixes'",
    }.get(biz_type, "automation workflows or web development using specific tools (n8n, Zapier, Klaviyo, Shopify)")

    prompt = (
        f"Write a cold outreach email from Emmanuel (automation & web specialist) "
        f"to the owner/founder of {business_name} — {type_context}.\n\n"
        f"Website: {website}\nTech: {tech_text}\nObservations:\n{obs_text}\n\n"
        f"What Emmanuel actually builds (use this to describe the solution specifically):\n{deliverable_hint}\n\n"
        f"Rules:\n"
        f"- 80-110 words max\n"
        f"- Open with THEIR specific situation (use the observation above), not 'I'\n"
        f"- Name a SPECIFIC tool or deliverable in the solution line (n8n, Klaviyo, Zapier, live chat, etc.)\n"
        f"- Include a rough timeline (1 week, 2 weeks, 1-2 week build)\n"
        f"- One clear, low-friction ask (quick call or just reply)\n"
        f"- Direct, slightly senior — sounds like a peer, not a vendor\n"
        f"- No 'passionate about', 'leverage', 'synergy', 'delighted', 'streamlined', 'fix the gaps'\n"
        f"- No em dashes. Short sentences.\n"
        f"- Sign off: Emmanuel\n"
        f"- Body only, no subject line\n"
        f"- The prospect must understand exactly what they're buying after reading this"
    )

    try:
        payload = json.dumps({
            "model":    "claude-haiku-4-5-20251001",
            "max_tokens": 350,
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


def build_email_body(business_name: str, website: str, biz_type: str,
                     tech_stack: list, observations: list) -> str:
    ai = _ai_write_email(business_name, website, biz_type, tech_stack, observations)
    if ai:
        return ai

    angle     = observations[0] if observations else "noticed something on your site worth flagging"
    tech_note = tech_stack[0] if tech_stack else ""

    # Type-specific fallback templates — specific tools, specific deliverables
    if biz_type == "agency":
        return (
            f"Hey,\n\n"
            f"{angle}.\n\n"
            f"I build automated reporting systems for agencies — data from GA, Meta, and your "
            f"ad platforms formatted per client and emailed out automatically, built in n8n. "
            f"Agencies usually recover 15-20 hours/week from manual reporting alone.\n\n"
            f"Usually a 1-2 week build. Worth a quick call?\n\n"
            f"Emmanuel"
        ).strip()

    if biz_type == "startup":
        return (
            f"Hey,\n\n"
            f"{angle}.\n\n"
            f"I build internal automation for early-stage teams — new user onboarding sequences, "
            f"Slack alerts, tool-to-tool data syncs, things that are manual now and break at scale. "
            f"Usually n8n or Zapier, 2-3 week project.\n\n"
            f"Worth a quick call?\n\n"
            f"Emmanuel"
        ).strip()

    if tech_note == "Shopify" or biz_type == "ecommerce":
        return (
            f"Hey,\n\n"
            f"{angle}.\n\n"
            f"I set up the conversion stack for Shopify stores — live chat (Tidio or Gorgias), "
            f"Klaviyo abandoned cart sequences, and automated review requests. "
            f"Most stores see a measurable lift in the first 30 days.\n\n"
            f"Usually a 1-week setup. Worth a quick call?\n\n"
            f"Emmanuel"
        ).strip()

    return (
        f"Hey,\n\n"
        f"{angle}.\n\n"
        f"I do web and automation work — Shopify builds, Klaviyo email sequences, "
        f"booking system integrations, that kind of thing. Usually 1-2 weeks depending on scope.\n\n"
        f"Worth a quick call?\n\n"
        f"Emmanuel"
    ).strip()


def build_subject(business_name: str, observations: list, biz_type: str) -> str:
    if observations:
        obs = observations[0]
        if len(obs) < 55:
            return obs

    if biz_type == "agency":
        # Short specific subjects for agencies
        obs = observations[0] if observations else ""
        if "report" in obs.lower():
            return f"Automated client reporting for {business_name}"
        if "portal" in obs.lower():
            return f"Client portal gap — {business_name}"
        if "schedul" in obs.lower():
            return f"Content scheduling at {business_name}"
        if "crm" in obs.lower():
            return f"CRM setup for {business_name}"
        return f"Agency ops angle — {business_name}"

    if biz_type == "startup":
        return f"Automation layer for {business_name}"

    return f"Quick thing on {business_name}"


# ─── Prospect node creation ───────────────────────────────────────────────────

def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower().strip())[:40].strip("-")


def create_prospect_node(business: dict, email: str,
                         body: str, analysis: dict, niche: str = "") -> Path:
    PROSPECTS_DIR.mkdir(parents=True, exist_ok=True)

    name     = business.get("name", "")
    website  = business.get("website", "")
    phone    = business.get("formatted_phone_number", "")
    address  = business.get("formatted_address", "")
    source   = business.get("source", "maps")
    biz_type = analysis.get("biz_type", "local")
    category = business.get("category", niche)
    min_proj = business.get("min_project", "")
    tagline  = business.get("tagline", "")
    batch    = business.get("batch", "")

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
        "dr":    f"Found on DesignRush ({category} agencies).",
        "yc":    f"YC company ({batch}). Tagline: {tagline}",
        "maps":  f"Found via Google Maps search.",
    }.get(source, "Found via prospector.")

    content = f"""---
name: {name}
company: {name}
role: {"Founder" if biz_type == "startup" else "Owner"}
email: {email}
phone: {phone}
website: {website}
address: {address}
category: {category}
biz_type: {biz_type}
niche: {niche}
source: {source}
status: prospect
outreach_sent_on:
platform: cold
sensitivity: private
---

## Context
{source_note}
Website: {website}
Tech stack: {tech_text}
Type: {biz_type}

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

    print(f"\n[prospector] Source: {source} | Limit: {limit} | Auto: {auto} | Dry: {dry_run}")

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
    else:
        print(f"[prospector] Unknown source: {source}. Use maps | dr | yc")
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
            name    = biz.get("name", "?")
            website = biz.get("website", "")
            src     = biz.get("source", source)
            print(f"  [{i}/{len(businesses)}] {name}")

            if not website:
                print(f"     No website — skipping")
                skipped.append(name)
                continue

            # Phase 2: Analyze website + extract email
            analysis = analyze_website_playwright(page, website, name, source=src)
            email    = analysis.get("email", "")
            biz_type = analysis.get("biz_type", "local")

            if not email:
                print(f"     No email ({biz_type}) — skipping")
                no_email.append(name)
                continue

            obs_count = len(analysis["observations"])
            print(f"     Email: {email} | Type: {biz_type} | Issues: {obs_count}")

            # Phase 3: Write email
            body    = build_email_body(name, website, biz_type, analysis["tech_stack"], analysis["observations"])
            subject = build_subject(name, analysis["observations"], biz_type)

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
        source_label = {"maps": "Maps", "dr": f"DesignRush/{category}", "yc": f"YC/{industry}"}.get(source, source)
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
    parser.add_argument("--source",   default="maps", choices=["maps","dr","yc"],
                        help="Prospecting source: maps | dr (DesignRush agencies) | yc (default: maps)")
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
