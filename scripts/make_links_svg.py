#!/usr/bin/env python3
"""
Generate the link tiles under the dashboard: one small flat SVG per link, laid
out by the README as a grid that lines up with the board above it.

An SVG embedded via <img> cannot carry clickable areas, so every link is its
own file, wrapped in <a><picture> by the README. One per theme: <name>.svg
(dark) and <name>-light.svg (light), on GitHub's own page background with a
1px Primer border, like the board's cards.

The grid. Tiles are drawn in the board's own units (924 wide, 16 gutter,
three columns) and the README gives each <img> a width in percent, with the
board itself at 100%, so tiles and board scale together and the tiles' outer
edges stay on the board's edges at any README width. The gutters are
transparent space inside the tiles -- half a gutter on each inner side -- and
the README writes a row's tiles with no whitespace between them, so nothing
of the page's own spacing gets in. The space above each tile plus the ~6px
GitHub leaves under every line of images makes the gap between rows, and
between the board and the first row, about one board gutter.

Rows: the "On repeat" tracks in data/music.json (cover, title, artist; linked
to the track on Apple Music), three to a row, then the contacts. The README
lines between <!-- links:start --> and <!-- links:end --> are rewritten to
match, and tiles of tracks no longer listed are deleted. After editing the
track list: fetch_music_art.py, then this script.

Usage: python scripts/make_links_svg.py   (stdlib only)
"""
import base64
import glob
import html
import json
import math
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
MUSIC = os.path.join(ROOT, "data", "music.json")
ART_DIR = os.path.join(ROOT, "assets", "music")
README = os.path.join(ROOT, "README.md")
MAX_TRACKS = 6         # as many as the board's carousel shows

# Primer bgColor-default / borderColor-default / fgColor-default / fgColor-muted /
# fgColor-success, plus bgColor-muted for the icon well
THEMES = {
    "":       {"bg": "#0d1117", "border": "#3d444d", "fg": "#f0f6fc", "muted": "#9198a1",
               "accent": "#3fb950", "well": "#151b23"},
    "-light": {"bg": "#ffffff", "border": "#d1d9e0", "fg": "#1f2328", "muted": "#59636e",
               "accent": "#1a7f37", "well": "#f6f8fa"},
}

SANS = ("-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans',Helvetica,Arial,"
        "sans-serif")

ROW_W = 924            # the board's width, in its units
GAP = 16               # the board's gutter
COLS = 3
TILE_W = (ROW_W - GAP * (COLS - 1)) / COLS
TILE_H = 60
TOP = 10               # space above a tile (GitHub adds ~6px under each row)
RAD = 8
WELL = 40              # cover / icon square
PAD = 10
TEXT_X = PAD + WELL + 12
TEXT_W = TILE_W - TEXT_X - 34   # leaves room for the mark at the right

CONTACTS = [
    # file, icon, label, value, href
    ("links-mail",      "mail",   "Email",     "iam74k4@gmail.com", "mailto:iam74k4@gmail.com"),
    ("links-discord",   "chat",   "Discord",   "@74k4",
     "https://discord.com/users/569686218632331264"),
    ("links-instagram", "camera", "Instagram", "@iam74k4", "https://www.instagram.com/iam74k4"),
]


def esc(s):
    return html.escape(s, quote=False)


def fit(s, size, width, bold=False):
    """Cut s with an ellipsis if its estimated advance runs past width."""
    adv = size * (0.6 if bold else 0.56)
    if len(s) * adv <= width:
        return s
    return s[:max(1, int(width / adv) - 1)].rstrip() + "…"


def icon(kind, cx, cy, c):
    """Line icons drawn here (not brand marks), centred on (cx, cy)."""
    line = f'fill="none" stroke="{c}" stroke-width="1.6" stroke-linejoin="round" stroke-linecap="round"'
    if kind == "mail":
        return (f'<rect x="{cx - 8}" y="{cy - 6}" width="16" height="12" rx="2" {line}/>'
                f'<path d="M{cx - 7} {cy - 4.5}l7 5l7-5" {line}/>')
    if kind == "chat":
        x0, x1, y0, y1 = cx - 8, cx + 8, cy - 7, cy + 4
        return (f'<path d="M{x0 + 3} {y0}H{x1 - 3}A3 3 0 0 1 {x1} {y0 + 3}V{y1 - 3}'
                f'A3 3 0 0 1 {x1 - 3} {y1}H{x0 + 7}L{x0 + 3} {y1 + 4}V{y1}'
                f'A3 3 0 0 1 {x0} {y1 - 3}V{y0 + 3}A3 3 0 0 1 {x0 + 3} {y0}Z" {line}/>'
                f'<circle cx="{cx - 3}" cy="{cy - 1.5}" r="1.3" fill="{c}"/>'
                f'<circle cx="{cx + 3}" cy="{cy - 1.5}" r="1.3" fill="{c}"/>')
    if kind == "camera":
        return (f'<rect x="{cx - 7.5}" y="{cy - 7.5}" width="15" height="15" rx="4.5" {line}/>'
                f'<circle cx="{cx}" cy="{cy}" r="3.5" {line}/>'
                f'<circle cx="{cx + 4}" cy="{cy - 4}" r="1" fill="{c}"/>')
    raise ValueError(kind)


