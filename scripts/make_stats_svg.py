#!/usr/bin/env python3
"""
Generate the stats panel: measured language share (byte counts across repos)
as ASCII bars on the left, and a commits-by-hour sparkline on the right.
Reads data/commit-activity.json (written by fetch_commit_activity.py), so the
daily workflow keeps it fresh. Same terminal chrome as every other panel;
the ./stats.sh command types itself out before the output appears.

Usage: python scripts/make_stats_svg.py [data.json] [output.svg]
"""
import html
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "data", "commit-activity.json")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "stats.svg")

BG = "#0d1117"
BG2 = "#111722"
FRAME = "#30363d"
GRAY = "#7d8590"
INK = "#c9d1d9"
GREEN = "#39d353"

W = 924               # matches the heatmap/stack panels
PAD = 18
TITLEBAR_H = 28
LINE_H = 22
CHAR_W = 7.8          # ~monospace advance at 13px
CHAR_T = 0.05         # typing speed, seconds per character
RIGHT_X = 500         # right column (punchcard) origin

N_LANGS = 6
BAR_CELLS = 12

data = json.load(open(SRC))
langs = data.get("languages", [])[:N_LANGS]
hours = data.get("hours", [0] * 24)
tz = data.get("tz_offset", 9)

PROMPT = "taka@github:~$ "
CMD = "./stats.sh --langs --hours"

content_top = TITLEBAR_H + PAD * 0.55 + 14
left_rows = 1 + len(langs)                 # header + bars
right_rows = 4                             # header + spark + axis + peak
n_rows = max(left_rows, right_rows)
H = int(content_top + LINE_H + 6 + n_rows * LINE_H + 4)   # cmd line + gap + rows

type_dur = len(CMD) * CHAR_T
reveal = 0.3 + type_dur + 0.15             # when the output starts appearing

parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
    f'font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace">',
    f'<defs><linearGradient id="tbg" x1="0" y1="0" x2="0" y2="1">'
    f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/>'
    f'</linearGradient></defs>',
    f'<rect width="{W}" height="{H}" rx="12" fill="url(#tbg)"/>',
    f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="{FRAME}"/>',
    f'<line x1="0" y1="{TITLEBAR_H}" x2="{W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
]
for i, c in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
    parts.append(f'<circle cx="{PAD + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{c}"/>')
parts.append(f'<text x="{W/2:.0f}" y="{TITLEBAR_H/2 + 4}" fill="{GRAY}" font-size="12" '
             f'text-anchor="middle">taka@github: ~</text>')

# ---- typed command line ---------------------------------------------------
cmd_x = PAD + len(PROMPT) * CHAR_W
cmd_w = len(CMD) * CHAR_W
parts.append(f'<text x="{PAD}" y="{content_top:.1f}" font-size="13">'
             f'<tspan fill="{GREEN}">taka@github</tspan><tspan fill="{GRAY}">:~$ </tspan></text>')
parts.append(f'<clipPath id="cmd"><rect x="{cmd_x:.1f}" y="{content_top-14:.1f}" height="18" width="0">'
             f'<animate attributeName="width" from="0" to="{cmd_w:.1f}" begin="0.3s" '
             f'dur="{type_dur:.2f}s" fill="freeze"/></rect></clipPath>')
parts.append(f'<g clip-path="url(#cmd)"><text x="{cmd_x:.1f}" y="{content_top:.1f}" '
             f'font-size="13" fill="{INK}" xml:space="preserve" textLength="{cmd_w:.1f}" '
             f'lengthAdjust="spacing">{html.escape(CMD)}</text></g>')
parts.append(f'<rect y="{content_top-12:.1f}" width="8" height="14" fill="{GREEN}" opacity="0">'
             f'<animate attributeName="x" from="{cmd_x:.1f}" to="{cmd_x+cmd_w:.1f}" begin="0.3s" '
             f'dur="{type_dur:.2f}s" fill="freeze"/>'
             f'<set attributeName="opacity" to="0.9" begin="0s"/>'
             f'<set attributeName="opacity" to="0" begin="{0.3+type_dur:.2f}s"/></rect>')


def line(x, y, body, begin):
    return (f'<text x="{x}" y="{y:.1f}" font-size="13" xml:space="preserve" opacity="0">{body}'
            f'<set attributeName="opacity" to="1" begin="{begin:.2f}s"/></text>')


rows_top = content_top + LINE_H + 6

# ---- left column: language bars ------------------------------------------
parts.append(line(PAD, rows_top, f'<tspan fill="{GRAY}">languages (by bytes)</tspan>', reveal))
top_pct = langs[0][1] if langs else 100.0
name_w = max((len(n) for n, _ in langs), default=8) + 2
for i, (name, pct) in enumerate(langs):
    filled = max(1, round(pct / top_pct * BAR_CELLS))
    bar = (f'<tspan fill="{GREEN}">{"█" * filled}</tspan>'
           f'<tspan fill="{FRAME}">{"░" * (BAR_CELLS - filled)}</tspan>')
    body = (f'<tspan fill="{INK}">{html.escape(name.lower().ljust(name_w))}</tspan>{bar}'
            f'<tspan fill="{GRAY}">  {pct:>5.1f}%</tspan>')
    parts.append(line(PAD, rows_top + (i + 1) * LINE_H, body, reveal + (i + 1) * 0.12))

# ---- right column: commits by hour ---------------------------------------
SPARK = " ▁▂▃▄▅▆▇█"
peak = max(hours) if any(hours) else 1
spark = "".join(SPARK[max(1, round(h / peak * (len(SPARK) - 1))) if h else 0] for h in hours)
peak_h = hours.index(max(hours)) if any(hours) else 0
sign = "+" if tz >= 0 else "-"
parts.append(line(RIGHT_X, rows_top, f'<tspan fill="{GRAY}">commits by hour (utc{sign}{abs(tz)})</tspan>', reveal))
parts.append(line(RIGHT_X, rows_top + LINE_H,
                  f'<tspan fill="{GREEN}" textLength="{24*CHAR_W:.1f}" lengthAdjust="spacing">{spark}</tspan>',
                  reveal + 0.12))
axis = "0     6     12    18    23"
parts.append(line(RIGHT_X, rows_top + 2 * LINE_H,
                  f'<tspan fill="{GRAY}" textLength="{len(axis)*CHAR_W:.1f}" lengthAdjust="spacing">{axis}</tspan>',
                  reveal + 0.12))
parts.append(line(RIGHT_X, rows_top + 3 * LINE_H,
                  f'<tspan fill="{INK}">peak </tspan><tspan fill="{GREEN}" font-weight="700">{peak_h:02d}:00</tspan>'
                  f'<tspan fill="{GRAY}"> ({max(hours)} commits)</tspan>',
                  reveal + 0.24))

parts.append("</svg>")
svg = "".join(parts)
with open(OUT, "w") as f:
    f.write(svg)
print("wrote", OUT, f"{W}x{H}", len(svg), "bytes;",
      f"{len(langs)} languages, peak hour {peak_h:02d}")
