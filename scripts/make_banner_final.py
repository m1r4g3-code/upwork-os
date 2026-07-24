"""
Phase 1: Full personality animation — character alone (glance, wink, wave, blink, hops)
Phase 2: Laptop appears as character lands — character types, screen builds through leg gaps

Laptop is rendered BEHIND the character. Leg gaps (transparent cols 0,1,3,5,7,9,10)
reveal the screen below. Lemon code appears through those gaps as typing progresses.
"""
from PIL import Image, ImageDraw, ImageFont
import os

SCRATCHPAD = r"C:\Users\HomePC\AppData\Local\Temp\claude\c--Users-HomePC-Documents-Upwork-OS\d63dfd35-0ee3-474d-bbd1-064aea242a83\scratchpad"
OUTPUT = os.path.join(SCRATCHPAD, "banner.gif")

W, H  = 1500, 400
BG    = (13, 17, 23)
LEMON = (232, 255, 58)
WHITE = (220, 210, 188)   # carton / warm cream (reduced)
MUTED = (68, 68, 68)
DARK  = (10, 10, 10)
ACCENT= (120, 132, 30)
KEY_C = (145, 150, 155)
BASE_C= (18, 20, 22)
SCR_C = (6,   6,   6)     # screen bg — near black, strong contrast with lemon legs

P = 26

COLORS = {1: LEMON, 2: DARK, 4: KEY_C, 5: BASE_C, 6: LEMON, 7: SCR_C, 8: LEMON}

# ------------------------------------------------------------------
# CHARACTER  (10 rows × 11 cols) — exact personality anim design
# ------------------------------------------------------------------
def make_char(el_col, er_col, el=2, er=2, arm='normal'):
    g = [
        [0]*11,                              # R0 arm raise top
        [0]*11,                              # R1 arm raise
        [0,0,1,1,1,1,1,1,1,0,0],            # R2 head
        [0,0,1,1,1,1,1,1,1,0,0],            # R3 eye row
        [1,1,1,1,1,1,1,1,1,1,1],            # R4 arms (full width)
        [1,1,1,1,1,1,1,1,1,1,1],            # R5 arms
        [0,0,1,1,1,1,1,1,1,0,0],            # R6 body
        [0,0,1,1,1,1,1,1,1,0,0],            # R7 body
        [0,0,1,0,1,0,1,0,1,0,0],            # R8 4 legs
        [0,0,1,0,1,0,1,0,1,0,0],            # R9 4 legs
    ]
    if el in (2,3): g[3][el_col] = el
    if er in (2,3): g[3][er_col] = er
    if arm == 'wave_up':
        g[0][9]=1; g[0][10]=1
        g[1][8]=1; g[1][9]=1
        g[4]=[1,1,1,1,1,1,1,1,0,0,0]
        g[5]=[1,1,1,1,1,1,1,1,0,0,0]
    elif arm == 'wave_mid':
        g[1][8]=1; g[1][9]=1
        g[4]=[1,1,1,1,1,1,1,1,0,0,0]
        g[5]=[1,1,1,1,1,1,1,1,0,0,0]
    return g

# ------------------------------------------------------------------
# LAPTOP  (4 rows × 11 cols) — rendered BEHIND character
#
#   R0 : screen bezel top           ← lines up with char R8 legs
#   R1 : screen interior            ← lines up with char R9 legs
#   R2 : keyboard (key glows here)  ← BELOW character (fully visible)
#   R3 : base bar                   ← BELOW character
#
# Screen content (row 1) shows through transparent leg cells:
#   leg columns:     2, 4, 6, 8  → covered by lemon leg pixels
#   transparent cols: 0,1,3,5,7,9,10 → screen peeks through
# ------------------------------------------------------------------
LEG_GAP_COLS = [0,1,3,5,7,9,10]   # cols visible through leg gaps

PRESS_COLS = {
    'outer': [2,8], 'inner': [4,6],
    'left':  [2,4], 'right': [6,8], 'all': [2,4,6,8],
}

def make_laptop(press=None, ss=0):
    # screen content — lemon appears at leg-gap columns as ss increases
    scr = [7]*11
    if ss > 0:
        lit = min(ss, len(LEG_GAP_COLS))
        for c in LEG_GAP_COLS[:lit]:
            scr[c] = 8           # lemon code peeking through legs

    # keyboard
    kb = [4]*11
    if press in PRESS_COLS:
        for c in PRESS_COLS[press]:
            kb[c] = 6            # lemon key glow at leg positions

    return [
        [5]*11,   # R0 bezel (behind leg row 8)
        scr,      # R1 screen (behind leg row 9, peeks through gaps)
        kb,       # R2 keyboard (below character, fully visible)
        [5]*11,   # R3 base
    ]

