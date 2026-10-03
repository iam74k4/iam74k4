#!/usr/bin/env python3
"""
Generate the link "chips" under the board, in AstLog's design: one filled
button -- the strongest single action, white with black type, like the
site's "一覧で見る →" -- and the rest as plain type on the black ground, the
way the site's Contact page sets them: the mail address itself as the link
(it stays readable as text), the other services as small monospace capitals
(the site's "GITHUB↗"). Square corners, no frames; the README sets them side
by side with no gaps, so on GitHub's light theme they read as one black strip
and on the dark theme as a button followed by text links. The row has to fit
GitHub's README column (~780 px) on one line.

Each chip is its own SVG so the README can wrap it in a normal markdown
link -- SVGs embedded via <img> cannot carry clickable areas themselves.
Every target leaves GitHub, so every chip ends in ↗ (AstLog keeps → for
moves inside the site).

Usage: python scripts/make_links_svg.py   (writes links-*.svg in the repo root)
"""
import html
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")

# palette -- AstLog's public/app.css :root (mono accent)
BG = "#0c0c0e"
INK = "#f2f2f4"
INK_MID = "#b4b4c2"
INK_WEAK = "#8a8a96"
ACCENT = INK            # the filled button
ACCENT_INK = "#12121a"  # type on it

SANS = "'Helvetica Neue','Hiragino Sans','Noto Sans JP',system-ui,-apple-system,sans-serif"
MONO = "ui-monospace,'SFMono-Regular','SF Mono',Menlo,Consolas,monospace"
FS_LABEL, FS_BASE = 11, 14
TRACKING = 0.16
H = 52          # --cta-h
PAD_X = 24      # --sp-6
ARROW_GAP = 24  # --sp-6, as the site's button
LABEL_GAP = 12  # --sp-4, after the small capitals

# (file, text, kind): "button" filled, "text" sans type, "label" monospace capitals
LINKS = [
    ("links-site.svg",      "AstLog を見る",     "button"),
    ("links-mail.svg",      "iam74k4@gmail.com", "text"),
    ("links-discord.svg",   "DISCORD",           "label"),
    ("links-instagram.svg", "INSTAGRAM",         "label"),
]


def width(s, size, mono=False):
    """A generous estimate, so the arrow never lands on the text in a wide system font."""
    if mono:
        return len(s) * size * (0.6 + TRACKING)
    return sum((1.0 if ord(c) >= 0x2E80 else 0.3 if c == " " else 0.62) for c in s) * size


for fname, value, kind in LINKS:
    filled, label = kind == "button", kind == "label"
    fill, ink = (ACCENT, ACCENT_INK) if filled else (BG, INK)
    gap = LABEL_GAP if label else ARROW_GAP
    text_w = width(value, FS_LABEL, mono=True) if label else width(value, FS_BASE)
    w = round(PAD_X + text_w + gap + width("↗", FS_BASE) + PAD_X)
    y = H / 2 + 5
    if label:
        body = (f'<text x="{PAD_X}" y="{y}" font-family="{MONO}" font-size="{FS_LABEL}" '
                f'letter-spacing="{TRACKING}em" fill="{INK_MID}">{value}</text>')
    else:
        body = (f'<text x="{PAD_X}" y="{y}" font-family="{SANS}" font-size="{FS_BASE}" '
                f'font-weight="{600 if filled else 400}" fill="{ink}">{html.escape(value)}</text>')
    svg = "".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{H}" viewBox="0 0 {w} {H}" '
        f'xml:lang="ja" role="img" aria-label="{html.escape(value.title() if label else value)}">',
        f'<rect width="{w}" height="{H}" fill="{fill}"/>',
        body,
        f'<text x="{w - PAD_X}" y="{y}" font-family="{SANS}" font-size="{FS_BASE}" '
        f'text-anchor="end" fill="{ink if filled else INK_MID}">↗</text>',
        "</svg>",
    ])
    with open(os.path.join(ROOT, fname), "w", encoding="utf-8") as f:
        f.write(svg)
    print("wrote", fname, f"{w}x{H}")
