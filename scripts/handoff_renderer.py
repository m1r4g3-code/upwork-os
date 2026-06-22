"""
handoff_renderer.py — SERAMAN system handoff document renderer.
Usage: python scripts/handoff_renderer.py <data.json> <output.pdf>

Brand: #1C1917 matte dark · #D4E832 lemon · #EDE5CF warm parchment
Fonts: Poppins (display) · Inter (body) · JetBrains Mono (technical)
Images: rounded corners (apple card style, border-radius 18px)
"""

import json, os, sys, base64
from pathlib import Path
from playwright.sync_api import sync_playwright

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600;700;800&family=Inter:ital,wght@0,300;0,400;0,500;1,300&family=JetBrains+Mono:wght@400;700&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg:        #EDE5CF;
  --ink:       #1C1712;
  --secondary: #7A6B56;
  --border:    #CEBF9A;
  --surface:   #E4D9C0;
  --dark:      #1C1917;
  --dark-2:    #252118;
  --dark-3:    #2D2720;
  --lemon:     #D4E832;
  --lemon-dim: rgba(212,232,50,0.12);
  --white:     #F8F4EC;
  --red:       #E84832;
  --green:     #32E87A;
}

html { font-size: 11.5pt; height: fit-content; }

body {
  background: var(--bg);
  color: var(--ink);
  font-family: 'Inter', -apple-system, sans-serif;
  font-weight: 300;
  line-height: 1.65;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
  width: 794px;
  height: fit-content;
}

/* ── TOPBAR ── */
.doc-topbar {
  background: var(--dark);
  border-bottom: 3px solid var(--lemon);
  padding: 0 20mm;
  height: 14mm;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.doc-topbar-brand {
  font-family: 'JetBrains Mono', monospace;
  font-size: 9pt;
  font-weight: 700;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--white);
}
.doc-topbar-right {
  font-size: 7pt;
  color: rgba(255,255,255,0.4);
  letter-spacing: 0.03em;
}

/* ── COVER ── */
.cover {
  background: var(--dark);
  min-height: 270mm;
  padding: 0 20mm 20mm;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  position: relative;
  overflow: hidden;
}
.cover::before {
  content:''; position:absolute;
  right:-45mm; top:10mm;
  width:170mm; height:170mm;
  border:1px solid rgba(255,255,255,0.03);
  border-radius:50%;
}
.cover::after {
  content:''; position:absolute;
  right:-70mm; top:-30mm;
  width:240mm; height:240mm;
  border:1px solid rgba(255,255,255,0.018);
  border-radius:50%;
}
.cover-badge {
  font-family: 'JetBrains Mono', monospace;
  font-size: 6.5pt;
  color: rgba(255,255,255,0.28);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  margin-bottom: 5mm;
}
.cover-title {
  font-family: 'Poppins', sans-serif;
  font-size: 30pt;
  font-weight: 800;
  color: var(--white);
  line-height: 1.08;
  letter-spacing: -0.025em;
  margin-bottom: 4mm;
  max-width: 148mm;
}
.cover-subtitle {
  font-size: 10pt;
  color: rgba(255,255,255,0.45);
  font-weight: 300;
  margin-bottom: 9mm;
}
.cover-tag {
  display: inline-block;
  background: var(--lemon);
  color: var(--dark);
  font-family: 'Inter', sans-serif;
  font-size: 6pt;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  padding: 3px 10px;
  margin-bottom: 9mm;
}
.cover-divider {
  border: none;
  border-top: 1px solid rgba(255,255,255,0.09);
  margin-bottom: 5mm;
}
.cover-meta {
  display: grid;
  grid-template-columns: repeat(4, auto);
  gap: 0 10mm;
}
.cover-meta-item { display: flex; flex-direction: column; gap: 1.5mm; }
.cover-meta-label {
  font-size: 5pt;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: rgba(255,255,255,0.25);
  font-family: 'JetBrains Mono', monospace;
}
.cover-meta-value {
  font-size: 8pt;
  color: rgba(255,255,255,0.7);
  font-weight: 400;
}

/* ── BODY SECTIONS ── */
.section {
  padding: 14mm 20mm;
  border-bottom: 1px solid var(--border);
}
.section:last-child { border-bottom: none; }

.section-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 6pt;
  font-weight: 700;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--secondary);
  margin-bottom: 3mm;
}
.section > h2 {
  font-family: 'Poppins', sans-serif;
  font-size: 18pt;
  font-weight: 700;
  color: var(--ink);
  line-height: 1.15;
  letter-spacing: -0.02em;
  margin-bottom: 5mm;
}
.section > p {
  font-size: 10pt;
  color: var(--ink);
  line-height: 1.7;
  margin-bottom: 4mm;
  max-width: 148mm;
}

