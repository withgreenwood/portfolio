#!/usr/bin/env python3
"""Rebuild content/monza.json + content/monza-images/ from browser packs.

The Monza page is a snapshot of two saved collections, not a live feed --
neither Instagram nor TikTok exposes saved collections to any API, so the
tiles are extracted through a signed-in browser and baked in. This script is
the second half of that: it turns the downloaded packs into repo content.

To refresh after adding posts to either collection, re-run the browser-side
extraction (see claude/monza-subpage.md in the project), drop the new packs in
~/Downloads, and run this, then `python3 build.py`.

Packs are JSON objects of {key: {b64, meta:{platform,user,url,taken_at,code}}}.
monza-fix*.json is a thin override keyed by post code, carrying only b64 --
used when a post's default cover frame is unusable (a black first frame, or a
carousel whose opening slide is off-topic). The newest fix file wins.
"""
import base64
import datetime
import glob
import json
import os
import re

REPO = os.path.dirname(os.path.abspath(__file__))
# ~/Downloads on the Mac; ~/mnt/Downloads when run from the sandboxed shell.
DL = next((d for d in (os.path.expanduser("~/Downloads"),
                       os.path.expanduser("~/mnt/Downloads"))
           if os.path.isdir(d)), os.path.expanduser("~/Downloads"))
OUT = os.path.join(REPO, "content", "monza-images")
PACKS = ["monza-ig-1.json", "monza-ig-2.json", "monza-ig-3.json", "monza-tt.json"]

# Posts left out on purpose: the cover frame is unusable and the post offers no
# alternative (no carousel slides, no second candidate).
EXCLUDE = {
    "Dc5_pj7O1OG",   # @team_theon reel -- opening frame is solid black
}


def main():
    fixes = {}
    for f in sorted(glob.glob(os.path.join(DL, "monza-fix*.json")),
                    key=os.path.getmtime):
        fixes.update(json.load(open(f)))

    entries = []
    for fn in PACKS:
        path = os.path.join(DL, fn)
        if not os.path.exists(path):
            raise SystemExit("missing pack: %s" % path)
        for v in json.load(open(path)).values():
            code = v["meta"].get("code")
            if code in EXCLUDE:
                continue
            if code in fixes:
                v["b64"] = fixes[code]["b64"]
            entries.append(v)

    # Newest first, which is how the page reads.
    entries.sort(key=lambda v: v["meta"]["taken_at"], reverse=True)

    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):
        os.remove(os.path.join(OUT, f))

    items = []
    for i, v in enumerate(entries, 1):
        m = v["meta"]
        handle = re.sub(r"[^a-z0-9]+", "-", (m.get("user") or "post").lower()).strip("-")
        name = "%03d-%s.jpg" % (i, handle)
        with open(os.path.join(OUT, name), "wb") as fh:
            fh.write(base64.b64decode(v["b64"]))
        items.append({
            "type": "ig" if m["platform"] == "ig" else "tt",
            "url": m["url"],
            "title": "@" + (m.get("user") or ""),
            "source": datetime.datetime.utcfromtimestamp(
                m["taken_at"]).strftime("%d %b %Y"),
            "image": name,
            "takenAt": m["taken_at"],
        })

    p = os.path.join(REPO, "content", "monza.json")
    doc = json.load(open(p)) if os.path.exists(p) else {}
    doc["items"] = items
    with open(p, "w") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)

    ig = sum(1 for i in items if i["type"] == "ig")
    mb = sum(os.path.getsize(os.path.join(OUT, f))
             for f in os.listdir(OUT)) / 1048576
    print("%d tiles (%d instagram, %d tiktok), %.1f MB, %d fix override(s)"
          % (len(items), ig, len(items) - ig, mb, len(fixes)))
    print("range: %s -> %s" % (items[-1]["source"], items[0]["source"]))


if __name__ == "__main__":
    main()
