#!/usr/bin/env python3
"""Build the archive pages (site/archive/...) from content/pages.json.

These are the prose pages that used to live on the Squarespace site, rebuilt
in the same "full flip" treatment as the grid. They are served at
archive.withgreenwood.com; the Worker maps that hostname onto /archive/*.

Run directly (`python3 archive.py`) or let build.py call it after the grid.
"""
import shutil
import sys
from pathlib import Path

from build import CONTENT, FONTS, SITE, die, esc, load, stylesheet

OUT = SITE / "archive"

# Prose lives inside the same token set as the grid, but undoes the global
# uppercase/mono treatment -- long-form text in wide mono is unreadable.
PROSE_CSS = """
/* ---- page nav ---- */
.pagenav{display:flex;flex-wrap:wrap;gap:0;
  border-bottom:1px solid var(--line);margin:0 var(--pad)}
.pagenav a{flex:1 1 auto;text-align:center;padding:11px 14px;
  font:500 11px/1 var(--mono);letter-spacing:.14em;text-decoration:none;
  border-left:1px solid var(--line);transition:background .15s,color .15s}
.pagenav a:first-child{border-left:0}
.pagenav a:hover{background:var(--ink);color:var(--bg)}
.pagenav a[aria-current="page"]{background:var(--accent)}

/* ---- prose ---- */
.prose{padding:clamp(26px,4vw,46px) var(--pad) 0;text-transform:none;
  font:400 16px/1.72 var(--disp);letter-spacing:0}
.prose>*{max-width:68ch}
.prose p{margin:0 0 1.2em}
.prose p+p{margin-top:0}
.prose .lede{max-width:26ch;
  font:600 clamp(23px,4.2vw,40px)/1.12 var(--disp);letter-spacing:-.035em;
  margin:0 0 1.1em}
.prose h2{font:600 clamp(18px,2.3vw,24px)/1.2 var(--disp);
  letter-spacing:-.03em;margin:2.2em 0 .7em}
.prose h2:first-child{margin-top:0}
.prose a{color:var(--accent);text-decoration:none;
  border-bottom:1px solid var(--accent)}
.prose ul{margin:0 0 1.2em;padding-left:1.1em}
.prose li{margin:0 0 .35em}
.prose blockquote{margin:1.6em 0;padding-left:18px;
  border-left:2px solid var(--accent);font-size:1.06em}
.prose figure{margin:1.8em 0;max-width:100%}
.prose figure img{display:block;width:100%;height:auto;border:1px solid var(--line)}
.prose figcaption{margin-top:8px;font:500 10.5px/1.4 var(--mono);
  letter-spacing:.11em;text-transform:uppercase;opacity:.62}

/* ---- hairline cells (areas of expertise etc.) ---- */
.cells{display:grid;grid-template-columns:1fr;gap:1px;max-width:none;
  background:var(--line);border:1px solid var(--line);margin:0 0 1.6em}
.cells div{background:var(--bg);padding:16px var(--pad);
  font:500 11.5px/1.35 var(--mono);letter-spacing:.12em;text-transform:uppercase}
@media(min-width:620px){.cells{grid-template-columns:repeat(2,1fr)}}
@media(min-width:940px){.cells{grid-template-columns:repeat(3,1fr)}}
"""


def rel(depth):
    """Link prefix back to the archive root from a page `depth` levels down."""
    return "../" * depth


def block_html(b, pfx):
    if isinstance(b, str):
        b = {"type": "p", "text": b}
    t = b.get("type", "p")

    if t == "p":
        return "<p>%s</p>" % esc(b.get("text"))
    if t == "lede":
        return '<p class="lede">%s</p>' % esc(b.get("text"))
    if t == "h2":
        return "<h2>%s</h2>" % esc(b.get("text"))
    if t == "quote":
        return "<blockquote>%s</blockquote>" % esc(b.get("text"))
    if t == "list":
        lis = "".join("<li>%s</li>" % esc(i) for i in b.get("items", []))
        return "<ul>%s</ul>" % lis
    if t == "cells":
        ds = "".join("<div>%s</div>" % esc(i) for i in b.get("items", []))
        return '<div class="cells">%s</div>' % ds
    if t == "image":
        src = str(b.get("src", ""))
        if not src.lower().startswith(("http://", "https://")):
            src = pfx + "images/" + src
        cap = b.get("caption")
        fig = '<img src="%s" alt="%s" loading="lazy" decoding="async">' % (
            esc(src), esc(b.get("alt") or cap or ""))
        if cap:
            fig += "<figcaption>%s</figcaption>" % esc(cap)
        return "<figure>%s</figure>" % fig
    if t == "html":
        return str(b.get("html", ""))
    die("unknown block type %r in pages.json" % t)


