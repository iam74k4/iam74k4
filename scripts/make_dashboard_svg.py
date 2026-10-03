#!/usr/bin/env python3
"""
Render the profile board (profile.svg) in AstLog's design.

The board is laid out like the AstLog landing page: the copy column on the
left (eyebrow, headline, lead), the star system on the right, a tally of
counts underneath, then languages and stack. One black sheet, square
corners, sections divided by hairlines rather than boxed into cards; white
type on black with no accent colour (only the nebula has colour). Sans for
the copy, monospace only for the English labels and numbers.

The star system is baked once into cosmos.svg (make_cosmos_svg.mjs) and
embedded here as a nested <svg>, the way the old board embedded the ASCII
portrait, so this script stays stdlib-only for the daily Action. cosmos.svg
darkens the sky under the copy column and records that box as data-copy;
copy that would spill out of it stops the build (nothing may sit behind the
text). Everything that changes daily -- the tally, languages, the date -- is
drawn here from data/commit-activity.json (fetch_commit_activity.py).

One image instead of loose panels: GitHub's markdown CSS then has nothing to
lay out, so the board keeps its exact positions at every width. The links
stay separate files (make_links_svg.py): an SVG behind <img> cannot carry
clickable areas, and nothing on the board may look pushable.

Usage: python scripts/make_dashboard_svg.py [data.json] [out.svg]
"""
import datetime
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "data", "commit-activity.json")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "profile.svg")
COSMOS = os.path.join(ROOT, "cosmos.svg")

# palette -- AstLog's public/app.css :root with the default mono accent
BG = "#0c0c0e"
INK = "#f2f2f4"
INK_MID = "#b4b4c2"
INK_WEAK = "#8a8a96"
LINE_OPACITY = 0.07     # --line: white at 7%

SANS = "'Helvetica Neue','Hiragino Sans','Noto Sans JP',system-ui,-apple-system,sans-serif"
MONO = "ui-monospace,'SFMono-Regular','SF Mono',Menlo,Consolas,monospace"
# AstLog's six static type steps (px). 11 is for English capitals only;
# Japanese never goes below 12
FS_LABEL, FS_META, FS_SM, FS_BASE, FS_MD = 11, 12, 13, 14, 15
TRACKING = 0.16         # letter-spacing of the capital labels (em)
MONO_ADVANCE = 0.6      # monospace advance as a fraction of font-size

# self-declared; everything in the tally and the rows is measured
NAME = "Taka"
ROLE = "System Engineer"
LOCATION = "Japan"
# the same sentence as AstLog's headline, broken at phrase boundaries
HEADLINE = ["つくる工程", "そのものを、", "速くする。"]
LEAD = ["個人でつくったアプリと、仕事で取り組んだ", "開発効率化を AstLog にまとめています。"]
STACK = [".NET", "Django", "Docker", "Google Cloud", "nginx", "MySQL",
         "Windows", "Linux", "Ubuntu", "VS Code", "Visual Studio"]

# AstLog's spring (--ease-spring) and arrival timing: the copy rises at once,
# the tally after the orbits are traced (cosmos.svg T.count)
SPRING = ("linear(0,0.008 1.5%,0.032 3%,0.068 4.5%,0.13 6.5%,0.246 9.5%,0.628 18.5%,"
          "0.739 21.5%,0.834 24.5%,0.901 27%,0.965 30%,1.007 32.5%,1.043 35.5%,1.076 40.5%,"
          "1.083 46%,1.071 52%,1.02 67%,1.003 75%,0.993 88%,0.995 99.5%,1)")
STAGGER = 90
COUNT_DELAY = 2600

W = 860
PAD = 32
# copy column
EYEBROW_Y = 70
H1_SIZE, H1_LH, H1_Y = 44, 55, 130
LEAD_LH, LEAD_Y = 28, 290
# tally, rows and footer
TALLY_RULE = 372
TALLY_NUM = TALLY_RULE + 46
TALLY_LABEL = TALLY_NUM + 22
ROWS_RULE = TALLY_LABEL + 34
ROW_X = PAD + 112
ROW_W = W - PAD - ROW_X
ROW_LH = 20


def esc(s):
    return html.escape(str(s), quote=False)


def is_wide(ch):
    return ord(ch) >= 0x2E80


def text_width(s, size, mono=False, tracking=0.0):
    """A generous estimate: CJK at a full em, Latin at the wide end of system sans."""
    if mono:
        return len(s) * size * (MONO_ADVANCE + tracking)
    em = 0.0
    for ch in s:
        if is_wide(ch):
            em += 1.0
        elif ch == " ":
            em += 0.3
        elif ch.isupper() or ch in "mw":
            em += 0.7
        else:
            em += 0.56
    return em * size + len(s) * size * tracking


