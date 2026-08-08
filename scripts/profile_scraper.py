"""
profile_scraper.py -- Upwork freelancer profile scraper (clipboard edition).

Opens the profile in your real Chrome browser (bypasses Cloudflare), waits
for you to press Ctrl+A + Ctrl+C, then parses and structures the profile.

USAGE:
  python scripts/profile_scraper.py <profile-url>
  python scripts/profile_scraper.py https://www.upwork.com/freelancers/~011b48d2eabbfa6361

  # Compare multiple profiles side-by-side:
  python scripts/profile_scraper.py --compare <url1> <url2> <url3>

  # Analyze from already-saved JSON:
  python scripts/profile_scraper.py --analyze sources/profiles/2026-08-05-xxx.json
"""

import sys
import json
import re
import time
import webbrowser
import subprocess
from pathlib import Path
from datetime import datetime

# Chrome profile that has adekoyaemmanuel15@gmail.com (Upwork account) logged in
CHROME_PROFILE = "Profile 7"
CHROME_EXE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

ROOT = Path(__file__).parent.parent
SOURCES = ROOT / "sources" / "profiles"
SOURCES.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Clipboard capture
# ---------------------------------------------------------------------------

def capture_via_clipboard(url: str) -> str:
    """Open URL in real Chrome, watch clipboard for Ctrl+A + Ctrl+C."""
    try:
        import pyperclip
        old_clip = pyperclip.paste()
    except Exception:
        old_clip = ""
        pyperclip = None

    print()
    print("  +----------------------------------------------------------+")
    print("  |  Opening profile in Chrome. When it fully loads:        |")
    print("  |    1. Press Ctrl+A  (select all)                        |")
    print("  |    2. Press Ctrl+C  (copy)                              |")
    print("  |  Auto-detects -- no Enter needed.                       |")
    print("  +----------------------------------------------------------+")
    print()

    # Open in Chrome with the Upwork profile (adekoyaemmanuel15) directly
    chrome_path = Path(CHROME_EXE)
    if chrome_path.exists():
        subprocess.Popen([
            str(chrome_path),
            f"--profile-directory={CHROME_PROFILE}",
            url,
        ])
    else:
        webbrowser.open(url)
    time.sleep(4)

    if pyperclip is None:
        input("  Press Enter after Ctrl+A + Ctrl+C... ")
        try:
            import pyperclip as pc
            return pc.paste()
        except Exception:
            print("ERROR: pyperclip not installed. Run: pip install pyperclip")
            sys.exit(1)

    import pyperclip as pc
    print("  Watching clipboard...", end="", flush=True)
    for _ in range(120):
        time.sleep(1)
        current = pc.paste()
        if current != old_clip and len(current) > 300:
            print(f" got {len(current):,} chars.")
            return current
        sys.stdout.write(".")
        sys.stdout.flush()

    print()
    print("  Timeout -- no clipboard content detected after 2 minutes.")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Profile text parser
# ---------------------------------------------------------------------------

