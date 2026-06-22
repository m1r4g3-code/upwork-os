"""
Proposal PDF renderer — Hephzibah brand / Terminal Precision.
Usage: python scripts/proposal_renderer.py <data.json> <output.pdf>

Brand: #1C1917 matte dark · #D4E832 lemon · #EDE5CF warm parchment
Fonts: Poppins (display) · Inter (body) · JetBrains Mono (technical)
Output: single-page continuous PDF (A4 width, dynamic height — no page breaks)
"""

import json, os, sys, tempfile
from playwright.sync_api import sync_playwright

# ── CSS ─────────────────────────────────────────────────────────────────────
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
  --lemon:     #D4E832;
  --lemon-dim: rgba(212,232,50,0.14);
  --white:     #F8F4EC;
}

html { font-size: 11.5pt; }

body {
  background: var(--bg);
  color: var(--ink);
  font-family: 'Inter', -apple-system, sans-serif;
  font-weight: 300;
  line-height: 1.65;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
  width: 794px;
}

/* ─ TOP BAR (static — built into HTML, not Playwright header template) ─ */
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
  color: #F8F4EC;
}
.doc-topbar-right {
  font-size: 7pt;
  color: rgba(255,255,255,0.45);
  letter-spacing: 0.03em;
}

/* ─ COVER ─ */
.cover {
  background: var(--dark);
  height: 283mm;
  padding: 0 20mm 18mm;
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

.cover-subtitle {
  font-family: 'JetBrains Mono', monospace;
  font-size: 6.5pt;
  font-weight: 400;
  color: rgba(255,255,255,0.28);
  letter-spacing: 0.06em;
  margin-bottom: 5mm;
}

.cover-title {
  font-family: 'Poppins', sans-serif;
  font-size: 30pt;
  font-weight: 800;
  color: var(--white);
  line-height: 1.08;
  letter-spacing: -0.025em;
  margin-bottom: 5mm;
  max-width: 140mm;
}

.cover-phase {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8mm;
}

.cover-phase-tag {
  background: var(--lemon);
  color: var(--dark);
  font-family: 'Inter', sans-serif;
  font-size: 6pt;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  padding: 3px 9px;
}

.cover-phase-label {
  font-size: 7pt;
  color: rgba(255,255,255,0.3);
  font-weight: 300;
}

.cover-divider {
  border: none;
  border-top: 1px solid rgba(255,255,255,0.09);
  margin-bottom: 5mm;
}

/* Cover meta grid */
.cover-meta {
  display: grid;
  grid-template-columns: repeat(4, auto);
  gap: 0 10mm;
}
.cover-meta-item {
  display: flex;
  flex-direction: column;
  gap: 1.5mm;
}
.cover-meta-label {
  font-size: 5pt;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: rgba(255,255,255,0.2);
  font-weight: 500;
}
.cover-meta-value {
  font-size: 7.5pt;
  color: rgba(255,255,255,0.5);
  font-weight: 300;
}
.cover-meta-value.status-ready {
  color: #4ADE80;
  font-weight: 500;
}

/* ─ DOC FOOTER ─ */
.doc-footer {
  background: var(--surface);
  border-top: 1px solid var(--border);
  padding: 4mm 20mm;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8mm;
}
.doc-footer span {
  font-size: 5.5pt;
  color: var(--secondary);
  letter-spacing: 0.03em;
}

/* ─ CONTENT ─ */
.content { padding: 16mm 20mm 12mm; }

/* ─ SECTIONS ─ */
.section { margin-top: 20mm; padding-bottom: 14mm; border-bottom: 1px solid var(--border); }
.section:first-child { margin-top: 0; }
.section:last-child { border-bottom: none; }

.section-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 6pt;
  font-weight: 700;
  letter-spacing: 0.1em;
  color: var(--secondary);
  margin-bottom: 2.5mm;
  display: block;
}

.section-rule {
  height: 1px;
  background: var(--border);
  margin-bottom: 5mm;
}

.section > h2 {
  font-family: 'Poppins', sans-serif;
  font-size: 18pt;
  font-weight: 800;
  line-height: 1.15;
  letter-spacing: -0.02em;
  margin-bottom: 6mm;
  color: var(--ink);
}

