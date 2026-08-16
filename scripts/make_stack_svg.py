#!/usr/bin/env python3
"""
Generate the tech-stack panel: a terminal window (same chrome and palette as
the other panels) whose content prints like the output of ./stack.sh, one
line per category, fading in top to bottom.

Usage: python scripts/make_stack_svg.py   (writes stack.svg in the repo root)
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "stack.svg")

BG = "#0d1117"
BG2 = "#111722"
FRAME = "#30363d"
GRAY = "#7d8590"
INK = "#c9d1d9"
GREEN = "#39d353"

# canvas width matches the heatmap panel so the two stack flush in the README
W = 924
PAD = 18
TITLEBAR_H = 28
LINE_H = 22
VALUE_X = 165          # second column: keys align left, values align here

ROWS = [
    ("languages",  ["python", "c#", "java", "php", "javascript", "html/css"]),
    ("frameworks", [".net", "django"]),
    ("infra",      ["docker", "gcp", "nginx", "mysql"]),
    ("env",        ["windows", "linux", "ubuntu", "vscode", "visual-studio"]),
]

STAGGER = 0.18
SEP = f'<tspan fill="{GRAY}"> · </tspan>'

content_top = TITLEBAR_H + PAD * 0.55 + 14
n_lines = len(ROWS) + 1                      # rows + trailing prompt
H = int(content_top + n_lines * LINE_H + 4)

parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
    f'font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace">',
    f'<defs><linearGradient id="sbg" x1="0" y1="0" x2="0" y2="1">'
    f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/>'
    f'</linearGradient></defs>',
    f'<rect width="{W}" height="{H}" rx="12" fill="url(#sbg)"/>',
    f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="{FRAME}"/>',
    f'<line x1="0" y1="{TITLEBAR_H}" x2="{W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
]
for i, c in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
    parts.append(f'<circle cx="{PAD + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{c}"/>')
parts.append(f'<text x="{W/2:.0f}" y="{TITLEBAR_H/2 + 4}" fill="{GRAY}" font-size="12" '
             f'text-anchor="middle">taka@github: ~$ ./stack.sh</text>')

for i, (key, values) in enumerate(ROWS):
    y = content_top + i * LINE_H
    t = i * STAGGER
    joined = SEP.join(f'<tspan fill="{INK}">{v}</tspan>' for v in values)
    parts.append(f'<text x="{PAD}" y="{y:.1f}" font-size="13" opacity="0">'
                 f'<tspan fill="{GREEN}">&gt; </tspan><tspan fill="{GRAY}">{key}</tspan>'
                 f'<set attributeName="opacity" to="1" begin="{t:.2f}s"/></text>')
    parts.append(f'<text x="{VALUE_X}" y="{y:.1f}" font-size="13" opacity="0">{joined}'
                 f'<set attributeName="opacity" to="1" begin="{t:.2f}s"/></text>')

# trailing prompt with the shared blinking cursor
py = content_top + len(ROWS) * LINE_H
pt = len(ROWS) * STAGGER
parts.append(f'<text x="{PAD}" y="{py:.1f}" font-size="13" opacity="0">'
             f'<tspan fill="{GREEN}">taka@github</tspan><tspan fill="{GRAY}">:~$</tspan>'
             f'<set attributeName="opacity" to="1" begin="{pt:.2f}s"/></text>')
parts.append(f'<rect x="{PAD + 122}" y="{py - 11:.1f}" width="8" height="14" fill="{GREEN}" '
             f'opacity="0"><animate attributeName="opacity" values="1;1;0;0" '
             f'keyTimes="0;0.5;0.51;1" dur="1s" begin="{pt:.2f}s" '
             f'repeatCount="indefinite"/></rect>')

parts.append("</svg>")
svg = "".join(parts)
with open(OUT, "w") as f:
    f.write(svg)
print("wrote", OUT, f"{W}x{H}", len(svg), "bytes")