/* ── PIPELINE FLOW ── */
.pipeline-flow {
  display: flex;
  align-items: center;
  gap: 0;
  flex-wrap: wrap;
  margin: 6mm 0;
}
.pipeline-step {
  background: var(--dark);
  color: var(--white);
  font-family: 'JetBrains Mono', monospace;
  font-size: 7pt;
  font-weight: 700;
  letter-spacing: 0.06em;
  padding: 5px 10px;
  white-space: nowrap;
}
.pipeline-arrow {
  color: var(--lemon);
  font-size: 10pt;
  font-weight: 700;
  padding: 0 4px;
}

/* ── STEPS (numbered walkthrough) ── */
.steps { display: flex; flex-direction: column; gap: 4mm; margin-top: 5mm; }
.step {
  display: grid;
  grid-template-columns: 10mm 1fr;
  gap: 4mm;
  align-items: start;
}
.step-num {
  width: 9mm; height: 9mm;
  background: var(--lemon);
  color: var(--dark);
  font-family: 'Poppins', sans-serif;
  font-size: 9pt;
  font-weight: 800;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.step-body { padding-top: 1mm; }
.step-title {
  font-family: 'Inter', sans-serif;
  font-size: 9pt;
  font-weight: 600;
  color: var(--ink);
  margin-bottom: 1mm;
}
.step-desc {
  font-size: 9pt;
  color: var(--secondary);
  line-height: 1.55;
}
.step-url {
  font-family: 'JetBrains Mono', monospace;
  font-size: 8pt;
  color: var(--dark);
  background: var(--lemon-dim);
  border-left: 2px solid var(--lemon);
  padding: 3px 7px;
  margin-top: 2mm;
  display: inline-block;
}

/* ── WORKFLOW CARDS (2-col grid) ── */
.workflow-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 5mm;
  margin-top: 5mm;
}
.workflow-card {
  background: var(--dark);
  padding: 6mm;
  position: relative;
}
.workflow-card-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 5.5pt;
  font-weight: 700;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--lemon);
  margin-bottom: 1.5mm;
}
.workflow-card-title {
  font-family: 'Poppins', sans-serif;
  font-size: 10pt;
  font-weight: 700;
  color: var(--white);
  margin-bottom: 2mm;
}
.workflow-card-desc {
  font-size: 8pt;
  color: rgba(255,255,255,0.5);
  line-height: 1.55;
}

/* ── IMAGES (apple card style) ── */
.doc-image {
  width: 100%;
  border-radius: 18px;
  overflow: hidden;
  margin: 5mm 0;
  box-shadow: 0 4px 24px rgba(0,0,0,0.18), 0 1px 4px rgba(0,0,0,0.10);
  display: block;
}
.doc-image img {
  width: 100%;
  display: block;
  border-radius: 18px;
}
.doc-image-caption {
  font-family: 'JetBrains Mono', monospace;
  font-size: 6.5pt;
  color: var(--secondary);
  letter-spacing: 0.04em;
  margin-top: 2mm;
  margin-bottom: 4mm;
}

/* ── IMAGE PAIR (side by side) ── */
.image-pair {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4mm;
  margin: 5mm 0;
}
.image-pair .doc-image { margin: 0; }

/* ── SHEET TABLE ── */
.sheet-legend {
  display: flex;
  flex-direction: column;
  gap: 3mm;
  margin-top: 5mm;
}
.sheet-row {
  display: grid;
  grid-template-columns: 24mm 1fr;
  gap: 5mm;
  align-items: start;
  padding: 4mm 5mm;
  background: var(--surface);
}
.sheet-tab {
  font-family: 'JetBrains Mono', monospace;
  font-size: 7.5pt;
  font-weight: 700;
  color: var(--dark);
  padding: 2px 7px;
  background: var(--lemon);
  display: inline-block;
  white-space: nowrap;
}
.sheet-desc {
  font-size: 9pt;
  color: var(--secondary);
  line-height: 1.55;
}

