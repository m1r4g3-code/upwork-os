#!/usr/bin/env python3
"""
quote.py -- Pricing calculator for Hephzibah Upwork OS

Two modes:
  Bid mode  -- Client posted a budget. Is it worth bidding? At what price?
  SOW mode  -- Post-discovery call. Generate tiered pricing + payment schedule.

Usage:
  python scripts/quote.py                          # interactive
  python scripts/quote.py --bid 1500 --type automation --complexity medium
  python scripts/quote.py --sow --type pipeline --complexity complex
  python scripts/quote.py --sow --hours 30 --tools "n8n:0.05,openai:0.02" --volume 200
"""

import argparse
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent.parent
OUTPUTS_DIR = ROOT / "outputs" / "strategy"

BASE_HOURLY = 75  # USD -- base rate for all calculations

COMPLEXITY_MULT = {
    "simple": 1.0,
    "medium": 1.6,
    "complex": 2.5,
    "enterprise": 4.0,
}

PROJECT_BASE_HOURS = {
    "integration": 8,    # Single API, webhook, basic connector
    "automation": 20,    # Multi-step workflow: n8n, Make, Zapier
    "pipeline": 40,      # Multi-system data pipeline with AI
    "agent": 35,         # Claude/GPT agent with tools and memory
    "fullstack": 60,     # Full-stack app or dashboard
    "scraper": 15,       # Data extraction + structured storage
    "crm": 25,           # CRM automation + flows + triggers
    "custom": 0,         # Manual hours input
}

TIER_MULT = {
    "core": 1.0,
    "full": 1.45,
    "premium": 1.95,
}

TIER_DESC = {
    "core": "Essential deliverables only. No extras or support.",
    "full": "Core + optimizations, full documentation, 1-week question support.",
    "premium": "Full + 30-day support, training walkthrough, one change order included.",
}


# --- Calculations -------------------------------------------------------------

def estimate_from_type(proj_type: str, complexity: str, manual_hours: float = 0) -> float:
    base = manual_hours if proj_type == "custom" else PROJECT_BASE_HOURS.get(proj_type, 20)
    mult = COMPLEXITY_MULT.get(complexity, 1.6)
    return base * mult * BASE_HOURLY


def build_tiers(base_estimate: float) -> dict:
    tiers = {}
    for key, mult in TIER_MULT.items():
        raw = base_estimate * mult
        # Round to nearest $50 for cleanliness
        tiers[key] = {
            "price": round(raw / 50) * 50,
            "label": key.capitalize(),
            "description": TIER_DESC[key],
        }
    return tiers


def payment_schedule(total: float) -> dict:
    return {
        "upfront":  round(total * 0.40),
        "midpoint": round(total * 0.30),
        "final":    round(total * 0.30),
        "total":    total,
    }


def assess_bid(client_budget: float, our_estimate: float) -> dict:
    if client_budget <= 0:
        return {"action": "NO_BUDGET", "note": "No budget posted -- bid at our estimate."}

    ratio = our_estimate / client_budget

    if ratio <= 0.9:
        action, note = "BID_AT_BUDGET", "Budget exceeds scope. Bid at budget or expand scope."
    elif ratio <= 1.1:
        action, note = "BID_AT_BUDGET", "Budget aligns with our estimate. Straightforward bid."
    elif ratio <= 1.5:
        action, note = "BID_ABOVE", "Budget is low. Bid above -- justify with a reframe in the proposal."
    elif ratio <= 2.5:
        action, note = "REFRAME_OR_SKIP", "Significant mismatch. Reframe deliverables or skip."
    else:
        action, note = "SKIP", "Budget signals commodity mindset. JSS risk. Skip."

    return {
        "client_budget": client_budget,
        "our_estimate":  our_estimate,
        "ratio":         round(ratio, 2),
        "action":        action,
        "note":          note,
    }