/* ─ BODY TYPE ─ */
p {
  font-size: 10pt;
  line-height: 1.75;
  margin-bottom: 4mm;
  font-weight: 300;
}

p strong { font-weight: 600; color: var(--ink); }

.sub-label {
  font-family: 'Poppins', sans-serif;
  font-size: 6pt;
  font-weight: 600;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--secondary);
  margin-top: 5mm;
  margin-bottom: 2.5mm;
  display: block;
}

.mono {
  font-family: 'JetBrains Mono', monospace;
  font-size: 7.5pt;
  background: var(--surface);
  padding: 1px 4px;
  border-radius: 2px;
}

/* ─ TOOL TAGS (lemon) ─ */
.tool-tags { margin-top: 3mm; display: flex; flex-wrap: wrap; gap: 4px; }
.tool-tag {
  display: inline-block;
  background: var(--lemon);
  color: var(--dark);
  font-family: 'JetBrains Mono', monospace;
  font-size: 6pt;
  font-weight: 700;
  letter-spacing: 0.04em;
  padding: 2.5px 7px;
  border-radius: 2px;
  white-space: nowrap;
}

/* ─ NUMBERED STEPS ─ */
.steps { margin-bottom: 4mm; }
.step {
  display: flex;
  gap: 10px;
  margin-bottom: 5.5mm;
  align-items: flex-start;
}
.step-num {
  background: var(--ink);
  color: var(--white);
  font-family: 'JetBrains Mono', monospace;
  font-size: 7pt;
  font-weight: 700;
  min-width: 22px;
  height: 22px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 0.5mm;
}
.step-body { flex: 1; }
.step-title {
  font-family: 'Poppins', sans-serif;
  font-size: 8pt;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-bottom: 1.5mm;
  color: var(--ink);
}
.step-desc {
  font-size: 10pt;
  line-height: 1.65;
  font-weight: 300;
  margin-bottom: 1.5mm;
}

/* ─ TABLES ─ */
table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 5mm;
  font-size: 8pt;
}
thead th {
  background: var(--dark);
  color: var(--white);
  font-family: 'Poppins', sans-serif;
  font-size: 6pt;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  padding: 6px 10px;
  text-align: left;
}
tbody tr:nth-child(even) { background: rgba(0,0,0,0.03); }
tbody td {
  padding: 5.5px 10px;
  border-bottom: 1px solid var(--border);
  vertical-align: top;
  line-height: 1.5;
  font-weight: 300;
}
tbody td:first-child {
  font-family: 'JetBrains Mono', monospace;
  font-size: 7.5pt;
  font-weight: 400;
}