def parse_profile_text(text: str, url: str) -> dict:
    """
    Parse clipboard text from an Upwork profile page into structured data.
    Handles Upwork's actual clipboard structure (CRLF line endings, nav header, etc.)
    """
    profile = {
        "url": url,
        "scraped_at": datetime.now().isoformat(),
        "method": "clipboard",
        "raw_text_length": len(text),
        "raw_text_sample": text[:6000],
    }

    # Normalize line endings — CRLF → LF throughout
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    lines = [ln.strip() for ln in text.splitlines()]
    nonempty = [ln for ln in lines if ln]

    rate_pat = re.compile(r"\$[\d,]+(?:\.\d+)?(?:/hr|/hour)", re.IGNORECASE)
    jss_pat = re.compile(r"(\d{1,3})%\s*[Jj]ob\s*[Ss]uccess")
    top_rated_pat = re.compile(r"top.?rated", re.IGNORECASE)
    earned_pat = re.compile(r"\$([\d,.]+[KMB]?)\+?\s*\nTotal earnings", re.IGNORECASE | re.MULTILINE)

    # ── Badges + JSS + Rate (scan first 80 non-empty lines) ──────────────────
    rate, jss, total_earned = "", "", ""
    badges = []
    rate_line_idx = -1  # index in `nonempty` where rate appears

    for i, ln in enumerate(nonempty[:80]):
        if rate_pat.search(ln) and not rate:
            rate = rate_pat.search(ln).group(0)
            rate_line_idx = i
        m = jss_pat.search(ln)
        if m and not jss:
            jss = m.group(1) + "%"
        if top_rated_pat.search(ln):
            badges.append("Top Rated")

    m = earned_pat.search(text)
    if m:
        total_earned = "$" + m.group(1)

    # ── Name ─────────────────────────────────────────────────────────────────
    # Upwork structure: nav → "Account Settings" → "FirstName L." → stats
    # Look for the name right after "Account Settings" marker
    nav_skip = {"Account Settings", "Skip to content", "Upwork home", "Find work",
                "Deliver work", "Manage finances", "Messages", "Search", "Jobs",
                "Find Talent", "My Jobs", "Reports", "Help", "Log In", "Sign Up"}
    name = ""
    # Name pattern: "Brian W." or "Brian Wade" (first name + abbreviated or full last name)
    name_pat = re.compile(r"^[A-Z][a-zA-Z'-]+\.?(?:\s+[A-Z][a-zA-Z'-]*\.?){1,3}$")
    found_acct = False
    for ln in nonempty[:30]:
        if "Account Settings" in ln:
            found_acct = True
            continue
        if found_acct and name_pat.match(ln) and ln not in nav_skip and len(ln) > 2:
            # Skip obvious non-names
            if any(x in ln for x in ("Status", "Verified", "Top Rated", "Available")):
                continue
            name = ln
            break

    # ── Title ─────────────────────────────────────────────────────────────────
    # Title is the line containing | separators right before the rate line
    title = ""
    if rate_line_idx > 0:
        # Look backwards from rate line for the title (pipe-separated or long text)
        for ln in reversed(nonempty[max(0, rate_line_idx-10):rate_line_idx]):
            if "|" in ln and len(ln) > 10:
                title = ln
                break
            # Also catch single-line titles without pipes (long descriptive lines)
            if len(ln) > 30 and not any(x in ln for x in
                    ("$", "%", "hours", "jobs", "earnings", "http", "Status", "Offline",
                     "Verified", "Available", "English", "Language", "Education",
                     "Associated", "GitHub")):
                title = ln
                break

    # ── Overview ─────────────────────────────────────────────────────────────
    # Overview = text from after the rate line to "less" toggle OR "Work history"
    overview = ""
    if rate_line_idx >= 0:
        after_rate = "\n".join(nonempty[rate_line_idx+1:])
        # Find the start of the overview: first paragraph-like line
        ov_start = _find_in_text(after_rate, ["Hi, I", "I am ", "I'm ", "I specialize",
                                               "Welcome", "As a ", "With ", "My name"])
        if ov_start == -1:
            # Just take whatever's after the rate until Work history
            ov_start = 0
        ov_text = after_rate[ov_start:]
        # Cut at "less" (Upwork read-more toggle) or "Work history"
        for end_marker in ["less\n", "\nWork history\n", "\nWork History\n",
                           "\nInsights from", "\nCompleted jobs"]:
            pos = ov_text.find(end_marker)
            if pos != -1:
                ov_text = ov_text[:pos]
                break
        overview = ov_text.strip()[:3000]

    profile["name"] = name
    profile["title"] = title
    profile["rate"] = rate
    profile["jss"] = jss
    profile["total_earned"] = total_earned
    profile["badges"] = list(set(badges))
    profile["overview"] = overview

    # ── Skills ───────────────────────────────────────────────────────────────
    skills_block = _extract_section(
        text,
        start_markers=["Skills\n"],
        end_markers=["Portfolio\n", "Work History\n", "Employment history\n",
                     "Employment History\n", "Education\n", "Certifications\n",
                     "Other experiences\n", "Other Experiences\n"],
        max_chars=1500,
    )
    skills = []
    for ln in skills_block.splitlines():
        ln = ln.strip()
        if 2 <= len(ln) <= 60 and not ln.startswith("$") and "%" not in ln:
            parts = [p.strip() for p in ln.split(",")]
            skills.extend(p for p in parts if p and len(p) > 1)
    profile["skills"] = skills[:30]

    # ── Portfolio ─────────────────────────────────────────────────────────────
    portfolio_block = _extract_section(
        text,
        start_markers=["Portfolio\n"],
        end_markers=["Pagination\n", "Current page 1", "Skills\n",
                     "Employment history\n", "Employment History\n"],
        max_chars=2000,
    )
    profile["portfolio"] = _parse_portfolio_block(portfolio_block)

    # ── Work History ──────────────────────────────────────────────────────────
    work_block = _extract_section(
        text,
        start_markers=["Work history\n", "Work History\n"],
        end_markers=["Portfolio\n", "Skills\n", "Employment history\n",
                     "Education\n", "Certifications\n"],
        max_chars=1500,
    )
    profile["work_history_raw"] = work_block.strip()[:800]

    # ── Certifications ────────────────────────────────────────────────────────
    cert_block = _extract_section(
        text,
        start_markers=["Certifications\n"],
        end_markers=["Education\n", "Other experiences\n", "Skills\n",
                     "Work history\n", "Testimonials\n"],
        max_chars=800,
    )
    certs = [ln.strip() for ln in cert_block.splitlines() if 3 <= len(ln.strip()) <= 80]
    profile["certifications"] = certs[:10]

    # ── Education ─────────────────────────────────────────────────────────────
    edu_block = _extract_section(
        text,
        start_markers=["Education\n"],
        end_markers=["Certifications\n", "Other experiences\n", "Skills\n",
                     "Work history\n", "Testimonials\n", "Employment history\n"],
        max_chars=600,
    )
    profile["education_raw"] = edu_block.strip()

    # ── Keyword frequency ─────────────────────────────────────────────────────
    profile["keyword_counts"] = _count_keywords(text, [
        "n8n", "automation", "python", "ai", "workflow", "integration",
        "make.com", "zapier", "airtable", "notion", "shopify", "openai",
        "langchain", "api", "crm", "webhook", "javascript", "typescript",
    ])

    return profile


