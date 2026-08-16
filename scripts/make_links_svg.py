#!/usr/bin/env python3
"""
Generate the link "chips": small terminal-styled SVG buttons that replace
stock shields.io badges so the links row shares the profile's palette
(same background gradient, frame, monospace type and green accent as the
portrait / wordmark / heatmap panels).

Each chip is its own SVG so the README can wrap it in a normal markdown
link -- SVGs embedded via <img> cannot carry clickable areas themselves.

Usage: python scripts/make_links_svg.py   (writes links-*.svg in the repo root)
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")

BG = "#0d1117"
BG2 = "#111722"
FRAME = "#30363d"
GRAY = "#7d8590"
INK = "#c9d1d9"
GREEN = "#39d353"

CHAR_W = 7.8       # ~monospace advance at 13px
H = 36
PAD_X = 14

LINKS = [
    ("links-mail.svg",      "mail",      "iam74k4@gmail.com"),
    ("links-discord.svg",   "discord",   "@74k4"),
    ("links-instagram.svg", "instagram", "@iam74k4"),
]

for fname, label, value in LINKS:
    text = f"> {label}  {value}"
    w = int(len(text) * CHAR_W + PAD_X * 2)
    y = H / 2 + 4.5
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{H}" '
        f'viewBox="0 0 {w} {H}" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace">'
        f'<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/>'
        f'</linearGradient></defs>'
        f'<rect width="{w}" height="{H}" rx="8" fill="url(#g)"/>'
        f'<rect x="0.5" y="0.5" width="{w-1}" height="{H-1}" rx="8" fill="none" stroke="{FRAME}"/>'
        f'<text x="{PAD_X}" y="{y:.1f}" font-size="13">'
        f'<tspan fill="{GREEN}">&gt; </tspan>'
        f'<tspan fill="{GRAY}">{label}  </tspan>'
        f'<tspan fill="{INK}">{value}</tspan></text>'
        f'</svg>'
    )
    out = os.path.join(ROOT, fname)
    with open(out, "w") as f:
        f.write(svg)
    print("wrote", fname, f"{w}x{H}")
