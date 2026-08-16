"""
Convert the profile avatar into a CLEAN, monochrome ASCII-art SVG (one
light-gray color, subject isolated on a dark background) that "types" itself
in like a terminal, then holds.

Monochrome is deliberate -- per-character rainbow color is what makes ASCII
portraits look noisy. One fill color + a good density ramp + high contrast
(so the background washes out to blank) reads as neat and legible.

GitHub renders SVGs embedded via <img> and runs their SMIL animations there
(JS does not run). Each row is revealed with a left-to-right clip wipe plus a
small block cursor riding the wipe edge, staggered top -> bottom, so the whole
portrait prints once and freezes.

The source avatar is a flat illustration on a pure-white background, so no
background removal is needed -- white maps straight to blank via WHITE_FLOOR.

Usage: python scripts/make_ascii_svg.py [input.png] [output.svg]
Style adapted from AVIVASHISHTA29/AVIVASHISHTA29.
"""
from PIL import Image, ImageEnhance
import html
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "source-avatar.png")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "taka-ascii.svg")

COLS = 100
ROWS = 53
CELL_W = 8
CELL_H = 15
RAMP = " .`:-=+*cs#%@"  # bright(sparse) -> dark(dense); leading space clears bg

# the avatar is a flat illustration: pure-white bg (255), light skin (~230),
# near-black hair/shirt (~35). WHITE_FLOOR sits between skin and bg so the
# face renders in sparse chars while the background stays blank.
CONTRAST = 1.0
BRIGHTNESS = 1.0
GAMMA = 1.0
WHITE_FLOOR = 0.97    # luminance above this is forced to blank (space)

PAD = 20
TITLEBAR_H = 30
STATUS_H = 30
ART_W = COLS * CELL_W
ART_H = ROWS * CELL_H
CANVAS_W = ART_W + PAD * 2
CANVAS_H = TITLEBAR_H + ART_H + STATUS_H + PAD

BG = "#0d1117"
BG2 = "#111722"
FRAME = "#30363d"
TITLE_TEXT = "#7d8590"
INK = "#c9d1d9"      # the single ascii color
GREEN = "#39d353"    # accent: the same green as the contribution heatmap
CURSOR = GREEN

# ---- reveal timing (one-shot; a cursor rasters top -> bottom) -------------
ROW_DUR = 0.11
STAGGER = 0.11       # == ROW_DUR -> a single cursor sweeping down

# ---- 1. sample the image into a COLS x ROWS grayscale grid ----------------
im = Image.open(SRC).convert("L")               # grayscale
im = ImageEnhance.Brightness(im).enhance(BRIGHTNESS)
im = ImageEnhance.Contrast(im).enhance(CONTRAST)
im = im.resize((COLS, ROWS), Image.LANCZOS)
px = im.load()

STATIC = bool(os.environ.get("STATIC"))  # emit frozen state for previews

rows_txt = []
for y in range(ROWS):
    chars = []
    for x in range(COLS):
        lum = px[x, y] / 255.0
        lum = pow(lum, GAMMA)
        if lum >= WHITE_FLOOR:
            chars.append(" ")
            continue
        idx = int((1.0 - lum) * (len(RAMP) - 1) + 0.5)
        idx = max(0, min(len(RAMP) - 1, idx))
        chars.append(RAMP[idx])
    rows_txt.append("".join(chars))

art_top = TITLEBAR_H + PAD * 0.35

# ---- 2. assemble SVG ------------------------------------------------------
parts = []
parts.append(
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_W}" height="{CANVAS_H}" '
    f'viewBox="0 0 {CANVAS_W} {CANVAS_H}" font-family="ui-monospace, SFMono-Regular, '
    f'Menlo, Consolas, monospace">'
)
parts.append('<defs>'
             f'<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
             f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/>'
             f'</linearGradient></defs>')

parts.append(f'<rect width="{CANVAS_W}" height="{CANVAS_H}" rx="12" fill="url(#bg)"/>')
parts.append(f'<rect x="0.5" y="0.5" width="{CANVAS_W-1}" height="{CANVAS_H-1}" rx="12" '
             f'fill="none" stroke="{FRAME}" stroke-width="1"/>')

parts.append(f'<line x1="0" y1="{TITLEBAR_H}" x2="{CANVAS_W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>')
for i, dotcol in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
    parts.append(f'<circle cx="{PAD + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{dotcol}"/>')
parts.append(f'<text x="{CANVAS_W/2}" y="{TITLEBAR_H/2 + 4}" fill="{TITLE_TEXT}" font-size="12" '
             f'text-anchor="middle">taka@github: ~$ ./portrait.sh</text>')