def _find_in_text(text: str, markers: list) -> int:
    """Return position of first matching marker, or -1."""
    lower = text.lower()
    best = -1
    for m in markers:
        pos = lower.find(m.lower())
        if pos != -1 and (best == -1 or pos < best):
            best = pos
    return best


def _extract_section(text: str, start_markers: list, end_markers: list, max_chars: int = 2000) -> str:
    """Extract a section of text between start and end markers."""
    lower = text.lower()
    start_pos = None

    for marker in start_markers:
        pos = lower.find(marker.lower())
        if pos != -1:
            start_pos = pos + len(marker)
            break

    if start_pos is None:
        return ""

    end_pos = start_pos + max_chars
    for marker in end_markers:
        pos = lower.find(marker.lower(), start_pos)
        if pos != -1 and pos < end_pos:
            end_pos = pos

    return text[start_pos:end_pos]


def _parse_portfolio_block(block: str) -> list:
    """Parse portfolio section into list of items.
    Upwork clipboard gives portfolio as a list of short title lines.
    """
    if not block.strip():
        return []

    skip_pat = re.compile(r"^(See all|Load more|View all|Pagination|go to page|\d+ items?|Current page)", re.IGNORECASE)
    items = []

    for ln in block.splitlines():
        ln = ln.strip()
        if not ln or len(ln) < 5:
            continue
        if skip_pat.match(ln):
            continue
        if len(ln) > 150:  # too long for a portfolio title
            continue
        items.append({"title": ln, "description": ""})

    return items[:12]


def _count_keywords(text: str, keywords: list) -> dict:
    """Count keyword frequency across the full profile text."""
    lower = text.lower()
    counts = {}
    for kw in keywords:
        pattern = re.compile(r"\b" + re.escape(kw.lower()) + r"\b")
        counts[kw] = len(pattern.findall(lower))
    return {k: v for k, v in sorted(counts.items(), key=lambda x: -x[1]) if v > 0}


# ---------------------------------------------------------------------------
# Output formatter
# ---------------------------------------------------------------------------

def format_profile(data: dict) -> str:
    """Human-readable profile analysis."""
    lines = []
    sep = "=" * 60
    lines.append(f"\n{sep}")
    lines.append(f"PROFILE: {data.get('name', '[name not found]')}")
    lines.append(f"URL: {data.get('url', '')}")
    lines.append(sep)

    lines.append(f"Title:   {data.get('title', '[not found]')}")
    lines.append(f"Rate:    {data.get('rate', '[not found]')}")
    lines.append(f"JSS:     {data.get('jss', '[not found]')}")
    lines.append(f"Earned:  {data.get('total_earned', '[not found]')}")

    badges = data.get("badges", [])
    if badges:
        lines.append(f"Badges:  {', '.join(badges)}")

    overview = data.get("overview", "")
    if overview:
        lines.append(f"\nOVERVIEW ({len(overview)} chars):")
        lines.append(overview[:600] + ("..." if len(overview) > 600 else ""))

    skills = data.get("skills", [])
    if skills:
        lines.append(f"\nSKILLS ({len(skills)}):")
        lines.append("  " + " | ".join(skills))

    portfolio = data.get("portfolio", [])
    if portfolio:
        lines.append(f"\nPORTFOLIO ({len(portfolio)} items):")
        for i, item in enumerate(portfolio[:6], 1):
            lines.append(f"  {i}. {item.get('title', '[untitled]')}")
            desc = item.get("description", "")
            if desc:
                lines.append(f"     {desc[:120]}")

    certs = data.get("certifications", [])
    if certs:
        lines.append(f"\nCERTIFICATIONS ({len(certs)}):")
        for c in certs:
            lines.append(f"  - {c}")

    kws = data.get("keyword_counts", {})
    if kws:
        lines.append(f"\nKEYWORD FREQUENCY (Ctrl+F check):")
        for kw, count in list(kws.items())[:12]:
            bar = "█" * min(count, 20)
            lines.append(f"  {kw:<20} {count:>3}x  {bar}")

    edu = data.get("education_raw", "")
    if edu:
        lines.append(f"\nEDUCATION:")
        lines.append(f"  {edu[:200]}")

    return "\n".join(lines)


