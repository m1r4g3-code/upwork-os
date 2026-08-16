"""
portfolio_batch_renderer.py -- Multi-project Upwork Portfolio Slide Generator

Generates 3-slide PNG sets for all portfolio projects using the same
scattered-card design language as the SERAMAN renderer.

Each project: slide-1 (hero stats), slide-2 (architecture), slide-3 (proof grid)

Usage:
  python scripts/portfolio_batch_renderer.py              -- render all
  python scripts/portfolio_batch_renderer.py --project avatar-doctor
  python scripts/portfolio_batch_renderer.py --project noryx-studio
  python scripts/portfolio_batch_renderer.py --slide 1   -- hero slides only
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
OUT    = ROOT / "outputs" / "portfolio"

FONTS_URL = (
    "https://fonts.googleapis.com/css2?"
    "family=Poppins:wght@300;400;700;800;900&"
    "family=Inter:wght@300;400;500&"
    "family=JetBrains+Mono:wght@400;500;600&"
    "display=swap"
)

W, H = 1280, 720

# Design tokens -- Terminal Precision system
BG     = "#080808"
LEMON  = "#E8FF3A"
TERRA  = "#C1714C"
WHITE  = "#F0F0F0"
DIM    = "#808080"
GREEN  = "#4ADE80"

CARD_SHADOW = "0 32px 80px rgba(0,0,0,0.75), 0 8px 24px rgba(0,0,0,0.45)"
CARD_BORDER = "rgba(255,255,255,0.10)"
CARD_RADIUS = "20px"


# ── Helpers ───────────────────────────────────────────────────────────────────

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

async def render_slide(html: str, project: str, slide_num: int, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    tmp = out_dir / f"_tmp_{project}_s{slide_num}.html"
    out = out_dir / f"{project}-slide-{slide_num}.png"

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
        await page.wait_for_timeout(1200)
        await page.screenshot(path=str(out), full_page=False)
        await browser.close()

    tmp.unlink(missing_ok=True)
    kb = out.stat().st_size // 1024
    print(f"  [{project} slide {slide_num}] -> {out.name}  ({kb} KB)")
    return out


# ── Shared slide templates ────────────────────────────────────────────────────

def slide_hero(
    eyebrow: str,
    stats: list,          # list of (number_str, label_str, is_accent_bool)
    tagline_html: str,
    img_a_b64: str,       # back card image
    img_b_b64: str,       # front card image
    accent_label: str,
    accent_val: str,
    accent_sub: str,
    img_a_rot: str = "-8deg",
    img_b_rot: str = "5deg",
    img_a_filter: str = "brightness(0.72) saturate(0.50)",
    img_b_filter: str = "brightness(0.88) saturate(0.90)",
    product_color: str = LEMON,
) -> str:
    h = product_color.lstrip('#')
    pc_r, pc_g, pc_b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    stat_rows = ""
    for num, lbl, is_accent in stats:
        accent_cls = " accent" if is_accent else ""
        stat_rows += f"""
        <div class="stat-row">
            <div class="num{accent_cls}">{num}</div>
            <div class="lbl">{lbl}</div>
        </div>"""

    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
{base_style()}
{card_css()}

.card-lemon {{
    border-color: rgba({pc_r},{pc_g},{pc_b},0.22);
    box-shadow: {CARD_SHADOW}, 0 0 60px rgba({pc_r},{pc_g},{pc_b},0.07);
    background: rgba({pc_r},{pc_g},{pc_b},0.05);
}}

.ca {{
    left: 510px; top: 55px;
    width: 350px; height: 440px;
    transform: rotate({img_a_rot});
    z-index: 1;
}}
.ca img {{ filter: {img_a_filter}; }}

.cb {{
    left: 740px; top: 40px;
    width: 330px; height: 420px;
    transform: rotate({img_b_rot});
    z-index: 2;
}}
.cb img {{ filter: {img_b_filter}; }}

.cc {{
    left: 608px; top: 468px;
    width: 320px; height: 118px;
    transform: rotate(-3deg);
    z-index: 3;
    padding: 18px 24px;
    gap: 6px;
}}

.sep {{
    position: absolute;
    top: 0; left: 320px;
    width: 240px; height: 100%;
    background: linear-gradient(to right, {BG} 0%, rgba(8,8,8,0) 100%);
    z-index: 5;
    pointer-events: none;
}}

.left {{
    position: absolute;
    top: 0; left: 0;
    width: 480px; height: 720px;
    padding: 52px 24px 52px 60px;
    z-index: 10;
    display: flex; flex-direction: column;
    justify-content: space-between;
}}

.brand-dot {{
    width: 6px; height: 6px;
    background: {LEMON};
    border-radius: 1px;
    margin-bottom: 10px;
}}

.eyebrow {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 8.5px; font-weight: 500;
    letter-spacing: 0.24em; text-transform: uppercase;
    color: {product_color};
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
.num.accent {{ color: {product_color}; }}

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

.cc-label {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 8px; letter-spacing: 0.20em; text-transform: uppercase;
    color: {product_color}; margin-bottom: 6px;
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

<div class="card ca"><img src="{img_a_b64}" /></div>
<div class="card cb"><img src="{img_b_b64}" /></div>
<div class="card-lemon cc">
    <div class="cc-label">{accent_label}</div>
    <div class="cc-val">{accent_val}</div>
    <div class="cc-sub">{accent_sub}</div>
</div>

<div class="sep"></div>

<div class="left">
    <div>
        <div class="brand-dot"></div>
        <div class="eyebrow">{eyebrow}</div>
    </div>
    <div class="stats">{stat_rows}
    </div>
    <div class="tagline">{tagline_html}</div>
</div>

<div class="brand">Hephzibah &middot; 2026</div>

</body></html>"""


def slide_arch(
    eyebrow: str,
    title: str,
    subtitle: str,
    phases: list,       # list of (num_str, title_str, desc_str)
    tools: list,        # list of tool name strings
    img_a_b64: str,     # back card image
    img_b_content: str, # HTML content for front dark card (already rendered HTML)
    product_color: str = LEMON,
) -> str:
    h = product_color.lstrip('#')
    pc_r, pc_g, pc_b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    phase_html = ""
    for num, ptitle, desc in phases:
        phase_html += f"""
        <div class="phase">
            <div class="phase-num">{num}</div>
            <div class="phase-body">
                <div class="phase-title">{ptitle}</div>
                <div class="phase-desc">{desc}</div>
            </div>
        </div>"""

    tool_html = "".join(f'<span class="tool">{t}</span>' for t in tools)

    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
{base_style()}
{card_css()}

.ca {{
    left: 460px; top: 30px;
    width: 500px; height: 380px;
    transform: rotate(-6deg);
    z-index: 1;
}}
.ca img {{ filter: brightness(0.65) saturate(0.45); }}

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
    position: absolute;
    top: 0; left: 0;
    width: 460px; height: 720px;
    padding: 52px 24px 52px 60px;
    z-index: 10;
    display: flex; flex-direction: column;
    justify-content: center; gap: 32px;
}}

.brand-dot {{
    width: 6px; height: 6px;
    background: {LEMON};
    border-radius: 1px;
    margin-bottom: 10px;
}}

.eyebrow {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 8px; font-weight: 500;
    letter-spacing: 0.26em; text-transform: uppercase;
    color: {product_color};
}}

.title {{
    font-family: 'Poppins', sans-serif;
    font-weight: 800; font-size: 38px;
    line-height: 1.05; letter-spacing: -0.03em;
    color: {WHITE}; margin-top: 8px;
}}

.subtitle {{
    font-family: 'Inter', sans-serif;
    font-weight: 300; font-size: 12.5px;
    color: {DIM}; line-height: 1.7; margin-top: 4px;
}}

.tools {{
    display: flex; flex-wrap: wrap; gap: 6px; margin-top: 4px;
}}

.tool {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 8.5px; font-weight: 500;
    letter-spacing: 0.12em; text-transform: uppercase;
    color: {product_color};
    border: 1px solid rgba({pc_r},{pc_g},{pc_b},0.30);
    padding: 4px 10px; border-radius: 4px;
}}

.phase {{
    display: flex; gap: 12px; align-items: flex-start;
    padding: 10px 0;
    border-top: 1px solid rgba(255,255,255,0.06);
}}
.phase:last-child {{ border-bottom: 1px solid rgba(255,255,255,0.06); }}

.phase-num {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px; font-weight: 600;
    color: {product_color}; min-width: 22px; padding-top: 1px;
    letter-spacing: 0.1em;
}}

.phase-title {{
    font-family: 'Poppins', sans-serif;
    font-size: 11.5px; font-weight: 700;
    color: {WHITE}; letter-spacing: -0.01em;
}}

