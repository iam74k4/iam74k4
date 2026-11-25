#!/usr/bin/env python3
"""
Generate the link "chips": small flat SVG buttons that replace stock
shields.io badges so the links row matches the dashboard -- GitHub's own page
background as the fill, a 1px Primer border, monospace type.

One file per link and per theme: links-<name>.svg (dark) and
links-<name>-light.svg (light). The README wraps each in <a><picture>, because
an SVG embedded via <img> cannot carry clickable areas itself.

Usage: python scripts/make_links_svg.py   (writes links-*.svg in the repo root)
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")

# Primer bgColor-default / borderColor-default / fgColor-default / fgColor-muted /
# fgColor-success (the accent dot)
THEMES = {
    "":       {"bg": "#0d1117", "border": "#3d444d", "fg": "#f0f6fc", "muted": "#9198a1",
               "accent": "#3fb950"},
    "-light": {"bg": "#ffffff", "border": "#d1d9e0", "fg": "#1f2328", "muted": "#59636e",
               "accent": "#1a7f37"},
}

MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace"
SIZE = 13
CHAR_W = SIZE * 0.6    # monospace advance
H = 34
PAD_X = 14
DOT = 14               # room for the accent dot before the label

LINKS = [
    ("links-mail",      "mail",      "iam74k4@gmail.com"),
    ("links-discord",   "discord",   "@74k4"),
    ("links-instagram", "instagram", "@iam74k4"),
]

for suffix, t in THEMES.items():
    for name, label, value in LINKS:
        body = f"{label}  {value}"
        w = int(PAD_X * 2 + DOT + len(body) * CHAR_W + 0.5)
        y = H / 2 + 4.5
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{H}" '
            f'viewBox="0 0 {w} {H}" font-family="{MONO}">'
            f'<rect x="0.5" y="0.5" width="{w - 1}" height="{H - 1}" rx="6" '
            f'fill="{t["bg"]}" stroke="{t["border"]}"/>'
            f'<circle cx="{PAD_X + 3}" cy="{H / 2}" r="3" fill="{t["accent"]}"/>'
            f'<text x="{PAD_X + DOT}" y="{y:.1f}" font-size="{SIZE}" xml:space="preserve">'
            f'<tspan fill="{t["muted"]}">{label}  </tspan>'
            f'<tspan fill="{t["fg"]}">{value}</tspan></text>'
            f'</svg>'
        )
        fname = f"{name}{suffix}.svg"
        with open(os.path.join(ROOT, fname), "w") as f:
            f.write(svg)
        print("wrote", fname, f"{w}x{H}")
