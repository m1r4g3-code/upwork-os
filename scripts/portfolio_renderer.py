"""
portfolio_renderer.py — SERAMAN Upwork Portfolio Piece Generator

Generates 4 PNG slides at 1280x720px (2x device scale -> 2560x1440 crisp output).

Card system: scattered/layered editorial cards with slight rotations, overlapping,
image content inside — not glass panels. Think polaroids laid on a dark surface.

Slides:
  1 — Hero:         Left stats + Right: 3 scattered image cards (canvas, video, accent)
  2 — Architecture: Left headline + Right: 2 stacked cards (canvas + phase list)
  3 — Reliability:  Left "0" + Right: 4 proof cards (grid + subtle rotations)
  4 — Output:       Full-bleed video bg + 2 large overlapping cards + bottom text

Usage:
  python scripts/portfolio_renderer.py
  python scripts/portfolio_renderer.py --slide 1
  python scripts/portfolio_renderer.py --out outputs/portfolio
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

ROOT   = Path(__file__).parent.parent
ASSETS = ROOT / "outputs" / "assets"
FRAMES = ASSETS / "final-test-frames"

FONTS_URL = (
    "https://fonts.googleapis.com/css2?"
    "family=Poppins:wght@300;400;700;800;900&"
    "family=Inter:wght@300;400;500&"
    "family=JetBrains+Mono:wght@400;500;600&"
    "display=swap"
)

W, H = 1280, 720

# Design tokens
BG      = "#080808"
LEMON   = "#E8FF3A"
TERRA   = "#C1714C"
WHITE   = "#F0F0F0"
DIM     = "#808080"
DIMMER  = "#1E1E1E"
GREEN   = "#4ADE80"

# Card shadow — the depth that makes them lift off the surface
CARD_SHADOW = "0 32px 80px rgba(0,0,0,0.75), 0 8px 24px rgba(0,0,0,0.45)"
CARD_BORDER = "rgba(255,255,255,0.10)"
CARD_RADIUS = "20px"


# ── helpers ──────────────────────────────────────────────────────────────────

def b64(path) -> str:
    p = Path(path)
    ext = p.suffix.lower().lstrip(".")
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png"}.get(ext, "image/jpeg")
    with open(p, "rb") as f:
        return f"data:{mime};base64,{base64.b64encode(f.read()).decode()}"


def base_style() -> str:
    return f"""
@import url('{FONTS_URL}');
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{
    width: {W}px; height: {H}px;
    background: {BG};
    overflow: hidden;
    font-family: 'Inter', sans-serif;
    position: relative;
}}
"""


def card_css() -> str:
    """Base card definition — scattered, lifted, editorial."""
    return f"""