# ------------------------------------------------------------------
def draw_grid(draw, grid, ox, oy):
    for ri, row in enumerate(grid):
        for ci, cell in enumerate(row):
            if cell == 0: continue
            x = ox + ci * P;  y = oy + ri * P
            if cell == 3:
                sq = y + int(P * 0.38)
                draw.rectangle([x, y,  x+P-1, sq-1], fill=LEMON)
                draw.rectangle([x, sq, x+P-1, y+P-1], fill=DARK)
            else:
                draw.rectangle([x, y, x+P-1, y+P-1], fill=COLORS.get(cell, LEMON))

def draw_text(draw, fb, fm, ft):
    draw.text((24, 24),  "m1r4g3-code",                                              font=ft, fill=MUTED)
    draw.text((22, 76),  "Hephzibah Ifeoluwa",                                       font=fb, fill=WHITE)
    draw.text((25, 210), "AI Automation & Software Engineer",                         font=fm, fill=LEMON)
    draw.text((26, 263), "n8n  ·  Claude API  ·  TypeScript  ·  Next.js  ·  Lagos, NG",
                                                                                      font=ft, fill=MUTED)

# Layout
CW      = 11 * P          # 286
CHAR_H  = 10 * P          # 260
# Keyboard (laptop R2) must align with character legs bottom
# char leg bottom = CHAR_Y + 9P + P = CHAR_Y + 260
# laptop R2 starts at LAP_Y + 2P
# so: CHAR_Y + 260 = LAP_Y + 2P  → LAP_Y = CHAR_Y + 260 - 2P
# Choose CHAR_Y so everything fits:
LAP_ROWS = 4
LAP_H    = LAP_ROWS * P   # 104
# Bottom of laptop = LAP_Y + LAP_H ≤ H - 15
# LAP_Y = CHAR_Y + 260 - 2*26 = CHAR_Y + 208
# CHAR_Y + 208 + 104 ≤ 385  → CHAR_Y ≤ 73
CHAR_Y  = 60
LAP_Y   = CHAR_Y + 10*P - 2*P   # = 60 + 260 - 52 = 268   (screen bezel behind leg R8)

CX = 870 + (W - 870 - CW) // 2   # 1042

# Verify: char leg R9 bottom = CHAR_Y + 9*P + P = 60+260=320; laptop kb top = LAP_Y+2*P = 268+52=320 ✓

