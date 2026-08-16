#!/usr/bin/env python3
"""
Aggregate real commit activity for the last year straight from the GitHub
REST API -- no third-party services, no HTML scraping.

Counts commits on the default branch of every repository the user owns
(forks skipped), including commits authored by tools on the user's behalf
that carry a Co-authored-by trailer for them. Writes
data/commit-activity.json:

    {"total": {"lastYear": N},
     "contributions": [{"date": "YYYY-MM-DD", "count": n, "level": 0-4}, ...]}

Levels are quartiles over the nonzero days, like GitHub's own calendar.
Run daily by .github/workflows/update-profile-art.yml; the render step
(generate_streak_svg.py) consumes the JSON offline.

Also aggregates, for the stats panel (make_stats_svg.py):
  languages  byte share per language across the same repos
  hours      commits-per-hour histogram in local time (GH_TZ_OFFSET)

Env:
  GH_PROFILE_USER  username to aggregate (default iam74k4)
  GH_REPOS         comma-separated owner/repo list; skips repo discovery
                   (useful where /users/{user}/repos is unreachable)
  GH_TZ_OFFSET     hours to shift commit times for the punchcard (default 9, JST)
  GITHUB_TOKEN     optional token for API rate limits
"""
import datetime
import json
import os
import sys
import urllib.request

USER = os.environ.get("GH_PROFILE_USER", "iam74k4")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
TZ_OFFSET = int(os.environ.get("GH_TZ_OFFSET", 9))
OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "commit-activity.json")

TODAY = datetime.datetime.now(datetime.timezone.utc).date()
START = TODAY - datetime.timedelta(days=364)


def api(url):
    headers = {"User-Agent": "profile-readme-bot/1.0",
               "Accept": "application/vnd.github+json"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def list_repos():
    env = os.environ.get("GH_REPOS")
    if env:
        return [r.strip() for r in env.split(",") if r.strip()]
    repos, page = [], 1
    while True:
        batch = api(f"https://api.github.com/users/{USER}/repos"
                    f"?per_page=100&page={page}&type=owner")
        if not batch:
            break
        repos += [r["full_name"] for r in batch if not r.get("fork")]
        if len(batch) < 100:
            break
        page += 1
    return repos


def is_mine(commit):
    """The user's own commits, plus tool-authored commits credited to them
    via a Co-authored-by trailer (GitHub's calendar counts those too)."""
    login = ((commit.get("author") or {}).get("login") or "").lower()
    email = commit["commit"]["author"].get("email", "").lower()
    msg = commit["commit"].get("message", "").lower()
    u = USER.lower()
    return u in login or u in email or (u in msg and "co-authored-by" in msg)


def count_commits(repo, counts, hours):
    page = 1
    while True:
        commits = api(f"https://api.github.com/repos/{repo}/commits"
                      f"?per_page=100&page={page}&since={START.isoformat()}T00:00:00Z")
        if not commits:
            break
        for c in commits:
            if is_mine(c):
                date = c["commit"]["author"]["date"]     # UTC ISO from the API
                counts[date[:10]] = counts.get(date[:10], 0) + 1
                hours[(int(date[11:13]) + TZ_OFFSET) % 24] += 1
        if len(commits) < 100:
            break
        page += 1


def count_languages(repos):
    """Byte share per language across the repos, as [(name, pct), ...]."""
    totals = {}
    for repo in repos:
        try:
            for lang, n in api(f"https://api.github.com/repos/{repo}/languages").items():
                totals[lang] = totals.get(lang, 0) + n
        except Exception as e:
            print(f"languages for {repo}: {e}", file=sys.stderr)
    grand = sum(totals.values())
    if not grand:
        return []
    ranked = sorted(totals.items(), key=lambda kv: -kv[1])
    return [(name, round(n * 100.0 / grand, 1)) for name, n in ranked]


def streaks(days):
    """(current, longest) run of consecutive active days. Today doesn't
    break the current streak while it's still in progress."""
    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] > 0 else 0
        longest = max(longest, run)
    idx = len(days) - 1
    if days[idx]["count"] == 0:
        idx -= 1
    current = 0
    while idx >= 0 and days[idx]["count"] > 0:
        current += 1
        idx -= 1
    return current, longest


def quartile_level(n, nonzero):
    if n == 0 or not nonzero:
        return 0
    q = [nonzero[min(len(nonzero) - 1, int(len(nonzero) * f))] for f in (0.25, 0.5, 0.75)]
    if n <= q[0]:
        return 1
    if n <= q[1]:
        return 2
    if n <= q[2]:
        return 3
    return 4


if __name__ == "__main__":
    repos = list_repos()
    if not repos:
        print("no repositories found", file=sys.stderr)
        sys.exit(1)

    counts = {}
    hours = [0] * 24
    for repo in repos:
        try:
            count_commits(repo, counts, hours)
        except Exception as e:                    # an empty/blocked repo must not kill the run
            print(f"skipping {repo}: {e}", file=sys.stderr)
    languages = count_languages(repos)

    nonzero = sorted(counts.values())
    days = []
    d = START
    while d <= TODAY:
        n = counts.get(d.isoformat(), 0)
        days.append({"date": d.isoformat(), "count": n,
                     "level": quartile_level(n, nonzero)})
        d += datetime.timedelta(days=1)

    total = sum(x["count"] for x in days)
    current, longest = streaks(days)
    best = max(days, key=lambda x: x["count"])
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump({"total": {"lastYear": total},
                   "stats": {"current_streak": current, "longest_streak": longest,
                             "best_day": best["count"]},
                   "hours": hours,
                   "tz_offset": TZ_OFFSET,
                   "languages": languages,
                   "contributions": days}, f)
    print(f"wrote {OUT_PATH}: {total} commits across "
          f"{sum(1 for x in days if x['count'])} active days, {len(repos)} repos")