def chrome(profile, doc):
    """The ticker + identity bar, shared with the grid."""
    phrases = [p for p in profile.get("ticker", []) if str(p).strip()]
    ticker = ""
    if phrases:
        run = "".join('<span>%s</span><span class="dot">&bull;</span>' % esc(p)
                      for p in phrases)
        ticker = '<div class="ticker"><div class="ticker-run">%s%s</div></div>' % (run, run)

    # Same plain-label treatment as the grid's identity bar.
    lis = ['<li><a href="%s">%s</a></li>' % (esc(l.get("url")), esc(l.get("label")))
           for l in profile.get("links", []) if l.get("url")]
    links = '<ul class="links">%s</ul>' % "".join(lis) if lis else ""

    name = esc(profile.get("name", "Portfolio"))
    home = esc(doc.get("homeUrl", "https://withgreenwood.com/"))
    return ticker, (
        '<header class="idbar">\n'
        '  <div class="idcell idcell-name">'
        '<a href="%s" style="text-decoration:none">'
        '<span class="wordmark">%s</span></a></div>\n'
        '  <div class="idcell idcell-links">%s</div>\n'
        '</header>' % (home, name, links))


def page_html(page, doc, profile, pages):
    depth = 0 if not page.get("slug") else 1
    pfx = rel(depth)

    nav = "".join(
        '<a href="%s"%s>%s</a>' % (
            pfx + (p["slug"] + "/" if p.get("slug") else ""),
            ' aria-current="page"' if p is page else "",
            esc(p.get("label") or p.get("title")))
        for p in pages)
    nav = '<nav class="pagenav">%s</nav>' % nav if len(pages) > 1 else ""

    body = "\n    ".join(block_html(b, pfx) for b in page.get("blocks", []))

    ticker, idbar = chrome(profile, doc)

    site_name = esc(profile.get("name", ""))
    title = esc(page.get("title") or site_name)
    full_title = "%s — %s" % (title, site_name) if page.get("slug") else site_name
    meta = esc(page.get("metaDescription") or doc.get("metaDescription") or "")
    base = str(doc.get("baseUrl", "")).rstrip("/")
    url = "%s/%s" % (base, page["slug"] + "/" if page.get("slug") else "") if base else ""

    foot_links = "".join(
        '<a href="%s">%s</a>' % (esc(l.get("url")), esc(l.get("label")))
        for l in profile.get("links", []) if l.get("url"))
    foot_links += '<a href="%s">%s</a>' % (
        esc(doc.get("homeUrl", "https://withgreenwood.com/")),
        esc(doc.get("homeLabel", "Work")))

    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%(full_title)s</title>
<meta name="description" content="%(meta)s">
<meta property="og:title" content="%(full_title)s">
<meta property="og:description" content="%(meta)s">
<meta property="og:type" content="article">
%(ogurl)s
<meta name="twitter:card" content="summary">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'><text y='13' font-size='14'>&#9642;</text></svg>">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="%(fonts)s">
<style>%(css)s</style>
</head>
<body>
%(ticker)s
%(idbar)s
<div class="wrap">
  <div class="rule">
    <div class="rule-in"><span>%(label)s</span><span class="rule-meta"><span>%(kicker)s</span></span></div>
  </div>
  %(nav)s
  <article class="prose">
    %(body)s
  </article>
</div>
<footer>
  <div class="foot-in">
    %(foot)s
    <span class="push">%(copy)s</span>
  </div>
</footer>
</body>
</html>
""" % {
        "full_title": full_title,
        "meta": meta,
        "ogurl": ('<meta property="og:url" content="%s">' % esc(url)) if url else "",
        "fonts": FONTS,
        "css": stylesheet(profile.get("layout", {})) + PROSE_CSS,
        "ticker": ticker,
        "idbar": idbar,
        "label": esc(page.get("title") or ""),
        "kicker": esc(doc.get("kicker", "Archive")),
        "nav": nav,
        "body": body,
        "foot": foot_links,
        "copy": esc(profile.get("footer", "")),
    }


def build_archive(profile=None, quiet=False):
    src = CONTENT / "pages.json"
    if not src.exists():
        if not quiet:
            print("no content/pages.json — skipping archive")
        return
    doc = load("pages.json")
    pages = doc.get("pages", [])
    if not pages:
        die("pages.json has no pages")
    if profile is None:
        profile = load("profile.json")

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    imgsrc = CONTENT / "archive-images"
    if imgsrc.exists():
        shutil.copytree(imgsrc, OUT / "images")

    for p in pages:
        slug = p.get("slug", "")
        d = OUT / slug if slug else OUT
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(page_html(p, doc, profile, pages))

    if not quiet:
        print("built site/archive/  (%d page%s)"
              % (len(pages), "" if len(pages) == 1 else "s"))


if __name__ == "__main__":
    build_archive()