/* ─ DARK CALLOUT BLOCK ─ */
.dark-block {
  background: var(--dark);
  color: var(--white);
  padding: 11mm 20mm;
  margin: 10mm -20mm;
}
.dark-block h3 {
  font-family: 'Poppins', sans-serif;
  font-size: 13pt;
  font-weight: 800;
  color: var(--white);
  line-height: 1.15;
  margin-bottom: 3.5mm;
  letter-spacing: -0.015em;
}
.dark-block > p {
  color: rgba(255,255,255,0.55);
  font-size: 8.5pt;
  font-weight: 300;
  margin-bottom: 5mm;
}
.dark-block-items { display: flex; flex-direction: column; gap: 0; }
.dark-block-item {
  display: flex;
  gap: 10px;
  padding: 5px 0;
  border-bottom: 1px solid rgba(255,255,255,0.07);
  align-items: flex-start;
}
.dark-block-item:last-child { border-bottom: none; }
.dark-item-icon {
  width: 17px;
  height: 17px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 7pt;
  font-weight: 700;
  flex-shrink: 0;
  margin-top: 1px;
  color: var(--dark);
}
.icon-green  { background: #4ADE80; }
.icon-blue   { background: #60A5FA; }
.icon-amber  { background: #FBBF24; }
.icon-teal   { background: #2DD4BF; }
.dark-item-text {
  font-size: 9.5pt;
  font-weight: 300;
  line-height: 1.55;
  color: rgba(255,255,255,0.72);
}
.dark-item-text strong {
  font-weight: 600;
  color: rgba(255,255,255,0.92);
}

/* ─ TIMELINE BLOCKS ─ */
.deliverable {
  padding-left: 12px;
  border-left: 2px solid var(--ink);
  margin-bottom: 8mm;
}
.deliverable-header {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 2.5mm;
}
.deliverable-week {
  font-family: 'JetBrains Mono', monospace;
  font-size: 6.5pt;
  font-weight: 700;
  color: var(--secondary);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  white-space: nowrap;
}
.deliverable-title {
  font-family: 'Poppins', sans-serif;
  font-size: 9pt;
  font-weight: 700;
  color: var(--ink);
}
.deliverable ul { padding-left: 12px; margin-bottom: 3mm; }
.deliverable li {
  font-size: 8pt;
  font-weight: 300;
  line-height: 1.55;
  margin-bottom: 1.5mm;
}
/* Checkpoint — the ONE lemon moment on content pages */
.checkpoint {
  font-family: 'JetBrains Mono', monospace;
  font-size: 6.5pt;
  color: var(--secondary);
  padding: 4px 8px;
  background: var(--lemon-dim);
  border-left: 2px solid var(--lemon);
  display: block;
  line-height: 1.5;
}

/* ─ INVESTMENT TABLE (SOW format) ─ */
.investment-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 4mm;
}
.investment-table tr { border-bottom: 1px solid var(--border); }
.investment-table tr.total-row {
  border-top: 2px solid var(--ink);
  border-bottom: 2px solid var(--ink);
}
.investment-table td {
  padding: 5.5px 0;
  font-size: 8.5pt;
  font-weight: 300;
}
.investment-table td.col-label { color: var(--secondary); width: 30%; }
.investment-table td.col-amount {
  font-family: 'JetBrains Mono', monospace;
  font-size: 9pt;
  font-weight: 700;
  color: var(--ink);
  width: 22%;
}
.investment-table td.col-note { font-size: 7.5pt; color: var(--secondary); }
.investment-table .total-row td { font-weight: 600; padding-top: 6px; padding-bottom: 6px; }
.investment-table .total-row td.col-label { color: var(--ink); }

/* ─ COST BREAKDOWN TABLE ─ */
.cost-table thead th:last-child,
.cost-table tbody td:last-child { text-align: right; }
.cost-table tbody td:nth-child(2),
.cost-table tbody td:nth-child(3) { text-align: center; }
.cost-total-row td {
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 8pt !important;
  font-weight: 700 !important;
  border-top: 2px solid var(--ink);
  border-bottom: 2px solid var(--ink) !important;
  background: var(--surface) !important;
}

/* ─ REQUIREMENTS ─ */
.requirements { list-style: none; }
.requirements li {
  display: flex;
  gap: 8px;
  padding: 5px 0;
  border-bottom: 1px solid var(--border);
  font-size: 8.5pt;
  font-weight: 300;
  line-height: 1.5;
}
.requirements li::before {
  content: '□';
  font-family: 'JetBrains Mono', monospace;
  font-size: 7.5pt;
  color: var(--secondary);
  flex-shrink: 0;
  margin-top: 1px;
}

/* ─ CALLOUT ─ */
.callout {
  border-left: 2px solid var(--border);
  background: var(--surface);
  padding: 7px 12px;
  margin: 3mm 0;
  font-size: 8pt;
  line-height: 1.6;
  font-weight: 300;
  font-style: italic;
  color: var(--secondary);
}

/* ─ PRINT ─ */
@media print { @page { margin: 0; } }
"""


# ── Helpers ──────────────────────────────────────────────────────────────────

def esc(text):
    return str(text).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

_sec_count = 0

def reset_sections():
    global _sec_count
    _sec_count = 0

def section(label, h2, content_html):
    global _sec_count
    _sec_count += 1
    num = f"{_sec_count:02d}"
    return f"""
<div class="section">
  <span class="section-label">&#8212; {num} &middot; {esc(label.upper())}</span>
  <div class="section-rule"></div>
  <h2>{esc(h2)}</h2>
  {content_html}
</div>"""

def tool_tags_html(tags):
    if not tags:
        return ""
    items = "".join(f'<span class="tool-tag">{esc(t)}</span>' for t in tags)
    return f'<div class="tool-tags">{items}</div>'

def steps_html(steps):
    html = '<div class="steps">'
    for i, s in enumerate(steps, 1):
        tags = tool_tags_html(s.get("tool_tags", []))
        html += f"""
<div class="step">
  <div class="step-num">{i:02d}</div>
  <div class="step-body">
    <div class="step-title">{esc(s['title'])}</div>
    <div class="step-desc">{s['description']}</div>
    {tags}
  </div>
</div>"""
    html += "</div>"
    return html

def table_html(headers, rows, col_widths=None, css_class=""):
    cg = ""
    if col_widths:
        cg = "<colgroup>" + "".join(f'<col style="width:{w}">' for w in col_widths) + "</colgroup>"
    ths = "".join(f"<th>{esc(h)}</th>" for h in headers)
    trs = "".join(
        "<tr>" + "".join(f"<td>{esc(c)}</td>" for c in row) + "</tr>"
        for row in rows
    )
    cls = f' class="{css_class}"' if css_class else ""
    return f"<table{cls}>{cg}<thead><tr>{ths}</tr></thead><tbody>{trs}</tbody></table>"

def cost_table_html(service_rows, unit_header="UNIT PRICE", qty_header="QTY / VIDEO", cost_header="COST"):
    ths = f"<th>SERVICE</th><th>{esc(unit_header)}</th><th>{esc(qty_header)}</th><th>{esc(cost_header)}</th>"
    trs = ""
    for row in service_rows:
        name = esc(row["service"])
        tag = f' <span class="tool-tag" style="font-size:5.5pt;">{esc(row["tag"])}</span>' if row.get("tag") else ""
        trs += f"""<tr>
          <td style="font-family:inherit;font-size:8pt;">{name}{tag}</td>
          <td style="text-align:center;font-family:\'JetBrains Mono\',monospace;font-size:7.5pt;">{esc(row.get('unit_price',''))}</td>
          <td style="text-align:center;font-family:\'JetBrains Mono\',monospace;font-size:7.5pt;">{esc(str(row.get('qty','')))}</td>
          <td style="text-align:right;font-family:\'JetBrains Mono\',monospace;font-size:7.5pt;font-weight:700;">{esc(row.get('cost',''))}</td>
        </tr>"""
    if service_rows:
        total = sum(
            float(str(r.get('cost','0')).replace('$','').replace(',',''))
            for r in service_rows if r.get('cost','').replace('$','').replace(',','').replace('.','').isdigit()
        )
    return f"""<table class="cost-table">
      <thead><tr>{ths}</tr></thead>
      <tbody>{trs}</tbody>
    </table>"""

def dark_block_html(d):
    items_html = ""
    for item in d.get("items", []):
        color_cls = f"icon-{item.get('icon','green')}"
        symbol = item.get("symbol", "&#10003;")
        items_html += f"""
<div class="dark-block-item">
  <div class="dark-item-icon {color_cls}">{symbol}</div>
  <div class="dark-item-text">{item['text']}</div>
</div>"""
    intro = f'<p>{esc(d["intro"])}</p>' if d.get("intro") else ""
    items_wrap = f'<div class="dark-block-items">{items_html}</div>' if items_html else ""
    return f"""<div class="dark-block">
  <h3>{esc(d['title'])}</h3>
  {intro}
  {items_wrap}
</div>"""

def deliverables_html(milestones):
    html = ""
    for m in milestones:
        bullets = "".join(f"<li>{esc(b)}</li>" for b in m["bullets"])
        html += f"""
<div class="deliverable">
  <div class="deliverable-header">
    <span class="deliverable-week">{esc(m['label'])}</span>
    <span class="deliverable-title">{esc(m['title'])}</span>
  </div>
  <ul>{bullets}</ul>
  <span class="checkpoint">Checkpoint &#8212; {esc(m['checkpoint'])}</span>
</div>"""
    return html

def investment_html(data):
    schedule = data.get("payment_schedule")
    opts = data.get("investment_options", [])
    if schedule:
        rows = "".join(f"""<tr>
          <td class="col-label">{esc(r['label'])}</td>
          <td class="col-amount">{esc(r['amount'])}</td>
          <td class="col-note">{esc(r.get('note',''))}</td>
        </tr>""" for r in schedule)
        total = data.get("investment_total", "")
        rows += f"""<tr class="total-row">
          <td class="col-label">Total</td>
          <td class="col-amount">{esc(total)}</td>
          <td class="col-note"></td>
        </tr>"""
        return f'<table class="investment-table">{rows}</table>'
    # Fallback
    rows = "".join(f"""<tr {"class=\"total-row\"" if o.get("primary") else ""}>
      <td class="col-label">{esc(o.get('scope',''))}</td>
      <td class="col-amount">{esc(o['price'])}</td>
      <td class="col-note">{esc(o['label'])}</td>
    </tr>""" for o in opts)
    return f'<table class="investment-table">{rows}</table>'


# ── Cover ────────────────────────────────────────────────────────────────────

def cover_html(d):
    status_cls = "status-ready" if d.get("status","").lower() in ("ready","ready for review","sent") else ""
    return f"""
<div class="cover">
  <div class="cover-subtitle">// {esc(d.get('document_type','Proposal &amp; Scope Breakdown'))}</div>
  <div class="cover-title">{esc(d['project_title'])}</div>
  <div class="cover-phase">
    <span class="cover-phase-tag">{esc(d.get('phase',''))}</span>
    <span class="cover-phase-label">{esc(d.get('phase_note',''))}</span>
  </div>
  <hr class="cover-divider">
  <div class="cover-meta">
    <div class="cover-meta-item">
      <span class="cover-meta-label">Prepared for</span>
      <span class="cover-meta-value">{esc(d['client_name'])}</span>
    </div>
    <div class="cover-meta-item">
      <span class="cover-meta-label">Date</span>
      <span class="cover-meta-value">{esc(d['date'])}</span>
    </div>
    <div class="cover-meta-item">
      <span class="cover-meta-label">Document type</span>
      <span class="cover-meta-value">{esc(d.get('document_type','Technical Proposal + Pricing'))}</span>
    </div>
    <div class="cover-meta-item">
      <span class="cover-meta-label">Status</span>
      <span class="cover-meta-value {status_cls}">{esc(d.get('status','Ready for Review'))}</span>
    </div>
  </div>
</div>"""


# ── Document builder ──────────────────────────────────────────────────────────

def build_html(data):
    reset_sections()
    cover = cover_html(data)

    body_sections = ""

    # ▪ OVERVIEW / SITUATION
    body_sections += section(
        "Overview",
        "What This Proposal Covers",
        f'<p>{data["situation"]}</p>'
    )

    # ▪ WORKFLOW STEPS (if provided)
    if data.get("workflow_steps"):
        body_sections += section(
            "The Pipeline",
            data.get("pipeline_title", "How the System Works — Step by Step"),
            steps_html(data["workflow_steps"])
        )

    # ▪ DARK CALLOUT (if provided)
    if data.get("dark_callout"):
        body_sections += dark_block_html(data["dark_callout"])

    # ▪ WHAT I'LL BUILD (scope)
    build_content = ""
    for s in data.get("solution_sections", []):
        build_content += f'<p class="sub-label">{esc(s["title"])}</p>'
        build_content += f'<p>{s["body"]}</p>'
        if s.get("table"):
            t = s["table"]
            build_content += table_html(t["headers"], t["rows"], t.get("widths"))
    if data.get("channels"):
        build_content += '<p class="sub-label">Channels in scope</p>'
        build_content += table_html(
            ["Channel", "Content Type", "Status"],
            data["channels"]
        )
    if data.get("deferred"):
        build_content += '<p class="sub-label">Intentionally deferred</p>'
        build_content += table_html(
            ["Feature", "Reason"],
            data["deferred"],
            col_widths=["44%","56%"]
        )
    if data.get("deferred_note"):
        build_content += f'<div class="callout">{esc(data["deferred_note"])}</div>'
    if build_content:
        body_sections += section("Scope", "What I'll Build", build_content)

    # ▪ COST PER RUN (if provided)
    if data.get("cost_per_run"):
        cpr = data["cost_per_run"]
        body_sections += section(
            "Cost Per Run",
            cpr.get("title", "Exact Cost Per Video — Automated Pipeline"),
            f'<p>{cpr.get("intro","")}</p>' + cost_table_html(
                cpr["rows"],
                cpr.get("unit_header","UNIT PRICE"),
                cpr.get("qty_header","QTY / VIDEO"),
                cpr.get("cost_header","COST / VIDEO"),
            )
        )

    # ▪ TIMELINE
    if data.get("milestones"):
        body_sections += section(
            "Timeline",
            "Milestone Breakdown",
            deliverables_html(data["milestones"])
        )

    # ▪ ONGOING COSTS
    infra_content = ""
    if data.get("infrastructure_note"):
        infra_content += f'<p>{data["infrastructure_note"]}</p>'
    if data.get("cost_rows"):
        infra_content += table_html(
            ["Service", "Monthly estimate"],
            data["cost_rows"],
            col_widths=["60%","40%"]
        )
    if infra_content:
        body_sections += section("Ongoing Costs", "Ongoing Platform Costs", infra_content)

    # ▪ INVESTMENT
    inv_content = investment_html(data)
    if data.get("investment_note"):
        inv_content += f'<div class="callout">{esc(data["investment_note"])}</div>'
    if data.get("payment_terms"):
        inv_content += f'<p class="sub-label">Payment terms</p><p>{data["payment_terms"]}</p>'
    body_sections += section("Investment", "Investment", inv_content)

    # ▪ WHAT I NEED FROM YOU
    reqs = data.get("requirements", [])
    if not reqs and data.get("next_step"):
        reqs = [data["next_step"]]
    req_items = "".join(f"<li>{esc(r)}</li>" for r in reqs)
    body_sections += section(
        "Next Step",
        "What I Need From You",
        f'<ul class="requirements">{req_items}</ul>'
    )

    topbar = (
        '<div class="doc-topbar">'
        '<span class="doc-topbar-brand">Hephzibah</span>'
        '<span class="doc-topbar-right">Emmanuel Adekoya &nbsp;&middot;&nbsp; adekoyaemmanuel15@gmail.com &nbsp;&middot;&nbsp; Confidential</span>'
        '</div>'
    )
    footer = (
        '<div class="doc-footer">'
        '<span>Emmanuel Adekoya &nbsp;&middot;&nbsp; adekoyaemmanuel15@gmail.com</span>'
        '<span>Confidential</span>'
        '</div>'
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <style>{CSS}</style>
</head>
<body>
{topbar}
{cover}
<div class="content">
{body_sections}
</div>
{footer}
</body>
</html>"""


# ── Renderer ──────────────────────────────────────────────────────────────────

def render_pdf(html: str, output_path: str):
    """Render as a single continuous page — A4 width, dynamic height."""
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False, encoding="utf-8"
        ) as f:
            f.write(html)
            tmp = f.name
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 794, "height": 1123})
            page.goto(
                "file:///" + tmp.replace(os.sep, "/"),
                wait_until="networkidle",
                timeout=18000,
            )
            height = page.evaluate("document.documentElement.scrollHeight")
            page.pdf(
                path=output_path,
                width="794px",
                height=f"{height}px",
                print_background=True,
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            )
            browser.close()
    finally:
        if tmp and os.path.exists(tmp):
            os.unlink(tmp)


def main():
    if len(sys.argv) < 3:
        print("Usage: python proposal_renderer.py <data.json> <output.pdf>")
        sys.exit(1)
    with open(sys.argv[1], encoding="utf-8") as f:
        data = json.load(f)
    os.makedirs(os.path.dirname(os.path.abspath(sys.argv[2])), exist_ok=True)
    render_pdf(build_html(data), sys.argv[2])
    print(f"PDF saved: {sys.argv[2]}")


if __name__ == "__main__":
    main()