.card {{
    position: absolute;
    border-radius: {CARD_RADIUS};
    border: 1px solid {CARD_BORDER};
    box-shadow: {CARD_SHADOW};
    overflow: hidden;
    transform-origin: center center;
}}
.card img {{
    width: 100%; height: 100%;
    object-fit: cover;
    display: block;
}}
/* Accent card — no image, dark content surface */
.card-dark {{
    position: absolute;
    border-radius: {CARD_RADIUS};
    border: 1px solid rgba(255,255,255,0.08);
    box-shadow: {CARD_SHADOW};
    background: #121212;
    transform-origin: center center;
    display: flex; flex-direction: column;
    justify-content: center;
}}
.card-lemon {{
    position: absolute;
    border-radius: {CARD_RADIUS};
    border: 1px solid rgba(232,255,58,0.22);
    box-shadow: {CARD_SHADOW}, 0 0 60px rgba(232,255,58,0.07);
    background: rgba(232,255,58,0.05);
    transform-origin: center center;
    display: flex; flex-direction: column;
    justify-content: center;
}}
"""


async def render_slide(html: str, slide_num: int, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    tmp = out_dir / f"_tmp_slide{slide_num}.html"
    out = out_dir / f"seraman-slide-{slide_num}.png"

    tmp.write_text(html, encoding="utf-8")
    uri = f"file:///{tmp.resolve().as_posix()}"

    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        page = await browser.new_page(
            viewport={"width": W, "height": H},
            device_scale_factor=2,
        )
        await page.goto(uri)
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(1000)
        await page.screenshot(path=str(out), full_page=False)
        await browser.close()

    tmp.unlink(missing_ok=True)
    kb = out.stat().st_size // 1024
    print(f"  [slide {slide_num}] -> {out.name}  ({kb} KB)")
    return out


# ── SLIDE 1 — HERO ───────────────────────────────────────────────────────────
#
# Left (480px): eyebrow + 3 large stat numbers + tagline — clean, flat, readable
# Right: 3 scattered cards (n8n canvas + video frame + lemon accent info card)
# Separator gradient at x=380 protects left text from card bleed-in

def html_slide1(canvas_b64: str, video_b64: str) -> str:
    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
{base_style()}
{card_css()}

/* ── Scattered card cluster ── */

/* Card A: n8n canvas screenshot — back, large, rotated left */
.ca {{
    left: 510px; top: 55px;
    width: 350px; height: 440px;
    transform: rotate(-8deg);
    z-index: 1;
}}
.ca img {{ filter: brightness(0.72) saturate(0.50); }}

/* Card B: video frame — front, rotated right */
.cb {{
    left: 740px; top: 40px;
    width: 330px; height: 420px;
    transform: rotate(5deg);
    z-index: 2;
}}
.cb img {{ filter: brightness(0.88) saturate(0.90); }}

/* Card C: lemon accent info card — front-bottom, slight lean */
.cc {{
    left: 608px; top: 468px;
    width: 320px; height: 118px;
    transform: rotate(-3deg);
    z-index: 3;
    padding: 18px 24px;
    gap: 6px;
}}

/* Separator — fades dark bg over the card edges near the text */
.sep {{
    position: absolute;
    top: 0; left: 320px;
    width: 240px; height: 100%;
    background: linear-gradient(to right, {BG} 0%, rgba(8,8,8,0) 100%);
    z-index: 5;
    pointer-events: none;
}}

/* ── Left text content ── */
.left {{
    position: absolute;
    top: 0; left: 0;
    width: 480px; height: 720px;
    padding: 52px 24px 52px 60px;
    z-index: 10;
    display: flex; flex-direction: column;
    justify-content: space-between;
}}

.eyebrow {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 8.5px; font-weight: 500;
    letter-spacing: 0.24em; text-transform: uppercase;
    color: {LEMON};
}}

.stats {{ display: flex; flex-direction: column; gap: 0; }}

.stat-row {{
    padding: 16px 0;
    border-top: 1px solid rgba(255,255,255,0.07);
    display: flex; flex-direction: column; gap: 5px;
}}
.stat-row:last-child {{ border-bottom: 1px solid rgba(255,255,255,0.07); }}

.num {{
    font-family: 'Poppins', sans-serif;
    font-weight: 800; font-size: 82px;
    line-height: 0.88; letter-spacing: -0.04em;
    color: {WHITE};
}}
.num.accent {{ color: {LEMON}; }}

.lbl {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 9.5px; font-weight: 500;
    letter-spacing: 0.26em; text-transform: uppercase;
    color: {DIM};
}}

.tagline {{
    font-family: 'Inter', sans-serif;
    font-weight: 300; font-size: 12px;
    color: {DIM}; line-height: 1.75;
}}
.tagline b {{ color: {WHITE}; font-weight: 400; }}

/* Card C inner text */
.cc-label {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 8px; letter-spacing: 0.20em; text-transform: uppercase;
    color: {LEMON}; margin-bottom: 6px;
}}
.cc-val {{
    font-family: 'Poppins', sans-serif;
    font-size: 15px; font-weight: 700;
    color: {WHITE}; letter-spacing: -0.01em;
}}
.cc-sub {{
    font-family: 'Inter', sans-serif;
    font-size: 10px; font-weight: 300;
    color: {DIM}; margin-top: 3px;
}}

.brand {{
    position: absolute; bottom: 28px; right: 36px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 7px; letter-spacing: 0.32em; text-transform: uppercase;
    color: rgba(255,255,255,0.10); z-index: 10;
}}
</style>
</head>
<body>

<!-- Scattered cards -->
<div class="card ca"><img src="{canvas_b64}" /></div>
<div class="card cb"><img src="{video_b64}" /></div>
<div class="card-lemon cc">
    <div class="cc-label">Status</div>
    <div class="cc-val">Running in production</div>
    <div class="cc-sub">Client: Giovanni &nbsp;&middot;&nbsp; 5&#9733; &nbsp;&middot;&nbsp; 7 videos / week</div>
</div>

<!-- Separator gradient -->
<div class="sep"></div>

<!-- Left text content -->
<div class="left">
    <div class="eyebrow">SERAMAN &mdash; AI Video Production Pipeline</div>
    <div class="stats">
        <div class="stat-row">
            <div class="num">4</div>
            <div class="lbl">n8n Workflows</div>
        </div>
        <div class="stat-row">
            <div class="num">7</div>
            <div class="lbl">Videos / Week</div>
        </div>
        <div class="stat-row">
            <div class="num accent">0</div>
            <div class="lbl">Manual Steps</div>
        </div>
    </div>
    <div class="tagline">
        <b>AI input. Published video.</b><br>
        Form submission through multi-platform publishing.<br>
        Running in production for a paying client.
    </div>
</div>

<div class="brand">Hephzibah &middot; 2026</div>

</body></html>"""


