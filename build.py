#!/usr/bin/env python3
"""Build site/index.html from content/profile.json + content/items.json.

The generated page needs no JavaScript: the All/Instagram/Writing tabs are
hidden radio inputs driven by CSS sibling selectors, so the grid filters even
if scripts fail to load.

Usage:  python3 build.py
"""
import html
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).parent
CONTENT = ROOT / "content"
SITE = ROOT / "site"


def die(msg):
    sys.stderr.write("build failed: %s\n" % msg)
    raise SystemExit(1)


def load(name):
    p = CONTENT / name
    if not p.exists():
        die("missing %s" % p)
    try:
        return json.loads(p.read_text())
    except json.JSONDecodeError as e:
        die("%s is not valid JSON — %s" % (p, e))


def esc(v):
    return html.escape(str(v or ""), quote=True)


ARTICLE_ICON = ('<svg viewBox="0 0 24 24" aria-hidden="true">'
                '<path d="M4 5h13v14H4z"/><path d="M8 9h5M8 13h5"/></svg>')


def stylesheet(lay):
    cols = int(lay.get("columns", 4))
    colsm = int(lay.get("columnsMobile", 3))
    gap = int(lay.get("gap", 4))
    gapm = int(lay.get("gapMobile", 2))
    radius = int(lay.get("radius", 0))
    pad = int(lay.get("pagePadding", 20))
    maxw = lay.get("maxWidth", 935)
    maxw = "100%" if maxw in ("100%", "full") else "%dpx" % int(maxw)
    return f"""
:root{{
  --ink:#16150f; --bg:#fcfcfb; --muted:#77756b; --line:#e6e4de;
  --max:{maxw}; --gap:{gap}px; --radius:{radius}px; --pad:{pad}px;
}}
@media (prefers-color-scheme:dark){{
  :root{{--ink:#efedE6; --bg:#121210; --muted:#96938a; --line:#2c2b27}}
}}
*{{box-sizing:border-box}}
html{{-webkit-text-size-adjust:100%}}
body{{margin:0;background:var(--bg);color:var(--ink);
  font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Helvetica,Arial,sans-serif;
  -webkit-font-smoothing:antialiased}}
.wrap{{max-width:var(--max);margin:0 auto;padding:0 var(--pad)}}
header{{padding:40px 0 4px}}
h1{{font-size:26px;font-weight:600;letter-spacing:-.02em;margin:0}}
.tagline{{color:var(--muted);font-size:13px;letter-spacing:.13em;
  text-transform:uppercase;margin:7px 0 0}}
.bio{{max-width:52ch;margin:26px 0 0;color:var(--ink);opacity:.85;font-size:15.5px}}
.links{{display:flex;gap:18px;flex-wrap:wrap;margin:18px 0 0;padding:0;list-style:none;
  align-items:center}}
.links a{{color:var(--ink);font-size:13px;letter-spacing:.05em;text-decoration:none;
  border-bottom:1px solid var(--line);padding-bottom:2px;transition:border-color .2s}}
.links a:hover{{border-bottom-color:currentColor}}
.links a.ic{{border:0;padding:0;display:inline-flex;width:21px;height:21px;
  opacity:.75;transition:opacity .2s}}
.links a.ic:hover{{opacity:1;border:0}}
.links a.ic svg{{width:100%;height:100%;display:block;fill:currentColor}}
.links a.ic svg *{{fill:currentColor}}
main{{padding:30px 0 0}}
footer{{padding:64px 0 56px;color:var(--muted);font-size:12.5px}}
hr.rule{{border:0;border-top:1px solid var(--line);margin:28px 0 0}}

.pgf{{position:relative}}
.pgf-r{{position:absolute;width:1px;height:1px;opacity:0;margin:0}}
.pgf-tabs{{display:flex;gap:26px;justify-content:center;margin:0 0 26px;
  flex-wrap:wrap;padding:0}}
.pgf-tab{{cursor:pointer;font-size:11px;letter-spacing:.15em;text-transform:uppercase;
  opacity:.5;padding-bottom:5px;border-bottom:1px solid transparent;
  transition:opacity .2s,border-color .2s;-webkit-user-select:none;user-select:none;
  display:inline-block}}
.pgf-tab:hover{{opacity:.85}}
.pgf-grid{{display:grid;grid-template-columns:repeat({colsm},1fr);gap:{gapm}px;
  margin:0 calc(-1 * var(--pad));padding:0}}
@media(min-width:700px){{.pgf-grid{{grid-template-columns:repeat({cols},1fr);
  gap:var(--gap);margin:0}}}}
.pgf-i{{position:relative;display:block;aspect-ratio:4/5;overflow:hidden;
  border-radius:var(--radius);background:rgba(128,128,128,.12);
  text-decoration:none;color:inherit}}
.pgf-i img{{width:100%;height:100%;object-fit:cover;display:block;
  transition:transform .55s cubic-bezier(.2,.7,.3,1)}}
.pgf-i:hover img{{transform:scale(1.045)}}
.pgf-ov{{position:absolute;inset:0;display:flex;flex-direction:column;
  justify-content:flex-end;padding:14px;opacity:0;transition:opacity .28s;
  background:linear-gradient(to top,rgba(0,0,0,.74),rgba(0,0,0,.2) 52%,rgba(0,0,0,0))}}
.pgf-i:hover .pgf-ov,.pgf-i:focus-visible .pgf-ov{{opacity:1}}
.pgf-t{{color:#fff;font-size:12.5px;line-height:1.35;font-weight:500;
  display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}}
.pgf-s{{color:rgba(255,255,255,.72);font-size:10.5px;letter-spacing:.05em;
  text-transform:uppercase;margin-top:5px}}
.pgf-b{{position:absolute;top:9px;right:9px;width:19px;height:19px;border-radius:50%;
  background:rgba(0,0,0,.5);display:flex;align-items:center;justify-content:center}}
.pgf-b svg{{width:10px;height:10px;fill:none;stroke:#fff;stroke-width:2;
  stroke-linecap:round;stroke-linejoin:round}}
.pgf-i:focus-visible{{outline:2px solid currentColor;outline-offset:2px}}
@media(hover:none){{.pgf-i[data-t="wr"] .pgf-ov{{opacity:1}}}}
@media(prefers-reduced-motion:reduce){{
  .pgf-i img{{transition:none}} .pgf-i:hover img{{transform:none}}
}}
#pgf-all:checked~.pgf-tabs [for="pgf-all"],
#pgf-ig:checked~.pgf-tabs [for="pgf-ig"],
#pgf-wr:checked~.pgf-tabs [for="pgf-wr"]{{opacity:1;border-bottom-color:currentColor}}
#pgf-ig:checked~.pgf-grid .pgf-i[data-t="wr"]{{display:none}}
#pgf-wr:checked~.pgf-grid .pgf-i[data-t="ig"]{{display:none}}
#pgf-all:focus-visible~.pgf-tabs [for="pgf-all"],
#pgf-ig:focus-visible~.pgf-tabs [for="pgf-ig"],
#pgf-wr:focus-visible~.pgf-tabs [for="pgf-wr"]{{outline:2px solid currentColor;
  outline-offset:3px}}
.empty{{text-align:center;color:var(--muted);font-size:14px;padding:60px 0;
  border:1px dashed var(--line);border-radius:8px}}

/* Full-bleed 3-up tiles are ~130px wide, far smaller than the desktop grid.
   Overlay type has to shrink with them or a headline swamps the image, so
   drop a step in size, clamp to two lines, and hide the source line. */
@media(max-width:699px){{
  .pgf-i{{border-radius:0}}
  .pgf-ov{{padding:7px}}
  .pgf-t{{font-size:10.5px;line-height:1.25;-webkit-line-clamp:2}}
  .pgf-s{{display:none}}
  .pgf-b{{top:5px;right:5px;width:15px;height:15px}}
  .pgf-b svg{{width:8px;height:8px}}
}}
"""