.phase-desc {{
    font-family: 'Inter', sans-serif;
    font-size: 10.5px; font-weight: 300;
    color: {DIM}; margin-top: 2px; line-height: 1.5;
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

<div class="card ca"><img src="{img_a_b64}" /></div>
<div class="card-dark cb">{img_b_content}</div>

<div class="sep"></div>

<div class="left">
    <div>
        <div class="brand-dot"></div>
        <div class="eyebrow">{eyebrow}</div>
        <div class="title">{title}</div>
        <div class="subtitle">{subtitle}</div>
    </div>
    <div class="phases">{phase_html}
    </div>
    <div class="tools">{tool_html}</div>
</div>

<div class="brand">Hephzibah &middot; 2026</div>

</body></html>"""


def slide_proof(
    eyebrow: str,
    hero_num: str,
    hero_label: str,
    proofs: list,       # list of (label, value, sub, is_terra)  -- 4 items
    product_color: str = LEMON,
) -> str:
    # Absolutely positioned 2x2 grid — explicit coords, no CSS grid ambiguity
    # Cards: 220px tall, 2 rows with 28px gap, total coverage = 52 to 520px, centered
    positions = [
        ("430px", "90px",  "392px", "220px", "-2.5deg"),   # top-left
        ("848px", "90px",  "392px", "220px",  "1.5deg"),   # top-right
        ("430px", "400px", "392px", "220px",  "1deg"),     # bottom-left
        ("848px", "400px", "392px", "220px", "-2deg"),     # bottom-right
    ]

    proof_cards = ""
    for i, (label, val, sub, is_terra) in enumerate(proofs):
        left, top, w, h, rot = positions[i]
        if is_terra:
            card_bg    = "#0D0D0D"
            val_color  = TERRA
            border_col = "rgba(193,113,76,0.22)"
        else:
            card_bg    = "#111111"
            val_color  = WHITE
            border_col = "rgba(255,255,255,0.09)"

        proof_cards += f"""
        <div style="
            position: absolute;
            left: {left}; top: {top};
            width: {w}; height: {h};
            background: {card_bg};
            border: 1px solid {border_col};
            border-radius: 18px;
            padding: 28px 28px;
            transform: rotate({rot});
            box-shadow: 0 20px 56px rgba(0,0,0,0.65);
            z-index: 2;
            display: flex; flex-direction: column; justify-content: center;
        ">
            <div style="
                font-family: 'JetBrains Mono', monospace;
                font-size: 7.5px; letter-spacing: 0.22em; text-transform: uppercase;
                color: {DIM}; margin-bottom: 12px;
            ">{label}</div>
            <div style="
                font-family: 'Poppins', sans-serif;
                font-size: 22px; font-weight: 800;
                color: {val_color}; letter-spacing: -0.02em; line-height: 1.1;
            ">{val}</div>
            <div style="
                font-family: 'Inter', sans-serif;
                font-size: 10.5px; font-weight: 300;
                color: {DIM}; margin-top: 10px; line-height: 1.55;
            ">{sub}</div>
        </div>"""

    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
{base_style()}

.sep {{
    position: absolute; top: 0; left: 310px;
    width: 200px; height: 100%;
    background: linear-gradient(to right, {BG} 0%, rgba(8,8,8,0) 100%);
    z-index: 5; pointer-events: none;
}}

.left {{
    position: absolute;
    top: 0; left: 0;
    width: 420px; height: 720px;
    padding: 52px 24px 52px 60px;
    z-index: 10;
    display: flex; flex-direction: column;
    justify-content: center;
}}

.brand-dot {{
    width: 6px; height: 6px;
    background: {LEMON};
    border-radius: 1px;
    margin-bottom: 10px;
}}

.eyebrow {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 8px; font-weight: 500;
    letter-spacing: 0.26em; text-transform: uppercase;
    color: {product_color}; margin-bottom: 24px;
}}

.hero-num {{
    font-family: 'Poppins', sans-serif;
    font-weight: 900; font-size: 180px;
    line-height: 0.82; letter-spacing: -0.06em;
    color: {WHITE};
}}

.hero-lbl {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px; font-weight: 500;
    letter-spacing: 0.22em; text-transform: uppercase;
    color: {DIM}; margin-top: 18px;
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

<div class="sep"></div>

<div class="left">
    <div class="brand-dot"></div>
    <div class="eyebrow">{eyebrow}</div>
    <div class="hero-num">{hero_num}</div>
    <div class="hero-lbl">{hero_label}</div>
</div>

{proof_cards}

<div class="brand">Hephzibah &middot; 2026</div>

</body></html>"""


# ── Noryx Studio: full-bleed site screenshot hero ─────────────────────────────

def slide_noryx_hero(site_b64: str) -> str:
    """Noryx is a web app -- hero shows the live site full-bleed as the main card."""
    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
{base_style()}
{card_css()}

/* Full site card - large, centered-right, slight rotation */
.site-card {{
    position: absolute;
    left: 440px; top: 20px;
    width: 820px; height: 680px;
    border-radius: 16px;
    border: 1px solid rgba(201,168,73,0.18);
    box-shadow: 0 40px 100px rgba(0,0,0,0.85), 0 0 80px rgba(201,168,73,0.06);
    overflow: hidden;
    transform: rotate(-2deg);
    z-index: 1;
}}
.site-card img {{
    width: 100%; height: 100%;
    object-fit: cover; object-position: top center;
    display: block;
    filter: brightness(0.95);
}}

/* Dark overlay gradient from left */
.overlay {{
    position: absolute; top: 0; left: 0;
    width: 560px; height: 100%;
    background: linear-gradient(to right, {BG} 55%, rgba(8,8,8,0) 100%);
    z-index: 5;
}}

/* Left text */
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
    color: #C9A849;
}}