# ── SLIDE 2 — ARCHITECTURE ───────────────────────────────────────────────────
#
# Left (460px): eyebrow + bold headline + subline + tool pills — flat, clean
# Right: 2 stacked/overlapping cards
#   Card A (back): n8n canvas screenshot (real workflow — proof of system)
#   Card B (front): dark card containing the 4 pipeline phases

def html_slide2(canvas_b64: str) -> str:
    phases = [
        ("01", "Input & Validation",   "Tally form extraction. Exactly-once job dedup."),
        ("02", "Script Generation",    "Claude AI builds scenes, narration, image prompts."),
        ("03", "Video Assembly",       "Kie AI generation -> Creatomate rendering."),
        ("04", "Social Publishing",    "Blotato auto-posts to Reels, TikTok, YouTube, Facebook."),
    ]
    phase_html = "".join(f"""
        <div class="phase">
            <div class="phase-num">{num}</div>
            <div class="phase-body">
                <div class="phase-title">{title}</div>
                <div class="phase-desc">{desc}</div>
            </div>
        </div>""" for num, title, desc in phases)

    tools = ["n8n", "Claude AI", "Kie AI", "Creatomate", "Blotato"]
    tool_html = "".join(f'<span class="tool">{t}</span>' for t in tools)

    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
{base_style()}
{card_css()}

/* Card A: n8n canvas — large, behind, rotated left */
.ca {{
    left: 460px; top: 30px;
    width: 500px; height: 380px;
    transform: rotate(-6deg);
    z-index: 1;
}}
.ca img {{ filter: brightness(0.65) saturate(0.45); }}

/* Card B: phase list — front, rotated right slightly */
.cb {{
    left: 620px; top: 220px;
    width: 480px; height: 360px;
    transform: rotate(3deg);
    z-index: 2;
    padding: 28px 30px;
    display: flex; flex-direction: column; gap: 0;
}}

.sep {{
    position: absolute; top: 0; left: 300px;
    width: 220px; height: 100%;
    background: linear-gradient(to right, {BG} 0%, rgba(8,8,8,0) 100%);
    z-index: 5; pointer-events: none;
}}

.left {{
    position: absolute; top: 0; left: 0;
    width: 460px; height: 720px;
    padding: 52px 20px 52px 60px;
    z-index: 10;
    display: flex; flex-direction: column;
    justify-content: center; gap: 0;
}}

.eyebrow {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 8.5px; font-weight: 500;
    letter-spacing: 0.24em; text-transform: uppercase;
    color: {LEMON}; margin-bottom: 14px;
}}

.headline {{
    font-family: 'Poppins', sans-serif;
    font-weight: 800; font-size: 58px;
    line-height: 1.02; letter-spacing: -0.03em;
    color: {WHITE};
}}

.subline {{
    font-family: 'Inter', sans-serif;
    font-size: 11px; font-weight: 300;
    color: {DIM}; line-height: 1.65;
    margin-top: 14px;
}}

.stack {{
    display: flex; align-items: center; gap: 6px;
    flex-wrap: wrap; margin-top: 20px;
}}
.tool {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 7.5px; font-weight: 500;
    letter-spacing: 0.10em; text-transform: uppercase;
    color: {DIM};
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 40px; padding: 5px 11px; line-height: 1;
}}

