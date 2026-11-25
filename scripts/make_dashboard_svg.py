#!/usr/bin/env python3
"""
Render the whole profile as one dashboard SVG, once per GitHub theme:
profile.svg (dark) and profile-light.svg (light). The README picks one with
<picture> + prefers-color-scheme, which GitHub resolves from the viewer's theme.

One image instead of six stacked panels: GitHub's markdown CSS then has
nothing to lay out, so the cards keep their exact positions and sizes at
every container width. The link chips stay separate files -- an SVG embedded
through <img> cannot carry clickable areas -- and remain the only pieces the
README wraps in a link.

Flat on purpose: every surface is filled with GitHub's own page background
(Primer bgColor-default), cards are told apart by a 1px border only, and
there are no gradients or shadows. Every colour is a Primer token
(@primer/primitives 11.10), the accent included: fgColor-success, with the
contribution graph's own greens for the heatmap.

Measured numbers come from data/commit-activity.json (fetch_commit_activity.py);
the ASCII portrait is embedded from taka-ascii.svg as a nested <svg> whose
viewBox crops away that panel's own window chrome, and is recoloured per theme,
so the art is reused rather than regenerated (no Pillow needed here -- this
script is stdlib only).

Usage: python scripts/make_dashboard_svg.py [data.json] [dark.svg] [light.svg]
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
OUT_DARK = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "profile.svg")
OUT_LIGHT = sys.argv[3] if len(sys.argv) > 3 else os.path.join(ROOT, "profile-light.svg")
PORTRAIT = os.path.join(ROOT, "taka-ascii.svg")

# Primer tokens: bg = bgColor-default (the page itself), border = borderColor-default,
# fg / muted = fgColor-default / fgColor-muted, accent = fgColor-success,
# levels = contribution-default-bgColor-0..4 (GitHub's own contribution greens).
THEMES = {
    "dark": {
        "bg": "#0d1117", "border": "#3d444d", "fg": "#f0f6fc", "muted": "#9198a1",
        "art": "#d1d9e0", "accent": "#3fb950",
        "levels": ["#151b23", "#033a16", "#196c2e", "#2ea043", "#56d364"],
    },
    "light": {
        "bg": "#ffffff", "border": "#d1d9e0", "fg": "#1f2328", "muted": "#59636e",
        "art": "#424a53", "accent": "#1a7f37",
        "levels": ["#eff2f5", "#aceebb", "#4ac26b", "#2da44e", "#116329"],
    },
}
# colours taka-ascii.svg is drawn in (make_ascii_svg.py) -> theme key they become
PORTRAIT_COLORS = {"#d1d9e0": "art", "#3fb950": "accent", "#9198a1": "muted"}

# self-declared; everything else on the board is measured
NAME = "Taka"
ROLE = "System Engineer"
FOCUS = "discord-bots · ai · financial-data"
LOCATION = "Japan · UTC+9"
STACK = [".net", "django", "docker", "gcp", "nginx", "mysql",
         "windows", "linux", "ubuntu", "vscode", "visual-studio"]

SANS = ("-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans',Helvetica,Arial,"
        "sans-serif")
MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace"
CHAR = 0.6              # monospace advance as a fraction of font-size

W = 924
GAP = 16
PAD = 20
RAD = 12                # Primer borderRadius-large

A_W, A_H = 352, 352                      # portrait card
B_X, B_W = A_W + GAP, W - A_W - GAP      # profile card
ROW2_Y, C_H = A_H + GAP, 224             # commit activity, full width
ROW3_Y = ROW2_Y + C_H + GAP
D_W = (W - GAP) // 2                     # languages | hours
E_X = W - D_W
ROW3_H = 214
FOOT_H = 30
H = ROW3_Y + ROW3_H + FOOT_H

CELL, CGAP = 12, 4                       # heatmap cell size / gutter
DAY_LBL_W = 32


def esc(s):
    return html.escape(str(s), quote=False)


def attrs(**kw):
    return "".join(f' {k.rstrip("_").replace("_", "-")}="{v}"'
                   for k, v in kw.items() if v is not None)


def text(x, y, s, fill, size=13, cls="sans", anchor=None, weight=None, delay=None, fade=False):
    c = f"{cls} fade" if fade or delay is not None else cls
    st = f"animation-delay:{delay}s" if delay is not None else None
    return (f'<text{attrs(x=x, y=y, fill=fill, font_size=size, class_=c, text_anchor=anchor, font_weight=weight, style=st)}>'
            f'{esc(s)}</text>')


def portrait_svg(t, x, y, size):
    """The ASCII art from taka-ascii.svg, cropped to the art box (20,37,800,795),
    with its own background dropped so the card shows through."""
    src = open(PORTRAIT).read()
    inner = src.split(">", 1)[1].rsplit("</svg>", 1)[0]     # drop its root <svg> tag
    inner = re.sub(r'<rect width="[\d.]+" height="[\d.]+" rx="12" fill="[^"]*"/>', "",
                   inner, count=1)                           # its own background
    inner = re.sub(r"<line [^>]*/>", "", inner)              # chrome rules at the crop edge
    inner = re.sub("|".join(map(re.escape, PORTRAIT_COLORS)),  # one pass: no chained swaps
                   lambda m: t[PORTRAIT_COLORS[m.group(0)]], inner)
    return (f'<svg x="{x}" y="{y}" width="{size}" height="{size * 795 / 800:.1f}" '
            f'viewBox="20 37 800 795" preserveAspectRatio="xMidYMid meet">{inner}</svg>')


def render(t, data):
    contribs = data["contributions"]
    total = data.get("total", {}).get("lastYear", sum(c["count"] for c in contribs))
    stats = data.get("stats", {})
    langs = data.get("languages", [])[:6]
    hours = data.get("hours", [0] * 24)
    tz = data.get("tz_offset", 9)
    peak = max(range(24), key=lambda h: hours[h]) if any(hours) else 0
    bg, border, fg, muted, accent, lv = (t["bg"], t["border"], t["fg"], t["muted"],
                                         t["accent"], t["levels"])

    def card(x, y, w, h):
        # one flat rect: page-coloured fill, 1px border, nothing else
        return (f'<rect x="{x + 0.5}" y="{y + 0.5}" width="{w - 1}" height="{h - 1}" '
                f'rx="{RAD}" fill="{bg}" stroke="{border}"/>')

    def heading(x, y, title, note=None):
        n = (f'<tspan fill="{muted}" font-weight="400">  {esc(note)}</tspan>'
             if note else "")
        return (f'<text x="{x}" y="{y}" class="sans" fill="{fg}" font-size="14" '
                f'font-weight="600">{esc(title)}{n}</text>')

    def rule(x1, y1, x2, y2):
        return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{border}"/>'

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}">',
        f'''<style>
  .sans {{ font-family:{SANS}; }}
  .mono {{ font-family:{MONO}; }}
  .fade {{ opacity:0; animation:fade .45s ease-out both; }}
  .cell {{ opacity:0; transform-box:fill-box; transform-origin:center;
           animation:pop .4s ease-out both; }}
  .bar  {{ transform-box:fill-box; transform-origin:left center;
           animation:grow .8s cubic-bezier(.2,.8,.2,1) both; }}
  .hbar {{ transform-box:fill-box; transform-origin:bottom center;
           animation:rise .6s cubic-bezier(.2,.8,.2,1) both; }}
  @keyframes fade {{ from{{opacity:0}} to{{opacity:1}} }}
  @keyframes pop  {{ from{{opacity:0;transform:scale(.4)}} to{{opacity:1;transform:scale(1)}} }}
  @keyframes grow {{ from{{transform:scaleX(0)}} to{{transform:scaleX(1)}} }}
  @keyframes rise {{ from{{transform:scaleY(0)}} to{{transform:scaleY(1)}} }}
  @media (prefers-reduced-motion: reduce) {{
    .fade,.cell,.bar,.hbar {{ opacity:1 !important; transform:none !important;
                              animation:none !important; }} }}
</style>''',
        # the page colour behind everything, so the image is never see-through
        f'<rect width="{W}" height="{H}" fill="{bg}"/>',
    ]

    # ------------------------------------------------------------ portrait
    p = 18
    parts.append(card(0, 0, A_W, A_H))
    parts.append(portrait_svg(t, p, p + 1, A_W - p * 2))

    # ------------------------------------------------------------- profile
    bx, bw = B_X + PAD, B_W - PAD * 2
    parts.append(card(B_X, 0, B_W, A_H))
    parts.append(text(bx, 56, NAME, fg, 30, weight=700, delay=0.1))
    parts.append(text(bx, 82, ROLE, fg, 16, delay=0.18))
    parts.append(f'<g class="fade" style="animation-delay:.26s">'
                 f'<circle cx="{bx + 4}" cy="{104}" r="4" fill="{accent}"/>'
                 f'{text(bx + 16, 108.5, FOCUS, muted, 13)}'
                 f'<circle cx="{bx + 4}" cy="{126}" r="4" fill="none" stroke="{muted}" '
                 f'stroke-width="1.5"/>'
                 f'{text(bx + 16, 130.5, LOCATION, muted, 13)}</g>')
    parts.append(rule(B_X, 154.5, B_X + B_W, 154.5))

    kpis = [(f"{total:,}", "commits · 365d"),
            (f'{stats.get("current_streak", 0)}d', "current streak"),
            (f'{stats.get("best_day", 0)}', "max / day"),
            (f"{peak:02d}:00", f"peak hour · utc+{tz}")]
    for i, (value, cap) in enumerate(kpis):
        kx = B_X + round(i * B_W / len(kpis))
        if i:
            parts.append(rule(kx + 0.5, 154.5, kx + 0.5, 236.5))
        parts.append(text(kx + PAD, 196, value, fg, 24, weight=600, delay=0.35 + i * 0.07))
        parts.append(text(kx + PAD, 218, cap, muted, 12, delay=0.4 + i * 0.07))
    parts.append(rule(B_X, 236.5, B_X + B_W, 236.5))

    parts.append(heading(bx, 268, "Stack"))
    cx, cy = bx, 282
    for i, item in enumerate(STACK):
        cw = len(item) * 12 * CHAR + 22
        if cx + cw > bx + bw:
            cx, cy = bx, cy + 32
        parts.append(f'<g class="fade" style="animation-delay:{0.55 + i * 0.035:.2f}s">'
                     f'<rect x="{cx + 0.5:.1f}" y="{cy + 0.5}" width="{cw - 1:.1f}" height="25" '
                     f'rx="12.5" fill="{bg}" stroke="{border}"/>'
                     f'{text(f"{cx + 11:.1f}", cy + 17, item, fg, 12, cls="mono")}</g>')
        cx += cw + 8

    # ----------------------------------------------------- commit activity
    parts.append(card(0, ROW2_Y, W, C_H))
    parts.append(heading(PAD, ROW2_Y + 34, "Commit activity", "last 12 months"))
    parts.append(
        f'<text x="{W - PAD}" y="{ROW2_Y + 34}" class="sans fade" font-size="13" '
        f'text-anchor="end" style="animation-delay:.5s">'
        f'<tspan fill="{fg}" font-weight="600">{total:,}</tspan>'
        f'<tspan fill="{muted}"> commits  ·  streak </tspan>'
        f'<tspan fill="{fg}" font-weight="600">{stats.get("current_streak", 0)}d</tspan>'
        f'<tspan fill="{muted}">  ·  longest </tspan>'
        f'<tspan fill="{fg}" font-weight="600">{stats.get("longest_streak", 0)}d</tspan>'
        f'<tspan fill="{muted}">  ·  max </tspan>'
        f'<tspan fill="{fg}" font-weight="600">{stats.get("best_day", 0)}</tspan>'
        f'<tspan fill="{muted}">/day</tspan></text>')

    weeks = (len(contribs) + 6) // 7
    grid_w = weeks * (CELL + CGAP) - CGAP
    gx = (W - grid_w + DAY_LBL_W) // 2               # centre grid + day labels
    gy = ROW2_Y + 68
    start = datetime.date.fromisoformat(contribs[0]["date"])
    last_month, last_lbl = None, -3
    for wk in range(weeks):
        d = start + datetime.timedelta(days=wk * 7)
        if d.month != last_month:
            last_month = d.month
            if wk - last_lbl >= 3:
                parts.append(text(gx + wk * (CELL + CGAP), gy - 9, d.strftime("%b"), muted, 12))
                last_lbl = wk
    for name, row in [("Mon", 1), ("Wed", 3), ("Fri", 5)]:
        parts.append(text(gx - DAY_LBL_W, gy + row * (CELL + CGAP) + CELL - 2, name, muted, 12))
    for i, c in enumerate(contribs):
        wk, row = i // 7, i % 7
        delay = 0.35 + (wk + row * 0.5) / weeks * 1.1
        parts.append(
            f'<rect class="cell" x="{gx + wk * (CELL + CGAP)}" y="{gy + row * (CELL + CGAP)}" '
            f'width="{CELL}" height="{CELL}" rx="2.5" fill="{lv[c["level"]]}" '
            f'style="animation-delay:{delay:.2f}s"/>')

    # legend, GitHub-style: Less [] [] [] [] [] More
    ly = gy + 7 * (CELL + CGAP) + 12
    more_x = gx + grid_w                              # "More" ends flush with the grid
    lx = more_x - 38 - (5 * (CELL + CGAP) - CGAP)
    parts.append(text(lx - 8, ly + CELL - 2, "Less", muted, 12, anchor="end"))
    for k in range(5):
        parts.append(f'<rect x="{lx + k * (CELL + CGAP)}" y="{ly}" width="{CELL}" '
                     f'height="{CELL}" rx="2.5" fill="{lv[k]}"/>')
    parts.append(text(more_x, ly + CELL - 2, "More", muted, 12, anchor="end"))

    # ---------------------------------------------------------- languages
    parts.append(card(0, ROW3_Y, D_W, ROW3_H))
    parts.append(heading(PAD, ROW3_Y + 34, "Languages", "by bytes"))
    track_x, track_w = PAD + 100, D_W - PAD * 2 - 100 - 58
    for i, (name, pct) in enumerate(langs):
        ly = ROW3_Y + 66 + i * 24
        parts.append(text(PAD, ly + 4.5, name, fg, 13))
        parts.append(f'<rect x="{track_x}" y="{ly - 4}" width="{track_w}" height="8" rx="4" '
                     f'fill="{lv[0]}"/>')
        parts.append(f'<rect class="bar" x="{track_x}" y="{ly - 4}" '
                     f'width="{max(track_w * pct / 100, 4):.1f}" height="8" rx="4" '
                     f'fill="{accent}" style="animation-delay:{0.3 + i * 0.07:.2f}s"/>')
        parts.append(text(D_W - PAD, ly + 4.5, f"{pct:.1f}%", muted, 12, cls="mono",
                          anchor="end"))

    # -------------------------------------------------------- commits/hour
    parts.append(card(E_X, ROW3_Y, D_W, ROW3_H))
    parts.append(heading(E_X + PAD, ROW3_Y + 34, "Commits by hour", f"UTC+{tz}"))
    base, hmax = ROW3_Y + 148, max(hours) or 1
    bw_, bpitch = 12, (D_W - PAD * 2 - 12) / 23
    parts.append(rule(E_X + PAD, base + 0.5, E_X + D_W - PAD, base + 0.5))
    for h, n in enumerate(hours):
        bh = max(n / hmax * 84, 2)
        parts.append(f'<rect class="hbar" x="{E_X + PAD + h * bpitch:.1f}" y="{base - bh:.1f}" '
                     f'width="{bw_}" height="{bh:.1f}" rx="2" '
                     f'fill="{accent if h == peak else lv[2]}" '
                     f'style="animation-delay:{0.3 + h * 0.02:.2f}s"/>')
    for h in (0, 6, 12, 18, 23):
        parts.append(text(f"{E_X + PAD + h * bpitch + bw_ / 2:.1f}", base + 20, f"{h:02d}",
                          muted, 12, cls="mono", anchor="middle"))
    parts.append(
        f'<text x="{E_X + PAD}" y="{ROW3_Y + ROW3_H - 18}" class="sans fade" font-size="13" '
        f'style="animation-delay:.8s"><tspan fill="{muted}">peak </tspan>'
        f'<tspan fill="{fg}" font-weight="600">{peak:02d}:00</tspan>'
        f'<tspan fill="{muted}">  ·  {hours[peak]} commits  ·  </tspan>'
        f'<tspan fill="{fg}" font-weight="600">{sum(hours[9:18])}</tspan>'
        f'<tspan fill="{muted}"> of {sum(hours)} in office hours</tspan></text>')

    # -------------------------------------------------------------- footer
    parts.append(text(4, H - 9, "Commits on public repos (default branches), counted "
                      "through the GitHub REST API", muted, 12))
    parts.append(text(W - 4, H - 9, f"Updated {datetime.date.today().isoformat()}",
                      muted, 12, anchor="end"))

    parts.append("</svg>")
    return "".join(parts), total, len(langs), peak


data = json.load(open(SRC))
for theme, out in (("dark", OUT_DARK), ("light", OUT_LIGHT)):
    svg, total, nlang, peak = render(THEMES[theme], data)
    with open(out, "w") as f:
        f.write(svg)
    print(f"wrote {out} ({theme}) {W}x{H} {len(svg)} bytes; "
          f"{total} commits, {nlang} languages, peak hour {peak}")
