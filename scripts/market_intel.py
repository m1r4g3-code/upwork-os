#!/usr/bin/env python3
"""
market_intel.py -- Multi-source market intelligence for the Upwork OS.

Zero API keys required for basic use.
Optional: add GITHUB_TOKEN = "..." to config.py for 5000 req/hr vs 60/hr.

Usage:
  python scripts/market_intel.py trends "voice AI agent" "n8n automation"
  python scripts/market_intel.py hn "AI automation"
  python scripts/market_intel.py github "python AI agents"
  python scripts/market_intel.py pulse "voice AI agent"
  python scripts/market_intel.py niche "AI automation"

Commands:
  trends   Google Trends: interest over time, direction, related queries, regions
  hn       Hacker News: how much engineers are discussing this topic
  github   GitHub: how many repos are being built around it
  pulse    All three sources combined for one keyword (fast snapshot)
  niche    Full niche intelligence report saved to outputs/intel/
"""

import argparse
import sys
import time
import warnings
from datetime import datetime, timedelta
from pathlib import Path

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*urllib3.*")
warnings.filterwarnings("ignore", message=".*RequestsDependencyWarning.*")

import requests

# pytrends 4.9.2 uses urllib3's removed 'method_whitelist' kwarg.
# Patch Retry.__init__ to map it to 'allowed_methods' before pytrends loads.
try:
    from urllib3.util.retry import Retry as _Retry
    _orig_retry_init = _Retry.__init__
    def _patched_retry_init(self, *args, **kwargs):
        if "method_whitelist" in kwargs:
            kwargs["allowed_methods"] = kwargs.pop("method_whitelist")
        _orig_retry_init(self, *args, **kwargs)
    _Retry.__init__ = _patched_retry_init
except Exception:
    pass

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from config import ROOT as CONFIG_ROOT  # noqa: F401 -- validates import works

TODAY = datetime.now().strftime("%Y-%m-%d")
OUTPUT_INTEL = ROOT / "outputs" / "intel"
OUTPUT_INTEL.mkdir(parents=True, exist_ok=True)


# ── Google Trends ─────────────────────────────────────────────────────────────

def fetch_trends(keywords: list, timeframe: str = "today 12-m") -> dict:
    try:
        from pytrends.request import TrendReq
    except ImportError:
        return {"error": "pytrends not installed. Run: pip install pytrends"}

    keywords = [k for k in keywords if k][:5]
    if not keywords:
        return {"error": "No keywords provided"}

    try:
        pt = TrendReq(hl="en-US", tz=0, timeout=(10, 30), retries=2, backoff_factor=1.0)
        pt.build_payload(keywords, timeframe=timeframe, geo="")

        df_time = pt.interest_over_time()
        time.sleep(1)
        related = pt.related_queries()
        time.sleep(1)
        regional = pt.interest_by_region(resolution="COUNTRY", inc_low_vol=False)

        result = {
            "keywords": keywords,
            "timeframe": timeframe,
            "current_score": {},
            "trend_direction": {},
            "six_month_change": {},
            "related_rising": {},
            "top_countries": {},
        }

        if not df_time.empty:
            for kw in keywords:
                if kw not in df_time.columns:
                    continue
                series = df_time[kw].tolist()

                # Current score: average of last 4 data points
                recent = series[-4:] if len(series) >= 4 else series
                current = round(sum(recent) / len(recent))

                # 6-month-ago score
                mid = max(0, len(series) - 26)
                past_slice = series[mid: mid + 4] if len(series) > 26 else series[:4]
                past = round(sum(past_slice) / len(past_slice)) if past_slice else 0

                delta = current - past
                if delta >= 15:
                    direction = "RISING"
                elif delta <= -15:
                    direction = "FALLING"
                else:
                    direction = "STABLE"

                result["current_score"][kw] = current
                result["trend_direction"][kw] = direction
                result["six_month_change"][kw] = delta

        for kw in keywords:
            if kw in related and related[kw] and related[kw].get("rising") is not None:
                df_rising = related[kw]["rising"]
                if df_rising is not None and not df_rising.empty:
                    result["related_rising"][kw] = df_rising["query"].head(5).tolist()

        if not regional.empty:
            for kw in keywords:
                if kw in regional.columns:
                    top = regional[kw].nlargest(5)
                    result["top_countries"][kw] = {
                        str(k): int(v) for k, v in top.items() if v > 0
                    }

        return result

    except Exception as exc:
        msg = str(exc)
        if "429" in msg or "too many" in msg.lower():
            return {"error": "Rate limited by Google Trends. Wait 60 seconds and retry."}
        return {"error": f"Google Trends: {msg[:120]}"}