/* Phase list inside card B */
.phase {{
    display: flex; align-items: flex-start; gap: 12px;
    padding: 14px 0;
    border-bottom: 1px solid rgba(255,255,255,0.07);
}}
.phase:first-child {{ border-top: 1px solid rgba(255,255,255,0.07); }}

.phase-num {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 7.5px; font-weight: 600;
    letter-spacing: 0.08em;
    color: {LEMON};
    background: rgba(232,255,58,0.10);
    border: 1px solid rgba(232,255,58,0.20);
    border-radius: 6px;
    padding: 3px 7px; flex-shrink: 0; margin-top: 1px; line-height: 1;
}}

.phase-title {{
    font-family: 'Inter', sans-serif;
    font-size: 12px; font-weight: 500;
    color: {WHITE}; line-height: 1.3;
}}

.phase-desc {{
    font-family: 'Inter', sans-serif;
    font-size: 9.5px; font-weight: 300;
    color: {DIM}; line-height: 1.4; margin-top: 2px;
}}

.cb-label {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 8px; letter-spacing: 0.20em; text-transform: uppercase;
    color: {DIM}; margin-bottom: 4px;
}}

.brand {{
    position: absolute; bottom: 28px; right: 36px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 7px; letter-spacing: 0.32em; text-transform: uppercase;
    color: rgba(255,255,255,0.10); z-index: 10;
}}
</style>
</head>
<body>

<div class="card ca"><img src="{canvas_b64}" /></div>
<div class="card-dark cb">
    <div class="cb-label">Pipeline Phases</div>
    {phase_html}
</div>

<div class="sep"></div>

<div class="left">
    <div>
        <div class="eyebrow">Pipeline Architecture</div>
        <div class="headline">Four workflows.<br>One pipeline.</div>
        <div class="subline">Built and maintained for a live client.<br>7 videos published weekly, zero human steps.</div>
        <div class="stack">{tool_html}</div>
    </div>
</div>

<div class="brand">Hephzibah &middot; 2026</div>

</body></html>"""


# ── SLIDE 3 — RELIABILITY ────────────────────────────────────────────────────
#
# Left (420px): "0" hero stat — clean flat, no card
# Right: 4 proof cards in a 2x2 grid, each with a subtle rotation for editorial feel

def html_slide3() -> str:
    proofs = [
        (GREEN,  "Exactly-once job tracking",
                 "Status column is the single arbiter. No duplicate runs even on webhook retries.",
                 "-2.5deg"),
        (LEMON,  "Amber / red error routing",
                 "Rate limit, content policy, and malformed response handled as separate failure modes.",
                 "1.5deg"),
        (WHITE,  "Human review gate",
                 "Videos queue for approval before any publishing event fires downstream.",
                 "1deg"),
        (TERRA,  "Silent-run detection",
                 "Notification fires if the weekly batch goes quiet. System self-monitors.",
                 "-2deg"),
    ]
    proof_html = "".join(f"""
        <div class="proof-card" style="transform:rotate({rot});">
            <div class="dot" style="background:{color};box-shadow:0 0 10px {color}55;"></div>
            <div class="proof-title">{title}</div>
            <div class="proof-desc">{desc}</div>
        </div>""" for color, title, desc, rot in proofs)

    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
{base_style()}

/* Left: "0" stat panel */
.left {{
    position: absolute; top: 0; left: 0;
    width: 420px; height: 720px;
    padding: 52px 32px 52px 60px;
    display: flex; flex-direction: column;
    z-index: 2;
}}

/* Vertical separator line fading at top+bottom */
.left::after {{
    content: '';
    position: absolute; right: 0; top: 48px; bottom: 48px;
    width: 1px;
    background: linear-gradient(to bottom,
        transparent,
        rgba(255,255,255,0.08) 25%,
        rgba(255,255,255,0.08) 75%,
        transparent);
}}

.eyebrow {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 8.5px; font-weight: 500;
    letter-spacing: 0.24em; text-transform: uppercase;
    color: {LEMON};
}}

.zero-block {{ margin-top: auto; margin-bottom: auto; }}

.zero {{
    font-family: 'Poppins', sans-serif;
    font-weight: 900; font-size: 220px;
    line-height: 0.85; letter-spacing: -0.06em;
    color: {WHITE};
}}

.zero-label {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px; font-weight: 500;
    letter-spacing: 0.2em; text-transform: uppercase;
    color: {DIM}; margin-top: 20px; line-height: 1.65;
}}

.zero-sub {{
    font-family: 'Inter', sans-serif;
    font-size: 10.5px; font-weight: 300;
    color: rgba(128,128,128,0.50); margin-top: 6px;
}}

/* Right: 2x2 scattered card grid */
.right {{
    position: absolute; top: 0; left: 420px; right: 0; bottom: 0;
    display: grid;
    grid-template-columns: 1fr 1fr;
    grid-template-rows: 1fr 1fr;
    gap: 14px;
    padding: 28px 28px 28px 24px;
    z-index: 1;
}}

.proof-card {{
    background: #111111;
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 18px;
    box-shadow: 0 24px 60px rgba(0,0,0,0.65), 0 6px 16px rgba(0,0,0,0.40);
    padding: 24px;
    display: flex; flex-direction: column; justify-content: space-between;
    transform-origin: center center;
}}

.dot {{
    width: 9px; height: 9px;
    border-radius: 50%; flex-shrink: 0;
}}

.proof-title {{
    font-family: 'Poppins', sans-serif;
    font-size: 13px; font-weight: 700;
    color: {WHITE}; line-height: 1.25;
    letter-spacing: -0.01em;
    margin: auto 0;
}}

.proof-desc {{
    font-family: 'Inter', sans-serif;
    font-size: 10px; font-weight: 300;
    color: {DIM}; line-height: 1.55;
}}

.brand {{
    position: absolute; bottom: 28px; right: 36px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 7px; letter-spacing: 0.32em; text-transform: uppercase;
    color: rgba(255,255,255,0.10); z-index: 10;
}}
</style>
</head>
<body>

<div class="left">
    <div class="eyebrow">Production Reliability</div>
    <div class="zero-block">
        <div class="zero">0</div>
        <div class="zero-label">Failed runs<br>in production</div>
        <div class="zero-sub">Active since v2 &nbsp;&middot;&nbsp; 5&#9733; client</div>
    </div>
</div>

<div class="right">
    {proof_html}
</div>

<div class="brand">Hephzibah &middot; 2026</div>

</body></html>"""


