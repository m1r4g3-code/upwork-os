"""
thumbnail_renderer.py — Hephzibah YouTube Thumbnail Generator

Renders a 1280x720 YouTube thumbnail PNG using Playwright (2x device scale
= 2560x1440 crisp output). Photo is embedded as base64 — no CDN, no web fonts,
no external requests. Follows the same pattern as portfolio_renderer.py.

Usage:
  python scripts/thumbnail_renderer.py --photo PATH [options]

Required:
  --photo PATH        Path to the presenter photo (jpg/png)

Optional:
  --line1 TEXT        First headline word  (default: AUTOMATE)
  --line2 TEXT        Second word in lemon (default: YOUR)
  --line3 TEXT        Third headline word  (default: WORKFLOWS)
  --stack TEXT        Tech stack pill line (default: n8n · Claude AI · Python)
  --channel TEXT      Channel pill label   (default: Hephzibah)
  --out PATH          Output path or dir   (default: Desktop)

Examples:
  python scripts/thumbnail_renderer.py --photo "C:/Users/HomePC/Pictures/ife final.jpeg"
  python scripts/thumbnail_renderer.py --photo "C:/Users/HomePC/Pictures/ife final.jpeg" --out outputs/assets/yt-thumb.png
"""

import argparse
import asyncio
import base64
import os
import sys
import tempfile

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("ERROR: playwright not installed. Run: pip install playwright && playwright install chromium")
    sys.exit(1)

try:
    import numpy as np
    from PIL import Image
    _PIL_OK = True
except ImportError:
    _PIL_OK = False


def darken_white_background(photo_path: str) -> str:
    """
    Detect near-white studio background and darken it to near-black,
    leaving skin tones untouched. Returns path to a processed temp PNG.

    Detection: pixels with high brightness (V > 0.78) AND low saturation
    (S < 0.22) are treated as background. Blend darkens them smoothly
    toward #0A0A0A without touching skin tones (high S, moderate V).
    """
    if not _PIL_OK:
        return photo_path

    img = Image.open(photo_path).convert("RGB")
    arr = np.array(img, dtype=np.float32) / 255.0

    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]

    # Per-pixel HSV components (no import needed — compute inline)
    cmax = np.maximum(np.maximum(r, g), b)   # Value
    cmin = np.minimum(np.minimum(r, g), b)
    delta = cmax - cmin
    s = np.where(cmax > 0, delta / cmax, 0)  # Saturation
    v = cmax                                   # Value (brightness)

    # Background confidence: bright AND desaturated
    # Wider ramp to catch the grey vignette transition zone in studio shots.
    # Face skin tones have S > 0.30 so they are safe from this range.
    v_factor = np.clip((v - 0.50) / 0.20, 0.0, 1.0)   # full at v >= 0.70
    s_factor = np.clip((0.28 - s) / 0.18, 0.0, 1.0)   # full at s <= 0.10
    bg_factor = v_factor * s_factor

    # Darken background to target (near-black matching #0A0A0A = 0.039)
    target = 0.04
    new_r = r * (1.0 - bg_factor) + target * bg_factor
    new_g = g * (1.0 - bg_factor) + target * bg_factor
    new_b = b * (1.0 - bg_factor) + target * bg_factor

    result = np.stack([new_r, new_g, new_b], axis=-1)
    result = np.clip(result * 255, 0, 255).astype(np.uint8)

    out_img = Image.fromarray(result)
    tmp = tempfile.mktemp(suffix=".png")
    out_img.save(tmp, format="PNG")
    print(f"[thumbnail_renderer] Background darkened → {tmp}")
    return tmp

DESKTOP = os.path.join(os.path.expanduser("~"), "Desktop")
W, H = 1280, 720


def image_to_b64(path: str) -> str:
    ext = os.path.splitext(path)[1].lower().lstrip(".")
    mime = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp",
    }.get(ext, "image/jpeg")
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime};base64,{b64}"