def tile(t, pos, k, well, title, sub, mark):
    """One tile at position pos of a row of k: half a gutter of transparent
    space on each inner side, so a full row spans exactly ROW_W."""
    left = GAP / 2 if pos > 0 else 0
    w = left + TILE_W + (GAP / 2 if pos < k - 1 else 0)
    h = TOP + TILE_H
    x, y = left, TOP
    wx, wy = x + PAD, y + (TILE_H - WELL) / 2
    my = y + TILE_H / 2
    mx = x + TILE_W - 22
    if mark == "play":
        m = (f'<path d="M{mx} {my - 5}v10l8.5-5z" fill="{t["accent"]}" stroke="{t["accent"]}" '
             f'stroke-width="1.5" stroke-linejoin="round"/>')
    else:   # leaves the page
        m = (f'<path d="M{mx} {my + 4}l8-8M{mx + 2} {my - 4}h6v6" fill="none" '
             f'stroke="{t["muted"]}" stroke-width="1.5" stroke-linecap="round" '
             f'stroke-linejoin="round"/>')
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:g}" height="{h}" '
        f'viewBox="0 0 {w:g} {h}" font-family="{SANS}">'
        f'<rect x="{x + 0.5:g}" y="{y + 0.5}" width="{TILE_W - 1:g}" height="{TILE_H - 1}" '
        f'rx="{RAD}" fill="{t["bg"]}" stroke="{t["border"]}"/>'
        f'{well(t, wx, wy)}'
        f'<text x="{x + TEXT_X:g}" y="{y + 25}" font-size="14" font-weight="600" '
        f'fill="{t["fg"]}">{esc(fit(title, 14, TEXT_W, bold=True))}</text>'
        f'<text x="{x + TEXT_X:g}" y="{y + 43.5}" font-size="13" '
        f'fill="{t["muted"]}">{esc(fit(sub, 13, TEXT_W))}</text>'
        f'{m}'
        f'</svg>'
    )
    return w, svg


def cover_well(b64):
    def draw(t, x, y):
        return (f'<clipPath id="c"><rect x="{x:g}" y="{y:g}" width="{WELL}" height="{WELL}" '
                f'rx="6"/></clipPath>'
                f'<image x="{x:g}" y="{y:g}" width="{WELL}" height="{WELL}" clip-path="url(#c)" '
                f'preserveAspectRatio="xMidYMid slice" href="data:image/jpeg;base64,{b64}"/>'
                f'<rect x="{x + 0.5:g}" y="{y + 0.5:g}" width="{WELL - 1}" height="{WELL - 1}" '
                f'rx="5.5" fill="none" stroke="{t["border"]}"/>')
    return draw


def icon_well(kind):
    def draw(t, x, y):
        return (f'<rect x="{x + 0.5:g}" y="{y + 0.5:g}" width="{WELL - 1}" height="{WELL - 1}" '
                f'rx="6" fill="{t["well"]}" stroke="{t["border"]}"/>'
                f'{icon(kind, x + WELL / 2, y + WELL / 2, t["accent"])}')
    return draw


def load_tracks():
    """The tracks the board shows: resolved (title, url) with a cover on disk."""
    if not os.path.exists(MUSIC):
        return []
    with open(MUSIC) as f:
        tracks = json.load(f).get("tracks", [])
    return [tr for tr in tracks
            if tr.get("title") and tr.get("url") and tr.get("art")
            and os.path.exists(os.path.join(ROOT, tr["art"]))][:MAX_TRACKS]


def write(path, svg):
    with open(path, "w") as f:
        f.write(svg)


def cell(href, base, alt, w):
    # floor to 1/100 %, so a full row never adds up past 100% and wraps
    pct = f"{math.floor(w / ROW_W * 10000) / 100:g}%"
    return (f'<a href="{html.escape(href)}"><picture>'
            f'<source media="(prefers-color-scheme: dark)" srcset="{base}.svg">'
            f'<source media="(prefers-color-scheme: light)" srcset="{base}-light.svg">'
            f'<img src="{base}.svg" width="{pct}" alt="{html.escape(alt)}" /></picture></a>')


# every link as (file stem relative to ROOT, href, alt, well, title, sub, mark),
# grouped into the rows they go in
tracks = load_tracks()
music = []
for tr in tracks:
    with open(os.path.join(ROOT, tr["art"]), "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    music.append((f"assets/music/{tr['track_id']}-link", tr["url"],
                  f"{tr['title']} by {tr['artist']} on Apple Music",
                  cover_well(b64), tr["title"], tr["artist"], "play"))
contacts = [(stem, href, f"{label}: {value}", icon_well(kind), label, value, "out")
            for stem, kind, label, value, href in CONTACTS]
rows = [music[i:i + COLS] for i in range(0, len(music), COLS)] + [contacts]

lines, keep = [], set()
for row in rows:
    cells = []
    for pos, (stem, href, alt, well, title, sub, mark) in enumerate(row):
        for suffix, t in THEMES.items():
            w, svg = tile(t, pos, len(row), well, title, sub, mark)
            path = os.path.join(ROOT, f"{stem}{suffix}.svg")
            write(path, svg)
            keep.add(os.path.abspath(path))
        cells.append(cell(href, f"./{stem}", alt, w))
        print(f"wrote {stem}{{,-light}}.svg  {w:g}x{TOP + TILE_H}")
    lines.append("".join(cells))
for path in glob.glob(os.path.join(ART_DIR, "*-link*.svg")):
    if os.path.abspath(path) not in keep:
        os.remove(path)
        print("removed", os.path.relpath(path, ROOT))

with open(README) as f:
    readme = f.read()
block = re.compile(r"(<!-- links:start -->\n).*?(<!-- links:end -->)", re.S)
if block.search(readme):
    # one line: a line break in the source after <br> turns into a second
    # <br> wherever GitHub renders newlines as breaks
    body = "<br>".join(lines) + "\n"
    readme = block.sub(lambda m: m.group(1) + body + m.group(2), readme)
    with open(README, "w") as f:
        f.write(readme)
    print(f"README: {len(rows)} row(s) between the links markers")
else:
    print("README: no <!-- links:start --> / <!-- links:end --> markers; left as is")
