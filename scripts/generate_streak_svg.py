#!/usr/bin/env python3
"""Generate an animated commit-activity SVG (squares light up one by one).
Reads data/commit-activity.json, written by fetch_commit_activity.py --
fully offline, no third-party APIs. Run daily by a GitHub Action to stay live.
Usage: python generate_streak_svg.py [data.json] [output.svg]
Animation style adapted from AVIVASHISHTA29/AVIVASHISHTA29.
"""
import sys, json, os, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "data", "commit-activity.json")
OUT = sys.argv[2] if len(sys.argv) > 2 else "contrib-heatmap.svg"

data = json.load(open(SRC))
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
CMD_LINE_H = 24                          # typed ./commits.sh line above the graph
W = GW + PAD*2
H = TITLEBAR_H + CMD_LINE_H + GH + PAD

GX = PAD                                  # graph origin inside the canvas
GY = TITLEBAR_H + CMD_LINE_H + PAD*0.55

# timing (seconds): cells start popping once the command finishes typing
CHAR_W, CHAR_T = 7.8, 0.05
PROMPT, CMD = "taka@github:~$ ", "./commits.sh --last-year"
TYPE_END = 0.3 + len(CMD) * CHAR_T + 0.15
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
    delay = round(TYPE_END + (wk + row*0.55)/maxorder * REVEAL, 3)
    cls = "c g" if lvl >= 1 else "c e"
    rects.append(
        f'<rect class="{cls}" x="{x}" y="{y:.0f}" width="{CELL}" height="{CELL}" rx="{RAD}" '
        f'fill="{COLORS[lvl]}" style="animation-delay:{delay}s"/>'
    )

dots = "".join(f'<circle cx="{PAD + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{c}"/>'
               for i, c in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]))

# typed command line under the titlebar (prompt static, command types out)
cy = TITLEBAR_H + 20
cmd_x = PAD + len(PROMPT) * CHAR_W
cmd_w = len(CMD) * CHAR_W
type_dur = len(CMD) * CHAR_T
cmd_line = (
    f'<text x="{PAD}" y="{cy}" font-size="13">'
    f'<tspan fill="{GREEN}">taka@github</tspan><tspan fill="{GRAY}">:~$ </tspan></text>'
    f'<clipPath id="cmd"><rect x="{cmd_x:.1f}" y="{cy-14}" height="18" width="0">'
    f'<animate attributeName="width" from="0" to="{cmd_w:.1f}" begin="0.3s" '
    f'dur="{type_dur:.2f}s" fill="freeze"/></rect></clipPath>'
    f'<g clip-path="url(#cmd)"><text x="{cmd_x:.1f}" y="{cy}" font-size="13" fill="{INK}" '
    f'xml:space="preserve" textLength="{cmd_w:.1f}" lengthAdjust="spacing">{CMD}</text></g>'
    f'<rect y="{cy-12}" width="8" height="14" fill="{GREEN}" opacity="0">'
    f'<animate attributeName="x" from="{cmd_x:.1f}" to="{cmd_x+cmd_w:.1f}" begin="0.3s" '
    f'dur="{type_dur:.2f}s" fill="freeze"/>'
    f'<set attributeName="opacity" to="0.9" begin="0s"/>'
    f'<set attributeName="opacity" to="0" begin="{0.3+type_dur:.2f}s"/></rect>')

# streak stats (right-aligned in the bottom line), when the data has them
stats = data.get("stats")
if stats:
    stats_text = (
        f'<text x="{GX+GW-6}" y="{H-16:.0f}" font-size="13" text-anchor="end">'
        f'<tspan fill="{INK}">streak </tspan><tspan fill="{GREEN}" font-weight="700">{stats["current_streak"]}d</tspan>'
        f'<tspan fill="{GRAY}"> · </tspan>'
        f'<tspan fill="{INK}">longest </tspan><tspan fill="{GREEN}" font-weight="700">{stats["longest_streak"]}d</tspan>'
        f'<tspan fill="{GRAY}"> · </tspan>'
        f'<tspan fill="{INK}">max </tspan><tspan fill="{GREEN}" font-weight="700">{stats["best_day"]}</tspan>'
        f'<tspan fill="{INK}">/day</tspan></text>')
else:
    stats_text = ""

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
<text x="{W/2:.0f}" y="{TITLEBAR_H/2 + 4}" fill="{GRAY}" font-size="12" text-anchor="middle">taka@github: ~</text>
{cmd_line}
{''.join(labels)}
{''.join(rects)}
<text x="{GX+LEFT}" y="{H-16:.0f}" font-size="13"><tspan fill="{GREEN}" font-weight="700">{total:,}</tspan><tspan fill="{INK}"> commits in the last year</tspan></text>
{stats_text}
</svg>'''

open(OUT, "w").write(svg)
print(f"Wrote {OUT}: {n} days, {total:,} commits, {len(svg)//1024} KB")
