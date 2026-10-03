<!-- the board is one SVG in the design of AstLog (the portfolio, noctifex.dev):
     copy on the left, the site's own star system on the right, measured counts
     below. GitHub has no layout of its own to get wrong: the board keeps its
     positions at every width, and everything sits on one left edge.
     palette: #0c0c0e ground / #f2f2f4 ink, no accent colour (only the nebula
     has colour); sans for the copy, monospace only for English labels.
     board:  python scripts/fetch_commit_activity.py
             && python scripts/make_dashboard_svg.py   (daily via Actions)
     stars:  node scripts/make_cosmos_svg.mjs --astlog ../AstLog
             baked once from AstLog's orbits.ts into cosmos.svg, which the
             board embeds; re-run it when the number of works on the site
             changes (--apps / --works).
     links:  python scripts/make_links_svg.py -- separate files on purpose:
             an SVG behind <img> cannot carry clickable areas, so only these
             chips can be wrapped in a link. Keep them on one line with no
             spaces between them: they butt into one strip.
     the earlier board's pieces (ASCII portrait, wordmark, heatmap / stats /
     stack panels) still build from their own scripts in scripts/. -->

<img src="./profile.svg" width="860" alt="Taka — System Engineer（日本）。つくる工程そのものを、速くする。個人でつくったアプリと、仕事で取り組んだ開発効率化を AstLog にまとめています。右は AstLog と同じ星系の図。下は過去365日のコミット数・連続日数・1日の最多・よく書く時刻と、言語の割合・技術（毎日 GitHub API から更新）。" />

[![AstLog を見る](./links-site.svg)](https://noctifex.dev)[![iam74k4@gmail.com にメールを送る](./links-mail.svg)](mailto:iam74k4@gmail.com)[![Discord](./links-discord.svg)](https://discord.com/users/569686218632331264)[![Instagram](./links-instagram.svg)](https://www.instagram.com/iam74k4)