# ── Hacker News ───────────────────────────────────────────────────────────────

def fetch_hn(keyword: str, days_back: int = 90, limit: int = 10) -> dict:
    cutoff = int((datetime.now() - timedelta(days=days_back)).timestamp())
    try:
        r = requests.get(
            "https://hn.algolia.com/api/v1/search",
            params={
                "query": keyword,
                "tags": "story",
                "numericFilters": f"created_at_i>{cutoff}",
                "hitsPerPage": limit,
            },
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()

        hits = data.get("hits", [])
        stories = sorted(
            [
                {
                    "title": h.get("title", ""),
                    "points": h.get("points", 0) or 0,
                    "comments": h.get("num_comments", 0) or 0,
                    "hn_url": f"https://news.ycombinator.com/item?id={h.get('objectID', '')}",
                    "date": (h.get("created_at") or "")[:10],
                }
                for h in hits
            ],
            key=lambda x: x["points"] + x["comments"],
            reverse=True,
        )

        total = sum(s["points"] + s["comments"] for s in stories)
        count = data.get("nbHits", 0)

        return {
            "keyword": keyword,
            "period_days": days_back,
            "story_count": count,
            "top_stories": stories[:5],
            "total_engagement": total,
            "signal": "HIGH" if count > 20 else ("MEDIUM" if count > 5 else "LOW"),
        }

    except Exception as exc:
        return {"error": f"HN: {exc}"}


# ── GitHub ────────────────────────────────────────────────────────────────────

def fetch_github(keyword: str, days_back: int = 30, limit: int = 8) -> dict:
    try:
        try:
            from config import GITHUB_TOKEN
            headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}
        except (ImportError, AttributeError):
            headers = {"Accept": "application/vnd.github+json"}

        cutoff = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        r = requests.get(
            "https://api.github.com/search/repositories",
            params={
                "q": f"{keyword} created:>{cutoff}",
                "sort": "stars",
                "order": "desc",
                "per_page": limit,
            },
            headers=headers,
            timeout=12,
        )

        if r.status_code == 403:
            return {"error": "GitHub rate limit. Add GITHUB_TOKEN to config.py for 5000 req/hr."}
        r.raise_for_status()
        data = r.json()

        repos = [
            {
                "name": item.get("full_name", ""),
                "description": (item.get("description") or "")[:120],
                "stars": item.get("stargazers_count", 0),
                "language": item.get("language") or "unknown",
                "url": item.get("html_url", ""),
                "created": (item.get("created_at") or "")[:10],
            }
            for item in data.get("items", [])
        ]

        count = data.get("total_count", 0)
        return {
            "keyword": keyword,
            "period_days": days_back,
            "total_repos_found": count,
            "top_repos": repos,
            "total_stars": sum(r["stars"] for r in repos),
            "signal": "HIGH" if count > 100 else ("MEDIUM" if count > 20 else "LOW"),
        }

    except Exception as exc:
        return {"error": f"GitHub: {exc}"}


# ── Pulse (all sources, one keyword) ─────────────────────────────────────────

def pulse(keyword: str) -> dict:
    print(f"\nPulling market pulse for: {keyword}")
    print("  Google Trends...", end=" ", flush=True)
    trends = fetch_trends([keyword])
    print("done")
    print("  Hacker News...", end=" ", flush=True)
    hn = fetch_hn(keyword, days_back=90)
    print("done")
    print("  GitHub...", end=" ", flush=True)
    gh = fetch_github(keyword, days_back=30)
    print("done\n")
    return {"keyword": keyword, "timestamp": TODAY, "trends": trends, "hacker_news": hn, "github": gh}


