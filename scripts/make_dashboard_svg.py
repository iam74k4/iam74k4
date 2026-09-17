#!/usr/bin/env python3
"""
Render the whole profile as one dashboard SVG (profile.svg).

One image instead of six stacked panels: GitHub's markdown CSS then has
nothing to lay out, so the cards keep their exact positions and sizes at
every container width. The link chips stay separate files -- an SVG embedded
through <img> cannot carry clickable areas -- and remain the only pieces the
README wraps in a markdown link.

Measured numbers come from data/commit-activity.json (fetch_commit_activity.py);
the ASCII portrait is embedded from taka-ascii.svg as a nested <svg> whose
viewBox crops away that panel's own window chrome, so the art is reused rather
than regenerated (no Pillow needed here -- this script is stdlib only).

Usage: python scripts/make_dashboard_svg.py [data.json] [out.svg]
"""
import datetime
import html
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "data", "commit-activity.json")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "profile.svg")
PORTRAIT = os.path.join(ROOT, "taka-ascii.svg")

# palette -- same values as the panel generators
BG = "#080d12"
BG2 = "#0d141c"
FRAME = "#22303d"
GRAY = "#7e91a6"
INK = "#cbd5e1"
ACCENT = "#22d3ee"
LEVELS = ["#111c26", "#0b4f5e", "#0e7490", "#15a5c4", "#22d3ee"]

# self-declared; everything else on the board is measured
NAME = "Taka"
ROLE = "System Engineer"
FOCUS = "discord-bots · ai · financial-data"
LOCATION = "Japan · UTC+9"
STACK = [".net", "django", "docker", "gcp", "nginx", "mysql",
         "windows", "linux", "ubuntu", "vscode", "visual-studio"]

FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
CHAR = 0.6              # monospace advance as a fraction of font-size

W = 924
GAP = 14
PAD = 16
RAD = 10

A_W, A_H = 352, 350                      # portrait card
B_X, B_W = A_W + GAP, W - A_W - GAP      # whoami card
ROW2_Y, C_H = A_H + GAP, 184             # commit activity, full width
ROW3_Y = ROW2_Y + C_H + GAP
D_W = (W - GAP) // 2                     # languages | hours
E_X = D_W + GAP
ROW3_H = 190
FOOT_H = 26
H = ROW3_Y + ROW3_H + FOOT_H

CELL, CGAP = 12, 4                       # heatmap cell size / gutter
DAY_LBL_W = 30


def esc(s):
    return html.escape(str(s), quote=False)


def card(x, y, w, h):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{RAD}" fill="url(#cbg)"/>'
            f'<rect x="{x + 0.5}" y="{y + 0.5}" width="{w - 1}" height="{h - 1}" rx="{RAD}" '
            f'fill="none" stroke="{FRAME}"/>')


def label(x, y, s):
    return (f'<text x="{x}" y="{y}" fill="{GRAY}" font-size="11" font-weight="600" '
            f'letter-spacing="1.4">{esc(s.upper())}</text>')


def text(x, y, s, fill=INK, size=13, anchor=None, weight=None, cls=None, delay=None):
    a = f' text-anchor="{anchor}"' if anchor else ""
    w = f' font-weight="{weight}"' if weight else ""
    c = f' class="{cls}"' if cls else ""
    d = f' style="animation-delay:{delay}s"' if delay is not None else ""
    return (f'<text x="{x}" y="{y}" fill="{fill}" font-size="{size}"{a}{w}{c}{d}>'
            f'{esc(s)}</text>')


def portrait_svg(x, y, size):
    """The ASCII art from taka-ascii.svg, cropped to the art box (20,37,800,795)."""
    src = open(PORTRAIT).read()
    inner = src.split(">", 1)[1].rsplit("</svg>", 1)[0]     # drop its root <svg> tag
    return (f'<svg x="{x}" y="{y}" width="{size}" height="{size * 795 / 800:.1f}" '
            f'viewBox="20 37 800 795" preserveAspectRatio="xMidYMid meet">{inner}</svg>')


data = json.load(open(SRC))
contribs = data["contributions"]
total = data.get("total", {}).get("lastYear", sum(c["count"] for c in contribs))
stats = data.get("stats", {})
langs = data.get("languages", [])[:6]
hours = data.get("hours", [0] * 24)
tz = data.get("tz_offset", 9)
peak = max(range(24), key=lambda h: hours[h]) if any(hours) else 0

parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
    f'font-family="{FONT}">',
    f'''<style>
  .fade {{ opacity:0; animation:fade .45s ease-out both; }}
  .cell {{ opacity:0; transform-box:fill-box; transform-origin:center;
           animation:pop .45s ease-out both; }}
  .bar  {{ transform-box:fill-box; transform-origin:left center;
           animation:grow .8s cubic-bezier(.2,.8,.2,1) both; }}
  .hbar {{ transform-box:fill-box; transform-origin:bottom center;
           animation:rise .6s cubic-bezier(.2,.8,.2,1) both; }}
  @keyframes fade {{ from{{opacity:0}} to{{opacity:1}} }}
  @keyframes pop  {{ 0%{{opacity:0;transform:scale(.2)}} 60%{{opacity:1;transform:scale(1.1)}}
                     100%{{opacity:1;transform:scale(1)}} }}
  @keyframes grow {{ from{{transform:scaleX(0)}} to{{transform:scaleX(1)}} }}
  @keyframes rise {{ from{{transform:scaleY(0)}} to{{transform:scaleY(1)}} }}
  @media (prefers-reduced-motion: reduce) {{
    .fade,.cell,.bar,.hbar {{ opacity:1 !important; transform:none !important;
                              animation:none !important; }} }}
</style>''',
    f'<defs><linearGradient id="cbg" x1="0" y1="0" x2="0" y2="1">'
    f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/>'
    f'</linearGradient></defs>',
]

# ---------------------------------------------------------------- portrait
parts.append(card(0, 0, A_W, A_H))
parts.append(portrait_svg(PAD, PAD, A_W - PAD * 2))

# ------------------------------------------------------------------ whoami
bx = B_X + PAD
parts.append(card(B_X, 0, B_W, A_H))
parts.append(label(bx, 34, "whoami"))
parts.append(text(bx, 76, NAME, ACCENT, 30, weight=700, cls="fade", delay=0.1))
parts.append(text(bx + len(NAME) * 30 * CHAR + 14, 76, f"— {ROLE}", INK, 15,
                  cls="fade", delay=0.2))
parts.append(text(bx, 102, FOCUS, GRAY, 13, cls="fade", delay=0.3))
parts.append(text(bx, 124, LOCATION, GRAY, 13, cls="fade", delay=0.35))
parts.append(f'<line x1="{bx}" y1="146" x2="{B_X + B_W - PAD}" y2="146" stroke="{FRAME}"/>')

kpis = [(f"{total:,}", "commits · 365d"),
        (f'{stats.get("current_streak", 0)}d', "current streak"),
        (f'{stats.get("best_day", 0)}', "max / day"),
        (f"{peak:02d}:00", f"peak hour (utc+{tz})")]