/* ── EMAIL ALERTS ── */
.alert-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 5mm;
  margin-top: 5mm;
}
.alert-card {
  background: var(--dark-3);
  padding: 5mm 6mm;
}
.alert-dot {
  display: inline-block;
  width: 8px; height: 8px;
  border-radius: 50%;
  margin-right: 5px;
  vertical-align: middle;
}
.alert-dot.green { background: var(--green); }
.alert-dot.red   { background: var(--red); }
.alert-title {
  font-family: 'JetBrains Mono', monospace;
  font-size: 7.5pt;
  font-weight: 700;
  color: var(--white);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-bottom: 2mm;
}
.alert-desc {
  font-size: 8.5pt;
  color: rgba(255,255,255,0.5);
  line-height: 1.5;
}

/* ── TECH CALLOUT (dark box for engineering depth) ── */
.tech-callout {
  background: var(--dark);
  padding: 8mm 9mm;
  margin: 5mm 0;
  position: relative;
}
.tech-callout::before {
  content: '';
  position: absolute;
  left: 0; top: 0; bottom: 0;
  width: 3px;
  background: var(--lemon);
}
.tech-callout-title {
  font-family: 'JetBrains Mono', monospace;
  font-size: 7pt;
  font-weight: 700;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--lemon);
  margin-bottom: 3mm;
}
.tech-callout-body {
  font-size: 9pt;
  color: rgba(255,255,255,0.65);
  line-height: 1.65;
}
.tech-callout-body strong { color: rgba(255,255,255,0.9); font-weight: 500; }
.tech-callout-body ul { padding-left: 4mm; list-style: none; }
.tech-callout-body ul li { margin-bottom: 1.5mm; }
.tech-callout-body ul li::before { content: '→ '; color: var(--lemon); font-family: 'JetBrains Mono', monospace; font-size: 8pt; }

/* ── COST TABLE ── */
.cost-table { width: 100%; border-collapse: collapse; margin-top: 5mm; }
.cost-table thead tr {
  background: var(--dark);
  color: var(--lemon);
  font-family: 'JetBrains Mono', monospace;
  font-size: 6.5pt;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}
.cost-table thead th { padding: 4mm 5mm; text-align: left; }
.cost-table tbody tr { border-bottom: 1px solid var(--border); }
.cost-table tbody tr:last-child { border-bottom: none; }
.cost-table tbody td { padding: 3.5mm 5mm; font-size: 9pt; }
.cost-table tbody td:first-child { font-weight: 400; color: var(--ink); }
.cost-table tbody td:last-child { font-family: 'JetBrains Mono', monospace; font-size: 8.5pt; color: var(--secondary); }
.cost-total-row td { background: var(--lemon-dim); font-weight: 600 !important; color: var(--ink) !important; }

/* ── CREDENTIAL CARDS ── */
.cred-grid { display: flex; flex-direction: column; gap: 3mm; margin-top: 5mm; }
.cred-row {
  display: grid;
  grid-template-columns: 42mm 1fr;
  gap: 5mm;
  align-items: center;
  padding: 3.5mm 5mm;
  background: var(--surface);
  border-left: 2px solid var(--border);
}
.cred-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 7.5pt;
  font-weight: 700;
  color: var(--dark);
}
.cred-value {
  font-size: 9pt;
  color: var(--secondary);
}

