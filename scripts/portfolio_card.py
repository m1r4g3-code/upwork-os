"""
portfolio_card.py — Generic Hephzibah Portfolio Card Generator

Renders a 1280x720 portfolio card: branded text panel left,
screenshot inside a wide rounded frame right.
2x device scale = 2560x1440 crisp PNG.

Works for any project — n8n workflows, full-stack apps, admin systems, pipelines.

Usage:
  python scripts/portfolio_card.py \\
    --screenshot outputs/assets/yct-admin-full-view.png \\
    --project "YCT Admin System" \\
    --label "Full-Stack Development" \\
    --headline "Timetables.\\nAutomated." \\
    --stats "3 Schools,500 Students,0 Scheduling Conflicts" \\
    --tools "Next.js,Supabase,TypeScript,Tailwind" \\
    --out outputs/portfolio/yct-card.png

Required:
  --screenshot PATH   Path to workflow or app screenshot
  --project TEXT      Project name (shows in frame bar + eyebrow)
  --headline TEXT     Bold headline. Use \\n for line breaks.
  --out PATH          Output PNG path

Optional:
  --label TEXT        Eyebrow category (defaults to --project value)
  --stats TEXT        Up to 3 stats, comma-separated: "7 Videos/Week,4 Workflows,0 Manual Steps"
  --tools TEXT        Comma-separated tool names
  --fit               Screenshot fit: contain (default, shows full image) or cover (fills frame)
"""

import argparse
import asyncio
import base64
import os
import sys
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("ERROR: playwright not installed. Run: pip install playwright && playwright install chromium")
    sys.exit(1)

W, H = 1280, 720

FONTS_URL = (
    "https://fonts.googleapis.com/css2?"
    "family=Poppins:wght@300;400;700;800;900&"
    "family=Inter:wght@300;400;500&"
    "family=JetBrains+Mono:wght@400;500;600&"
    "display=swap"
)

BG    = "#080808"
LEMON = "#E8FF3A"
WHITE = "#F0F0F0"
DIM   = "#686868"


def b64(path: str) -> str:
    p = Path(path)
    ext = p.suffix.lower().lstrip(".")
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}.get(ext, "image/jpeg")
    with open(p, "rb") as f:
        return f"data:{mime};base64,{base64.b64encode(f.read()).decode()}"


def parse_stats(stats_str: str) -> list:
    if not stats_str.strip():
        return []
    result = []
    for item in stats_str.split(","):
        item = item.strip()
        if not item:
            continue
        parts = item.split(" ", 1)
        result.append((parts[0], parts[1] if len(parts) > 1 else ""))
    return result[:3]


def build_html(
    screenshot_b64: str,
    project: str,
    label: str,
    headline: str,
    stats: list,
    tools: list,
    fit: str,
) -> str:
    # Handle both real newline and literal \n in headline
    headline_html = headline.replace("\\n", "<br>").replace("\n", "<br>")

    # Stats block
    if stats:
        items = ""
        for i, (val, lbl) in enumerate(stats):
            border = "" if i == 0 else "border-left: 1.5px solid rgba(232,255,58,0.18); padding-left: 18px;"
            lemon_num = "color: #E8FF3A;" if val == "0" else ""
            items += f"""
            <div class="stat-item" style="{border}">
                <div class="stat-num" style="{lemon_num}">{val}</div>
                <div class="stat-lbl">{lbl}</div>
            </div>"""
        stats_html = f'<div class="stats-row">{items}</div>'
    else:
        stats_html = ""

    # Tools block
    if tools:
        pills = "".join(f'<span class="tool">{t.strip()}</span>' for t in tools)
        tools_html = f'<div class="tools">{pills}</div>'
    else:
        tools_html = ""

    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<link href="{FONTS_URL}" rel="stylesheet">
<style>
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

html, body {{
    width: {W}px; height: {H}px;
    background: {BG};
    overflow: hidden;
    font-family: 'Inter', sans-serif;
    display: flex;
    flex-direction: row;
}}

/* ── LEFT TEXT PANEL ── */
.left {{
    width: 408px;
    flex-shrink: 0;
    height: {H}px;
    padding: 54px 28px 48px 54px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    position: relative;
    z-index: 2;
}}

/* Bleed edge so left panel fades into dark rather than hard-cutting */
.left::after {{
    content: '';
    position: absolute;
    right: -1px; top: 0; bottom: 0; width: 48px;
    background: linear-gradient(to right, transparent, {BG});
    pointer-events: none;
}}

.eyebrow {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 8px; font-weight: 500;
    letter-spacing: 0.28em; text-transform: uppercase;
    color: {LEMON};
    margin-bottom: 18px;
}}

.headline {{
    font-family: 'Poppins', sans-serif;
    font-weight: 800; font-size: 50px;
    line-height: 1.04; letter-spacing: -0.035em;
    color: {WHITE};
}}

.stats-row {{
    display: flex;
    gap: 0;
    margin-top: 32px;
    align-items: flex-start;
}}

.stat-item {{
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 5px;
}}

.stat-num {{
    font-family: 'Poppins', sans-serif;
    font-weight: 800; font-size: 30px;
    line-height: 1; letter-spacing: -0.03em;
    color: {WHITE};
}}

.stat-lbl {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 7px; font-weight: 500;
    letter-spacing: 0.18em; text-transform: uppercase;
    color: {DIM};
    line-height: 1.4;
}}