for i, (value, cap) in enumerate(kpis):
    kx = bx + i * ((B_W - PAD * 2) // len(kpis))
    parts.append(text(kx, 192, value, ACCENT, 26, weight=700, cls="fade", delay=0.4 + i * 0.08))
    parts.append(text(kx, 210, cap, GRAY, 11, cls="fade", delay=0.45 + i * 0.08))

parts.append(label(bx, 252, "stack"))
cx, cy, avail = bx, 262, B_W - PAD * 2
for i, item in enumerate(STACK):
    cw = len(item) * 12 * CHAR + 20
    if cx + cw > bx + avail:
        cx, cy = bx, cy + 28
    parts.append(f'<g class="fade" style="animation-delay:{0.6 + i * 0.04:.2f}s">'
                 f'<rect x="{cx}" y="{cy}" width="{cw:.0f}" height="22" rx="6" fill="none" '
                 f'stroke="{FRAME}"/>'
                 f'{text(cx + 10, cy + 15, item, INK, 12)}</g>')
    cx += cw + 6

# --------------------------------------------------------- commit activity
parts.append(card(0, ROW2_Y, W, C_H))
parts.append(label(PAD, ROW2_Y + 28, "commit activity — last 12 months"))
parts.append(
    f'<text x="{W - PAD}" y="{ROW2_Y + 28}" font-size="12" text-anchor="end" class="fade" '
    f'style="animation-delay:.5s">'
    f'<tspan fill="{ACCENT}" font-weight="700">{total:,}</tspan>'
    f'<tspan fill="{GRAY}"> commits · streak </tspan>'
    f'<tspan fill="{ACCENT}" font-weight="700">{stats.get("current_streak", 0)}d</tspan>'
    f'<tspan fill="{GRAY}"> · longest </tspan>'
    f'<tspan fill="{ACCENT}" font-weight="700">{stats.get("longest_streak", 0)}d</tspan>'
    f'<tspan fill="{GRAY}"> · max </tspan>'
    f'<tspan fill="{ACCENT}" font-weight="700">{stats.get("best_day", 0)}</tspan>'
    f'<tspan fill="{GRAY}">/day</tspan></text>')

gx, gy = PAD + DAY_LBL_W, ROW2_Y + 62
weeks = (len(contribs) + 6) // 7
start = datetime.date.fromisoformat(contribs[0]["date"])
last_month, last_lbl = None, -3
for wk in range(weeks):
    d = start + datetime.timedelta(days=wk * 7)
    if d.month != last_month:
        last_month = d.month
        if wk - last_lbl >= 3:
            parts.append(text(gx + wk * (CELL + CGAP), gy - 8,
                              d.strftime("%b"), GRAY, 11))
            last_lbl = wk
for name, row in [("Mon", 1), ("Wed", 3), ("Fri", 5)]:
    parts.append(text(PAD, gy + row * (CELL + CGAP) + CELL - 2, name, GRAY, 11))
for i, c in enumerate(contribs):
    wk, row = i // 7, i % 7
    delay = 0.35 + (wk + row * 0.5) / weeks * 1.1
    parts.append(
        f'<rect class="cell" x="{gx + wk * (CELL + CGAP)}" y="{gy + row * (CELL + CGAP)}" '
        f'width="{CELL}" height="{CELL}" rx="3" fill="{LEVELS[c["level"]]}" '
        f'style="animation-delay:{delay:.2f}s"/>')

# -------------------------------------------------------------- languages
parts.append(card(0, ROW3_Y, D_W, ROW3_H))
parts.append(label(PAD, ROW3_Y + 28, "languages (by bytes)"))
track_x, track_w = PAD + 96, D_W - PAD * 2 - 96 - 52
for i, (name, pct) in enumerate(langs):
    ly = ROW3_Y + 54 + i * 23
    parts.append(text(PAD, ly + 4, name.lower(), INK, 12.5))
    parts.append(f'<rect x="{track_x}" y="{ly - 4}" width="{track_w}" height="8" rx="4" '
                 f'fill="{LEVELS[0]}"/>')
    parts.append(f'<rect class="bar" x="{track_x}" y="{ly - 4}" '
                 f'width="{max(track_w * pct / 100, 3):.1f}" height="8" rx="4" fill="{ACCENT}" '
                 f'style="animation-delay:{0.3 + i * 0.07:.2f}s"/>')
    parts.append(text(D_W - PAD, ly + 4, f"{pct:.1f}%", GRAY, 12, anchor="end"))

# ------------------------------------------------------------ commits/hour
parts.append(card(E_X, ROW3_Y, D_W, ROW3_H))
parts.append(label(E_X + PAD, ROW3_Y + 28, f"commits by hour (utc+{tz})"))
base, hmax = ROW3_Y + 140, max(hours) or 1
bw, bpitch = 12, (D_W - PAD * 2 - 12) / 24
for h, n in enumerate(hours):
    bh = max(n / hmax * 74, 2)
    parts.append(f'<rect class="hbar" x="{E_X + PAD + h * bpitch:.1f}" y="{base - bh:.1f}" '
                 f'width="{bw}" height="{bh:.1f}" rx="2" '
                 f'fill="{ACCENT if h == peak else LEVELS[2]}" '
                 f'style="animation-delay:{0.3 + h * 0.02:.2f}s"/>')
for h in (0, 6, 12, 18, 23):
    parts.append(text(E_X + PAD + h * bpitch + bw / 2, base + 18, f"{h}", GRAY, 11,
                      anchor="middle"))
parts.append(
    f'<text x="{E_X + PAD}" y="{ROW3_Y + 176}" font-size="12.5" class="fade" '
    f'style="animation-delay:.8s"><tspan fill="{GRAY}">peak </tspan>'
    f'<tspan fill="{ACCENT}" font-weight="700">{peak:02d}:00</tspan>'
    f'<tspan fill="{GRAY}"> · {hours[peak]} commits · </tspan>'
    f'<tspan fill="{INK}">{sum(hours[9:18])}</tspan>'
    f'<tspan fill="{GRAY}"> of {sum(hours)} in office hours</tspan></text>')

# ------------------------------------------------------------------ footer
parts.append(text(PAD, H - 8, "commits on public repos (default branches), counted "
                  "through the GitHub REST API", GRAY, 11))
parts.append(text(W - PAD, H - 8, f"updated {datetime.date.today().isoformat()}",
                  GRAY, 11, anchor="end"))

parts.append("</svg>")

svg = "".join(parts)
with open(OUT, "w") as f:
    f.write(svg)
print(f"wrote {OUT} {W}x{H} {len(svg)} bytes; "
      f"{total} commits, {len(langs)} languages, peak hour {peak}")