def build():
    profile = load("profile.json")
    items = load("items.json")
    if not isinstance(items, list):
        die("items.json must be a JSON array")

    imgdir = CONTENT / "images"

    def is_remote(v):
        return str(v or "").lower().startswith(("http://", "https://"))

    missing = [i.get("image") for i in items
               if not i.get("image")
               or (not is_remote(i["image"]) and not (imgdir / i["image"]).exists())]
    if missing:
        die("images not found in content/images: %s" % ", ".join(map(str, missing)))

    SITE.mkdir(exist_ok=True)
    dest = SITE / "images"
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    used = {i["image"] for i in items if not is_remote(i["image"])}
    for f in sorted(imgdir.iterdir()):
        if f.name in used:
            shutil.copy2(f, dest / f.name)

    tabs = profile.get("tabs", {})
    lay = profile.get("layout", {})
    has_ig = any(i.get("type") == "ig" for i in items)
    has_wr = any(i.get("type") == "wr" for i in items)

    tiles = []
    for it in items:
        t, s = esc(it.get("title")), esc(it.get("source"))
        typ = "wr" if it.get("type") == "wr" else "ig"
        alt = esc(it.get("title") or ("Article" if typ == "wr" else "Instagram post"))
        ov = ""
        if t or s:
            ov = ('<span class="pgf-ov">'
                  + (f'<span class="pgf-t">{t}</span>' if t else "")
                  + (f'<span class="pgf-s">{s}</span>' if s else "")
                  + "</span>")
        badge = f'<span class="pgf-b">{ARTICLE_ICON}</span>' if typ == "wr" else ""
        tiles.append(
            f'<a class="pgf-i" data-t="{typ}" href="{esc(it.get("url"))}" '
            f'target="_blank" rel="noopener noreferrer">'
            f'<img src="{esc(it["image"]) if is_remote(it["image"]) else "images/" + esc(it["image"])}" alt="{alt}" width="1080" '
            f'height="1350" loading="lazy" decoding="async">{ov}{badge}</a>')

    if tiles:
        grid = '<div class="pgf-grid">\n      ' + "\n      ".join(tiles) + "\n    </div>"
    else:
        grid = ('<div class="empty">No items yet — add some in '
                '<code>content/items.json</code> and run <code>python3 build.py</code>.</div>')

    tabbar = ""
    if has_ig and has_wr:
        tabbar = f"""<input class="pgf-r" type="radio" name="pgf-f" id="pgf-all" checked>
    <input class="pgf-r" type="radio" name="pgf-f" id="pgf-ig">
    <input class="pgf-r" type="radio" name="pgf-f" id="pgf-wr">
    <div class="pgf-tabs">
      <label class="pgf-tab" for="pgf-all">{esc(tabs.get("all", "All"))}</label>
      <label class="pgf-tab" for="pgf-ig">{esc(tabs.get("ig", "Instagram"))}</label>
      <label class="pgf-tab" for="pgf-wr">{esc(tabs.get("wr", "Writing"))}</label>
    </div>
    """

    icons = profile.get("icons", {})

    def link_html(l):
        # a link naming an icon present in profile.icons renders as that glyph,
        # labelled for screen readers; anything else stays a text link
        key = l.get("icon")
        if key and key in icons:
            return (f'<li><a class="ic" href="{esc(l.get("url"))}" '
                    f'aria-label="{esc(l.get("label"))}">{icons[key]}</a></li>')
        return f'<li><a href="{esc(l.get("url"))}">{esc(l.get("label"))}</a></li>'

    links = "".join(link_html(l) for l in profile.get("links", []) if l.get("url"))
    links_html = f'<ul class="links">{links}</ul>' if links else ""

    name = esc(profile.get("name", "Portfolio"))
    tagline = profile.get("tagline")
    bio = profile.get("bio")
    # metaDescription lets a minimal page (no visible bio) still have a real
    # description for search results and link previews.
    meta = profile.get("metaDescription") or bio
    # og:image must be an absolute URL — relative paths are ignored by most
    # link-preview crawlers. siteUrl in profile.json supplies the origin.
    site_url = str(profile.get("siteUrl", "")).rstrip("/")
    og = ""
    if items:
        first = items[0]["image"]
        og = esc(first) if is_remote(first) else esc(site_url + "/images/" + str(first))

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{name}</title>
<meta name="description" content="{esc(meta)}">
<meta property="og:title" content="{name}">
<meta property="og:description" content="{esc(meta)}">
<meta property="og:type" content="website">
{f'<meta property="og:url" content="{esc(site_url)}/">' if site_url else ''}
<meta name="twitter:card" content="summary_large_image">
{f'<meta property="og:image" content="{og}">' if og else ''}
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'><text y='13' font-size='14'>◼</text></svg>">
<style>{stylesheet(lay)}</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>{name}</h1>
    {f'<p class="tagline">{esc(tagline)}</p>' if tagline else ''}
    {f'<p class="bio">{esc(bio)}</p>' if bio else ''}
    {links_html}
    <hr class="rule">
  </header>
  <main>
    <div class="pgf">
    {tabbar}{grid}
    </div>
  </main>
  <footer>{esc(profile.get("footer", ""))}</footer>
</div>
</body>
</html>
"""
    (SITE / "index.html").write_text(page)
    kb = len(page.encode()) / 1024
    print("built site/index.html  (%d items, %.1f KB, %d images)"
          % (len(items), kb, len(used)))


if __name__ == "__main__":
    build()
