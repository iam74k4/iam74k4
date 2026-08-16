#!/usr/bin/env python3
"""Generate an animated GitHub-contribution SVG (squares light up one by one).
Works standalone; designed to run in a GitHub Action daily to stay live.
Usage: python generate_streak_svg.py [username] [output.svg]
Adapted from AVIVASHISHTA29/AVIVASHISHTA29.
"""
import sys, json, os, datetime, urllib.request

USER = sys.argv[1] if len(sys.argv) > 1 else "iam74k4"
OUT  = sys.argv[2] if len(sys.argv) > 2 else "contrib-heatmap.svg"

def get_data(user):
    url = f"https://github-contributions-api.jogruber.de/v4/{user}?y=last"
    try:
        with urllib.request.urlopen(url, timeout=25) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        # fallback to the local snapshot if the API is unreachable
        here = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "contrib.json")
        if os.path.exists(here):
            print("API failed (%s); using local data/contrib.json" % e)
            return json.load(open(here))
        raise

data = get_data(USER)
contribs = data["contributions"]
total = data["total"]["lastYear"]

# ---- layout ----
# the graph sits inside the same terminal-window chrome as the portrait and
# wordmark panels, so all three read as one continuous session.
CELL, GAP, RAD, LEFT, TOP = 13, 3, 2.5, 34, 24
COLORS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
BG = "#0d1117"
BG2 = "#111722"
FRAME = "#30363d"
GRAY = "#7d8590"
INK = "#c9d1d9"
GREEN = "#39d353"
PAD = 18
TITLEBAR_H = 28
MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

n = len(contribs)
NW = (n + 6) // 7
GW = LEFT + NW*(CELL+GAP) + 6            # graph width, inside the frame
GH = TOP + 7*(CELL+GAP) + 26             # graph height incl. total line
W = GW + PAD*2
H = TITLEBAR_H + GH + PAD

GX = PAD                                  # graph origin inside the canvas
GY = TITLEBAR_H + PAD*0.55

# timing (seconds)
REVEAL, DUR = 3.6, 0.55
maxorder = (NW-1) + 6*0.55

rects, labels = [], []
sd = datetime.date.fromisoformat(contribs[0]["date"])
last_m = None
last_lbl_wk = -3
for wk in range(NW):
    d = sd + datetime.timedelta(days=wk*7)
    if d.month != last_m:
        last_m = d.month
        # a new month can start 1-2 columns after the window's first label;
        # 13px labels need >= 3 columns of separation or they overlap
        if wk - last_lbl_wk >= 3:
            labels.append(f'<text class="lbl" x="{GX+LEFT+wk*(CELL+GAP)}" y="{GY+TOP-8:.0f}">{MONTHS[d.month-1]}</text>')
            last_lbl_wk = wk
for name, r in [("Mon",1),("Wed",3),("Fri",5)]:
    labels.append(f'<text class="lbl" x="{GX+2}" y="{GY+TOP+r*(CELL+GAP)+CELL-2:.0f}">{name}</text>')

for i, c in enumerate(contribs):
    wk, row, lvl = i//7, i%7, c["level"]
    x = GX + LEFT + wk*(CELL+GAP); y = GY + TOP + row*(CELL+GAP)
    delay = round((wk + row*0.55)/maxorder * REVEAL, 3)
    cls = "c g" if lvl >= 1 else "c e"
    rects.append(
        f'<rect class="{cls}" x="{x}" y="{y:.0f}" width="{CELL}" height="{CELL}" rx="{RAD}" '
        f'fill="{COLORS[lvl]}" style="animation-delay:{delay}s"/>'
    )

dots = "".join(f'<circle cx="{PAD + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{c}"/>'
               for i, c in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]))

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace">
<style>
  text.lbl {{ fill:{GRAY}; font-size:13px; font-weight:600; }}
  .c {{ transform-box:fill-box; transform-origin:center; opacity:0; animation:pop {DUR}s ease-out both; }}
  .g {{ animation:pop {DUR}s ease-out both, flash {DUR+0.15}s ease-out both; }}
  @keyframes pop {{ 0%{{opacity:0;transform:scale(.2)}} 60%{{opacity:1;transform:scale(1.1)}} 100%{{opacity:1;transform:scale(1)}} }}
  @keyframes flash {{ 0%{{filter:brightness(2.4)}} 45%{{filter:brightness(2.4)}} 100%{{filter:brightness(1)}} }}
  @media (prefers-reduced-motion: reduce) {{ .c {{ opacity:1 !important; animation:none !important; }} }}
</style>
<defs><linearGradient id="hbg" x1="0" y1="0" x2="0" y2="1">
<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/></linearGradient></defs>
<rect width="{W}" height="{H}" rx="12" fill="url(#hbg)"/>
<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="{FRAME}"/>
<line x1="0" y1="{TITLEBAR_H}" x2="{W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>
{dots}
<text x="{W/2:.0f}" y="{TITLEBAR_H/2 + 4}" fill="{GRAY}" font-size="12" text-anchor="middle">taka@github: ~$ ./contributions.sh</text>
{''.join(labels)}
{''.join(rects)}
<text x="{GX+LEFT}" y="{H-16:.0f}" font-size="13"><tspan fill="{GREEN}" font-weight="700">{total:,}</tspan><tspan fill="{INK}"> contributions in the last year</tspan></text>
</svg>'''

open(OUT, "w").write(svg)
print(f"Wrote {OUT}: {n} days, {total:,} contributions, {len(svg)//1024} KB")
