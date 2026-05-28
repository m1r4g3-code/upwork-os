"""
Generate a clean PDF proposal from the Eugen 5-socials architecture doc.
Usage: python scripts/generate_proposal_pdf.py
Output: outputs/strategy/2026-05-28-eugen-5socials-proposal.pdf
"""

from fpdf import FPDF
from fpdf.enums import XPos, YPos
import os

OUTPUT_PATH = "outputs/strategy/2026-05-28-eugen-5socials-proposal.pdf"

DARK = (15, 15, 15)
ACCENT = (41, 98, 255)      # blue
LIGHT_BG = (245, 246, 250)
MID_GRAY = (120, 120, 130)
WHITE = (255, 255, 255)
RULE = (220, 222, 230)


FONT_DIR = r"C:\Windows\Fonts"
FONT_REG  = os.path.join(FONT_DIR, "arial.ttf")
FONT_BOLD = os.path.join(FONT_DIR, "arialbd.ttf")
FONT_ITAL = os.path.join(FONT_DIR, "ariali.ttf")
FONT_BI   = os.path.join(FONT_DIR, "arialbi.ttf")


class ProposalPDF(FPDF):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_font("Arial", style="",  fname=FONT_REG,  uni=True)
        self.add_font("Arial", style="B", fname=FONT_BOLD, uni=True)
        self.add_font("Arial", style="I", fname=FONT_ITAL, uni=True)
        self.add_font("Arial", style="BI",fname=FONT_BI,   uni=True)

    def _f(self, style="", size=10):
        self.set_font("Arial", style, size)

    def header(self):
        pass

    def footer(self):
        self.set_y(-14)
        self._f("I", 8)
        self.set_text_color(*MID_GRAY)
        self.cell(0, 6, f"Prepared by Emmanuel Adekoya  ·  Confidential  ·  Page {self.page_no()}", align="C")

    def cover(self):
        # Full-width dark header band
        self.set_fill_color(*DARK)
        self.rect(0, 0, 210, 72, "F")

        self.set_y(18)
        self.set_font("Arial", "B", 22)
        self.set_text_color(*WHITE)
        self.cell(0, 10, "5-Channel Social Media Automation", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        self.set_font("Arial", "", 13)
        self.set_text_color(200, 205, 220)
        self.cell(0, 8, "Project Proposal — Phase 1A", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        self.set_y(52)
        self.set_font("Arial", "", 9)
        self.set_text_color(160, 165, 185)
        self.cell(0, 6, "Prepared for: Eugen    |    Prepared by: Emmanuel Adekoya    |    28 May 2026", align="C")

        self.set_y(76)

    def section_title(self, text):
        self.ln(4)
        self.set_font("Arial", "B", 12)
        self.set_text_color(*ACCENT)
        self.cell(0, 7, text.upper(), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        # Thin rule
        self.set_draw_color(*ACCENT)
        self.set_line_width(0.5)
        self.line(self.l_margin, self.get_y(), 210 - self.r_margin, self.get_y())
        self.ln(3)
        self.set_text_color(*DARK)
        self.set_draw_color(*RULE)
        self.set_line_width(0.2)

    def body(self, text, bold=False):
        self.set_font("Arial", "B" if bold else "", 10)
        self.set_text_color(*DARK)
        self.multi_cell(0, 5.5, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1)

    def sub_label(self, text):
        self.set_font("Arial", "B", 9)
        self.set_text_color(*MID_GRAY)
        self.cell(0, 5, text.upper(), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(*DARK)
        self.ln(1)

    def bullet(self, text, indent=6):
        self.set_font("Arial", "", 10)
        self.set_text_color(*DARK)
        x = self.get_x()
        self.set_x(self.l_margin + indent)
        self.cell(4, 5.5, "-", new_x=XPos.RIGHT, new_y=YPos.LAST)
        self.multi_cell(0, 5.5, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def tag_row(self, label, value, accent=False):
        self.set_font("Arial", "B", 9)
        self.set_text_color(*MID_GRAY)
        self.cell(52, 6, label, new_x=XPos.RIGHT, new_y=YPos.LAST)
        self.set_font("Arial", "", 9)
        self.set_text_color(*ACCENT if accent else DARK)
        self.multi_cell(0, 6, value, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def info_box(self, text):
        self.set_fill_color(*LIGHT_BG)
        self.set_draw_color(*RULE)
        self.set_line_width(0.3)
        x, y = self.get_x(), self.get_y()
        self.set_font("Arial", "I", 9)
        self.set_text_color(80, 85, 100)
        self.multi_cell(0, 5.5, text, border=1, fill=True,
                        new_x=XPos.LMARGIN, new_y=YPos.NEXT, padding=4)
        self.ln(2)
        self.set_text_color(*DARK)
        self.set_line_width(0.2)

    def milestone_block(self, week, title, bullets, checkpoint):
        self.set_fill_color(*LIGHT_BG)
        self.set_draw_color(*RULE)
        self.set_line_width(0.3)
        self.rect(self.l_margin, self.get_y(), 170, 3, "F")  # top accent bar
        self.set_fill_color(*ACCENT)
        self.rect(self.l_margin, self.get_y(), 3, 3, "F")
        self.ln(3)

        self.set_font("Arial", "B", 10)
        self.set_text_color(*ACCENT)
        self.cell(28, 5.5, week, new_x=XPos.RIGHT, new_y=YPos.LAST)
        self.set_font("Arial", "B", 10)
        self.set_text_color(*DARK)
        self.cell(0, 5.5, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1)

        for b in bullets:
            self.bullet(b, indent=4)

        self.ln(1)
        self.set_font("Arial", "BI", 9)
        self.set_text_color(*MID_GRAY)
        self.cell(28, 5, "Checkpoint:", new_x=XPos.RIGHT, new_y=YPos.LAST)
        self.set_font("Arial", "I", 9)
        self.cell(0, 5, checkpoint, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(4)
        self.set_text_color(*DARK)

    def price_block(self, label, price, primary=False):
        if primary:
            self.set_fill_color(*ACCENT)
            self.set_text_color(*WHITE)
        else:
            self.set_fill_color(*LIGHT_BG)
            self.set_text_color(*DARK)
        self.set_draw_color(*RULE)
        self.set_font("Arial", "B", 10)
        w = 82
        h = 14
        self.cell(w, h, label, border=1, fill=True, new_x=XPos.RIGHT, new_y=YPos.LAST, align="C")
        if primary:
            self.set_font("Arial", "B", 12)
        else:
            self.set_font("Arial", "", 10)
        self.cell(w, h, price, border=1, fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        self.set_text_color(*DARK)
        self.ln(1)


def build():
    pdf = ProposalPDF(orientation="P", unit="mm", format="A4")
    pdf.set_margins(left=20, top=20, right=20)
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    pdf.cover()

    # ── SITUATION ────────────────────────────────────────────────
    pdf.section_title("The Situation")
    pdf.body(
        "You have two n8n workflows that work in isolation:\n"
        "  •  HeyGen workflow — generates avatar videos\n"
        "  •  Blotato posting workflow — publishes to TikTok, LinkedIn, Facebook, and Instagram\n\n"
        "The problem: they don’t talk to each other. There’s no central orchestration layer. "
        "Every post still requires a manual trigger, which defeats the point of automation.\n\n"
        "Phase 1A wires them together through a single Google Sheets CMS so the system runs on its own."
    )

    # ── WHAT WE BUILD ─────────────────────────────────────────────
    pdf.section_title("What We’re Building")

    pdf.sub_label("Google Sheets CMS — The Orchestration Layer")
    pdf.body(
        "Google Sheets becomes the single source of truth. Every piece of content lives in one place. "
        "Workflows read from it and write back to it. Nothing posts unless Sheets says it’s ready."
    )

    # Content Queue table
    headers = ["Field", "Purpose"]
    rows = [
        ["topic", "What the post is about"],
        ["content_type", "Reel, photo, or carousel"],
        ["platform", "TikTok, LinkedIn, Facebook, Instagram"],
        ["status", "ready → locked → posting → done / failed"],
        ["scheduled_time", "When to post"],
        ["drive_file_id", "Generated media location in Google Drive"],
        ["post_id", "Platform’s returned confirmation ID"],
        ["attempt_count", "Retry counter"],
        ["error_log", "Last error message if failed"],
    ]

    pdf.set_font("Arial", "B", 9)
    pdf.set_fill_color(*ACCENT)
    pdf.set_text_color(*WHITE)
    pdf.cell(55, 7, headers[0], border=1, fill=True, new_x=XPos.RIGHT, new_y=YPos.LAST)
    pdf.cell(0, 7, headers[1], border=1, fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    for i, row in enumerate(rows):
        bg = LIGHT_BG if i % 2 == 0 else WHITE
        pdf.set_fill_color(*bg)
        pdf.set_font("Arial", "B", 9)
        pdf.set_text_color(*DARK)
        pdf.cell(55, 6, row[0], border=1, fill=True, new_x=XPos.RIGHT, new_y=YPos.LAST)
        pdf.set_font("Arial", "", 9)
        pdf.cell(0, 6, row[1], border=1, fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.ln(4)

    pdf.sub_label("Workflow Adaptations")
    pdf.body(
        "HeyGen Workflow — input swapped from hardcoded source to Sheets row trigger. "
        "Generates video, saves to Google Drive, writes file ID back to the row, sets status to ready_to_post.\n\n"
        "Blotato Channel Nodes — existing posting nodes for all 4 channels are kept. "
        "Only the input source changes: Blotato replaced with Sheets queue.\n\n"
        "Queue collision prevention: the moment a workflow picks up a row, it sets status to ‘locked’ "
        "before doing anything else. A second instance seeing ‘locked’ skips — no duplicate posts."
    )

    pdf.sub_label("Channels in Phase 1A")
    ch_data = [
        ("TikTok", "Avatar reels", "Included"),
        ("LinkedIn", "Photos + carousels", "Included"),
        ("Facebook", "Reels + photos + carousels", "Included"),
        ("Instagram", "Reels + photos + carousels", "Included"),
        ("YouTube", "Shorts", "Phase 1B"),
    ]
    pdf.set_font("Arial", "B", 9)
    pdf.set_fill_color(*ACCENT)
    pdf.set_text_color(*WHITE)
    for h in ["Channel", "Content Type", "Status"]:
        pdf.cell(55, 7, h, border=1, fill=True, new_x=XPos.RIGHT, new_y=YPos.LAST)
    pdf.ln()
    for i, (ch, ct, st) in enumerate(ch_data):
        bg = LIGHT_BG if i % 2 == 0 else WHITE
        pdf.set_fill_color(*bg)
        pdf.set_font("Arial", "B" if st == "Included" else "", 9)
        pdf.set_text_color(*DARK if st == "Included" else MID_GRAY)
        pdf.cell(55, 6, ch, border=1, fill=True, new_x=XPos.RIGHT, new_y=YPos.LAST)
        pdf.set_font("Arial", "", 9)
        pdf.cell(55, 6, ct, border=1, fill=True, new_x=XPos.RIGHT, new_y=YPos.LAST)
        pdf.set_text_color(*ACCENT if st == "Included" else MID_GRAY)
        pdf.cell(55, 6, st, border=1, fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(*DARK)
    pdf.ln(4)

    # ── MILESTONES ────────────────────────────────────────────────
    pdf.section_title("Milestone Breakdown")

    pdf.milestone_block(
        "Week 1",
        "Sheets Schema + HeyGen",
        [
            "Google Sheets CMS built (Content Queue, Settings tabs)",
            "HeyGen workflow updated to read from Sheets",
            "Generated videos save to Google Drive",
            "Row status updates correctly after generation",
        ],
        "HeyGen generates an avatar video from a Sheets row with no manual input"
    )

    pdf.milestone_block(
        "Week 2",
        "Publisher Workflows Live",
        [
            "Blotato channel nodes updated to read from Sheets queue",
            "Queue lock pattern implemented — no duplicate posts",
            "Rate limit counters active (daily TikTok cap, carousel counters)",
            "All 4 channels posting successfully from queue (manual trigger to test)",
        ],
        "One complete cycle runs: row in queue → video generates → posts to all 4 channels → row updates to done"
    )

    pdf.milestone_block(
        "Week 3",
        "Stability + Handoff",
        [
            "End-to-end automated run (no manual trigger)",
            "Basic error logging (failed rows clearly marked in Sheets)",
            "Cross-platform testing across all content types",
            "Handoff: Sheets schema docs, workflow logic, how to add new content rows",
        ],
        "System completes one full automated cycle with no manual input, posts correctly to all 4 channels"
    )

    # ── WHAT’S DEFERRED ─────────────────────────────────────────────
    pdf.section_title("What’s Deferred")

    deferred = [
        ("Content generator (News API + GPT-4 + image gen)",
         "Phase 1A uses manual Sheets input — you write topics directly"),
        ("Advanced retry (exponential backoff)",
         "Basic failure logging only; manual fix on failed rows"),
        ("Telegram monitoring",
         "Phase 1B"),
        ("YouTube Shorts",
         "Same architecture, added in Phase 1B"),
        ("Carousel automation",
         "Counter logic deferred; carousels added manually for v1"),
        ("Approval/review toggle",
         "Phase 2 feature"),
    ]

    pdf.set_font("Arial", "B", 9)
    pdf.set_fill_color(*ACCENT)
    pdf.set_text_color(*WHITE)
    pdf.cell(80, 7, "Feature", border=1, fill=True, new_x=XPos.RIGHT, new_y=YPos.LAST)
    pdf.cell(0, 7, "Reason for deferral", border=1, fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    for i, (feat, reason) in enumerate(deferred):
        bg = LIGHT_BG if i % 2 == 0 else WHITE
        pdf.set_fill_color(*bg)
        pdf.set_font("Arial", "", 9)
        pdf.set_text_color(*DARK)
        pdf.cell(80, 6, feat, border=1, fill=True, new_x=XPos.RIGHT, new_y=YPos.LAST)
        pdf.set_text_color(*MID_GRAY)
        pdf.cell(0, 6, reason, border=1, fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(*DARK)
    pdf.ln(3)

    pdf.info_box(
        "Important trade-off: Without the content generator, you write topics into Sheets manually for Phase 1A. "
        "The ‘5 minutes/day’ goal is not fully achieved yet — closer to 15-20 minutes. "
        "Phase 1B eliminates that. The trade-off is intentional: prove the publishing layer first, then automate the input."
    )

    # ── INFRASTRUCTURE ────────────────────────────────────────────
    pdf.section_title("Infrastructure")

    pdf.body(
        "n8n hosting: Start on n8n cloud ($20/month). Avoids Docker/SSL/backup overhead while workflows are being proven. "
        "Migration to self-hosted VPS (Hetzner CX21, €5/month) is a JSON export/import — 30 minutes — "
        "once Phase 1A is stable."
    )

    pdf.sub_label("Ongoing API Costs (your operational costs, separate from build fee)")
    cost_rows = [
        ("HeyGen (60 videos/month)", "$80 – 120"),
        ("DALL-E 3 (photos)", "$7"),
        ("n8n cloud", "$20"),
        ("Total", "~$107 – 147 / month"),
    ]
    pdf.set_font("Arial", "B", 9)
    pdf.set_fill_color(*ACCENT)
    pdf.set_text_color(*WHITE)
    pdf.cell(95, 7, "Service", border=1, fill=True, new_x=XPos.RIGHT, new_y=YPos.LAST)
    pdf.cell(0, 7, "Monthly estimate", border=1, fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    for i, (svc, cost) in enumerate(cost_rows):
        is_total = i == len(cost_rows) - 1
        pdf.set_fill_color(*DARK if is_total else (LIGHT_BG if i % 2 == 0 else WHITE))
        pdf.set_font("Arial", "B", 9)
        pdf.set_text_color(*WHITE if is_total else DARK)
        pdf.cell(95, 6, svc, border=1, fill=True, new_x=XPos.RIGHT, new_y=YPos.LAST)
        pdf.cell(0, 6, cost, border=1, fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(*DARK)
    pdf.ln(4)

    # ── INVESTMENT ────────────────────────────────────────────────
    pdf.section_title("Investment")

    pdf.ln(2)
    pdf.price_block("Phase 1A  (4 channels, 3 weeks)", "$1,200 – $1,500", primary=True)
    pdf.price_block("Phase 1B add-on  (content gen, retry, Telegram, YouTube)", "$800 – $1,000")
    pdf.price_block("Full Phase 1A + 1B", "$2,000 – $2,500")
    pdf.ln(3)

    pdf.info_box(
        "The range on Phase 1A depends on the condition of your existing workflows. "
        "Once I review them (JSON export from n8n or a 2-minute Loom of the canvas), "
        "I’ll give you a single fixed number — no range."
    )

    pdf.sub_label("Payment Terms — Phase 1A")
    pdf.body("50% upfront · 50% on completion (stable automated run across all 4 channels)")

    # ── NEXT STEP ─────────────────────────────────────────────────
    pdf.section_title("Next Step")
    pdf.body(
        "Share your existing workflows — export as JSON from n8n, or record a 2-minute Loom of "
        "the workflow canvas. That’s all I need to lock in the fixed price and confirm the start date.\n\n"
        "If a 20-minute call is faster, I can work around your schedule this week."
    )

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    pdf.output(OUTPUT_PATH)
    print(f"PDF saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    build()