# ── Niche Report ──────────────────────────────────────────────────────────────

def niche_report(niche: str) -> str:
    # Use niche as-is for HN/GitHub; build one clean related variant for Trends
    niche_lower = niche.lower()
    if "ai" in niche_lower and "automation" in niche_lower:
        variants = [niche]  # already specific enough, no duplication
    elif "ai" in niche_lower:
        variants = [niche, f"{niche} automation"]
    elif "automation" in niche_lower:
        variants = [niche, f"AI {niche}"]
    else:
        variants = [niche, f"AI {niche}", f"{niche} automation"]

    print(f"\nNICHE INTELLIGENCE: {niche}")
    print("=" * 55)

    print("Google Trends...", end=" ", flush=True)
    trends = fetch_trends(variants[:3])
    print("done")
    time.sleep(2)

    print("Hacker News...", end=" ", flush=True)
    hn = fetch_hn(niche, days_back=180)
    print("done")

    print("GitHub...", end=" ", flush=True)
    gh = fetch_github(f"AI {niche}", days_back=60)
    print("done\n")

    lines = [
        f"# Niche Intelligence: {niche}",
        f"**Date:** {TODAY}",
        f"**Source:** market_intel.py",
        "",
        "---",
        "",
        "## Google Trends",
    ]

    if "error" not in trends:
        for kw in variants[:3]:
            score = trends.get("current_score", {}).get(kw, "N/A")
            direction = trends.get("trend_direction", {}).get(kw, "N/A")
            delta = trends.get("six_month_change", {}).get(kw, "N/A")
            arrow = "RISING" if direction == "RISING" else ("FALLING" if direction == "FALLING" else "STABLE")
            lines.append(f"- **{kw}:** score {score}/100, trend {arrow} (6-month change: {delta:+d})" if isinstance(delta, int) else f"- **{kw}:** score {score}/100, trend {arrow}")

        rising = trends.get("related_rising", {}).get(niche, [])
        if rising:
            lines.append(f"\nRising related searches: {', '.join(rising)}")

        countries = trends.get("top_countries", {}).get(niche, {})
        if countries:
            top = list(countries.items())[:3]
            lines.append(f"Top regions: {', '.join(f'{c} ({s})' for c, s in top)}")
    else:
        lines.append(f"Error: {trends['error']}")

    lines += ["", "## Hacker News (last 180 days)"]
    if "error" not in hn:
        lines.append(f"- Stories: {hn.get('story_count', 0)} | Engagement: {hn.get('total_engagement', 0)} | Signal: **{hn.get('signal', 'N/A')}**")
        for story in hn.get("top_stories", [])[:3]:
            lines.append(f"  - [{story['title']}]({story['hn_url']}) -- {story['points']} pts ({story['date']})")
    else:
        lines.append(f"Error: {hn['error']}")

    lines += ["", "## GitHub (repos created last 60 days)"]
    if "error" not in gh:
        lines.append(f"- New repos: {gh.get('total_repos_found', 0)} | Signal: **{gh.get('signal', 'N/A')}**")
        for repo in gh.get("top_repos", [])[:3]:
            lines.append(f"  - [{repo['name']}]({repo['url']}) -- {repo['stars']} stars ({repo['language']})")
            if repo["description"]:
                lines.append(f"    {repo['description']}")
    else:
        lines.append(f"Error: {gh['error']}")

    # Verdict
    t_dir = trends.get("trend_direction", {}).get(niche, "") if "error" not in trends else ""
    hn_sig = hn.get("signal", "") if "error" not in hn else ""
    gh_sig = gh.get("signal", "") if "error" not in gh else ""

    score = (
        (2 if t_dir == "RISING" else 1 if t_dir == "STABLE" else 0) +
        (2 if hn_sig == "HIGH" else 1 if hn_sig == "MEDIUM" else 0) +
        (2 if gh_sig == "HIGH" else 1 if gh_sig == "MEDIUM" else 0)
    )

    verdict = (
        "STRONG -- High demand, active community, growing developer activity."
        if score >= 5 else
        "MODERATE -- Established niche, steady interest."
        if score >= 3 else
        "WEAK -- Low signal. Consider adjacent niches."
    )

    lines += [
        "",
        "## Verdict",
        f"**Signal score: {score}/6**",
        f"**Assessment:** {verdict}",
        "",
        "---",
    ]

    report = "\n".join(lines)

    slug = niche.lower().replace(" ", "-")
    out = OUTPUT_INTEL / f"{TODAY}-niche-{slug}.md"
    out.write_text(report, encoding="utf-8")

    print(report)
    print(f"\nSaved: {out}")
    return report


