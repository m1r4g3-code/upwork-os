"""
render_card.py — Hephzibah LinkedIn Brand Card Renderer

Usage:
  python scripts/render_card.py --image PATH [options]

Required:
  --image PATH        Path to the hero image (jpg/png)

Content (all optional — defaults to placeholders):
  --eyebrow TEXT      Top label, e.g. "SavvySox × Hephzibah — AI Product Video"
  --quote TEXT        Pull quote inside the card
  --stats TEXT        Stats line, e.g. "13 videos · 2 days · All approved"
  --role1 TEXT        First attribution role label
  --name1 TEXT        First attribution name
  --role2 TEXT        Second attribution role label
  --name2 TEXT        Second attribution name

Output:
  --theme THEME       light | dark | both   (default: both)
  --out PATH          Output file or directory (default: Desktop)
                      If directory: saves card_light.png / card_dark.png
                      If file: saves that exact file (only works with single theme)

Examples:
  python scripts/render_card.py --image outputs/assets/savvysox_frame.jpg \\
    --eyebrow "SavvySox x Hephzibah — AI Product Video" \\
    --quote "Make the socks float in space." \\
    --stats "13 videos · 2 days · All approved" \\
    --role1 "Creative direction" --name1 "Adelaja Obanijesu" \\
    --role2 "Automation design" --name2 "Emmanuel Adekoya" \\
    --theme both

  python scripts/render_card.py --image path/to/img.jpg --theme dark --out Desktop
"""

import argparse
import asyncio
import base64
import os
import sys

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("ERROR: playwright not installed. Run: pip install playwright && playwright install chromium")
    sys.exit(1)


DESKTOP = os.path.join(os.path.expanduser("~"), "Desktop")


def image_to_b64(path: str) -> str:
    ext = os.path.splitext(path)[1].lower().lstrip(".")
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}.get(ext, "image/jpeg")
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime};base64,{b64}"


