<div align="center">

<!-- the board is one SVG, so GitHub has no layout of its own to get wrong:
     the cards keep their positions and sizes at every width.
     palette: #080d12 bg / #cbd5e1 ink / #22d3ee accent, monospace throughout.
     board:     python scripts/fetch_commit_activity.py
                && python scripts/make_dashboard_svg.py   (daily via Actions)
     portrait:  python scripts/make_ascii_svg.py          (feeds the board)
     wordmark:  python scripts/make_wordmark_svg.py --mode rock
     links:     python scripts/make_links_svg.py   -- separate files on purpose:
                an SVG behind <img> cannot carry clickable areas, so only these
                chips can be wrapped in a link.
     portrait and wordmark need Pillow + numpy:
                pip install -r scripts/requirements.txt
     the earlier stacked panels (heatmap / stats / stack) still build from
     their own scripts in scripts/. -->

<img src="./profile.svg" width="860" alt="Taka — System Engineer in Japan. Commit activity for the last 12 months, language share, tech stack and commits by hour — auto-refreshed daily from the GitHub API." />

<br>

[![Email](./links-mail.svg)](mailto:iam74k4@gmail.com)
[![Discord](./links-discord.svg)](https://discord.com/users/569686218632331264)
[![Instagram](./links-instagram.svg)](https://www.instagram.com/iam74k4)

</div>
