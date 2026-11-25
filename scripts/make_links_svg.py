#!/usr/bin/env python3
"""
Generate the link "chips": small flat SVG buttons that replace stock
shields.io badges so the links row matches the dashboard -- GitHub's own page
background as the fill, a 1px Primer border, monospace type.

One file per link and per theme: links-<name>.svg (dark) and
links-<name>-light.svg (light). The README wraps each in <a><picture>, because
an SVG embedded via <img> cannot carry clickable areas itself.

The tracks in data/music.json (the board's "On repeat" card) get a chip each
too -- a play mark, the title and the artist -- written next to their covers
as assets/music/<id>-link.svg / <id>-link-light.svg and linked to the track
on Apple Music. The README lines between <!-- music:start --> and
<!-- music:end --> are rewritten to match the list, and chips of tracks no
longer on it are deleted. After editing the list: fetch_music_art.py, then
this script.

Usage: python scripts/make_links_svg.py   (stdlib only)
"""
import glob
import html
import json
import os
import re
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
MUSIC = os.path.join(ROOT, "data", "music.json")
ART_DIR = os.path.join(ROOT, "assets", "music")
README = os.path.join(ROOT, "README.md")
MAX_TRACKS = 6         # as many as the board's carousel shows

# Primer bgColor-default / borderColor-default / fgColor-default / fgColor-muted /
# fgColor-success (the accent mark)
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
DOT = 14               # room for the accent mark before the label

LINKS = [
    ("links-mail",      "mail",      "iam74k4@gmail.com"),
    ("links-discord",   "discord",   "@74k4"),
    ("links-instagram", "instagram", "@iam74k4"),
]


def text_w(s):
    """Monospace advance of s; wide (CJK) characters take two cells."""
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in s) * CHAR_W


def chip(t, mark, parts):
    """One chip: the accent mark, then parts = [(text, colour key), ...] in a row."""
    w = int(PAD_X * 2 + DOT + text_w("".join(s for s, _ in parts)) + 0.5)
    y = H / 2 + 4.5
    if mark == "play":
        m = (f'<path d="M{PAD_X} {H / 2 - 4.5}v9l7.5-4.5z" fill="{t["accent"]}" '
             f'stroke="{t["accent"]}" stroke-width="1.5" stroke-linejoin="round"/>')
    else:
        m = f'<circle cx="{PAD_X + 3}" cy="{H / 2}" r="3" fill="{t["accent"]}"/>'
    spans = "".join(f'<tspan fill="{t[k]}">{html.escape(s, quote=False)}</tspan>'
                    for s, k in parts)
    return w, (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{H}" '
        f'viewBox="0 0 {w} {H}" font-family="{MONO}">'
        f'<rect x="0.5" y="0.5" width="{w - 1}" height="{H - 1}" rx="6" '
        f'fill="{t["bg"]}" stroke="{t["border"]}"/>'
        f'{m}'
        f'<text x="{PAD_X + DOT}" y="{y:.1f}" font-size="{SIZE}" xml:space="preserve">'
        f'{spans}</text>'
        f'</svg>'
    )


def write(path, svg, w):
    with open(path, "w") as f:
        f.write(svg)
    print("wrote", os.path.relpath(path, ROOT), f"{w}x{H}")


def load_tracks():
    """The tracks the board shows: resolved (title, url) with a cover on disk."""
    if not os.path.exists(MUSIC):
        return []
    with open(MUSIC) as f:
        tracks = json.load(f).get("tracks", [])
    return [tr for tr in tracks
            if tr.get("title") and tr.get("url") and tr.get("art")
            and os.path.exists(os.path.join(ROOT, tr["art"]))][:MAX_TRACKS]


def readme_lines(tracks):
    lines = []
    for tr in tracks:
        base = f"./assets/music/{tr['track_id']}-link"
        alt = html.escape(f"{tr['title']} by {tr['artist']} on Apple Music")
        lines.append(
            f'<a href="{html.escape(tr["url"])}"><picture>'
            f'<source media="(prefers-color-scheme: dark)" srcset="{base}.svg">'
            f'<source media="(prefers-color-scheme: light)" srcset="{base}-light.svg">'
            f'<img src="{base}.svg" alt="{alt}" /></picture></a>')
    return lines


for suffix, t in THEMES.items():
    for name, label, value in LINKS:
        w, svg = chip(t, "dot", [(f"{label}  ", "muted"), (value, "fg")])
        write(os.path.join(ROOT, f"{name}{suffix}.svg"), svg, w)

tracks = load_tracks()
keep = set()
for tr in tracks:
    for suffix, t in THEMES.items():
        path = os.path.join(ART_DIR, f"{tr['track_id']}-link{suffix}.svg")
        w, svg = chip(t, "play", [(tr["title"], "fg"), (f"  {tr['artist']}", "muted")])
        write(path, svg, w)
        keep.add(os.path.abspath(path))
for path in glob.glob(os.path.join(ART_DIR, "*-link*.svg")):
    if os.path.abspath(path) not in keep:
        os.remove(path)
        print("removed", os.path.relpath(path, ROOT))

with open(README) as f:
    readme = f.read()
block = re.compile(r"(<!-- music:start -->\n).*?(<!-- music:end -->)", re.S)
if block.search(readme):
    body = "".join(line + "\n" for line in readme_lines(tracks))
    readme = block.sub(lambda m: m.group(1) + body + m.group(2), readme)
    with open(README, "w") as f:
        f.write(readme)
    print(f"README: {len(tracks)} track link(s) between the music markers")
else:
    print("README: no <!-- music:start --> / <!-- music:end --> markers; left as is")