# ── Print helpers ─────────────────────────────────────────────────────────────

def _print_trends(data: dict):
    if "error" in data:
        print(f"  Google Trends ERROR: {data['error']}\n")
        return
    print("GOOGLE TRENDS")
    print("-" * 45)
    for kw in data.get("keywords", []):
        score = data.get("current_score", {}).get(kw, "N/A")
        direction = data.get("trend_direction", {}).get(kw, "UNKNOWN")
        delta = data.get("six_month_change", {}).get(kw)
        delta_str = f"  ({delta:+d} vs 6mo ago)" if isinstance(delta, int) else ""
        arrow = "UP" if direction == "RISING" else ("DOWN" if direction == "FALLING" else "--")
        print(f"  [{arrow}] {kw}: {score}/100{delta_str}")
        rising = data.get("related_rising", {}).get(kw, [])
        if rising:
            print(f"       Rising: {', '.join(rising[:3])}")
        countries = data.get("top_countries", {}).get(kw, {})
        if countries:
            print(f"       Top region: {list(countries.keys())[0]}")
    print()


def _print_hn(data: dict):
    if "error" in data:
        print(f"  HN ERROR: {data['error']}\n")
        return
    print("HACKER NEWS (90 days)")
    print("-" * 45)
    print(f"  Stories: {data.get('story_count', 0)}  |  Engagement: {data.get('total_engagement', 0)}  |  Signal: {data.get('signal', 'N/A')}")
    for s in data.get("top_stories", [])[:3]:
        title = s["title"][:55] + "..." if len(s["title"]) > 55 else s["title"]
        print(f"  [{s['points']}pts] {title}")
    print()


def _print_github(data: dict):
    if "error" in data:
        print(f"  GitHub ERROR: {data['error']}\n")
        return
    print("GITHUB (30 days)")
    print("-" * 45)
    print(f"  New repos: {data.get('total_repos_found', 0)}  |  Signal: {data.get('signal', 'N/A')}")
    for r in data.get("top_repos", [])[:3]:
        print(f"  [{r['stars']} stars] {r['name']} ({r['language']})")
    print()


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Market intelligence: Google Trends, Hacker News, GitHub",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="cmd")

    p = sub.add_parser("trends", help="Google Trends comparison (up to 5 keywords)")
    p.add_argument("keywords", nargs="+")
    p.add_argument("--timeframe", default="today 12-m")

    p = sub.add_parser("hn", help="Hacker News signal for a keyword")
    p.add_argument("keyword")
    p.add_argument("--days", type=int, default=90)

    p = sub.add_parser("github", help="GitHub repo activity for a keyword")
    p.add_argument("keyword")
    p.add_argument("--days", type=int, default=30)

    p = sub.add_parser("pulse", help="All sources combined for one keyword")
    p.add_argument("keyword")

    p = sub.add_parser("niche", help="Full niche report saved to outputs/intel/")
    p.add_argument("niche")

    args = parser.parse_args()

    if args.cmd == "trends":
        _print_trends(fetch_trends(args.keywords, args.timeframe))

    elif args.cmd == "hn":
        _print_hn(fetch_hn(args.keyword, args.days))

    elif args.cmd == "github":
        _print_github(fetch_github(args.keyword, args.days))

    elif args.cmd == "pulse":
        data = pulse(args.keyword)
        _print_trends(data["trends"])
        _print_hn(data["hacker_news"])
        _print_github(data["github"])

    elif args.cmd == "niche":
        niche_report(args.niche)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