def calc_cost_per_run(tools: dict, volume: int) -> dict:
    total_per_run = sum(tools.values())
    return {
        "tools":       tools,
        "per_run":     round(total_per_run, 5),
        "monthly":     round(total_per_run * volume, 2),
        "volume":      volume,
    }


# --- Output formatters --------------------------------------------------------

def fmt_bid(rec: dict) -> str:
    lines = [
        "-" * 52,
        "  BID ASSESSMENT",
        "-" * 52,
        f"  Client budget:   ${rec.get('client_budget', 0):,.0f}",
        f"  Our estimate:    ${rec.get('our_estimate', 0):,.0f}",
        f"  Ratio:           {rec.get('ratio', '--')}x",
        f"  Action:          {rec['action']}",
        f"  Note:            {rec['note']}",
        "-" * 52,
    ]
    return "\n".join(lines)


def fmt_sow(tiers: dict, cost_run: dict = None, ongoing: dict = None,
            recommended: str = "full") -> str:
    lines = ["-" * 52, "  SOW PRICING TIERS", "-" * 52]

    for key, tier in tiers.items():
        s = payment_schedule(tier["price"])
        marker = " < recommended" if key == recommended else ""
        lines += [
            f"\n  [{tier['label']}]{marker}   ${tier['price']:,.0f}",
            f"  {tier['description']}",
            f"  Schedule:  ${s['upfront']:,} upfront  /  ${s['midpoint']:,} midpoint  /  ${s['final']:,} final",
        ]

    if cost_run:
        lines += ["", "-" * 52, "  COST PER RUN", "-" * 52]
        for tool, cost in cost_run["tools"].items():
            lines.append(f"  {tool:<28} ${cost:.5f}")
        lines += [
            "  " + "." * 48,
            f"  {'Per run':<28} ${cost_run['per_run']:.5f}",
            f"  {'At {v}/month'.format(v=cost_run['volume']):<28} ${cost_run['monthly']:,.2f}/mo",
        ]

    if ongoing:
        total_mo = sum(ongoing.values())
        lines += ["", "-" * 52, "  ONGOING PLATFORM COSTS", "-" * 52]
        for tool, cost in ongoing.items():
            lines.append(f"  {tool:<28} ${cost:.2f}/mo")
        lines += [
            "  " + "." * 48,
            f"  {'Total':<28} ${total_mo:.2f}/mo",
            "  (Tool subscriptions -- not fees to Emmanuel)",
        ]

    lines += ["", "-" * 52]
    return "\n".join(lines)


def sow_investment_block(tiers: dict, recommended: str = "full",
                          cost_run: dict = None, ongoing: dict = None) -> str:
    tier = tiers[recommended]
    s = payment_schedule(tier["price"])
    lines = [
        "* INVESTMENT",
        "",
        f"  [{tier['label']}]  {tier['description']}",
        "",
        f"  Upfront  (40%)   ${s['upfront']:,}  -- due to start",
        f"  Midpoint (30%)   ${s['midpoint']:,}  -- due at milestone",
        f"  Final    (30%)   ${s['final']:,}  -- due at delivery",
        "  " + "-" * 36,
        f"  Total            ${s['total']:,}",
        "",
        "  Other options:",
    ]
    for key, t in tiers.items():
        if key != recommended:
            lines.append(f"    {t['label']}: ${t['price']:,}  --  {t['description']}")
    return "\n".join(lines)


# --- Markdown output ----------------------------------------------------------