def wrap_balanced(items, max_chars, sep=" · "):
    """Fewest lines that fit, then items spread so the lines end up about even.
    An item longer than a line gets a line of its own rather than no answer."""
    total = len(sep.join(items))
    lines = max(1, -(-total // max_chars))
    while lines < len(items):
        target = total / lines
        out, line = [], []
        for item in items:
            candidate = sep.join(line + [item])
            if line and (len(candidate) > max_chars or len(sep.join(line)) >= target):
                out.append(line)
                line = [item]
            else:
                line.append(item)
        out.append(line)
        if len(out) <= lines and all(len(sep.join(l)) <= max_chars for l in out):
            return out
        lines += 1
    return [[item] for item in items]


def cosmos():
    """cosmos.svg as a nested <svg>, plus the box its veil keeps dark."""
    src = open(COSMOS, encoding="utf-8").read()
    head_end = src.index(">", src.index("<svg")) + 1
    head = src[:head_end]
    attr = lambda name: re.search(rf'\s{name}="([^"]*)"', head).group(1)
    width, height = float(attr("width")), float(attr("height"))
    if width != W:
        sys.exit(f"cosmos.svg is {width:g} wide; the board is {W}")
    copy_box = [float(v) for v in attr("data-copy").split()]
    inner = src[head_end:src.rindex("</svg>")]
    return (f'<svg x="0" y="0" width="{width:g}" height="{height:g}" '
            f'viewBox="0 0 {width:g} {height:g}">{inner}</svg>'), copy_box


data = json.load(open(SRC))
contribs = data["contributions"]
total = data.get("total", {}).get("lastYear", sum(c["count"] for c in contribs))
stats = data.get("stats", {})
langs = [(n, p) for n, p in data.get("languages", []) if p >= 1][:6]
hours = data.get("hours", [0] * 24)
tz = data.get("tz_offset", 9)
peak = max(range(24), key=lambda h: hours[h]) if any(hours) else 0

art, (_, _, copy_right, copy_bottom) = cosmos()

# the copy has to stay on the dark ground cosmos.svg lays under it
copy_lines = ([(PAD, EYEBROW_Y, text_width(f"{ROLE} — {LOCATION}".upper(), FS_LABEL, True, TRACKING))]
              + [(PAD - 2, H1_Y + i * H1_LH, text_width(s, H1_SIZE)) for i, s in enumerate(HEADLINE)]
              + [(PAD, LEAD_Y + i * LEAD_LH, text_width(s, FS_MD)) for i, s in enumerate(LEAD)])
for x, y, w in copy_lines:
    if x + w > copy_right or y > copy_bottom:
        sys.exit(f"copy at y={y} runs to x={x + w:.0f}; cosmos.svg darkens up to "
                 f"x={copy_right:g}, y={copy_bottom:g} (widen COPY in make_cosmos_svg.mjs or shorten the line)")


def rule(y):
    return (f'<line x1="{PAD}" y1="{y + 0.5}" x2="{W - PAD}" y2="{y + 0.5}" '
            f'stroke="#fff" stroke-opacity="{LINE_OPACITY}"/>')


def text(x, y, s, cls, extra=""):
    return f'<text x="{x}" y="{y}" class="{cls}"{extra}>{esc(s)}</text>'


def tags(x, y, items):
    """One row of English labels (markup) joined by middle dots (AstLog's tag row)."""
    body = "".join(('<tspan class="dim"> · </tspan>' if i else "") + item
                   for i, item in enumerate(items))
    return f'<text x="{x}" y="{y}" class="tags">{body}</text>'


STYLE = f'''<style>
text{{font-family:{SANS}}}
.eyebrow,.label{{font-family:{MONO};font-size:{FS_LABEL}px;letter-spacing:{TRACKING}em;fill:{INK_WEAK}}}
.h1{{font-size:{H1_SIZE}px;font-weight:600;letter-spacing:-.02em;font-feature-settings:'palt';fill:{INK}}}
.lead{{font-size:{FS_MD}px;fill:{INK_MID}}}
.num{{font-size:30px;font-weight:300;letter-spacing:-.02em;font-variant-numeric:tabular-nums;fill:{INK}}}
.tags{{font-family:{MONO};font-size:{FS_META}px;fill:{INK_MID}}}
.dim{{fill:{INK_WEAK}}}
.name{{font-size:{FS_BASE}px;font-weight:600;fill:{INK}}}
.role{{font-size:{FS_SM}px;fill:{INK_MID}}}
@keyframes rise{{from{{opacity:0;transform:translateY(12px)}}}}
@media (prefers-reduced-motion:no-preference){{.rise{{animation:rise 640ms {SPRING} backwards}}}}
</style>'''

# the height is known only once the rows have wrapped, so the root goes on last
parts = [art]

# ------------------------------------------------------------------ copy
parts.append(text(PAD, EYEBROW_Y, f"{ROLE} — {LOCATION}".upper(), "eyebrow rise"))
for i, line in enumerate(HEADLINE):
    parts.append(text(PAD - 2, H1_Y + i * H1_LH, line, "h1 rise",
                      f' style="animation-delay:{(i + 1) * STAGGER}ms"'))
for i, line in enumerate(LEAD):
    parts.append(text(PAD, LEAD_Y + i * LEAD_LH, line, "lead rise",
                      f' style="animation-delay:{(len(HEADLINE) + 1) * STAGGER}ms"'))

# ------------------------------------------------------------------ tally
tally = [(f"{total:,}", "COMMITS · 365D"),
         (f'{stats.get("current_streak", 0)}', "DAY STREAK"),
         (f'{stats.get("best_day", 0)}', "MAX / DAY"),
         (f"{peak:02d}:00", f"PEAK · UTC+{tz}")]
parts.append(rule(TALLY_RULE))
cell = (W - PAD * 2) / len(tally)
for i, (value, cap) in enumerate(tally):
    x = round(PAD + i * cell, 1)
    parts.append(f'<g class="rise" style="animation-delay:{COUNT_DELAY + i * STAGGER}ms">'
                 f'{text(x, TALLY_NUM, value, "num")}{text(x, TALLY_LABEL, cap, "label")}</g>')

# ------------------------------------------------------------ languages
# one hairline split by byte share; no colours, just steps of the ink
parts.append(rule(ROWS_RULE))
bar_y = ROWS_RULE + 28
parts.append(text(PAD, bar_y + 4, "LANGUAGES", "label"))
gap, inks = 3, [1, 0.62, 0.44, 0.32, 0.24, 0.18]
share = sum(p for _, p in langs) or 1
bx = ROW_X
for i, (_, pct) in enumerate(langs):
    seg = max(2, pct / share * (ROW_W - gap * (len(langs) - 1)))
    parts.append(f'<rect x="{bx:.1f}" y="{bar_y - 1}" width="{seg:.1f}" height="2" '
                 f'fill="{INK}" fill-opacity="{inks[i]}"/>')
    bx += seg + gap
max_chars = int(ROW_W // (FS_META * MONO_ADVANCE))
legend = [f'{esc(name)}<tspan class="dim"> {pct:.1f}%</tspan>' for name, pct in langs]
y, done = bar_y + 22, 0
for line in wrap_balanced([f"{name} {pct:.1f}%" for name, pct in langs], max_chars):
    parts.append(tags(ROW_X, y, legend[done:done + len(line)]))
    done += len(line)
    y += ROW_LH

# ---------------------------------------------------------------- stack
y += 10
parts.append(text(PAD, y, "STACK", "label"))
for line in wrap_balanced(STACK, max_chars):
    parts.append(tags(ROW_X, y, [esc(item) for item in line]))
    y += ROW_LH

# --------------------------------------------------------------- footer
foot_rule = y + 4
foot_y = foot_rule + 30
H = foot_y + 22
parts.append(rule(foot_rule))
parts.append(f'<text x="{PAD}" y="{foot_y}"><tspan class="name">{esc(NAME)}</tspan>'
             f'<tspan class="role" dx="10">{esc(ROLE)}</tspan></text>')
parts.append(text(W - PAD, foot_y,
                  f"PUBLIC REPOS · DEFAULT BRANCHES · UPDATED {datetime.date.today().isoformat()}",
                  "label", ' text-anchor="end"'))
title = (f"{NAME} — {ROLE}。{''.join(HEADLINE)}{''.join(LEAD)} "
         f"過去365日のコミット {total:,}、連続 {stats.get('current_streak', 0)} 日、"
         f"1日の最多 {stats.get('best_day', 0)}、よく書く時刻 {peak:02d}:00（UTC+{tz}）。")
svg = "".join([
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
    f'xml:lang="ja" role="img" aria-labelledby="title">',
    f'<title id="title">{esc(title)}</title>',
    STYLE,
    f'<rect width="{W}" height="{H}" fill="{BG}"/>',
    *parts,
    "</svg>",
])
with open(OUT, "w", encoding="utf-8") as f:
    f.write(svg)
print(f"wrote {OUT} {W}x{H} {len(svg.encode()) // 1024}KB; "
      f"{total} commits, {len(langs)} languages, peak hour {peak}")