def build_html(img_src: str, theme: str, eyebrow: str, quote: str, stats: str,
               role1: str, name1: str, role2: str, name2: str) -> str:

    if theme == "light":
        page_bg   = "#E2DDD0"
        card_bg   = "#EDE8DC"
        card_shad = "0 2px 6px rgba(0,0,0,0.05), 0 10px 28px rgba(0,0,0,0.09), 0 28px 56px rgba(0,0,0,0.07)"
        card_bord = "rgba(0,0,0,0.06)"
        eyebrow_c = "#7A7468"
        quote_c   = "#18140E"
        rule_c    = "rgba(0,0,0,0.09)"
        role_c    = "#706860"
        name_c    = "#26201A"
        stats_block = f"""<div class="stats-pill">
          <span>{stats}</span>
        </div>"""
        brand_block = """<div class="brand-line">
          <span class="brand-chip">HEPHZIBAH</span>
          <span class="brand-year">&copy;&nbsp;2026</span>
        </div>"""
        theme_css = """
        .stats-pill { display: block; margin-bottom: 18px; }
        .stats-pill span {
          font-family: 'JetBrains Mono', monospace;
          font-weight: 500;
          font-size: 9px;
          letter-spacing: 0.18em;
          text-transform: uppercase;
          color: #E8FF3A;
          background: #18140E;
          border-radius: 8px;
          padding: 8px 14px;
          display: inline-block;
          line-height: 1;
        }
        .brand-chip {
          font-family: 'JetBrains Mono', monospace;
          font-size: 8px;
          letter-spacing: 0.28em;
          text-transform: uppercase;
          color: #E8FF3A;
          background: #18140E;
          border-radius: 6px;
          padding: 5px 11px;
          display: inline-block;
          line-height: 1;
        }
        .brand-year {
          font-family: 'JetBrains Mono', monospace;
          font-size: 8px;
          letter-spacing: 0.18em;
          color: #9A9080;
        }
        """
    else:
        page_bg   = "#060608"
        card_bg   = "#0C0C12"
        card_shad = "0 2px 8px rgba(0,0,0,0.3), 0 12px 32px rgba(0,0,0,0.4), 0 32px 64px rgba(0,0,0,0.3)"
        card_bord = "rgba(255,255,255,0.08)"
        eyebrow_c = "#7A7890"
        quote_c   = "#E8E4DC"
        rule_c    = "rgba(255,255,255,0.08)"
        role_c    = "#6A6880"
        name_c    = "#C0BCB8"
        stats_block = f"""<div class="stats">{stats}</div>"""
        brand_block = """<div class="brand-line">
          <span class="brand-name">HEPHZIBAH</span>
          <span class="brand-year">&copy;&nbsp;2026</span>
        </div>"""
        theme_css = """
        .stats {
          font-family: 'Inter', sans-serif;
          font-weight: 500;
          font-size: 8.5px;
          letter-spacing: 0.28em;
          text-transform: uppercase;
          color: #E8FF3A;
          margin-bottom: 18px;
        }
        .brand-name {
          font-family: 'JetBrains Mono', monospace;
          font-size: 7.5px;
          letter-spacing: 0.36em;
          text-transform: uppercase;
          color: #E8FF3A;
        }
        .brand-year {
          font-family: 'JetBrains Mono', monospace;
          font-size: 8px;
          letter-spacing: 0.2em;
          color: #3A3850;
        }
        """

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=Poppins:ital,wght@0,600;0,700;1,600;1,700&family=Inter:wght@300;400;500&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html, body {{
    width: 540px; height: 675px;
    background: {page_bg};
    overflow: hidden;
    display: flex;
    align-items: flex-start;
    justify-content: center;
    padding: 24px;
  }}
  .card {{
    width: 492px;
    background: {card_bg};
    border-radius: 24px;
    border: 1px solid {card_bord};
    box-shadow: {card_shad};
    padding: 24px 24px 22px;
    display: flex;
    flex-direction: column;
  }}
  .eyebrow {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 8px;
    letter-spacing: 0.28em;
    text-transform: uppercase;
    color: {eyebrow_c};
    margin-bottom: 14px;
  }}
  .img-wrap {{
    width: 100%;
    height: 296px;
    border-radius: 14px;
    overflow: hidden;
    margin-bottom: 18px;
  }}
  .img-wrap img {{
    width: 100%; height: 100%;
    object-fit: cover;
    object-position: center 22%;
    filter: contrast(0.88) brightness(1.05) saturate(0.82);
    display: block;
  }}
  .quote {{
    font-family: 'Poppins', sans-serif;
    font-style: italic;
    font-weight: 700;
    font-size: 15px;
    line-height: 1.5;
    color: {quote_c};
    letter-spacing: -0.01em;
    margin-bottom: 11px;
  }}
  .rule {{ height: 1px; background: {rule_c}; margin-bottom: 15px; }}
  .attribution {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    row-gap: 7px;
    margin-bottom: 15px;
  }}
  .attr-role {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 7.5px;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: {role_c};
    align-self: center;
  }}
  .attr-name {{
    font-family: 'Inter', sans-serif;
    font-weight: 400;
    font-size: 10.5px;
    color: {name_c};
    text-align: right;
    align-self: center;
  }}
  .brand-line {{
    border-top: 1px solid {rule_c};
    padding-top: 13px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}
  {theme_css}
</style>
</head>
<body>
<div class="card">
  <div class="eyebrow">{eyebrow}</div>
  <div class="img-wrap"><img src="{img_src}" /></div>
  <p class="quote">&ldquo;{quote}&rdquo;</p>
  {stats_block}
  <div class="rule"></div>
  <div class="attribution">
    <span class="attr-role">{role1}</span>
    <span class="attr-name">{name1}</span>
    <span class="attr-role">{role2}</span>
    <span class="attr-name">{name2}</span>
  </div>
  {brand_block}
</div>
</body>
</html>"""


async def render_theme(html: str, theme: str, out_path: str) -> None:
    tmp = out_path.replace(".png", f"_{theme}_tmp.html")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(html)
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(
            viewport={"width": 540, "height": 675},
            device_scale_factor=2
        )
        await page.goto(f"file:///{tmp.replace(os.sep, '/')}")
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(800)
        await page.screenshot(path=out_path, full_page=False)
        await browser.close()
    os.remove(tmp)
    size_kb = os.path.getsize(out_path) // 1024
    print(f"[render_card] Saved {out_path} ({size_kb} KB)")


def resolve_out(out_arg: str, theme: str) -> str:
    if os.path.isdir(out_arg) or out_arg.lower() in ("desktop", ""):
        base = DESKTOP if out_arg.lower() in ("desktop", "") else out_arg
        return os.path.join(base, f"card_{theme}.png")
    # treat as exact file path
    if not out_arg.endswith(".png"):
        out_arg += ".png"
    return out_arg


def main():
    parser = argparse.ArgumentParser(description="Hephzibah LinkedIn card renderer")
    parser.add_argument("--image",   required=True,  help="Path to hero image")
    parser.add_argument("--eyebrow", default="Hephzibah Studio — Project Card")
    parser.add_argument("--quote",   default="We built the system. Not just the process.")
    parser.add_argument("--stats",   default="Delivered on time · All approved")
    parser.add_argument("--role1",   default="Creative direction")
    parser.add_argument("--name1",   default="Adelaja Obanijesu")
    parser.add_argument("--role2",   default="Automation design")
    parser.add_argument("--name2",   default="Emmanuel Adekoya")
    parser.add_argument("--theme",   default="both", choices=["light", "dark", "both"])
    parser.add_argument("--out",     default="Desktop", help="Output dir or file path")
    args = parser.parse_args()

    if not os.path.exists(args.image):
        print(f"ERROR: image not found: {args.image}")
        sys.exit(1)

    print(f"[render_card] Loading image from {args.image}...")
    img_src = image_to_b64(args.image)

    themes = ["light", "dark"] if args.theme == "both" else [args.theme]

    async def run():
        for theme in themes:
            html = build_html(
                img_src=img_src,
                theme=theme,
                eyebrow=args.eyebrow,
                quote=args.quote,
                stats=args.stats,
                role1=args.role1,
                name1=args.name1,
                role2=args.role2,
                name2=args.name2,
            )
            out_path = resolve_out(args.out, theme)
            await render_theme(html, theme, out_path)

    asyncio.run(run())
    print("[render_card] Done.")


if __name__ == "__main__":
    main()