.project-title {{
    font-family: 'Poppins', sans-serif;
    font-weight: 900; font-size: 52px;
    line-height: 0.95; letter-spacing: -0.04em;
    color: {WHITE}; margin-top: 12px;
}}
.project-title span {{ color: #C9A849; }}

.stats {{ display: flex; flex-direction: column; gap: 0; margin-top: 8px; }}

.stat-row {{
    padding: 14px 0;
    border-top: 1px solid rgba(255,255,255,0.07);
    display: flex; flex-direction: column; gap: 4px;
}}
.stat-row:last-child {{ border-bottom: 1px solid rgba(255,255,255,0.07); }}

.num {{
    font-family: 'Poppins', sans-serif;
    font-weight: 800; font-size: 52px;
    line-height: 0.88; letter-spacing: -0.03em;
    color: {WHITE};
}}
.num.gold {{ color: #C9A849; }}

.lbl {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px; font-weight: 500;
    letter-spacing: 0.26em; text-transform: uppercase;
    color: {DIM};
}}

.tagline {{
    font-family: 'Inter', sans-serif;
    font-weight: 300; font-size: 12px;
    color: {DIM}; line-height: 1.75;
}}
.tagline b {{ color: {WHITE}; font-weight: 400; }}

.brand {{
    position: absolute; bottom: 28px; right: 36px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 7px; letter-spacing: 0.32em; text-transform: uppercase;
    color: rgba(255,255,255,0.10); z-index: 10;
}}
</style>
</head>
<body>

<div class="site-card"><img src="{site_b64}" /></div>
<div class="overlay"></div>

<div class="left">
    <div>
        <div class="eyebrow">Full-Stack Web App &middot; Live on Vercel</div>
        <div class="project-title">NORYX<br><span>STUDIO</span></div>
    </div>
    <div class="stats">
        <div class="stat-row">
            <div class="num">100%</div>
            <div class="lbl">Custom Design System</div>
        </div>
        <div class="stat-row">
            <div class="num gold">Live</div>
            <div class="lbl">Booking &middot; Gallery &middot; Reviews</div>
        </div>
        <div class="stat-row">
            <div class="num">0</div>
            <div class="lbl">Templates used</div>
        </div>
    </div>
    <div class="tagline">
        <b>Next.js. Tailwind. Framer Motion.</b><br>
        Premium Lagos barbershop. Built from scratch.<br>
        Dark/gold identity. Mobile-first. Deployed.
    </div>
</div>

<div class="brand">Hephzibah &middot; 2026</div>

</body></html>"""


def slide_noryx_arch(site_b64: str) -> str:
    features = [
        ("Services", "Tiered service cards with pricing, duration, and booking CTAs per service."),
        ("Gallery", "Filterable portfolio grid with lightbox. Client photo management ready."),
        ("Booking Flow", "Click-to-book integrated with WhatsApp and direct call fallback."),
        ("Reviews", "Google-style review cards with star ratings and client avatars."),
    ]
    feature_html = "".join(f"""
        <div class="feat">
            <div class="feat-title">{t}</div>
            <div class="feat-desc">{d}</div>
        </div>""" for t, d in features)

    tools = ["Next.js", "React", "Tailwind CSS", "Framer Motion", "Vercel"]
    tool_html = "".join(f'<span class="tool">{t}</span>' for t in tools)

    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
{base_style()}
{card_css()}

.site-card {{
    position: absolute;
    left: 450px; top: 20px;
    width: 800px; height: 660px;
    border-radius: 16px;
    border: 1px solid rgba(201,168,73,0.15);
    box-shadow: 0 40px 100px rgba(0,0,0,0.85);
    overflow: hidden;
    transform: rotate(4deg);
    z-index: 1;
}}
.site-card img {{
    width: 100%; height: 100%;
    object-fit: cover; object-position: top;
    filter: brightness(0.60) saturate(0.70);
}}

.overlay {{
    position: absolute; top: 0; left: 0;
    width: 540px; height: 100%;
    background: linear-gradient(to right, {BG} 55%, rgba(8,8,8,0) 100%);
    z-index: 5;
}}

.left {{
    position: absolute;
    top: 0; left: 0;
    width: 480px; height: 720px;
    padding: 52px 24px 52px 60px;
    z-index: 10;
    display: flex; flex-direction: column;
    justify-content: center; gap: 28px;
}}

.eyebrow {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 8px; letter-spacing: 0.26em; text-transform: uppercase;
    color: #C9A849;
}}

.title {{
    font-family: 'Poppins', sans-serif;
    font-weight: 800; font-size: 34px;
    line-height: 1.1; letter-spacing: -0.03em;
    color: {WHITE}; margin-top: 6px;
}}

.feat {{
    padding: 10px 0;
    border-top: 1px solid rgba(255,255,255,0.06);
}}
.feat:last-child {{ border-bottom: 1px solid rgba(255,255,255,0.06); }}

.feat-title {{
    font-family: 'Poppins', sans-serif;
    font-size: 12px; font-weight: 700;
    color: {WHITE}; margin-bottom: 3px;
}}

.feat-desc {{
    font-family: 'Inter', sans-serif;
    font-size: 10.5px; font-weight: 300;
    color: {DIM}; line-height: 1.55;
}}

.tools {{ display: flex; flex-wrap: wrap; gap: 6px; }}

.tool {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 8px; letter-spacing: 0.10em; text-transform: uppercase;
    color: #C9A849;
    border: 1px solid rgba(201,168,73,0.30);
    padding: 4px 10px; border-radius: 4px;
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

<div class="site-card"><img src="{site_b64}" /></div>
<div class="overlay"></div>

<div class="left">
    <div>
        <div class="eyebrow">Noryx Studio &middot; What was built</div>
        <div class="title">Every section.<br>From scratch.</div>
    </div>
    <div class="features">{feature_html}
    </div>
    <div class="tools">{tool_html}</div>
</div>

<div class="brand">Hephzibah &middot; 2026</div>

</body></html>"""


# ── Project definitions ───────────────────────────────────────────────────────

async def render_project_avatar_doctor(out_dir: Path):
    """AI Avatar Content Automation for Doctors"""
    project = "avatar-doctor"
    PC = "#2DD4BF"  # medical teal -- HeyGen, healthcare, clean clinical

    img_wf  = b64(ASSETS / "avatar-content-1.png")
    img_wf2 = b64(ASSETS / "avatar-content-2.png")
    img_wf3 = b64(ASSETS / "avatar-content-3.png")
    img_av  = b64(ASSETS / "doctor-avatar-videos.png")  # avatar video thumbnails

    # Slide 1 -- Hero
    html1 = slide_hero(
        eyebrow="AI Avatar Content Automation &middot; Medical / Aesthetics",
        stats=[
            ("10", "n8n Workflows", False),
            ("5",  "Publishing Platforms", False),
            ("Daily", "Automated Output", True),
        ],
        tagline_html=(
            "<b>German plastic surgery client.</b><br>"
            "AI avatar videos generated and published<br>"
            "automatically. Zero manual production steps."
        ),
        img_a_b64=img_wf,
        img_b_b64=img_av,
        accent_label="Client",
        accent_val="Oliver Schumacher &middot; Plastic Surgeon",
        accent_sub="Germany &nbsp;&middot;&nbsp; Aesthetics &nbsp;&middot;&nbsp; Running in production",
        img_b_filter="brightness(0.82) saturate(0.75)",
        product_color=PC,
    )

    # Slide 2 -- Architecture
    phases = [
        ("01", "Source Content Ingestion",    "German-language patient education videos extracted and transcribed via n8n."),
        ("02", "Script Generation",           "AI adapts content into short-form scripts: hooks, body, CTA for each platform."),
        ("03", "AI Avatar Production",        "HeyGen API renders a photorealistic AI avatar delivering the script."),
        ("04", "Multilingual & Publishing",   "Videos translated, captioned, and auto-posted to 5 platforms daily."),
    ]
    arch_card_content = f"""
        <div style="padding: 0 4px;">
            <div style="font-family:'JetBrains Mono',monospace;font-size:7.5px;letter-spacing:0.20em;text-transform:uppercase;color:{PC};margin-bottom:14px;">Pipeline output</div>
            <div style="font-family:'Poppins',sans-serif;font-size:28px;font-weight:800;color:{WHITE};letter-spacing:-0.03em;line-height:1.1;">5 platforms.<br>1 workflow.</div>
            <div style="font-family:'Inter',sans-serif;font-size:10.5px;font-weight:300;color:{DIM};margin-top:14px;line-height:1.6;">Instagram Reels &middot; TikTok &middot; YouTube Shorts &middot; Facebook &middot; LinkedIn. Automated from script to published post.</div>
        </div>"""

    html2 = slide_arch(
        eyebrow="AI Avatar Doctor &middot; How it works",
        title="Human face.\nZero recording.",
        subtitle="The client never records a video. The system handles script, avatar, translation, and publishing.",
        phases=phases,
        tools=["n8n", "HeyGen", "OpenAI", "Whisper", "Creatomate"],
        img_a_b64=img_wf2,
        img_b_content=arch_card_content,
        product_color=PC,
    )

    # Slide 3 -- Proof
    html3 = slide_proof(
        eyebrow="AI Avatar Doctor &middot; Results",
        hero_num="5",
        hero_label="Platforms, one workflow",
        proofs=[
            ("Output",      "Daily Publishing",    "Automated every day without client input",             False),
            ("Client",      "German Surgeon",      "Plastic surgery / aesthetics niche, EU market",        False),
            ("Production",  "Zero recording",      "AI avatar replaces all on-camera requirements",        True),
            ("Reliability", "10 Workflows",        "Error routing, retry logic, human review gate built in", False),
        ],
        product_color=PC,
    )

    tasks = [
        render_slide(html1, project, 1, out_dir),
        render_slide(html2, project, 2, out_dir),
        render_slide(html3, project, 3, out_dir),
    ]
    for t in tasks:
        await t


async def render_project_multilingual(out_dir: Path):
    """Multilingual Video Content Automation (German to English)"""
    project = "multilingual"
    PC = "#A78BFA"  # purple -- AI/language processing, translation intelligence

    img_wf   = b64(ASSETS / "multilingual-1.png")
    img_wf2  = b64(ASSETS / "multilingual-2.png")
    img_doc  = b64(ASSETS / "doctor-original-views.png")  # 1.3M views screenshot

    # Slide 1 -- Hero
    html1 = slide_hero(
        eyebrow="Multilingual Video Automation &middot; German to English",
        stats=[
            ("1.3M", "Views on source content", False),
            ("5",    "Target languages", False),
            ("0",    "Manual translation steps", True),
        ],
        tagline_html=(
            "<b>Translate. Caption. Republish.</b><br>"
            "German medical content auto-converted<br>"
            "to English-language short-form video."
        ),
        img_a_b64=img_wf,
        img_b_b64=img_doc,
        accent_label="Proof",
        accent_val="1.3M views on source",
        accent_sub="Fachkompetenz bei der Implantatwahl &nbsp;&middot;&nbsp; Oliver Schumacher",
        img_b_filter="brightness(0.80) saturate(0.70)",
        product_color=PC,
    )

    # Slide 2 -- Architecture
    phases = [
        ("01", "Source Video Extraction",   "German-language video ingested via URL. Transcript extracted with Whisper."),
        ("02", "Translation Pipeline",      "OpenAI translates transcript segment-by-segment, preserving medical accuracy."),
        ("03", "Caption Sync",              "Translated captions aligned to original video timestamps. Burned in."),
        ("04", "Multi-platform Publish",    "Localized video posted to YouTube, Instagram, TikTok, Facebook automatically."),
    ]
    arch_card_content = f"""
        <div style="padding: 0 4px;">
            <div style="font-family:'JetBrains Mono',monospace;font-size:7.5px;letter-spacing:0.20em;text-transform:uppercase;color:{PC};margin-bottom:14px;">Translation accuracy</div>
            <div style="font-family:'Poppins',sans-serif;font-size:26px;font-weight:800;color:{WHITE};letter-spacing:-0.03em;line-height:1.1;">Medical grade.<br>Automated.</div>
            <div style="font-family:'Inter',sans-serif;font-size:10.5px;font-weight:300;color:{DIM};margin-top:14px;line-height:1.6;">Preserves clinical terminology. Prompt-engineered translation pipeline tuned for plastic surgery and aesthetics vocabulary.</div>
        </div>"""

    html2 = slide_arch(
        eyebrow="Multilingual Pipeline &middot; Architecture",
        title="One video.\nFive markets.",
        subtitle="German content republished in English without a single manual translation step. Timestamps preserved.",
        phases=phases,
        tools=["n8n", "Whisper", "OpenAI GPT-4", "FFmpeg", "Blotato"],
        img_a_b64=img_wf2,
        img_b_content=arch_card_content,
        product_color=PC,
    )

    # Slide 3 -- Proof
    html3 = slide_proof(
        eyebrow="Multilingual Pipeline &middot; Results",
        hero_num="0",
        hero_label="Manual steps",
        proofs=[
            ("Source reach",  "1.3M Views",       "Highest-viewed source video from this client",         False),
            ("Languages",     "DE to EN",          "German medical content to English-speaking markets",   False),
            ("Automation",    "Full pipeline",     "Ingest to published in under 12 minutes per video",    True),
            ("Client",        "Plastic Surgeon",   "EU-based aesthetics practice, Oliver Schumacher",      False),
        ],
        product_color=PC,
    )

    for t in [
        render_slide(html1, project, 1, out_dir),
        render_slide(html2, project, 2, out_dir),
        render_slide(html3, project, 3, out_dir),
    ]:
        await t


async def render_project_noryx(out_dir: Path):
    """Noryx Studio -- Full-Stack Web Application"""
    project = "noryx-studio"
    PC = "#C9A849"  # gold -- Noryx brand, already used in the hero card border

    img_site = b64(ASSETS / "noryx-hero.png")

    html1 = slide_noryx_hero(img_site)
    html2 = slide_noryx_arch(img_site)

    # Slide 3 -- Proof (adapted for web app, not automation)
    html3 = slide_proof(
        eyebrow="Noryx Studio &middot; What was delivered",
        hero_num="4",
        hero_label="Core sections built",
        proofs=[
            ("Stack",      "Next.js + Tailwind",  "Zero templates. Custom design system from scratch",    False),
            ("Deployment", "Live on Vercel",       "noryx-studio.vercel.app -- production deployed",       False),
            ("Design",     "Dark / Gold Identity", "Brand identity, typography, and UI system built fresh",True),
            ("Features",   "Booking Ready",        "Services, gallery, reviews, appointment flow",         False),
        ],
        product_color=PC,
    )

    for t in [
        render_slide(html1, project, 1, out_dir),
        render_slide(html2, project, 2, out_dir),
        render_slide(html3, project, 3, out_dir),
    ]:
        await t


async def render_project_personal_assistant(out_dir: Path):
    """AI Personal Assistant -- Email, Calendar & Multi-Tool"""
    project = "personal-assistant"
    PC = "#FF6D5A"  # n8n orange -- the workflow engine at the core

    img_a = b64(ASSETS / "personal-assistant-1.png")
    img_b = b64(ASSETS / "personal-assistant-3.png")
    img_c = b64(ASSETS / "personal-assistant-2.png")

    html1 = slide_hero(
        eyebrow="AI Personal Assistant &middot; Email, Calendar & Multi-Tool",
        stats=[
            ("3",  "Core tool integrations", False),
            ("24/7", "Always-on automation", True),
            ("0",  "Manual scheduling steps", False),
        ],
        tagline_html=(
            "<b>Email. Calendar. Research. Automated.</b><br>"
            "One AI agent managing daily operations<br>"
            "across connected tools and data sources."
        ),
        img_a_b64=img_a,
        img_b_b64=img_b,
        accent_label="Capabilities",
        accent_val="Inbox triage &middot; Calendar management",
        accent_sub="Web research &nbsp;&middot;&nbsp; Meeting prep &nbsp;&middot;&nbsp; Task routing",
        product_color=PC,
    )

    phases = [
        ("01", "Email Monitoring",    "Gmail inbox monitored via n8n. Priority triage by sender and content."),
        ("02", "Calendar Management", "Google Calendar integration. Scheduling, conflicts, reminders auto-handled."),
        ("03", "Research Agent",      "Claude AI performs web research on demand. Summaries delivered to inbox."),
        ("04", "Task Orchestration",  "Action items extracted from email. Routed to Notion, Slack, or calendar."),
    ]
    arch_card = f"""
        <div style="padding:0 4px;">
            <div style="font-family:'JetBrains Mono',monospace;font-size:7.5px;letter-spacing:0.20em;text-transform:uppercase;color:{PC};margin-bottom:14px;">Daily time saved</div>
            <div style="font-family:'Poppins',sans-serif;font-size:28px;font-weight:800;color:{WHITE};letter-spacing:-0.03em;line-height:1.1;">One agent.<br>Full stack.</div>
            <div style="font-family:'Inter',sans-serif;font-size:10.5px;font-weight:300;color:{DIM};margin-top:14px;line-height:1.6;">Email, calendar, research, and task routing connected. The agent knows context across all tools.</div>
        </div>"""

    html2 = slide_arch(
        eyebrow="Personal Assistant &middot; Architecture",
        title="Every tool.\nOne brain.",
        subtitle="Claude AI as the reasoning core. n8n as the integration layer. Tools connected, not siloed.",
        phases=phases,
        tools=["n8n", "Claude AI", "Gmail API", "Google Calendar", "Notion"],
        img_a_b64=img_c,
        img_b_content=arch_card,
        product_color=PC,
    )

    html3 = slide_proof(
        eyebrow="Personal Assistant &middot; What it handles",
        hero_num="3",
        hero_label="Tool categories automated",
        proofs=[
            ("Email",      "Inbox Triage",       "Priority sorting, auto-replies, forwarding logic",        False),
            ("Calendar",   "Smart Scheduling",   "Conflict detection, reminders, meeting prep briefs",       False),
            ("Research",   "On-Demand Intel",    "Claude AI runs searches and delivers summaries to inbox",  True),
            ("Routing",    "Zero Manual Steps",  "Actions extracted and dispatched to the right tool",       False),
        ],
        product_color=PC,
    )

    for t in [
        render_slide(html1, project, 1, out_dir),
        render_slide(html2, project, 2, out_dir),
        render_slide(html3, project, 3, out_dir),
    ]:
        await t


async def render_project_youtube_summarizer(out_dir: Path):
    """AI-Powered YouTube Video Summarizer"""
    project = "youtube-summarizer"
    PC = "#EF4444"  # YouTube red

    img_wf = b64(ASSETS / "youtube-summarizer.png")

    html1 = slide_hero(
        eyebrow="AI YouTube Summarizer &middot; Video to Structured Notes",
        stats=[
            ("100%", "Automated transcript processing", False),
            ("5min",  "Summary delivery time", True),
            ("0",     "Manual note-taking", False),
        ],
        tagline_html=(
            "<b>Any YouTube video. Instant notes.</b><br>"
            "Transcript extracted, AI-summarized,<br>"
            "and delivered as structured Markdown."
        ),
        img_a_b64=img_wf,
        img_b_b64=img_wf,
        accent_label="Output format",
        accent_val="Key points &middot; Timestamps &middot; Action items",
        accent_sub="Delivered to email, Notion, or Slack automatically",
        img_a_rot="-7deg",
        img_b_rot="4deg",
        img_a_filter="brightness(0.68) saturate(0.50)",
        img_b_filter="brightness(0.90) saturate(0.80)",
        product_color=PC,
    )

    phases = [
        ("01", "URL Ingestion",       "YouTube URL passed to n8n trigger. Video ID extracted."),
        ("02", "Transcript Fetch",    "YouTube transcript API retrieves full caption data with timestamps."),
        ("03", "AI Summarization",    "Claude AI processes transcript: key points, quotes, action items, chapters."),
        ("04", "Structured Delivery", "Summary formatted in Markdown and sent to Notion, email, or Slack."),
    ]
    arch_card = f"""
        <div style="padding:0 4px;">
            <div style="font-family:'JetBrains Mono',monospace;font-size:7.5px;letter-spacing:0.20em;text-transform:uppercase;color:{PC};margin-bottom:14px;">Output structure</div>
            <div style="font-family:'Poppins',sans-serif;font-size:26px;font-weight:800;color:{WHITE};letter-spacing:-0.03em;line-height:1.1;">TL;DR in<br>5 minutes.</div>
            <div style="font-family:'Inter',sans-serif;font-size:10.5px;font-weight:300;color:{DIM};margin-top:14px;line-height:1.6;">Summary, key quotes, timestamps, action items. Structured Markdown ready to paste anywhere.</div>
        </div>"""

    html2 = slide_arch(
        eyebrow="YouTube Summarizer &middot; Pipeline",
        title="Watch less.\nLearn more.",
        subtitle="2-hour video distilled in under 5 minutes. Timestamped, structured, and delivered automatically.",
        phases=phases,
        tools=["n8n", "Claude AI", "YouTube API", "Notion", "Gmail"],
        img_a_b64=img_wf,
        img_b_content=arch_card,
        product_color=PC,
    )

    html3 = slide_proof(
        eyebrow="YouTube Summarizer &middot; Output",
        hero_num="5",
        hero_label="Minute delivery",
        proofs=[
            ("Input",    "Any YouTube URL",     "Public videos with captions. Any length, any topic",     False),
            ("AI Model", "Claude AI",           "Prompt-engineered for structure: points, quotes, actions", False),
            ("Format",   "Structured Markdown", "Key points, timestamps, action items -- copy-paste ready", True),
            ("Delivery", "Multi-destination",   "Notion, email, Slack -- configured per workflow",          False),
        ],
        product_color=PC,
    )

    for t in [
        render_slide(html1, project, 1, out_dir),
        render_slide(html2, project, 2, out_dir),
        render_slide(html3, project, 3, out_dir),
    ]:
        await t


async def render_project_tiktok_performance(out_dir: Path):
    """TikTok Video Performance Automation"""
    project = "tiktok-performance"
    PC = "#EE1D52"  # TikTok signature pink-red

    img_wf = b64(ASSETS / "tiktok-performance.png")

    html1 = slide_hero(
        eyebrow="TikTok Performance Tracker &middot; Viral Video Ranker",
        stats=[
            ("100+", "Videos analyzed per run", False),
            ("Auto",  "Daily performance reports", True),
            ("0",     "Manual data exports", False),
        ],
        tagline_html=(
            "<b>Track. Rank. Optimize.</b><br>"
            "TikTok analytics pulled automatically,<br>"
            "ranked by viral potential, delivered daily."
        ),
        img_a_b64=img_wf,
        img_b_b64=img_wf,
        accent_label="Ranking signals",
        accent_val="Views, likes, shares, saves, comments",
        accent_sub="Weighted viral score per video &nbsp;&middot;&nbsp; Daily leaderboard",
        img_a_rot="-6deg",
        img_b_rot="5deg",
        img_a_filter="brightness(0.65) saturate(0.50)",
        img_b_filter="brightness(0.88) saturate(0.80)",
        product_color=PC,
    )

    phases = [
        ("01", "Account Monitoring",  "TikTok API pulls all recent video metrics on schedule."),
        ("02", "Viral Scoring",       "Weighted algorithm ranks videos by engagement velocity, not raw views."),
        ("03", "Pattern Extraction",  "Claude AI identifies what hooks, formats, and topics drove top performers."),
        ("04", "Daily Brief Delivery","Ranked leaderboard + content recommendations sent to email or Notion."),
    ]
    arch_card = f"""
        <div style="padding:0 4px;">
            <div style="font-family:'JetBrains Mono',monospace;font-size:7.5px;letter-spacing:0.20em;text-transform:uppercase;color:{PC};margin-bottom:14px;">Scoring model</div>
            <div style="font-family:'Poppins',sans-serif;font-size:26px;font-weight:800;color:{WHITE};letter-spacing:-0.03em;line-height:1.1;">Velocity,<br>not volume.</div>
            <div style="font-family:'Inter',sans-serif;font-size:10.5px;font-weight:300;color:{DIM};margin-top:14px;line-height:1.6;">Viral score weights early engagement rate over total views. Catches rising content before it peaks.</div>
        </div>"""

    html2 = slide_arch(
        eyebrow="TikTok Tracker &middot; How it works",
        title="Know what\nworks. Daily.",
        subtitle="Every video ranked. Winning patterns surfaced automatically. No dashboard to check.",
        phases=phases,
        tools=["n8n", "TikTok API", "Claude AI", "Google Sheets", "Gmail"],
        img_a_b64=img_wf,
        img_b_content=arch_card,
        product_color=PC,
    )

    html3 = slide_proof(
        eyebrow="TikTok Tracker &middot; Output",
        hero_num="1",
        hero_label="Daily automated report",
        proofs=[
            ("Analysis",   "100+ Videos",       "All account videos scored and ranked per daily run",      False),
            ("Signals",    "5 Metrics",          "Views, likes, shares, saves, comments weighted",          False),
            ("AI Layer",   "Pattern Detection",  "What hooks and formats drove the top 10% this week",      True),
            ("Delivery",   "Zero manual checks", "Leaderboard delivered to inbox without logging in",       False),
        ],
        product_color=PC,
    )

    for t in [
        render_slide(html1, project, 1, out_dir),
        render_slide(html2, project, 2, out_dir),
        render_slide(html3, project, 3, out_dir),
    ]:
        await t


async def render_project_kairos(out_dir: Path):
    """Kairos -- Football Value Bet Prediction Engine"""
    project = "kairos"
    PC = "#F59E0B"  # amber -- betting odds, Pinnacle precision aesthetic

    img_code = b64(ASSETS / "kairos-vscode-code.png")
    img_chat = b64(ASSETS / "kairos-chat-analysis.png")

    html1 = slide_hero(
        eyebrow="Value Bet Prediction Engine &middot; Football &middot; Python",
        stats=[
            ("4",      "Markets with edge detection",   False),
            ("Sharp",  "Pinnacle odds as reference",    False),
            ("Kelly",  "Position sizing algorithm",     True),
        ],
        tagline_html=(
            "<b>Statistical edge, not gut feel.</b><br>"
            "Poisson + Dixon-Coles vs Pinnacle sharp lines.<br>"
            "Kelly criterion staking. BET or SKIP in seconds."
        ),
        img_a_b64=img_code,
        img_b_b64=img_chat,
        accent_label="Stack",
        accent_val="Pure Python &middot; Statistical Modeling",
        accent_sub="No API fees &nbsp;&middot;&nbsp; Local computation &nbsp;&middot;&nbsp; Open source",
        img_a_rot="-7deg",
        img_b_rot="4deg",
        img_a_filter="brightness(0.65) saturate(0.55)",
        img_b_filter="brightness(0.88) saturate(0.80)",
        product_color=PC,
    )

    phases = [
        ("01", "Sharp-Line Comparison",   "Fetches Pinnacle odds as reference. Implied probability via no-vig formula."),
        ("02", "Poisson Probability Model","Dixon-Coles attack/defense ratings per team. True win/draw/lose probabilities."),
        ("03", "Value Detection",          "Model probability vs market implied. Edge above threshold = value bet flagged."),
        ("04", "Kelly Criterion Staking",  "Optimal stake sizing computed. Trap bets filtered. BET/SKIP/SPECULATIVE verdict."),
    ]
    arch_card = f"""
        <div style="padding:0 4px;">
            <div style="font-family:'JetBrains Mono',monospace;font-size:7.5px;letter-spacing:0.20em;text-transform:uppercase;color:{PC};margin-bottom:14px;">Market tier list</div>
            <div style="font-family:'Poppins',sans-serif;font-size:24px;font-weight:800;color:{WHITE};letter-spacing:-0.03em;line-height:1.15;">Sharp book<br>or no bet.</div>
            <div style="font-family:'Inter',sans-serif;font-size:10px;font-weight:300;color:{DIM};margin-top:14px;line-height:1.65;">
                1X2 / O&amp;U / Handicap / Double Chance fully checked.<br>
                GG/NG only when Pinnacle prices it.<br>
                Half-time / corners = no sharp line = skip.
            </div>
        </div>"""

    html2 = slide_arch(
        eyebrow="Kairos &middot; How the edge is found",
        title="Beat the\nbook or fold.",
        subtitle="Kairos refuses to guess. Every market checked against Pinnacle. No sharp reference means no bet.",
        phases=phases,
        tools=["Python", "Pinnacle API", "Dixon-Coles", "Kelly Criterion", "Poisson"],
        img_a_b64=img_code,
        img_b_content=arch_card,
        product_color=PC,
    )

    html3 = slide_proof(
        eyebrow="Kairos &middot; System design",
        hero_num="4",
        hero_label="Markets with verified edge",
        proofs=[
            ("Model",     "Poisson + D-C",       "Dixon-Coles attack/defense ratings. True outcome probabilities",  False),
            ("Reference", "Pinnacle Lines",       "Sharpest book in the industry used as implied-prob baseline",    False),
            ("Markets",   "1X2, O/U, HC, DC",    "Four markets with Pinnacle sharp lines. Others auto-skipped",    True),
            ("Staking",   "Kelly Criterion",      "Position size scales with edge size. Trap bets filtered at source", False),
        ],
        product_color=PC,
    )

    for t in [
        render_slide(html1, project, 1, out_dir),
        render_slide(html2, project, 2, out_dir),
        render_slide(html3, project, 3, out_dir),
    ]:
        await t


async def render_project_yct_exam_nav(out_dir: Path):
    """YCT Exam Nav -- Yabatech University Deployment"""
    project = "yct-exam-nav"
    PC = "#60A5FA"  # light blue -- academic, institutional, Next.js

    img_admin   = b64(ASSETS / "yct-admin-full-view.png")    # full admin, 7 depts, 119 exams
    img_student = b64(ASSETS / "yct-student-timetable.png")  # student UI with seat number
    img_seats   = b64(ASSETS / "yct-seat-assignments.png")   # seat assignments modal

    html1 = slide_hero(
        eyebrow="University Deployment &middot; Yabatech CS Dept &middot; Live System",
        stats=[
            ("119",  "Exams scheduled",       False),
            ("7",    "Departments managed",   False),
            ("Live", "Production deployment", True),
        ],
        tagline_html=(
            "<b>Zero scheduling conflicts guaranteed.</b><br>"
            "DSatur graph coloring. Every student has a seat,<br>"
            "a hall, and a navigation button to find it."
        ),
        img_a_b64=img_admin,
        img_b_b64=img_student,
        accent_label="Institution",
        accent_val="Yaba College of Technology",
        accent_sub="7 departments &nbsp;&middot;&nbsp; Computer Science to Nutrition &nbsp;&middot;&nbsp; Vercel deployed",
        img_a_rot="-6deg",
        img_b_rot="4.5deg",
        img_a_filter="brightness(0.70) saturate(0.55)",
        img_b_filter="brightness(0.90) saturate(0.85)",
        product_color=PC,
    )

    phases = [
        ("01", "DSatur Graph Coloring",  "Courses as graph nodes. Student conflicts as edges. DSatur assigns time slots with zero clashes."),
        ("02", "Hall and Seat Allocation","Exam halls loaded with capacity constraints. Seat number assigned per student per course."),
        ("03", "Student Dashboard",       "Personal timetable: hall name, seat number, exam time, navigate-to-hall button."),
        ("04", "Admin Management",        "Admin generates and publishes timetables across 7 departments. Seat export available."),
    ]
    arch_card = f"""
        <div style="padding:0 4px;">
            <div style="font-family:'JetBrains Mono',monospace;font-size:7.5px;letter-spacing:0.20em;text-transform:uppercase;color:{PC};margin-bottom:14px;">Seat assignments</div>
            <div style="font-family:'Poppins',sans-serif;font-size:26px;font-weight:800;color:{WHITE};letter-spacing:-0.03em;line-height:1.1;">Every student.<br>Every seat.</div>
            <div style="font-family:'Inter',sans-serif;font-size:10px;font-weight:300;color:{DIM};margin-top:14px;line-height:1.65;">
                Real student records. Multiple buildings.<br>
                SCI-CPLX, NEW-BLDG, SMBS-OLD.<br>
                Assigned automatically from course enrollment data.
            </div>
        </div>"""

    html2 = slide_arch(
        eyebrow="YCT Exam Nav &middot; Architecture",
        title="Zero clashes.\nEvery seat.",
        subtitle="DSatur graph coloring. Dijkstra navigation. Full-stack TypeScript. Deployed at Yabatech.",
        phases=phases,
        tools=["Next.js", "TypeScript", "Supabase", "PostgreSQL", "Vercel", "DSatur"],
        img_a_b64=img_seats,
        img_b_content=arch_card,
        product_color=PC,
    )

    html3 = slide_proof(
        eyebrow="YCT Exam Nav &middot; Deployment results",
        hero_num="119",
        hero_label="Exams, zero conflicts",
        proofs=[
            ("Departments", "7 Schools",         "Agric Tech, CS, Food Tech, Hospitality, Leisure, Nutrition, Polymer",    False),
            ("Algorithm",   "DSatur Coloring",   "Graph coloring with saturation degree. Optimal slots, minimum conflicts", False),
            ("Deployment",  "Live at Yabatech",  "admin@yabatech-examportal.com &middot; real students, real halls, real seats",  True),
            ("Stack",       "Next.js + Supabase","Full-stack TypeScript. Auth, RBAC, real-time updates. Vercel deployed",    False),
        ],
        product_color=PC,
    )

    for t in [
        render_slide(html1, project, 1, out_dir),
        render_slide(html2, project, 2, out_dir),
        render_slide(html3, project, 3, out_dir),
    ]:
        await t


async def render_project_hephzibah_os(out_dir: Path):
    """Hephzibah OS -- AI Cold Outreach Intelligence System"""
    project = "hephzibah-os"
    PC = "#229ED9"  # Telegram blue -- the approval gate that makes the system human

    img_vscode = b64(ASSETS / "hephzi-os-vscode.png")
    img_brain  = b64(ASSETS / "hephzi-os-brain-graph.png")

    html1 = slide_hero(
        eyebrow="AI Outreach Intelligence &middot; Multi-source Prospecting",
        stats=[
            ("5",    "Autonomous background daemons", False),
            ("3",    "Lead discovery sources",        False),
            ("24/7", "Always-on operation",           True),
        ],
        tagline_html=(
            "<b>The OS that runs the freelancer.</b><br>"
            "Gmail. Telegram. Google Maps. DesignRush.<br>"
            "Human approves. System executes."
        ),
        img_a_b64=img_vscode,
        img_b_b64=img_brain,
        accent_label="Architecture",
        accent_val="Brain &middot; Daemons &middot; Approval Flow",
        accent_sub="Email watcher &nbsp;&middot;&nbsp; Job watcher &nbsp;&middot;&nbsp; Follow-up engine &nbsp;&middot;&nbsp; Prospector",
        img_a_rot="-8deg",
        img_b_rot="5deg",
        img_a_filter="brightness(0.65) saturate(0.50)",
        img_b_filter="brightness(0.80) saturate(0.65)",
        product_color=PC,
    )

    phases = [
        ("01", "Lead Discovery",       "Playwright scrapes Google Maps and DesignRush. Emails extracted, gaps identified per site."),
        ("02", "Outreach Generation",  "Claude AI writes personalized emails per prospect: specific gap, specific tool, specific timeline."),
        ("03", "Human Approval Gate",  "Telegram card arrives on phone. Tap Approve or Skip. Approved emails sent immediately."),
        ("04", "Reply Detection",       "Gmail watcher scans for replies. Telegram alert fires. /prep-call triggered automatically."),
    ]
    arch_card = f"""
        <div style="padding:0 4px;">
            <div style="font-family:'JetBrains Mono',monospace;font-size:7.5px;letter-spacing:0.20em;text-transform:uppercase;color:{PC};margin-bottom:14px;">Brain graph</div>
            <div style="font-family:'Poppins',sans-serif;font-size:24px;font-weight:800;color:{WHITE};letter-spacing:-0.03em;line-height:1.15;">300+ linked<br>memory nodes.</div>
            <div style="font-family:'Inter',sans-serif;font-size:10px;font-weight:300;color:{DIM};margin-top:14px;line-height:1.65;">
                Obsidian-based persistent brain. Clients, prospects,<br>
                proposals, patterns, and decisions stored as<br>
                linked markdown. Git-synced. Private. Always current.
            </div>
        </div>"""

    html2 = slide_arch(
        eyebrow="Hephzibah OS &middot; Architecture",
        title="The brain\nthat never sleeps.",
        subtitle="Five daemons run on Windows Task Scheduler. Telegram delivers decisions. Nothing ships without a human tap.",
        phases=phases,
        tools=["Python", "Claude AI", "Playwright", "Gmail API", "Telegram Bot", "Obsidian"],
        img_a_b64=img_brain,
        img_b_content=arch_card,
        product_color=PC,
    )

    html3 = slide_proof(
        eyebrow="Hephzibah OS &middot; System capabilities",
        hero_num="5",
        hero_label="Daemons, always running",
        proofs=[
            ("Prospecting", "Maps + DesignRush",   "Two-source US lead discovery. Playwright extracts emails from live sites",   False),
            ("Outreach",    "AI-personalized",     "Claude writes emails naming the specific gap found on each prospect's site", False),
            ("Approval",    "Telegram gate",       "Zero emails sent without human tap. Fraud-safe by design",                  True),
            ("Memory",      "300+ Brain nodes",    "Persistent Obsidian brain. Clients, patterns, proposals. Git-synced",       False),
        ],
        product_color=PC,
    )

    for t in [
        render_slide(html1, project, 1, out_dir),
        render_slide(html2, project, 2, out_dir),
        render_slide(html3, project, 3, out_dir),
    ]:
        await t


# ── HephFlow ──────────────────────────────────────────────────────────────────

async def _render_synthetic_png(html_content: str, width: int, height: int) -> str:
    """Render an HTML string to PNG and return as a base64 data URI."""
    tmp = Path(__file__).parent.parent / "outputs" / "assets" / "_hf_tmp_synth.html"
    tmp.write_text(html_content, encoding="utf-8")
    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch()
            page = await browser.new_page(
                viewport={"width": width, "height": height},
                device_scale_factor=2,
            )
            await page.goto(f"file:///{tmp.resolve().as_posix()}")
            await page.wait_for_load_state("domcontentloaded")
            await page.wait_for_timeout(600)
            png_bytes = await page.screenshot(full_page=False)
            await browser.close()
        return "data:image/png;base64," + base64.b64encode(png_bytes).decode()
    finally:
        tmp.unlink(missing_ok=True)


async def render_project_hephflow(out_dir: Path):
    """HephFlow -- Offline Push-to-Talk Voice Dictation Tool for Windows"""
    project = "hephflow"
    PC = "#E84040"  # red -- the recording dot, the app's core visual signal

    # ── Synthetic source images ───────────────────────────────────────────────

    CODE_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { width:700px; height:880px; background:#1E1E2E; font-family:'JetBrains Mono','Consolas',monospace; font-size:13.5px; overflow:hidden; }
.bar { height:36px; background:#181825; display:flex; align-items:center; padding:0 14px; gap:8px; border-bottom:1px solid #313244; }
.dot { width:12px; height:12px; border-radius:50%; flex-shrink:0; }
.tab { color:#CDD6F4; padding:7px 18px; font-size:12px; border-top:2px solid #E84040; background:#1E1E2E; margin-left:16px; }
.crumb { font-size:11px; color:#6C7086; padding:5px 20px; border-bottom:1px solid #313244; }
.code { padding:10px 0; line-height:1.85; }
.ln-row { display:flex; padding:0 8px 0 4px; }
.ln { color:#45475A; width:38px; text-align:right; margin-right:22px; flex-shrink:0; font-size:12px; }
.k{color:#CBA6F7} .f{color:#89B4FA} .s{color:#A6E3A1} .c{color:#6C7086}
.v{color:#CDD6F4} .m{color:#FAB387} .p{color:#F5C2E7} .n{color:#F38BA8}
.bl { height:24.9px; }
</style></head><body>
<div class="bar">
  <div class="dot" style="background:#F38BA8"></div>
  <div class="dot" style="background:#F9E2AF"></div>
  <div class="dot" style="background:#A6E3A1"></div>
  <div class="tab">hephflow.py</div>
</div>
<div class="crumb">src &gt; hephflow &gt; hephflow.py &nbsp; &nbsp; Python</div>
<div class="code">
<div class="ln-row"><span class="ln">1</span><span class="k">import</span> <span class="m">whisper</span></div>
<div class="ln-row"><span class="ln">2</span><span class="k">import</span> <span class="m">pyaudio</span></div>
<div class="ln-row"><span class="ln">3</span><span class="k">import</span> <span class="m">numpy</span> <span class="k">as</span> <span class="n">np</span></div>
<div class="ln-row"><span class="ln">4</span><span class="k">import</span> <span class="m">pyperclip</span></div>
<div class="ln-row"><span class="ln">5</span><span class="k">from</span> <span class="m">pynput</span> <span class="k">import</span> <span class="n">keyboard</span></div>
<div class="bl"></div>
<div class="ln-row"><span class="ln">7</span><span class="c"># Loaded once at startup &mdash; stays resident</span></div>
<div class="ln-row"><span class="ln">8</span><span class="v">model</span> <span class="v">=</span> <span class="m">whisper</span><span class="v">.</span><span class="f">load_model</span><span class="v">(</span><span class="s">"base.en"</span><span class="v">)</span></div>
<div class="bl"></div>
<div class="ln-row"><span class="ln">10</span><span class="v">recording</span> <span class="v">=</span> <span class="k">False</span></div>
<div class="ln-row"><span class="ln">11</span><span class="v">audio_buffer</span> <span class="v">= []</span></div>
<div class="bl"></div>
<div class="ln-row"><span class="ln">13</span><span class="k">def</span> <span class="f">on_key_press</span><span class="v">(</span><span class="p">key</span><span class="v">):</span></div>
<div class="ln-row"><span class="ln">14</span><span class="v">&nbsp;&nbsp;&nbsp;&nbsp;</span><span class="k">global</span> <span class="v">recording, audio_buffer</span></div>
<div class="ln-row"><span class="ln">15</span><span class="v">&nbsp;&nbsp;&nbsp;&nbsp;</span><span class="k">if</span> <span class="v">key</span> <span class="v">==</span> <span class="n">HOTKEY</span> <span class="k">and not</span> <span class="v">recording:</span></div>
<div class="ln-row"><span class="ln">16</span><span class="v">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;recording</span> <span class="v">=</span> <span class="k">True</span></div>
<div class="ln-row"><span class="ln">17</span><span class="v">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;audio_buffer</span> <span class="v">= []</span></div>
<div class="ln-row"><span class="ln">18</span><span class="v">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;pill</span><span class="v">.</span><span class="f">show</span><span class="v">(state</span><span class="v">=</span><span class="s">"recording"</span><span class="v">)</span></div>
<div class="bl"></div>
<div class="ln-row"><span class="ln">20</span><span class="k">def</span> <span class="f">on_key_release</span><span class="v">(</span><span class="p">key</span><span class="v">):</span></div>
<div class="ln-row"><span class="ln">21</span><span class="v">&nbsp;&nbsp;&nbsp;&nbsp;</span><span class="k">global</span> <span class="v">recording</span></div>
<div class="ln-row"><span class="ln">22</span><span class="v">&nbsp;&nbsp;&nbsp;&nbsp;</span><span class="k">if</span> <span class="v">key</span> <span class="v">==</span> <span class="n">HOTKEY</span> <span class="k">and</span> <span class="v">recording:</span></div>
<div class="ln-row"><span class="ln">23</span><span class="v">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;recording</span> <span class="v">=</span> <span class="k">False</span></div>
<div class="ln-row"><span class="ln">24</span><span class="v">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;pill</span><span class="v">.</span><span class="f">show</span><span class="v">(state</span><span class="v">=</span><span class="s">"transcribing"</span><span class="v">)</span></div>
<div class="bl"></div>
<div class="ln-row"><span class="ln">26</span><span class="v">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;audio</span> <span class="v">=</span> <span class="m">np</span><span class="v">.</span><span class="f">frombuffer</span><span class="v">(</span></div>
<div class="ln-row"><span class="ln">27</span><span class="v">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</span><span class="s">b""</span><span class="v">.</span><span class="f">join</span><span class="v">(audio_buffer),</span></div>
<div class="ln-row"><span class="ln">28</span><span class="v">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;dtype</span><span class="v">=</span><span class="m">np</span><span class="v">.float32</span></div>
<div class="ln-row"><span class="ln">29</span><span class="v">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;)</span></div>
<div class="ln-row"><span class="ln">30</span><span class="v">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;result</span> <span class="v">=</span> <span class="v">model</span><span class="v">.</span><span class="f">transcribe</span><span class="v">(audio)</span></div>
<div class="ln-row"><span class="ln">31</span><span class="v">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;pyperclip</span><span class="v">.</span><span class="f">copy</span><span class="v">(result[</span><span class="s">"text"</span><span class="v">])</span></div>
<div class="ln-row"><span class="ln">32</span><span class="v">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;keyboard</span><span class="v">.</span><span class="f">press_and_release</span><span class="v">(</span><span class="s">"ctrl+v"</span><span class="v">)</span></div>
<div class="ln-row"><span class="ln">33</span><span class="v">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;pill</span><span class="v">.</span><span class="f">hide</span><span class="v">()</span></div>
</div>
</body></html>"""

    PILL_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { width:660px; height:840px; background:#1E1E2E; position:relative; overflow:hidden;
       font-family:'JetBrains Mono','Consolas',monospace; }
.bg { position:absolute; inset:0; padding:46px 28px; font-size:12px; line-height:1.9;
      color:rgba(205,214,244,0.17); overflow:hidden; }
.pill { position:absolute; bottom:96px; left:50%; transform:translateX(-50%);
        display:flex; align-items:center; gap:9px; padding:0 16px 0 12px; height:34px;
        background:rgba(14,14,24,0.97);
        border:1px solid rgba(232,64,64,0.55); border-radius:50px;
        box-shadow:0 0 0 1px rgba(232,64,64,0.18),0 10px 40px rgba(0,0,0,0.8),0 0 32px rgba(232,64,64,0.18);
        white-space:nowrap; }
.dot { width:9px; height:9px; border-radius:50%; background:#E84040;
       box-shadow:0 0 8px rgba(232,64,64,0.7); }
.wav { display:flex; align-items:center; gap:3px; }
.b { width:2.5px; border-radius:2px; background:rgba(232,64,64,0.6); }
.tm { font-size:12px; font-weight:500; color:rgba(255,255,255,0.55); letter-spacing:0.06em; }
</style></head><body>
<div class="bg">
import whisper<br>import pyaudio, numpy as np<br>import pyperclip<br>
from pynput import keyboard<br><br>
model = whisper.load_model("base.en")<br><br>
def on_key_press(key):<br>
&nbsp;&nbsp;global recording<br>
&nbsp;&nbsp;if key == HOTKEY and not recording:<br>
&nbsp;&nbsp;&nbsp;&nbsp;recording = True<br>
&nbsp;&nbsp;&nbsp;&nbsp;pill.show(state="recording")<br><br>
def on_key_release(key):<br>
&nbsp;&nbsp;if key == HOTKEY and recording:<br>
&nbsp;&nbsp;&nbsp;&nbsp;recording = False<br>
&nbsp;&nbsp;&nbsp;&nbsp;audio = np.frombuffer(b"".join(buffer), dtype=np.float32)<br>
&nbsp;&nbsp;&nbsp;&nbsp;result = model.transcribe(audio)<br>
&nbsp;&nbsp;&nbsp;&nbsp;pyperclip.copy(result["text"])<br>
&nbsp;&nbsp;&nbsp;&nbsp;keyboard.press_and_release("ctrl+v")<br>
&nbsp;&nbsp;&nbsp;&nbsp;pill.hide()
</div>
<div class="pill">
    <div class="dot"></div>
    <div class="wav">
        <div class="b" style="height:4px"></div><div class="b" style="height:11px"></div>
        <div class="b" style="height:6px"></div><div class="b" style="height:15px"></div>
        <div class="b" style="height:5px"></div><div class="b" style="height:11px"></div>
        <div class="b" style="height:7px"></div><div class="b" style="height:13px"></div>
        <div class="b" style="height:4px"></div>
    </div>
    <div class="tm">0:08</div>
</div>
</body></html>"""

    print("  [hephflow] Generating synthetic source images...")
    img_code = await _render_synthetic_png(CODE_HTML, 700, 880)
    img_pill = await _render_synthetic_png(PILL_HTML, 660, 840)
    print("  [hephflow] Source images ready.")

    # ── Slide 1 — Hero ────────────────────────────────────────────────────────

    html1 = slide_hero(
        eyebrow="Voice Dictation Tool &middot; Windows &middot; Python &middot; Whisper",
        stats=[
            ("0",       "API calls required &middot; fully offline",         False),
            ("Whisper", "On-device speech-to-text engine",                   True),
            ("Push",    "To talk &middot; release to paste anywhere",        False),
        ],
        tagline_html=(
            "<b>Offline voice dictation for any Windows app.</b><br>"
            "Hold hotkey. Speak. Release. Text pasted instantly.<br>"
            "No internet. No API key. No window switching."
        ),
        img_a_b64=img_code,
        img_b_b64=img_pill,
        accent_label="Stack",
        accent_val="Python &middot; Whisper &middot; Windows API",
        accent_sub="Fully offline &nbsp;&middot;&nbsp; 0 cloud calls &nbsp;&middot;&nbsp; CPU-only inference",
        img_a_rot="-7deg",
        img_b_rot="4deg",
        img_a_filter="brightness(0.68) saturate(0.55)",
        img_b_filter="brightness(0.90) saturate(0.85)",
        product_color=PC,
    )

    # ── Slide 2 — Architecture ────────────────────────────────────────────────

    phases = [
        ("01", "Global Hotkey Hook",    "Win+Alt+H captured by pynput listener. Pill appears immediately. PyAudio stream opens at 16kHz mono."),
        ("02", "Local Audio Capture",   "Float32 audio chunks streamed to in-memory buffer. No disk writes. Recording ends on key release."),
        ("03", "Whisper Transcription", "openai-whisper base.en runs CPU-only inference locally. 74M params. Result in under 3 seconds."),
        ("04", "Clipboard Paste",       "Text copied via pyperclip. Ctrl+V fired programmatically. Active cursor position unchanged. Pill hides."),
    ]
    arch_card_html = f"""
        <div style="padding:0 4px;">
            <div style="font-family:'JetBrains Mono',monospace;font-size:7.5px;letter-spacing:0.20em;text-transform:uppercase;color:{PC};margin-bottom:14px;">How it works</div>
            <div style="font-family:'Poppins',sans-serif;font-size:22px;font-weight:800;color:{WHITE};letter-spacing:-0.03em;line-height:1.15;">Speak once.<br>Type never.</div>
            <div style="font-family:'Inter',sans-serif;font-size:10px;font-weight:300;color:{DIM};margin-top:14px;line-height:1.65;">
                Hold Win+Alt+H. Speak naturally.<br>
                Release the key. Text appears at cursor.<br>
                No window focus change. No cloud latency.
            </div>
        </div>"""

    html2 = slide_arch(
        eyebrow="HephFlow &middot; How it works",
        title="Speak once.\nType never.",
        subtitle="HephFlow captures voice on key hold, transcribes locally with Whisper, and pastes directly into the active cursor position. Zero cloud calls. Works in any app.",
        phases=phases,
        tools=["Python", "OpenAI Whisper", "PyAudio", "pynput", "pyperclip", "Tkinter"],
        img_a_b64=img_code,
        img_b_content=arch_card_html,
        product_color=PC,
    )

    # ── Slide 3 — System Design ───────────────────────────────────────────────

    html3 = slide_proof(
        eyebrow="HephFlow &middot; System design",
        hero_num="3",
        hero_label="Pill states. Zero API calls. Instant paste.",
        proofs=[
            ("Engine",   "Whisper base.en",   "74M params · English · CPU inference · no GPU · no API key · ships with model file",    False),
            ("Capture",  "PyAudio Stream",     "16kHz mono · float32 · key-gated buffer · stops on release · no disk writes",           False),
            ("Trigger",  "Win+Alt+H",          "Global hotkey via pynput · works in any focused app · no window switch required",       True),
            ("Output",   "Clipboard Paste",    "pyperclip.copy() + programmatic Ctrl+V · cursor stays in original position",            False),
        ],
        product_color=PC,
    )

    for coro in [
        render_slide(html1, project, 1, out_dir),
        render_slide(html2, project, 2, out_dir),
        render_slide(html3, project, 3, out_dir),
    ]:
        await coro


# ── Main ──────────────────────────────────────────────────────────────────────

ALL_PROJECTS = {
    "avatar-doctor":        render_project_avatar_doctor,
    "multilingual":         render_project_multilingual,
    "noryx-studio":         render_project_noryx,
    "personal-assistant":   render_project_personal_assistant,
    "youtube-summarizer":   render_project_youtube_summarizer,
    "tiktok-performance":   render_project_tiktok_performance,
    "kairos":               render_project_kairos,
    "yct-exam-nav":         render_project_yct_exam_nav,
    "hephzibah-os":         render_project_hephzibah_os,
    "hephflow":             render_project_hephflow,
}


async def main():
    parser = argparse.ArgumentParser(description="Portfolio batch renderer")
    parser.add_argument("--project", choices=list(ALL_PROJECTS.keys()), help="Render one project only")
    parser.add_argument("--out", default=str(OUT), help="Output directory")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    projects_to_render = (
        {args.project: ALL_PROJECTS[args.project]} if args.project else ALL_PROJECTS
    )

    print(f"\nRendering {len(projects_to_render)} project(s) to {out_dir}\n")

    for name, fn in projects_to_render.items():
        print(f"[{name}]")
        await fn(out_dir)

    print(f"\nDone. Files in {out_dir}")


if __name__ == "__main__":
    asyncio.run(main())