def build_html(img_src: str, line1: str, line2: str, line3: str,
               stack: str, channel: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  *, *::before, *::after {{ margin: 0; padding: 0; box-sizing: border-box; }}

  html, body {{
    width: {W}px;
    height: {H}px;
    background: #0A0A0A;
    overflow: hidden;
    display: flex;
    flex-shrink: 0;
  }}

  /* ── Photo zone: left 44% with diagonal clip ─── */
  .photo-zone {{
    position: relative;
    width: 44%;
    height: {H}px;
    background: #0C0C0C;
    flex-shrink: 0;
    clip-path: polygon(0 0, 88% 0, 100% 100%, 0 100%);
    overflow: hidden;
  }}

  .photo-img {{
    position: absolute;
    width: 130%;
    height: 100%;
    object-fit: cover;
    object-position: 38% 8%;
    /* background already darkened in preprocessing — just mild cinematic grade */
    filter: contrast(1.08) saturate(0.90) brightness(1.05);
    z-index: 1;
  }}

  /* right edge: blend into the dark text zone */
  .photo-overlay {{
    position: absolute;
    inset: 0;
    background: linear-gradient(90deg,
      transparent 35%,
      rgba(0,0,0,0.45) 76%,
      rgba(0,0,0,0.85) 100%
    );
    z-index: 2;
    pointer-events: none;
  }}

  /* bottom vignette */
  .photo-vignette-bottom {{
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 25%;
    background: linear-gradient(0deg, rgba(10,10,10,0.68) 0%, transparent 100%);
    z-index: 3;
    pointer-events: none;
  }}

  /* ── Diagonal lemon slash ───────────────────── */
  /*
    photo-zone width = 44% * 1280 = 563.2px
    clip top-right   = 88% * 563.2 = 495.6px  (from left edge of thumbnail)
    clip bottom-right = 563.2px
    center           = (495.6 + 563.2) / 2 = 529.4px = 41.36%
    skew angle       = arctan(67.6 / 720) ≈ 5.37deg  → skewX(-5.4deg)
  */
  .slash {{
    position: absolute;
    left: calc(41.4% - 2.5px);
    top: -10px;
    width: 5px;
    height: 740px;
    background: linear-gradient(180deg,
      rgba(232,255,58,0.0) 0%,
      #E8FF3A 8%,
      #E8FF3A 92%,
      rgba(232,255,58,0.0) 100%
    );
    transform: skewX(-5.4deg);
    transform-origin: top center;
    z-index: 15;
    box-shadow: 0 0 12px 1px rgba(232,255,58,0.26), 0 0 3px 0 rgba(232,255,58,0.48);
  }}

  /* ── Text zone ──────────────────────────────── */
  .text-zone {{
    flex: 1;
    height: {H}px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    padding: 52px 60px 52px 54px;
    position: relative;
    z-index: 10;
  }}

  /* Channel pill */
  .channel-pill {{
    display: inline-flex;
    align-items: center;
    gap: 9px;
    border: 1.5px solid rgba(232, 255, 58, 0.28);
    padding: 6px 16px 6px 12px;
    border-radius: 100px;
    margin-bottom: 28px;
    width: fit-content;
  }}

  .channel-dot {{
    width: 7px;
    height: 7px;
    background: #E8FF3A;
    border-radius: 50%;
    flex-shrink: 0;
  }}

  .channel-name {{
    font-family: Arial, Helvetica, sans-serif;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: rgba(232, 255, 58, 0.6);
    line-height: 1;
  }}

  /* Headline */
  .headline {{ display: flex; flex-direction: column; margin-bottom: 30px; }}

  .w-line1 {{
    font-family: "Arial Black", "Arial Bold", Arial, Helvetica, sans-serif;
    font-size: 98px;
    font-weight: 900;
    line-height: 0.84;
    letter-spacing: -0.03em;
    text-transform: uppercase;
    color: #F5F5F5;
    white-space: nowrap;
  }}

  .w-your-row {{
    display: flex;
    justify-content: flex-end;
    padding-right: 4px;
    margin: 8px 0 3px;
  }}

  .w-line2 {{
    font-family: "Arial Black", "Arial Bold", Arial, Helvetica, sans-serif;
    font-size: 56px;
    font-weight: 900;
    line-height: 1;
    letter-spacing: -0.01em;
    text-transform: uppercase;
    color: #E8FF3A;
    white-space: nowrap;
  }}

  .w-line3 {{
    font-family: "Arial Black", "Arial Bold", Arial, Helvetica, sans-serif;
    font-size: 84px;
    font-weight: 900;
    line-height: 0.86;
    letter-spacing: -0.03em;
    text-transform: uppercase;
    color: #F5F5F5;
    white-space: nowrap;
  }}

  /* Stack line */
  .stack {{
    font-family: Arial, Helvetica, sans-serif;
    font-size: 14px;
    font-weight: 400;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #484848;
    margin-top: 2px;
  }}

  /* Right lemon bar */
  .right-bar {{
    position: absolute;
    right: 0;
    top: 0;
    width: 9px;
    height: {H}px;
    background: #E8FF3A;
    z-index: 20;
    flex-shrink: 0;
  }}

  /* Hairline rules */
  .rule-top {{
    position: absolute;
    top: 0;
    left: 42%;
    right: 8px;
    height: 2px;
    background: linear-gradient(90deg, transparent, rgba(232,255,58,0.15) 70%, rgba(232,255,58,0.06));
    z-index: 5;
  }}

  .rule-bottom {{
    position: absolute;
    bottom: 0;
    left: 42%;
    right: 8px;
    height: 2px;
    background: linear-gradient(90deg, transparent, rgba(232,255,58,0.15) 70%, rgba(232,255,58,0.06));
    z-index: 5;
  }}

  /* Wordmark */
  .wordmark {{
    position: absolute;
    bottom: 18px;
    right: 22px;
    font-family: Arial, Helvetica, sans-serif;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.24em;
    text-transform: uppercase;
    color: rgba(255,255,255,0.09);
    z-index: 12;
  }}

</style>
</head>
<body>

  <!-- Photo zone -->
  <div class="photo-zone">
    <img class="photo-img" src="{img_src}" alt="{channel}">
    <div class="photo-overlay"></div>
    <div class="photo-vignette-bottom"></div>
  </div>

  <!-- Lemon diagonal slash -->
  <div class="slash"></div>

  <!-- Text zone -->
  <div class="text-zone">
    <div class="channel-pill">
      <span class="channel-dot"></span>
      <span class="channel-name">{channel}</span>
    </div>

    <div class="headline">
      <div class="w-line1">{line1}</div>
      <div class="w-your-row">
        <div class="w-line2">{line2}</div>
      </div>
      <div class="w-line3">{line3}</div>
    </div>

    <div class="stack">{stack}</div>
  </div>

  <!-- Decorative elements -->
  <div class="rule-top"></div>
  <div class="rule-bottom"></div>
  <div class="right-bar"></div>
  <div class="wordmark">{channel}</div>

</body>
</html>"""


async def render(html: str, out_path: str) -> None:
    tmp = out_path.replace(".png", "_tmp.html")
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
        await page.wait_for_timeout(400)
        await page.screenshot(path=out_path, full_page=False)
        await browser.close()
    os.remove(tmp)
    size_kb = os.path.getsize(out_path) // 1024
    print(f"[thumbnail_renderer] Saved {out_path} ({size_kb} KB)")


def resolve_out(out_arg: str, channel: str) -> str:
    slug = channel.lower().replace(" ", "-")
    if os.path.isdir(out_arg) or out_arg.lower() in ("desktop", ""):
        base = DESKTOP if out_arg.lower() in ("desktop", "") else out_arg
        return os.path.join(base, f"yt-thumbnail-{slug}.png")
    if not out_arg.endswith(".png"):
        out_arg += ".png"
    return out_arg


def main():
    parser = argparse.ArgumentParser(description="Hephzibah YouTube Thumbnail renderer")
    parser.add_argument("--photo",   required=True, help="Path to presenter photo")
    parser.add_argument("--line1",   default="AUTOMATE",              help="Headline word 1 (white)")
    parser.add_argument("--line2",   default="YOUR",                  help="Headline word 2 (lemon, right-aligned)")
    parser.add_argument("--line3",   default="WORKFLOWS",             help="Headline word 3 (white)")
    parser.add_argument("--stack",   default="n8n · Claude AI · Python", help="Stack pill line")
    parser.add_argument("--channel", default="Hephzibah",             help="Channel pill label")
    parser.add_argument("--out",     default="Desktop",               help="Output dir or file path")
    args = parser.parse_args()

    if not os.path.exists(args.photo):
        print(f"ERROR: photo not found: {args.photo}")
        sys.exit(1)

    print(f"[thumbnail_renderer] Loading photo from {args.photo}...")
    processed = darken_white_background(args.photo)
    img_src = image_to_b64(processed)
    if processed != args.photo and os.path.exists(processed):
        os.remove(processed)

    html = build_html(
        img_src=img_src,
        line1=args.line1,
        line2=args.line2,
        line3=args.line3,
        stack=args.stack,
        channel=args.channel,
    )

    out_path = resolve_out(args.out, args.channel)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    asyncio.run(render(html, out_path))
    print(f"[thumbnail_renderer] Done — {W}x{H}px (2x device scale = {W*2}x{H*2} crisp PNG)")


if __name__ == "__main__":
    main()