def compare_profiles(profiles: list) -> str:
    """Side-by-side comparison of multiple profiles for competitor research."""
    lines = ["\n" + "=" * 70, "COMPETITOR ANALYSIS — PROFILE COMPARISON", "=" * 70]

    # Rate comparison
    lines.append("\nRATE COMPARISON:")
    for p in profiles:
        lines.append(f"  {p.get('name', 'Unknown'):<30} {p.get('rate', '[not found]')}")

    # JSS comparison
    lines.append("\nJSS COMPARISON:")
    for p in profiles:
        lines.append(f"  {p.get('name', 'Unknown'):<30} {p.get('jss', '[not found]')}")

    # Skills overlap analysis
    all_skills = {}
    for p in profiles:
        for s in p.get("skills", []):
            all_skills[s.lower()] = all_skills.get(s.lower(), 0) + 1
    common = [s for s, c in all_skills.items() if c > 1]
    unique_sets = {}
    for p in profiles:
        name = p.get("name", "Unknown")
        mine = {s.lower() for s in p.get("skills", [])}
        unique_sets[name] = mine - {s for s in common}

    lines.append(f"\nCOMMON SKILLS ({len(common)}):")
    lines.append("  " + " | ".join(common[:15]))

    for name, unique in unique_sets.items():
        if unique:
            lines.append(f"\nUNIQUE TO {name.upper()} ({len(unique)}):")
            lines.append("  " + " | ".join(list(unique)[:10]))

    # Portfolio count
    lines.append("\nPORTFOLIO COUNT:")
    for p in profiles:
        count = len(p.get("portfolio", []))
        bar = "▓" * count
        lines.append(f"  {p.get('name', 'Unknown'):<30} {count} items  {bar}")

    # Keyword saturation comparison
    lines.append("\nKEYWORD SATURATION (top keywords across all profiles):")
    all_kws = set()
    for p in profiles:
        all_kws.update(p.get("keyword_counts", {}).keys())
    for kw in sorted(all_kws):
        row = f"  {kw:<20}"
        for p in profiles:
            count = p.get("keyword_counts", {}).get(kw, 0)
            row += f"  {p.get('name', '?')[:12]:<12}: {count:>3}x"
        lines.append(row)

    # Title comparison
    lines.append("\nTITLES:")
    for p in profiles:
        lines.append(f"  {p.get('name', 'Unknown'):<30} {p.get('title', '[not found]')[:60]}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Save / load
# ---------------------------------------------------------------------------

def _slug(url: str) -> str:
    m = re.search(r"~([a-zA-Z0-9]+)", url)
    return m.group(1)[:14] if m else datetime.now().strftime("%H%M%S")


def save_profile(data: dict, slug: str) -> Path:
    date_str = datetime.now().strftime("%Y-%m-%d")
    out = SOURCES / f"{date_str}-{slug}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return out


def load_profile(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

    # Analyze from saved JSON
    if args[0] == "--analyze":
        if len(args) < 2:
            print("Usage: --analyze <path-to-json>")
            sys.exit(1)
        data = load_profile(args[1])
        print(format_profile(data))
        return

    # Compare mode
    if args[0] == "--compare":
        urls = [a for a in args[1:] if a.startswith("http")]
        if not urls:
            print("No URLs provided after --compare")
            sys.exit(1)
        profiles = []
        for url in urls:
            print(f"\n--- Profile {len(profiles)+1}/{len(urls)}: {url} ---")
            text = capture_via_clipboard(url)
            data = parse_profile_text(text, url)
            slug = _slug(url)
            path = save_profile(data, slug)
            print(format_profile(data))
            print(f"  Saved: {path}")
            profiles.append(data)
            if len(profiles) < len(urls):
                print(f"\n  Next profile opens in 5 seconds... (profile {len(profiles)+1}/{len(urls)})")
                time.sleep(5)
        if len(profiles) > 1:
            print(compare_profiles(profiles))
        return

    # Single profile
    url = args[0]
    if not url.startswith("http"):
        print(f"Expected a URL or --compare / --analyze flag. Got: {url}")
        sys.exit(1)

    slug = _slug(url)
    text = capture_via_clipboard(url)
    data = parse_profile_text(text, url)
    path = save_profile(data, slug)
    print(format_profile(data))
    print(f"\nSaved: {path}")


if __name__ == "__main__":
    main()