# ── SLIDE 4 — OUTPUT ─────────────────────────────────────────────────────────
#
# Full-bleed cinematic video as background (very dimmed — becomes texture)
# Center: 2 large overlapping scattered cards (canvas + video frame)
# Bottom left: flat headline + meta + platform pills
# No glass card — the cards ARE the visual design

def html_slide4(canvas_b64: str, video_b64: str) -> str:
    platforms = ["Instagram Reels", "TikTok", "YouTube Shorts", "Facebook"]
    pills = "".join(f'<span class="pill">{p}</span>' for p in platforms)

    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
{base_style()}
{card_css()}

/* Full-bleed background — very dimmed, acts as texture */
.bg-img {{
    position: absolute; inset: 0; z-index: 0;
}}
.bg-img img {{
    width: 100%; height: 100%;
    object-fit: cover; object-position: center;
    filter: brightness(0.20) saturate(0.40);
    display: block;
}}

/* Bottom gradient to create text legibility zone */
.overlay-bottom {{
    position: absolute; bottom: 0; left: 0; right: 0; height: 340px;
    background: linear-gradient(to top, {BG} 0%, rgba(8,8,8,0.85) 55%, transparent 100%);
    z-index: 3; pointer-events: none;
}}
/* Top gradient */
.overlay-top {{
    position: absolute; top: 0; left: 0; right: 0; height: 160px;
    background: linear-gradient(to bottom, {BG} 0%, transparent 100%);
    z-index: 3; pointer-events: none;
}}

/* Card A: canvas screenshot — back, large, left-leaning */
.ca {{
    left: 260px; top: 40px;
    width: 440px; height: 360px;
    transform: rotate(-7deg);
    z-index: 1;
}}
.ca img {{ filter: brightness(0.70) saturate(0.48); }}

/* Card B: video frame — front, right-leaning */
.cb {{
    left: 560px; top: 20px;
    width: 420px; height: 340px;
    transform: rotate(5deg);
    z-index: 2;
}}
.cb img {{ filter: brightness(0.90) saturate(0.92); }}