# one <text> per row (single color -> no per-char markup, tiny file)
font_size = CELL_H * 0.86
for ry, line in enumerate(rows_txt):
    y = art_top + ry * CELL_H + CELL_H * 0.74
    row_y = art_top + ry * CELL_H
    delay = ry * STAGGER
    safe = html.escape(line)
    text = (f'<text xml:space="preserve" x="{PAD}" y="{y:.1f}" fill="{INK}" '
            f'font-size="{font_size:.1f}" textLength="{ART_W}" lengthAdjust="spacing">{safe}</text>')

    if STATIC:
        parts.append(text)
        continue

    parts.append(
        f'<clipPath id="r{ry}"><rect x="{PAD}" y="{row_y:.1f}" height="{CELL_H}" width="0">'
        f'<animate attributeName="width" from="0" to="{ART_W}" begin="{delay:.3f}s" '
        f'dur="{ROW_DUR:.2f}s" fill="freeze"/></rect></clipPath>'
    )
    parts.append(f'<g clip-path="url(#r{ry})">{text}</g>')
    parts.append(
        f'<rect y="{row_y+1:.1f}" width="{CELL_W}" height="{CELL_H-2}" fill="{CURSOR}" opacity="0">'
        f'<animate attributeName="x" from="{PAD}" to="{PAD+ART_W}" begin="{delay:.3f}s" '
        f'dur="{ROW_DUR:.2f}s" fill="freeze"/>'
        f'<set attributeName="opacity" to="0.85" begin="{delay:.3f}s"/>'
        f'<set attributeName="opacity" to="0" begin="{delay+ROW_DUR:.3f}s"/></rect>'
    )

# status bar with a steady blinking cursor
status_line_y = TITLEBAR_H + ART_H + PAD * 0.35
status_y = status_line_y + 19
parts.append(f'<line x1="0" y1="{status_line_y:.1f}" x2="{CANVAS_W}" y2="{status_line_y:.1f}" stroke="{FRAME}"/>')
CHAR_W, CHAR_T = 7.8, 0.05
prompt_len = len("taka@github:~$ ")
whoami_x = PAD + prompt_len * CHAR_W
whoami_w = len("whoami") * CHAR_W
type_dur = len("whoami") * CHAR_T
answer_t = 0.4 + type_dur + 0.25          # "Taka" prints after the command runs
parts.append(f'<text x="{PAD}" y="{status_y:.1f}" font-size="13">'
             f'<tspan fill="{GREEN}">taka@github</tspan><tspan fill="{TITLE_TEXT}">:~$ </tspan></text>')
if STATIC:
    parts.append(f'<text x="{whoami_x:.1f}" y="{status_y:.1f}" font-size="13" fill="{INK}" '
                 f'xml:space="preserve">whoami <tspan fill="{GREEN}">Taka</tspan></text>')
else:
    # the command types out, then its answer appears
    parts.append(f'<clipPath id="who"><rect x="{whoami_x:.1f}" y="{status_y-14:.1f}" height="18" width="0">'
                 f'<animate attributeName="width" from="0" to="{whoami_w:.1f}" begin="0.4s" '
                 f'dur="{type_dur:.2f}s" fill="freeze"/></rect></clipPath>')
    parts.append(f'<g clip-path="url(#who)"><text x="{whoami_x:.1f}" y="{status_y:.1f}" font-size="13" '
                 f'fill="{INK}" xml:space="preserve" textLength="{whoami_w:.1f}" '
                 f'lengthAdjust="spacing">whoami</text></g>')
    parts.append(f'<text x="{whoami_x + (len("whoami ")*CHAR_W):.1f}" y="{status_y:.1f}" font-size="13" '
                 f'fill="{GREEN}" opacity="0">Taka'
                 f'<set attributeName="opacity" to="1" begin="{answer_t:.2f}s"/></text>')
parts.append(f'<rect x="{PAD+206}" y="{status_y-12:.1f}" width="8" height="14" fill="{GREEN}" '
             f'opacity="{1 if STATIC else 0}">'
             f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.51;1" '
             f'dur="1s" begin="{0 if STATIC else answer_t:.2f}s" repeatCount="indefinite"/></rect>')

parts.append("</svg>")
svg = "".join(parts)
with open(OUT, "w") as f:
    f.write(svg)
print("wrote", OUT, len(svg), "bytes;", CANVAS_W, "x", CANVAS_H)