.tools {{
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 20px;
}}

.tool {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 7px; font-weight: 500;
    letter-spacing: 0.10em; text-transform: uppercase;
    color: {DIM};
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 40px;
    padding: 5px 12px; line-height: 1;
}}

.brand {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 7px; letter-spacing: 0.32em; text-transform: uppercase;
    color: rgba(255,255,255,0.12);
}}

/* ── RIGHT PANEL — screenshot frame ── */
.right {{
    flex: 1;
    height: {H}px;
    padding: 32px 44px 32px 6px;
    display: flex;
    align-items: center;
    justify-content: center;
}}

/* The wide rounded frame */
.frame {{
    width: 100%;
    height: 100%;
    border-radius: 22px;
    border: 1.5px solid rgba(232,255,58,0.38);
    background: #0d0d0d;
    box-shadow:
        0 0 0 1px rgba(255,255,255,0.04),
        0 40px 100px rgba(0,0,0,0.85),
        0 8px 24px rgba(0,0,0,0.55),
        0 0 80px rgba(232,255,58,0.05);
    overflow: hidden;
    display: flex;
    flex-direction: column;
}}

/* Minimal top bar — browser chrome feel */
.frame-bar {{
    height: 32px;
    background: #131313;
    border-bottom: 1px solid rgba(255,255,255,0.07);
    flex-shrink: 0;
    display: flex;
    align-items: center;
    padding: 0 14px;
    gap: 7px;
}}

.dot {{ width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0; }}

.frame-title {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 8px;
    letter-spacing: 0.18em; text-transform: uppercase;
    color: rgba(255,255,255,0.22);
    margin-left: auto;
}}

/* Screenshot inside frame */
.frame-content {{
    flex: 1;
    overflow: hidden;
    background: #0d0d0d;
    display: flex;
    align-items: center;
    justify-content: center;
}}

.frame-content img {{
    width: 100%;
    height: 100%;
    object-fit: {fit};
    object-position: top center;
    display: block;
}}

</style>
</head>
<body>

<!-- Left text panel -->
<div class="left">
    <div>
        <div class="eyebrow">{label}</div>
        <div class="headline">{headline_html}</div>
    </div>
    <div>
        {stats_html}
        {tools_html}
    </div>
    <div class="brand">Hephzibah &middot; 2026</div>
</div>

<!-- Right screenshot frame -->
<div class="right">
    <div class="frame">
        <div class="frame-bar">
            <div class="dot" style="background:rgba(255,255,255,0.14);"></div>
            <div class="dot" style="background:rgba(255,255,255,0.10);"></div>
            <div class="dot" style="background:rgba(232,255,58,0.50);"></div>
            <div class="frame-title">{project}</div>
        </div>
        <div class="frame-content">
            <img src="{screenshot_b64}" alt="{project}">
        </div>
    </div>
</div>

</body></html>"""


async def render(html: str, out_path: str) -> None:
    tmp = out_path.replace(".png", "_tmp_card.html")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(html)
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(
            viewport={"width": W, "height": H},
            device_scale_factor=2,
        )
        await page.goto(f"file:///{tmp.replace(os.sep, '/')}")
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(700)
        await page.screenshot(path=out_path, full_page=False)
        await browser.close()
    os.remove(tmp)
    size_kb = os.path.getsize(out_path) // 1024
    print(f"[portfolio_card] Saved: {out_path} ({size_kb} KB)")


def main():
    parser = argparse.ArgumentParser(description="Hephzibah Portfolio Card Renderer")
    parser.add_argument("--screenshot", required=True, help="Path to workflow/app screenshot")
    parser.add_argument("--project",    required=True, help="Project name (frame bar + eyebrow)")
    parser.add_argument("--headline",   required=True, help="Bold headline (use \\n for line breaks)")
    parser.add_argument("--label",      default=None,  help="Eyebrow category label (defaults to --project)")
    parser.add_argument("--stats",      default="",    help='Up to 3 stats: "7 Videos/Week,4 Workflows,0 Manual Steps"')
    parser.add_argument("--tools",      default="",    help="Comma-separated tool names")
    parser.add_argument("--fit",        default="contain", choices=["contain", "cover"],
                        help="Screenshot fit mode: contain (default) or cover")
    parser.add_argument("--out",        required=True, help="Output PNG path")
    args = parser.parse_args()

    if not os.path.exists(args.screenshot):
        print(f"ERROR: screenshot not found: {args.screenshot}")
        sys.exit(1)

    label  = args.label or args.project
    stats  = parse_stats(args.stats)
    tools  = [t.strip() for t in args.tools.split(",")] if args.tools.strip() else []

    print(f"[portfolio_card] Loading screenshot: {args.screenshot}")
    screenshot_b64 = b64(args.screenshot)

    html = build_html(
        screenshot_b64=screenshot_b64,
        project=args.project,
        label=label,
        headline=args.headline,
        stats=stats,
        tools=tools,
        fit=args.fit,
    )

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    asyncio.run(render(html, args.out))
    print(f"[portfolio_card] Done — {W}x{H} at 2x = {W*2}x{H*2} crisp PNG")

    if sys.platform == "win32":
        import subprocess
        subprocess.Popen(["explorer", "/select,", os.path.abspath(args.out)])


if __name__ == "__main__":
    main()
