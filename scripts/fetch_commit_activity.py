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

Env:
  GH_PROFILE_USER  username to aggregate (default iam74k4)
  GH_REPOS         comma-separated owner/repo list; skips repo discovery
                   (useful where /users/{user}/repos is unreachable)
  GITHUB_TOKEN     optional token for API rate limits
"""
import datetime
import json
import os
import sys
import urllib.request

USER = os.environ.get("GH_PROFILE_USER", "iam74k4")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
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


def count_commits(repo, counts):
    page = 1
    while True:
        commits = api(f"https://api.github.com/repos/{repo}/commits"
                      f"?per_page=100&page={page}&since={START.isoformat()}T00:00:00Z")
        if not commits:
            break
        for c in commits:
            if is_mine(c):
                d = c["commit"]["author"]["date"][:10]
                counts[d] = counts.get(d, 0) + 1
        if len(commits) < 100:
            break
        page += 1


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
    for repo in repos:
        try:
            count_commits(repo, counts)
        except Exception as e:                    # an empty/blocked repo must not kill the run
            print(f"skipping {repo}: {e}", file=sys.stderr)

    nonzero = sorted(counts.values())
    days = []
    d = START
    while d <= TODAY:
        n = counts.get(d.isoformat(), 0)
        days.append({"date": d.isoformat(), "count": n,
                     "level": quartile_level(n, nonzero)})
        d += datetime.timedelta(days=1)

    total = sum(x["count"] for x in days)
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump({"total": {"lastYear": total}, "contributions": days}, f)
    print(f"wrote {OUT_PATH}: {total} commits across "
          f"{sum(1 for x in days if x['count'])} active days, {len(repos)} repos")
