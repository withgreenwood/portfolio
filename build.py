#!/usr/bin/env python3
"""Build site/index.html from content/profile.json + content/items.json.

Layout: the "full flip" treatment — flat white ground, black hairline rules,
one accent colour, a tight uppercase grotesk for the wordmark and a wide
uppercase monospace for everything else. The page needs no JavaScript.

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

FONTS = ("https://fonts.googleapis.com/css2"
         "?family=IBM+Plex+Mono:wght@400;500;600"
         "&family=Inter+Tight:wght@500;600;700&display=swap")


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


# Written mobile-first with __TOKEN__ placeholders rather than an f-string, so
# the CSS braces stay readable instead of being doubled throughout.
CSS = """
:root{
  --ink:#000; --bg:#fff; --accent:__ACCENT__; --panel:#dedede; --line:#000;
  --max:__MAX__; --gap:__GAP__px; --radius:__RADIUS__px; --pad:__PADM__px;
  --disp:"Helvetica Neue","Inter Tight",Helvetica,Arial,sans-serif;
  --mono:"IBM Plex Mono",ui-monospace,Menlo,Consolas,monospace;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);
  font:500 14px/1.5 var(--mono);text-transform:uppercase;
  -webkit-font-smoothing:antialiased}
a{color:inherit}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}

/* ---- ticker ---- */
.ticker{background:var(--accent);border-bottom:1px solid var(--line);
  overflow:hidden;white-space:nowrap}
.ticker-run{display:inline-block;padding:6px 0;
  font:500 11px/1.2 var(--mono);letter-spacing:.14em;
  animation:ticker 34s linear infinite}
.ticker-run span{padding:0 20px}
.ticker-run .dot{padding:0;opacity:.55}
@keyframes ticker{from{transform:translateX(0)}to{transform:translateX(-50%)}}
@media(prefers-reduced-motion:reduce){.ticker-run{animation:none}}

/* ---- identity bar ---- */
.idbar{position:sticky;top:0;z-index:10;display:flex;flex-wrap:wrap;
  align-items:stretch;border-bottom:1px solid var(--line);background:var(--bg)}
.idcell{display:flex;align-items:center;padding:0 var(--pad);min-height:52px}
.idcell+.idcell{border-left:1px solid var(--line)}
.idcell-name{width:100%;border-bottom:1px solid var(--line)}
.idcell-role{display:none}
.idcell-links{border-left:0}
.wordmark{font:600 clamp(17px,2.1vw,25px)/1 var(--disp);
  letter-spacing:-.045em;white-space:nowrap}
.role{font:500 11px/1.4 var(--mono);letter-spacing:.13em;white-space:nowrap}
.links{display:flex;gap:20px;list-style:none;margin:0;padding:0;flex-wrap:wrap}
.links a{font:500 11.5px/1 var(--mono);letter-spacing:.12em;text-decoration:none;
  padding-bottom:2px;border-bottom:1px solid transparent;
  transition:color .15s,border-color .15s}
.links a:hover{color:var(--accent);border-bottom-color:var(--accent)}

/* ---- section rule ---- */
.wrap{max-width:var(--max);margin:0 auto}
.rule{padding:clamp(26px,4vw,44px) var(--pad) 0}
.rule-in{display:flex;flex-wrap:wrap;justify-content:space-between;
  align-items:baseline;gap:6px 16px;
  padding-bottom:10px;border-bottom:1px solid var(--line);
  font:500 11px/1.4 var(--mono);letter-spacing:.14em}
.rule-meta{display:flex;flex-wrap:wrap;gap:6px 26px;margin-left:auto}

/* ---- grid ---- */
.pgf-grid{display:grid;grid-template-columns:repeat(__COLSM__,1fr);
  gap:var(--gap);background:var(--line);border:1px solid var(--line);
  margin:18px var(--pad) 0;padding:0}
.pgf-i{position:relative;display:block;aspect-ratio:4/5;max-width:100%;
  overflow:hidden;border-radius:var(--radius);background:var(--panel);
  text-decoration:none;color:inherit}
.pgf-i img{width:100%;height:100%;object-fit:cover;display:block;
  transition:transform .5s cubic-bezier(.2,.7,.3,1)}
.pgf-i:hover img,.pgf-i:focus-visible img{transform:scale(1.04)}
.pgf-ov{position:absolute;left:0;right:0;bottom:0;background:var(--ink);
  color:var(--bg);padding:9px 10px;transform:translateY(101%);
  transition:transform .22s cubic-bezier(.2,.7,.3,1)}
.pgf-i:hover .pgf-ov,.pgf-i:focus-visible .pgf-ov{transform:translateY(0)}
.pgf-t{display:block;font:500 10.5px/1.3 var(--mono);letter-spacing:.05em}
.pgf-s{display:block;margin-top:4px;font:400 9.5px/1.3 var(--mono);
  letter-spacing:.1em;color:var(--accent)}
.pgf-a{position:absolute;top:8px;right:8px;width:20px;height:20px;
  display:flex;align-items:center;justify-content:center;background:var(--bg);
  border:1px solid var(--line);font:500 11px/1 var(--mono);opacity:0;
  transition:opacity .22s}