def build_markdown(project: str, bid_rec: dict = None, tiers: dict = None,
                   cost_run: dict = None, ongoing: dict = None,
                   recommended: str = "full") -> str:
    today = date.today().isoformat()
    lines = [
        f"# Quote -- {project}",
        f"**Date:** {today}  |  **Command:** python scripts/quote.py",
        f"**Status:** draft",
        "---",
        "",
    ]

    if bid_rec and bid_rec.get("action") != "NO_BUDGET":
        lines += [
            "## Bid Assessment",
            "",
            f"| Field | Value |",
            f"|---|---|",
            f"| Client budget | ${bid_rec.get('client_budget', 0):,.0f} |",
            f"| Our estimate | ${bid_rec.get('our_estimate', 0):,.0f} |",
            f"| Ratio | {bid_rec.get('ratio', '--')}x |",
            f"| **Action** | **{bid_rec['action']}** |",
            f"| Note | {bid_rec['note']} |",
            "",
        ]

    if tiers:
        lines += ["## Pricing Tiers", ""]
        for key, tier in tiers.items():
            s = payment_schedule(tier["price"])
            rec_flag = " *(recommended)*" if key == recommended else ""
            lines += [
                f"### {tier['label']}{rec_flag}  --  ${tier['price']:,}",
                f"{tier['description']}",
                f"- Upfront (40%): ${s['upfront']:,}",
                f"- Midpoint (30%): ${s['midpoint']:,}",
                f"- Final (30%): ${s['final']:,}",
                "",
            ]

    if cost_run:
        lines += ["## Cost Per Run", ""]
        for tool, cost in cost_run["tools"].items():
            lines.append(f"- {tool}: ${cost:.5f}")
        lines += [
            f"- **Per run total:** ${cost_run['per_run']:.5f}",
            f"- **At {cost_run['volume']} runs/month:** ${cost_run['monthly']:,.2f}/mo",
            "",
        ]

    if ongoing:
        lines += ["## Ongoing Platform Costs", ""]
        total = sum(ongoing.values())
        for tool, cost in ongoing.items():
            lines.append(f"- {tool}: ${cost:.2f}/mo")
        lines += [f"- **Total:** ${total:.2f}/mo", ""]

    if tiers:
        lines += ["## SOW Investment Block (copy-paste ready)", "", "```"]
        lines.append(sow_investment_block(tiers, recommended, cost_run, ongoing))
        lines += ["```", ""]

    return "\n".join(lines)


def save(content: str, slug: str) -> Path:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUTS_DIR / f"{date.today().isoformat()}-quote-{slug}.md"
    path.write_text(content, encoding="utf-8")
    return path


# --- Interactive mode ---------------------------------------------------------

def interactive():
    print("\n+====================================+")
    print("|   Hephzibah -- Quote Generator     |")
    print("+====================================+\n")

    project = input("Project name / slug: ").strip() or "project"

    print("\nMode:")
    print("  1  Bid check (client has posted a budget)")
    print("  2  SOW pricing (post-call, generate tiers)")
    print("  3  Both")
    mode = input("> ").strip()

    bid_rec = None
    tiers = None
    cost_run = None
    ongoing = None
    our_estimate = 0

    if mode in ("1", "3"):
        print("\n--- BID MODE ---")
        client_budget = float(input("Client's posted budget ($): ").strip() or "0")

        print(f"\nProject type: {list(PROJECT_BASE_HOURS.keys())}")
        proj_type = input("> ").strip() or "automation"
        hours = PROJECT_BASE_HOURS.get(proj_type, 0)
        if hours == 0:
            hours = float(input("Manual hours estimate: ").strip() or "20")

        print("Complexity: simple / medium / complex / enterprise")
        complexity = input("> ").strip() or "medium"
        our_estimate = estimate_from_type(proj_type, complexity, hours)

        bid_rec = assess_bid(client_budget, our_estimate)
        print("\n" + fmt_bid(bid_rec))

    if mode in ("2", "3"):
        print("\n--- SOW MODE ---")

        if not our_estimate:
            print(f"\nProject type: {list(PROJECT_BASE_HOURS.keys())}")
            proj_type = input("> ").strip() or "automation"
            hours = PROJECT_BASE_HOURS.get(proj_type, 0)
            if hours == 0:
                hours = float(input("Hours estimate: ").strip() or "20")
            print("Complexity: simple / medium / complex / enterprise")
            complexity = input("> ").strip() or "medium"
            our_estimate = estimate_from_type(proj_type, complexity, hours)

        tiers = build_tiers(our_estimate)

        is_auto = input("\nAutomation project with recurring output costs? [y/n]: ").strip().lower()
        if is_auto == "y":
            print("Enter tool costs as  name:cost_per_run  (empty line to finish)")
            tools = {}
            while True:
                entry = input("  > ").strip()
                if not entry:
                    break
                if ":" in entry:
                    k, v = entry.split(":", 1)
                    tools[k.strip()] = float(v.strip())
            volume = int(input("Expected runs per month: ").strip() or "100")
            cost_run = calc_cost_per_run(tools, volume)

        has_ongoing = input("\nClient needs ongoing tool subscriptions? [y/n]: ").strip().lower()
        if has_ongoing == "y":
            print("Enter ongoing costs as  tool:monthly_cost  (empty line to finish)")
            on = {}
            while True:
                entry = input("  > ").strip()
                if not entry:
                    break
                if ":" in entry:
                    k, v = entry.split(":", 1)
                    on[k.strip()] = float(v.strip())
            ongoing = on

        print("Recommended tier for SOW: core / full / premium")
        recommended = input("> ").strip() or "full"

        print("\n" + fmt_sow(tiers, cost_run, ongoing, recommended))
        print("\n--- SOW INVESTMENT BLOCK ---")
        print(sow_investment_block(tiers, recommended, cost_run, ongoing))

    md = build_markdown(project, bid_rec, tiers, cost_run, ongoing,
                         recommended if tiers else "full")
    out = save(md, project.lower().replace(" ", "-"))
    print(f"\n  Saved -> {out}\n")


