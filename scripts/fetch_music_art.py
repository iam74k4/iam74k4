#!/usr/bin/env python3
"""
Resolve the tracks listed in data/music.json through Apple's public iTunes
Search API (no key needed) and save each cover to assets/music/<id>.jpg, for
the "On repeat" card that make_dashboard_svg.py draws in place of the portrait.

Run it by hand after editing the list -- the picks are fixed, so CI never
calls it; the daily workflow only embeds the covers already committed.

data/music.json holds {"tracks": [...]}; each entry needs only a search
"term". The first run fills in the rest (track_id, title, artist, kind,
year, duration, url, art), and later runs look the track up by its id, so a
re-run never drifts to a different version. To pick another version, set
"track_id" by hand; to drop a track, delete its entry.

Usage: python scripts/fetch_music_art.py   (stdlib only)
"""
import json
import os
import re
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
LIST = os.path.join(ROOT, "data", "music.json")
ART_DIR = os.path.join(ROOT, "assets", "music")
COUNTRY = "US"          # US store: artist names in Latin script
ART_PX = 256            # ~2x the size the card draws a cover at
UA = {"User-Agent": "profile-art/1.0"}


def get_json(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20) as r:
        return json.load(r)


def track_url(url):
    """Apple Music link with only the ?i=<track> part of the query kept."""
    base, _, query = url.partition("?")
    i = urllib.parse.parse_qs(query).get("i")
    return f"{base}?i={i[0]}" if i else base


def resolve(entry):
    if entry.get("track_id"):
        q = urllib.parse.urlencode({"id": entry["track_id"], "country": COUNTRY})
        results = get_json(f"https://itunes.apple.com/lookup?{q}")["results"]
    else:
        q = urllib.parse.urlencode({"term": entry["term"], "entity": "song",
                                    "limit": 1, "country": COUNTRY})
        results = get_json(f"https://itunes.apple.com/search?{q}")["results"]
    if not results:
        raise SystemExit(f"no match for {entry}")
    return results[0]


def main():
    with open(LIST) as f:
        data = json.load(f)
    os.makedirs(ART_DIR, exist_ok=True)
    for entry in data["tracks"]:
        r = resolve(entry)
        # "No Sleep (feat. Bonn)" -> title "No Sleep", artist "Martin Garrix, Bonn"
        m = re.match(r"(.*?)\s*\((?:feat\.|with) ([^)]*)\)\s*$", r["trackName"])
        title, feat = (m.group(1), m.group(2)) if m else (r["trackName"], None)
        album = r.get("collectionName", "")
        secs = round(r.get("trackTimeMillis", 0) / 1000)
        art_url = re.sub(r"/[^/]*$", f"/{ART_PX}x{ART_PX}bb.jpg", r["artworkUrl100"])
        art_rel = f"assets/music/{r['trackId']}.jpg"

        with urllib.request.urlopen(urllib.request.Request(art_url, headers=UA),
                                    timeout=20) as resp:
            jpg = resp.read()
        if not jpg.startswith(b"\xff\xd8\xff"):
            raise SystemExit(f"cover for {title} is not a JPEG")
        with open(os.path.join(ROOT, art_rel), "wb") as f:
            f.write(jpg)

        entry.update({
            "track_id": r["trackId"],
            "title": title,
            "artist": r["artistName"] + (f", {feat}" if feat else ""),
            "kind": ("Single" if album.endswith(" - Single")
                     else "EP" if album.endswith(" - EP") else "Album"),
            "year": r["releaseDate"][:4],
            "duration": f"{secs // 60}:{secs % 60:02d}",
            "url": track_url(r["trackViewUrl"]),
            "art": art_rel,
        })
        print(f"{entry['title']} — {entry['artist']} ({entry['year']}) -> {art_rel} "
              f"{len(jpg) // 1024} KB")

    with open(LIST, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