# ------------------------------------------------------------------
# Sequence: (el_col, er_col, el, er, arm, yo, press, ss, lap, ms)
# lap = show laptop (True/False)
# ss  = screen state 0-7 (how many leg-gap cols lit on screen)
# ------------------------------------------------------------------
SEQ = [
    # ── PHASE 1: PERSONALITY (no laptop) ──────────────────────────
    # idle
    (3,6, 2,2, 'normal',   0, None, 0, False, 480),

    # glance right + wink
    (4,7, 2,2, 'normal',   0, None, 0, False,  90),
    (4,7, 2,2, 'normal',   0, None, 0, False, 370),
    (4,7, 2,0, 'normal',   0, None, 0, False, 260),   # wink right eye
    (4,7, 2,2, 'normal',   0, None, 0, False, 120),
    (3,6, 2,2, 'normal',   0, None, 0, False, 165),

    # wave
    (3,6, 3,3, 'wave_mid', 0, None, 0, False, 120),
    (3,6, 3,3, 'wave_up',  0, None, 0, False, 185),
    (3,6, 3,3, 'wave_mid', 0, None, 0, False, 120),
    (3,6, 3,3, 'wave_up',  0, None, 0, False, 185),
    (3,6, 3,3, 'wave_mid', 0, None, 0, False, 120),
    (3,6, 2,2, 'normal',   0, None, 0, False, 165),

    # glance left
    (2,5, 2,2, 'normal',   0, None, 0, False,  90),
    (2,5, 2,2, 'normal',   0, None, 0, False, 370),
    (3,6, 2,2, 'normal',   0, None, 0, False, 120),

    # double blink
    (3,6, 0,0, 'normal',   0, None, 0, False,  68),
    (3,6, 2,2, 'normal',   0, None, 0, False,  82),
    (3,6, 0,0, 'normal',   0, None, 0, False,  68),
    (3,6, 2,2, 'normal',   0, None, 0, False, 170),

    # hop × 2 (squint = excited)
    (3,6, 3,3, 'normal',  -4, None, 0, False,  65),
    (3,6, 3,3, 'normal',  -9, None, 0, False,  65),
    (3,6, 3,3, 'normal',-13,  None, 0, False,  70),
    (3,6, 3,3, 'normal',  -9, None, 0, False,  65),
    (3,6, 3,3, 'normal',  -4, None, 0, False,  65),
    (3,6, 2,2, 'normal',   0, None, 0, False,  95),
    (3,6, 2,2, 'normal',   0, None, 0, False, 110),
    (3,6, 3,3, 'normal',  -4, None, 0, False,  56),
    (3,6, 3,3, 'normal',  -9, None, 0, False,  56),
    (3,6, 3,3, 'normal',-13,  None, 0, False,  60),
    (3,6, 3,3, 'normal',  -9, None, 0, False,  56),
    (3,6, 3,3, 'normal',  -4, None, 0, False,  56),

    # ── TRANSITION: laptop appears as character descends ──────────
    # (last hop landing — laptop snaps in, character lands on keyboard)
    (3,6, 3,3, 'normal',   0, None, 0, True,  95),   # land — laptop appears

    # ── PHASE 2: TYPING (laptop visible, screen builds) ───────────
    (3,6, 3,3, 'normal',   0, None,    0, True, 130),  # settle

    # typing: each press advances screen state (code builds in leg gaps)
    (3,6, 3,3, 'normal',   0, 'outer', 1, True,  60),
    (3,6, 3,3, 'normal',   0,  None,   1, True,  38),
    (3,6, 3,3, 'normal',   0, 'inner', 2, True,  60),
    (3,6, 3,3, 'normal',   0,  None,   2, True,  38),
    (3,6, 3,3, 'normal',   0, 'left',  3, True,  60),
    (3,6, 3,3, 'normal',   0,  None,   3, True,  38),
    (3,6, 3,3, 'normal',   0, 'right', 4, True,  60),
    (3,6, 3,3, 'normal',   0,  None,   4, True,  38),

    # look up, blink
    (3,6, 2,2, 'normal',   0,  None,   4, True, 190),
    (3,6, 0,0, 'normal',   0,  None,   4, True,  58),
    (3,6, 2,2, 'normal',   0,  None,   4, True, 150),

    # glance right, back
    (4,7, 2,2, 'normal',   0,  None,   4, True,  80),
    (4,7, 2,2, 'normal',   0,  None,   4, True, 310),
    (3,6, 2,2, 'normal',   0,  None,   4, True, 100),

    # more typing
    (3,6, 3,3, 'normal',   0, 'inner', 5, True,  60),
    (3,6, 3,3, 'normal',   0,  None,   5, True,  38),
    (3,6, 3,3, 'normal',   0, 'outer', 6, True,  60),
    (3,6, 3,3, 'normal',   0,  None,   6, True,  38),

    # wink mid-type
    (3,6, 0,3, 'normal',   0, 'left',  6, True, 165),
    (3,6, 3,3, 'normal',   0,  None,   6, True, 110),

    # fast burst — fill screen
    (3,6, 3,3, 'normal',   0, 'right', 6, True,  48),
    (3,6, 3,3, 'normal',  -2,  None,   6, True,  35),
    (3,6, 3,3, 'normal',   0, 'left',  7, True,  48),
    (3,6, 3,3, 'normal',  -2,  None,   7, True,  35),
    (3,6, 3,3, 'normal',   0, 'all',   7, True,  70),  # all keys + screen full
    (3,6, 3,3, 'normal',  -2,  None,   7, True,  50),
    (3,6, 3,3, 'normal',   0,  None,   7, True,  85),

    # screen full — look satisfied
    (3,6, 2,2, 'normal',   0,  None,   7, True, 240),
    (3,6, 0,0, 'normal',   0,  None,   7, True,  55),  # happy blink
    (3,6, 2,2, 'normal',   0,  None,   7, True, 100),

    # ENTER key — screen clears
    (3,6, 3,3, 'normal',   0, 'both',  0, True, 130),
    (3,6, 3,3, 'normal',   0,  None,   0, True, 100),

    # idle hold before loop
    (3,6, 2,2, 'normal',   0,  None,   0, True, 450),
]

try:
    fb = ImageFont.truetype(os.path.join(SCRATCHPAD, "Poppins-ExtraBold.ttf"),      90)
    fm = ImageFont.truetype(os.path.join(SCRATCHPAD, "JetBrainsMono-SemiBold.ttf"), 28)
    ft = ImageFont.truetype(os.path.join(SCRATCHPAD, "JetBrainsMono-SemiBold.ttf"), 18)
except Exception as e:
    print(f"Font warn: {e}"); fb=fm=ft=ImageFont.load_default()

frames, durs = [], []
for (el_col,er_col, el,er, arm, yo, press, ss, lap, dur) in SEQ:
    img  = Image.new("RGB", (W,H), BG)
    draw = ImageDraw.Draw(img)
    draw.rectangle([0,0,3,H], fill=ACCENT)
    draw_text(draw, fb, fm, ft)

    if lap:
        # laptop drawn FIRST (behind character)
        draw_grid(draw, make_laptop(press if yo==0 else None,
                                    ss    if yo==0 else 0), CX, LAP_Y)

    draw_grid(draw, make_char(el_col,er_col,el,er,arm), CX, CHAR_Y+yo)

    frames.append(img.quantize(colors=64, method=Image.Quantize.MEDIANCUT, dither=0))
    durs.append(dur)

frames[0].save(OUTPUT, save_all=True, append_images=frames[1:],
               duration=durs, loop=0, optimize=False)
total = sum(durs)
print(f"Done — {len(frames)} frames, {total}ms ({total/1000:.1f}s)")
print(f"Saved: {OUTPUT}")