/* ── FOOTER ── */
.doc-footer {
  background: var(--dark);
  padding: 6mm 20mm;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 3px solid var(--lemon);
}
.doc-footer-left {
  font-family: 'JetBrains Mono', monospace;
  font-size: 7pt;
  color: rgba(255,255,255,0.3);
  letter-spacing: 0.06em;
}
.doc-footer-right {
  font-size: 7pt;
  color: rgba(255,255,255,0.25);
}
"""


def img_to_b64(path: str) -> str:
    """Convert image file to base64 data URI."""
    p = Path(path)
    if not p.exists():
        return ""
    ext = p.suffix.lower().lstrip(".")
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png"}.get(ext, "image/png")
    data = base64.b64encode(p.read_bytes()).decode()
    return f"data:{mime};base64,{data}"


def render_image(path: str, caption: str = "") -> str:
    b64 = img_to_b64(path)
    if not b64:
        return ""
    cap = f'<div class="doc-image-caption">↑ {caption}</div>' if caption else ""
    return f'<div class="doc-image"><img src="{b64}" alt="{caption}"></div>{cap}'


def render_image_pair(left_path, left_cap, right_path, right_cap) -> str:
    def _img(path, cap):
        b64 = img_to_b64(path)
        if not b64:
            return ""
        c = f'<div class="doc-image-caption">↑ {cap}</div>' if cap else ""
        return f'<div class="doc-image"><img src="{b64}" alt="{cap}"></div>{c}'
    return f'<div class="image-pair">{_img(left_path, left_cap)}{_img(right_path, right_cap)}</div>'


def build_html(d: dict) -> str:
    meta = d.get("meta", {})
    cover = d.get("cover", {})
    sections = d.get("sections", [])

    # ── Topbar
    topbar = f"""
    <div class="doc-topbar">
      <span class="doc-topbar-brand">{meta.get('brand', 'SERAMAN')}</span>
      <span class="doc-topbar-right">{meta.get('doc_type', 'System Handoff')} · {meta.get('version', 'v1.0')} · {meta.get('date', '')}</span>
    </div>"""

    # ── Cover
    cover_meta_html = ""
    for item in cover.get("meta_items", []):
        cover_meta_html += f"""
        <div class="cover-meta-item">
          <span class="cover-meta-label">{item['label']}</span>
          <span class="cover-meta-value">{item['value']}</span>
        </div>"""

    cover_html = f"""
    <div class="cover">
      <div class="cover-badge">{cover.get('badge', '')}</div>
      <div class="cover-title">{cover.get('title', '')}</div>
      <div class="cover-subtitle">{cover.get('subtitle', '')}</div>
      <div class="cover-tag">{cover.get('tag', 'SYSTEM HANDOFF')}</div>
      <hr class="cover-divider">
      <div class="cover-meta">{cover_meta_html}</div>
    </div>"""

    # ── Sections
    body_html = ""
    for sec in sections:
        kind = sec.get("type", "text")
        label = f'<div class="section-label">{sec["label"]}</div>' if sec.get("label") else ""
        title = f'<h2>{sec["title"]}</h2>' if sec.get("title") else ""
        body_html += f'<div class="section">{label}{title}'

        if kind == "text":
            for para in sec.get("paragraphs", []):
                body_html += f'<p>{para}</p>'

        elif kind == "pipeline":
            for para in sec.get("paragraphs", []):
                body_html += f'<p>{para}</p>'
            steps_html = ""
            for s in sec.get("flow", []):
                steps_html += f'<span class="pipeline-step">{s}</span><span class="pipeline-arrow">→</span>'
            steps_html = steps_html.rstrip('<span class="pipeline-arrow">→</span>')
            body_html += f'<div class="pipeline-flow">{steps_html}</div>'
            for para in sec.get("paragraphs_after", []):
                body_html += f'<p>{para}</p>'

        elif kind == "steps":
            for para in sec.get("paragraphs", []):
                body_html += f'<p>{para}</p>'
            steps_html = ""
            for i, s in enumerate(sec.get("steps", []), 1):
                url_html = f'<div class="step-url">{s["url"]}</div>' if s.get("url") else ""
                steps_html += f"""
                <div class="step">
                  <div class="step-num">{i}</div>
                  <div class="step-body">
                    <div class="step-title">{s['title']}</div>
                    <div class="step-desc">{s['desc']}</div>
                    {url_html}
                  </div>
                </div>"""
            body_html += f'<div class="steps">{steps_html}</div>'

        elif kind == "workflow_cards":
            for para in sec.get("paragraphs", []):
                body_html += f'<p>{para}</p>'
            cards_html = ""
            for c in sec.get("cards", []):
                cards_html += f"""
                <div class="workflow-card">
                  <div class="workflow-card-label">{c['label']}</div>
                  <div class="workflow-card-title">{c['title']}</div>
                  <div class="workflow-card-desc">{c['desc']}</div>
                </div>"""
            body_html += f'<div class="workflow-grid">{cards_html}</div>'
            img = sec.get("image")
            if img:
                body_html += render_image(img["path"], img.get("caption", ""))

        elif kind == "image_section":
            for para in sec.get("paragraphs", []):
                body_html += f'<p>{para}</p>'
            img = sec.get("image")
            if img:
                body_html += render_image(img["path"], img.get("caption", ""))
            for para in sec.get("paragraphs_after", []):
                body_html += f'<p>{para}</p>'

        elif kind == "image_pair_section":
            for para in sec.get("paragraphs", []):
                body_html += f'<p>{para}</p>'
            imgs = sec.get("images", [])
            if len(imgs) >= 2:
                body_html += render_image_pair(
                    imgs[0]["path"], imgs[0].get("caption", ""),
                    imgs[1]["path"], imgs[1].get("caption", "")
                )
            elif len(imgs) == 1:
                body_html += render_image(imgs[0]["path"], imgs[0].get("caption", ""))

        elif kind == "sheet_legend":
            for para in sec.get("paragraphs", []):
                body_html += f'<p>{para}</p>'
            img = sec.get("image")
            if img:
                body_html += render_image(img["path"], img.get("caption", ""))
            rows_html = ""
            for r in sec.get("sheets", []):
                rows_html += f"""
                <div class="sheet-row">
                  <div><span class="sheet-tab">{r['tab']}</span></div>
                  <div class="sheet-desc">{r['desc']}</div>
                </div>"""
            body_html += f'<div class="sheet-legend">{rows_html}</div>'

        elif kind == "alerts":
            for para in sec.get("paragraphs", []):
                body_html += f'<p>{para}</p>'
            alerts_html = ""
            for a in sec.get("alerts", []):
                dot_class = "green" if a["color"] == "green" else "red"
                alerts_html += f"""
                <div class="alert-card">
                  <div class="alert-title">
                    <span class="alert-dot {dot_class}"></span>{a['title']}
                  </div>
                  <div class="alert-desc">{a['desc']}</div>
                </div>"""
            body_html += f'<div class="alert-grid">{alerts_html}</div>'
            imgs = sec.get("images", [])
            if len(imgs) >= 2:
                body_html += render_image_pair(
                    imgs[0]["path"], imgs[0].get("caption", ""),
                    imgs[1]["path"], imgs[1].get("caption", "")
                )
            elif len(imgs) == 1:
                body_html += render_image(imgs[0]["path"], imgs[0].get("caption", ""))

        elif kind == "tech":
            for para in sec.get("paragraphs", []):
                body_html += f'<p>{para}</p>'
            for box in sec.get("callouts", []):
                items_html = "".join(f"<li>{i}</li>" for i in box.get("items", []))
                list_html = f"<ul>{items_html}</ul>" if items_html else ""
                body_html += f"""
                <div class="tech-callout">
                  <div class="tech-callout-title">{box['title']}</div>
                  <div class="tech-callout-body">{box['body']}{list_html}</div>
                </div>"""

        elif kind == "cost":
            for para in sec.get("paragraphs", []):
                body_html += f'<p>{para}</p>'
            rows_html = ""
            for r in sec.get("rows", []):
                total_class = ' class="cost-total-row"' if r.get("total") else ""
                rows_html += f'<tr{total_class}><td>{r["item"]}</td><td>{r["cost"]}</td></tr>'
            body_html += f"""
            <table class="cost-table">
              <thead><tr><th>Service</th><th>Cost</th></tr></thead>
              <tbody>{rows_html}</tbody>
            </table>"""
            for para in sec.get("paragraphs_after", []):
                body_html += f'<p style="margin-top:4mm">{para}</p>'

        elif kind == "credentials":
            for para in sec.get("paragraphs", []):
                body_html += f'<p>{para}</p>'
            rows_html = ""
            for r in sec.get("items", []):
                rows_html += f"""
                <div class="cred-row">
                  <div class="cred-label">{r['label']}</div>
                  <div class="cred-value">{r['value']}</div>
                </div>"""
            body_html += f'<div class="cred-grid">{rows_html}</div>'

        body_html += "</div>"

    # ── Footer
    footer = f"""
    <div class="doc-footer">
      <span class="doc-footer-left">{meta.get('footer_left', 'SERAMAN · Confidential')}</span>
      <span class="doc-footer-right">Delivered by {meta.get('delivered_by', 'Emmanuel Adekoya')}</span>
    </div>"""

    return f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>{CSS}</style>
</head><body>
{topbar}
{cover_html}
{body_html}
{footer}
</body></html>"""


def render_pdf(html: str, output_path: str):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 794, "height": 800})
        page.set_content(html, wait_until="networkidle")
        # Measure true content height — use footer's bottom edge, not scrollHeight
        # scrollHeight includes viewport minimum; getBoundingClientRect gives exact content bottom
        full_height = page.evaluate("""() => {
            const els = document.querySelectorAll('body > *');
            let max = 0;
            els.forEach(el => {
                const b = el.getBoundingClientRect().bottom;
                if (b > max) max = b;
            });
            return Math.ceil(max) + 1;
        }""")
        page.pdf(
            path=output_path,
            width="794px",
            height=f"{full_height}px",
            print_background=True,
            margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
        )
        browser.close()
    print(f"PDF saved: {output_path}")


def main():
    if len(sys.argv) < 3:
        print("Usage: python scripts/handoff_renderer.py <data.json> <output.pdf>")
        sys.exit(1)
    data_path, output_path = sys.argv[1], sys.argv[2]
    with open(data_path, encoding="utf-8") as f:
        data = json.load(f)
    html = build_html(data)
    render_pdf(html, output_path)


if __name__ == "__main__":
    main()