/* Bottom text content — floating over gradient */
.bottom {{
    position: absolute;
    bottom: 44px; left: 60px; right: 60px;
    z-index: 10;
    display: flex; flex-direction: column; gap: 12px;
}}

.eyebrow {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 8.5px; font-weight: 500;
    letter-spacing: 0.24em; text-transform: uppercase;
    color: {LEMON};
}}

.headline {{
    font-family: 'Poppins', sans-serif;
    font-weight: 800; font-size: 44px;
    line-height: 1.02; letter-spacing: -0.025em;
    color: {WHITE};
}}
.headline .arrow {{ color: {LEMON}; font-weight: 300; margin: 0 10px; font-size: 38px; }}

.meta {{
    font-family: 'Inter', sans-serif;
    font-size: 11px; font-weight: 300;
    color: {DIM}; letter-spacing: 0.02em;
}}

.platforms {{ display: flex; gap: 8px; align-items: center; }}

.pill {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 7.5px; font-weight: 600;
    letter-spacing: 0.14em; text-transform: uppercase;
    color: {BG};
    background: {LEMON};
    border-radius: 40px;
    padding: 6px 14px; display: inline-block; line-height: 1;
}}

.brand {{
    position: absolute; top: 44px; right: 60px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 7px; letter-spacing: 0.32em; text-transform: uppercase;
    color: rgba(255,255,255,0.14); z-index: 10;
}}
</style>
</head>
<body>

<div class="bg-img"><img src="{video_b64}" /></div>
<div class="overlay-top"></div>
<div class="overlay-bottom"></div>

<div class="card ca"><img src="{canvas_b64}" /></div>
<div class="card cb"><img src="{video_b64}" /></div>

<div class="brand">Hephzibah &middot; 2026</div>

<div class="bottom">
    <div class="eyebrow">SERAMAN &mdash; Final Output</div>
    <div class="headline">Form submission<span class="arrow">&#8594;</span>Published video.</div>
    <div class="meta">Automated &middot; Unattended &middot; Client: Giovanni &middot; 5&#9733; &middot; Running in production</div>
    <div class="platforms">{pills}</div>
</div>

</body></html>"""


# ── MAIN ─────────────────────────────────────────────────────────────────────

async def main():
    parser = argparse.ArgumentParser(description="SERAMAN portfolio renderer")
    parser.add_argument("--slide", type=int, choices=[1, 2, 3, 4], help="Render single slide only")
    parser.add_argument("--out", default=str(ROOT / "outputs" / "portfolio"), help="Output directory")
    args = parser.parse_args()

    out_dir = Path(args.out)

    print(f"[portfolio_renderer] Output -> {out_dir}")
    print("[portfolio_renderer] Loading assets...")

    video1_path = FRAMES / "v1_001.jpg"   # camping lantern — dramatic
    video3_path = FRAMES / "v3_001.jpg"   # sunglasses/compass — clean product
    canvas_path = ASSETS / "workflow-main.png"

    missing = [(l, p) for l, p in [("v1_001", video1_path), ("v3_001", video3_path), ("canvas", canvas_path)] if not p.exists()]
    for label, p in missing:
        print(f"  WARNING: {label} not found at {p}")

    video1_b64 = b64(video1_path) if video1_path.exists() else ""
    video3_b64 = b64(video3_path) if video3_path.exists() else ""
    canvas_b64 = b64(canvas_path) if canvas_path.exists() else ""

    slides = {
        1: lambda: html_slide1(canvas_b64, video3_b64),   # canvas + sunglasses/compass frame
        2: lambda: html_slide2(canvas_b64),               # canvas card + phase list card
        3: lambda: html_slide3(),                          # "0" + scattered proof cards
        4: lambda: html_slide4(canvas_b64, video1_b64),   # canvas + camping lantern
    }

    to_render = [args.slide] if args.slide else [1, 2, 3, 4]

    print()
    for n in to_render:
        print(f"[slide {n}] Rendering...")
        html = slides[n]()
        await render_slide(html, n, out_dir)

    print(f"\n[portfolio_renderer] Done. {len(to_render)} slide(s) saved to {out_dir}")

    if sys.platform == "win32":
        os.startfile(str(out_dir))


if __name__ == "__main__":
    asyncio.run(main())