# --- CLI mode -----------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(description="Hephzibah Quote Generator")
    p.add_argument("--bid", type=float, help="Client posted budget")
    p.add_argument("--sow", action="store_true", help="Generate SOW tiers")
    p.add_argument("--type", dest="proj_type", default="automation")
    p.add_argument("--complexity", default="medium",
                   choices=["simple", "medium", "complex", "enterprise"])
    p.add_argument("--hours", type=float, help="Manual hours override")
    p.add_argument("--tools", help="Tool costs: 'n8n:0.05,openai:0.02'")
    p.add_argument("--volume", type=int, default=100)
    p.add_argument("--ongoing", help="Ongoing costs: 'n8n:50,openai:20'")
    p.add_argument("--recommended", default="full",
                   choices=["core", "full", "premium"])
    p.add_argument("--slug", default="project")
    args = p.parse_args()

    if not any([args.bid, args.sow, args.hours]):
        interactive()
        return

    hours = args.hours or PROJECT_BASE_HOURS.get(args.proj_type, 20)
    our_estimate = estimate_from_type(args.proj_type, args.complexity, hours)

    bid_rec = assess_bid(args.bid, our_estimate) if args.bid else None
    if bid_rec:
        print(fmt_bid(bid_rec))

    tiers = build_tiers(our_estimate) if (args.sow or args.bid) else None

    cost_run = None
    if args.tools:
        tools = {}
        for item in args.tools.split(","):
            if ":" in item:
                k, v = item.split(":", 1)
                tools[k.strip()] = float(v.strip())
        cost_run = calc_cost_per_run(tools, args.volume)

    ongoing = None
    if args.ongoing:
        on = {}
        for item in args.ongoing.split(","):
            if ":" in item:
                k, v = item.split(":", 1)
                on[k.strip()] = float(v.strip())
        ongoing = on

    if tiers:
        print(fmt_sow(tiers, cost_run, ongoing, args.recommended))
        print("\n--- SOW INVESTMENT BLOCK ---")
        print(sow_investment_block(tiers, args.recommended, cost_run, ongoing))

    md = build_markdown(args.slug, bid_rec, tiers, cost_run, ongoing, args.recommended)
    out = save(md, args.slug)
    print(f"\n  Saved -> {out}\n")


if __name__ == "__main__":
    main()