.pgf-i:hover .pgf-a,.pgf-i:focus-visible .pgf-a{opacity:1}
.pgf-i:focus-visible{outline:2px solid var(--accent);outline-offset:-3px}
@media(hover:none){.pgf-ov{transform:translateY(0)}}
@media(prefers-reduced-motion:reduce){
  .pgf-i img,.pgf-ov,.pgf-a{transition:none}
  .pgf-i:hover img,.pgf-i:focus-visible img{transform:none}
}
.empty{margin:18px var(--pad) 0;text-align:center;font-size:12px;padding:60px 0;
  border:1px dashed var(--line)}

/* ---- footer ---- */
footer{margin-top:clamp(40px,6vw,72px);border-top:1px solid var(--line);
  background:var(--ink);color:var(--bg)}
.foot-in{max-width:var(--max);margin:0 auto;display:flex;flex-wrap:wrap;
  gap:20px 38px;align-items:baseline;padding-block:28px 32px;
  padding-left:var(--pad);padding-right:var(--pad);
  font:500 11px/1.6 var(--mono);letter-spacing:.13em}
.foot-in a{text-decoration:none;border-bottom:1px solid transparent;
  padding-bottom:2px}
.foot-in a:hover{color:var(--accent);border-bottom-color:var(--accent)}
.push{margin-left:0}

/* ---- wider ---- */
@media(min-width:620px){
  :root{--pad:__PAD__px}
  .idcell{min-height:62px}
  .idcell-name{width:auto;border-bottom:0}
  .idcell-links{border-left:1px solid var(--line);margin-left:auto}
  .pgf-grid{grid-template-columns:repeat(__COLSMID__,1fr)}
  .push{margin-left:auto}
}
@media(min-width:940px){
  .pgf-grid{grid-template-columns:repeat(__COLS__,1fr)}
}
@media(min-width:1000px){
  .idcell-role{display:flex}
}
"""


def stylesheet(lay):
    maxw = lay.get("maxWidth", 1180)
    maxw = "100%" if maxw in ("100%", "full") else "%dpx" % int(maxw)
    subs = {
        "__ACCENT__": str(lay.get("accent", "#ff5232")),
        "__MAX__": maxw,
        "__GAP__": str(int(lay.get("gap", 1))),
        "__RADIUS__": str(int(lay.get("radius", 0))),
        "__PAD__": str(int(lay.get("pagePadding", 24))),
        "__PADM__": str(int(lay.get("pagePaddingMobile", 15))),
        "__COLS__": str(int(lay.get("columns", 4))),
        "__COLSMID__": str(int(lay.get("columnsMid", 3))),
        "__COLSM__": str(int(lay.get("columnsMobile", 2))),
    }
    css = CSS
    for k, v in subs.items():
        css = css.replace(k, v)
    return css


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

    lay = profile.get("layout", {})

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
        src = esc(it["image"]) if is_remote(it["image"]) else "images/" + esc(it["image"])
        tiles.append(
            f'<a class="pgf-i" data-t="{typ}" href="{esc(it.get("url"))}" '
            f'target="_blank" rel="noopener noreferrer">'
            f'<img src="{src}" alt="{alt}" width="1080" height="1350" '
            f'loading="lazy" decoding="async">'
            f'<span class="pgf-a" aria-hidden="true">&#8599;</span>{ov}</a>')

    if tiles:
        grid = '<main class="pgf-grid">\n    ' + "\n    ".join(tiles) + "\n  </main>"
    else:
        grid = ('<div class="empty">No items yet — add some in '
                '<code>content/items.json</code> and run <code>python3 build.py</code>.</div>')

    # ---- ticker: the phrase list is duplicated so the -50% keyframe loops seamlessly
    phrases = [p for p in profile.get("ticker", []) if str(p).strip()]
    ticker = ""
    if phrases:
        run = "".join(f'<span>{esc(p)}</span><span class="dot">&bull;</span>'
                      for p in phrases)
        ticker = (f'<div class="ticker"><div class="ticker-run">{run}{run}</div></div>')

    links = "".join(
        f'<li><a href="{esc(l.get("url"))}">{esc(l.get("label"))}</a></li>'
        for l in profile.get("links", []) if l.get("url"))
    links_html = f'<ul class="links">{links}</ul>' if links else ""

    foot_links = "".join(
        f'<a href="{esc(l.get("url"))}">{esc(l.get("label"))}</a>'
        for l in profile.get("links", []) if l.get("url"))

    name = esc(profile.get("name", "Portfolio"))
    tagline = profile.get("tagline")
    work_label = esc(profile.get("workLabel", "Selected Work"))
    count = "%d Project%s" % (len(items), "" if len(items) == 1 else "s")
    meta = profile.get("metaDescription") or profile.get("bio")
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
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<style>{stylesheet(lay)}</style>
</head>
<body>
{ticker}
<header class="idbar">
  <div class="idcell idcell-name"><span class="wordmark">{name}</span></div>
  {f'<div class="idcell idcell-role"><span class="role">{esc(tagline)}</span></div>' if tagline else ''}
  <div class="idcell idcell-links">{links_html}</div>
</header>
<div class="wrap">
  <div class="rule">
    <div class="rule-in"><span>{esc(tagline)}</span><span class="rule-meta"><span>{work_label}</span><span>{count}</span></span></div>
  </div>
  {grid}
</div>
<footer>
  <div class="foot-in">
    {foot_links}
    <span class="push">{esc(profile.get("footer", ""))}</span>
  </div>
</footer>
</body>
</html>
"""
    (SITE / "index.html").write_text(page)
    kb = len(page.encode()) / 1024
    print("built site/index.html  (%d items, %.1f KB, %d images)"
          % (len(items), kb, len(used)))


if __name__ == "__main__":
    build()
