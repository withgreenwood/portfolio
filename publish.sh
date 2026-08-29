#!/usr/bin/env bash
# Collect exports from admin.html, rebuild the site, and show what changed.
#
#   ./publish.sh            # pull from ~/Downloads
#   ./publish.sh ~/Desktop  # pull from somewhere else
#
# Then push with:  git add -A && git commit -m "Update" && git push

set -euo pipefail
cd "$(dirname "$0")"
SRC="${1:-$HOME/Downloads}"

moved_json=0
moved_imgs=0

if [ -r "$SRC/items.json" ]; then
  mv "$SRC/items.json" content/items.json
  moved_json=1
fi

# admin.html exports thumbnails as NN-slug.jpg
shopt -s nullglob
for f in "$SRC"/[0-9][0-9]-*.jpg; do
  mv "$f" content/images/
  moved_imgs=$((moved_imgs + 1))
done
shopt -u nullglob

if [ "$moved_json" -eq 0 ] && [ "$moved_imgs" -eq 0 ]; then
  echo "Nothing new found in $SRC"
  echo "If macOS is blocking access to that folder, drag the files in manually:"
  echo "  items.json      -> content/"
  echo "  NN-name.jpg     -> content/images/"
  echo "Rebuilding with existing content anyway..."
else
  [ "$moved_json" -eq 1 ] && echo "Moved items.json -> content/"
  [ "$moved_imgs" -gt 0 ] && echo "Moved $moved_imgs image(s) -> content/images/"
fi

echo
python3 build.py
echo

# prune images no longer referenced, so the repo doesn't accumulate orphans
python3 - <<'PY'
import json, pathlib
used = {i["image"] for i in json.load(open("content/items.json"))
        if not str(i["image"]).startswith(("http://", "https://"))}
orphans = [p for p in pathlib.Path("content/images").iterdir()
           if p.is_file() and p.name not in used]
if orphans:
    print("Unused images still in content/images (safe to delete):")
    for p in sorted(orphans):
        print("  ", p.name)
PY

echo "Preview locally:  python3 -m http.server 8747 --directory site"
echo "Publish:          git add -A && git commit -m \"Update\" && git push"
