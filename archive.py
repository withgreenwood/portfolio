#!/usr/bin/env python3
"""Build the archive pages (site/archive/...) from content/pages.json.

These are the prose and case-study pages that used to live on the Squarespace
site, rebuilt in the same "full flip" treatment as the grid. They are served
from the same Worker as the grid, at /archive/*.

Page slugs may nest: a slug of "work/trillectro" builds
site/archive/work/trillectro/index.html and links back up two levels. Only
pages with "nav": true appear in the page nav.

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
.prose .intro{max-width:60ch;font-size:1.17em;line-height:1.6;
  margin:0 0 1.35em}
.prose .lede{max-width:34ch;
  font:600 clamp(21px,3.4vw,33px)/1.16 var(--disp);letter-spacing:-.032em;
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

/* ---- hairline cells (areas of expertise, credit lists) ----
   The rules are drawn by a 1px shadow on every cell rather than by letting a
   black container show through a 1px gap: a part-filled last row would
   otherwise leave a black slab where the missing cells are. */
.cells{display:grid;grid-template-columns:1fr;gap:1px;max-width:none;
  background:var(--bg);padding:1px;margin:0 0 1.6em}
.cells div{background:var(--bg);box-shadow:0 0 0 1px var(--line);
  padding:16px var(--pad);
  font:500 11.5px/1.35 var(--mono);letter-spacing:.12em;text-transform:uppercase}
.cells a{color:inherit;text-decoration:none;border:0;
  border-bottom:1px solid transparent}
.cells a:hover{color:var(--accent);border-bottom-color:var(--accent)}
@media(min-width:620px){.cells{grid-template-columns:repeat(2,1fr)}}
@media(min-width:940px){.cells{grid-template-columns:repeat(3,1fr)}}

/* ---- lead image: full-bleed inside the wrap, no figure margins ---- */
.lead{margin:0 var(--pad);max-width:none;border:1px solid var(--line);
  border-top:0}
.lead img{display:block;width:100%;height:auto}

/* ---- gallery: justified rows ----
   These photographs are 3:2, 2:3, 4:3, square and 16:9 all mixed together, so
   a fixed column grid leaves every short image sitting in a pocket of white --
   which, in a layout made of flush hairlines, reads as broken.

   Instead each figure carries its own aspect ratio in --r (written by
   archive.py from the JPEG header) and flexes in proportion to it. Within any
   one line, widths are proportional to ratios, so every image on that line
   lands on the same height and the line fills the width exactly. Nothing is
   cropped and no row is ragged. The ::after with an enormous flex-grow eats
   the slack on the final line so a short last row keeps its natural size
   instead of being stretched across the page.

   --gh is the base row height; the real height per line is whatever filling
   the width requires, so this is a floor rather than a fixed value. */
.gal{display:flex;flex-wrap:wrap;gap:1px;max-width:none;
  background:var(--bg);padding:1px;margin:0 0 1.8em;--gh:120px}
.gal::after{content:"";flex-grow:999999}
.gal figure{margin:0;min-width:0;background:var(--bg);
  box-shadow:0 0 0 1px var(--line);
  flex-grow:var(--r);flex-shrink:1;flex-basis:calc(var(--r) * var(--gh))}
.gal img{display:block;width:100%;height:auto;border:0;aspect-ratio:var(--r)}
.gal figcaption{padding:0 12px 12px}
@media(min-width:620px){.gal{--gh:165px}}
@media(min-width:940px){.gal{--gh:215px}}

/* ---- index cards (the projects page) ----
   Same treatment as the grid tiles in build.py -- image fills the cell, slow
   zoom on hover, the label riding up over it, and the corner badge fading in.
   The one difference is the crop: these keep 4/3 rather than the grid's 4/5.
   Timings and easings are copied verbatim so the two read as one system. */
.cards{display:grid;grid-template-columns:repeat(1,1fr);gap:1px;
  max-width:none;background:var(--bg);padding:1px;margin:0 0 1.8em}
.card{position:relative;display:block;aspect-ratio:4/3;max-width:100%;
  overflow:hidden;background:var(--panel);box-shadow:0 0 0 1px var(--line);
  text-decoration:none;color:inherit;border:0}
.card:hover{border:0}
.card-img{display:block;width:100%;height:100%;object-fit:cover;
  transition:transform .5s cubic-bezier(.2,.7,.3,1)}
.card:hover .card-img,.card:focus-visible .card-img{transform:scale(1.04)}
.card-ov{position:absolute;left:0;right:0;bottom:0;background:var(--ink);
  color:var(--bg);padding:9px 10px;transform:translateY(101%);
  transition:transform .22s cubic-bezier(.2,.7,.3,1)}
.card:hover .card-ov,.card:focus-visible .card-ov{transform:translateY(0)}
.card-t{display:block;font:500 10.5px/1.3 var(--mono);letter-spacing:.05em;
  text-transform:uppercase}
.card-a{position:absolute;top:8px;right:8px;width:20px;height:20px;
  display:flex;align-items:center;justify-content:center;background:var(--bg);
  border:1px solid var(--line);color:var(--ink);font:500 11px/1 var(--mono);
  opacity:0;transition:opacity .22s}
.card:hover .card-a,.card:focus-visible .card-a{opacity:1}
.card:focus-visible{outline:2px solid var(--accent);outline-offset:-3px}
@media(hover:none){.card-ov{transform:translateY(0)}}
@media(prefers-reduced-motion:reduce){
  .card-img,.card-ov,.card-a{transition:none}
  .card:hover .card-img,.card:focus-visible .card-img{transform:none}
}
@media(min-width:620px){.cards{grid-template-columns:repeat(2,1fr)}}
@media(min-width:940px){.cards{grid-template-columns:repeat(3,1fr)}}

/* ---- back link ---- */
.back{padding:22px var(--pad) 0;font:500 11px/1 var(--mono);
  letter-spacing:.14em}
.back a{text-decoration:none;border-bottom:1px solid transparent}
.back a:hover{color:var(--accent);border-bottom-color:var(--accent)}
"""


def rel(slug):
    """Link prefix back to the archive root from a page at `slug`."""
    if not slug:
        return ""
    return "../" * (slug.strip("/").count("/") + 1)


# Justified rows need every image's shape at build time. Reading the JPEG
# header directly avoids a Pillow dependency for what is four bytes of data.
_RATIOS = {}
_SOF = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
        0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}


def ratio(name, default=1.5):
    """Width/height of an image in content/archive-images, 1.5 if unknown."""
    if name in _RATIOS:
        return _RATIOS[name]
    r = default
    path = CONTENT / "archive-images" / str(name)
    try:
        data = path.read_bytes()
        i = 2
        while i < len(data) - 9:
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            if marker in _SOF:
                h = (data[i + 5] << 8) | data[i + 6]
                w = (data[i + 7] << 8) | data[i + 8]
                if h:
                    r = round(w / h, 4)
                break
            if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
                i += 2
                continue
            i += 2 + ((data[i + 2] << 8) | data[i + 3])
    except (OSError, IndexError, ZeroDivisionError):
        pass
    _RATIOS[name] = r
    return r


def img_src(src, pfx):
    src = str(src or "")
    if src.lower().startswith(("http://", "https://")):
        return src
    return pfx + "images/" + src


def block_html(b, pfx):
    if isinstance(b, str):
        b = {"type": "p", "text": b}
    t = b.get("type", "p")

    if t == "p":
        return "<p>%s</p>" % esc(b.get("text"))
    if t == "lede":
        return '<p class="lede">%s</p>' % esc(b.get("text"))
    if t == "intro":
        return '<p class="intro">%s</p>' % esc(b.get("text"))
    if t == "h2":
        return "<h2>%s</h2>" % esc(b.get("text"))
    if t == "quote":
        return "<blockquote>%s</blockquote>" % esc(b.get("text"))
    if t == "list":
        lis = "".join("<li>%s</li>" % esc(i) for i in b.get("items", []))
        return "<ul>%s</ul>" % lis
    if t == "cells":
        ds = []
        for i in b.get("items", []):
            if isinstance(i, dict):
                label = esc(i.get("label"))
                url = i.get("url")
                inner = ('<a href="%s" rel="noopener">%s</a>' % (esc(url), label)
                         if url else label)
            else:
                inner = esc(i)
            ds.append("<div>%s</div>" % inner)
        return '<div class="cells">%s</div>' % "".join(ds)
    if t == "image":
        cap = b.get("caption")
        fig = '<img src="%s" alt="%s" loading="lazy" decoding="async">' % (
            esc(img_src(b.get("src"), pfx)), esc(b.get("alt") or cap or ""))
        if cap:
            fig += "<figcaption>%s</figcaption>" % esc(cap)
        return "<figure>%s</figure>" % fig
    if t == "gallery":
        # "cols" is still accepted in pages.json but no longer does anything:
        # justified rows decide how many images a line holds by their shapes.
        figs = []
        for i in b.get("items", []):
            if isinstance(i, str):
                i = {"src": i}
            cap = i.get("caption")
            r = ratio(i.get("src"))
            f = '<img src="%s" alt="%s" loading="lazy" decoding="async">' % (
                esc(img_src(i.get("src"), pfx)), esc(i.get("alt") or cap or ""))
            if cap:
                f += "<figcaption>%s</figcaption>" % esc(cap)
            figs.append('<figure style="--r:%g">%s</figure>' % (r, f))
        return '<div class="gal">%s</div>' % "".join(figs)
    if t == "cards":
        cs = []
        for i in b.get("items", []):
            # Title only in the overlay -- the client sits on the case study
            # itself, as its kicker, and a second line here was noise.
            # The badge is an arrow, not the grid's diagonal: these go to
            # another page on this site, not off it.
            cs.append(
                '<a class="card" href="%s">'
                '<img class="card-img" src="%s" alt="%s" width="1200" height="900" '
                'loading="lazy" decoding="async">'
                '<span class="card-a" aria-hidden="true">&#8594;</span>'
                '<span class="card-ov"><span class="card-t">%s</span></span>'
                '</a>' % (
                    esc(pfx + str(i.get("href", "")).lstrip("/")),
                    esc(img_src(i.get("image"), pfx)),
                    esc(i.get("title")), esc(i.get("title"))))
        return '<div class="cards">%s</div>' % "".join(cs)
    if t == "html":
        return str(b.get("html", ""))
    die("unknown block type %r in pages.json" % t)


def chrome(profile, doc, pfx):
    """The identity bar. No ticker — that belongs to the grid.

    The archive pages are for reading, and a looping marquee of current
    clients sits wrong above ten-year-old work. The ticker CSS stays in the
    shared stylesheet; nothing here emits the markup.
    """
    ticker = ""

    # Same plain-label treatment as the grid's identity bar.
    lis = ['<li><a href="%s">%s</a></li>' % (esc(l.get("url")), esc(l.get("label")))
           for l in profile.get("links", []) if l.get("url")]
    links = '<ul class="links">%s</ul>' % "".join(lis) if lis else ""

    name = esc(profile.get("name", "Portfolio"))
    home = esc(doc.get("homeUrl", "/"))
    return ticker, (
        '<header class="idbar">\n'
        '  <div class="idcell idcell-name">'
        '<a href="%s" style="text-decoration:none">'
        '<span class="wordmark">%s</span></a></div>\n'
        '  <div class="idcell idcell-links">%s</div>\n'
        '</header>' % (home, name, links))


def page_html(page, doc, profile, pages):
    slug = page.get("slug", "")
    pfx = rel(slug)

    navpages = [p for p in pages if p.get("nav")]
    nav = ""
    if len(navpages) > 1:
        # A nested page highlights the section it belongs to.
        section = slug.split("/")[0] if slug else ""
        nav = "".join(
            '<a href="%s"%s>%s</a>' % (
                pfx + (p["slug"] + "/" if p.get("slug") else ""),
                ' aria-current="page"' if p.get("slug", "") == section else "",
                esc(p.get("label") or p.get("title")))
            for p in navpages)
        nav = '<nav class="pagenav">%s</nav>' % nav

    lead = ""
    if page.get("lead"):
        lead = ('<div class="lead"><img src="%s" alt="%s" '
                'decoding="async"></div>' % (
                    esc(img_src(page["lead"], pfx)),
                    esc(page.get("leadAlt") or page.get("title") or "")))

    back = ""
    if page.get("back"):
        back = ('<div class="back"><a href="%s">&larr; %s</a></div>' % (
            esc(pfx + str(page["back"]["href"]).lstrip("/")),
            esc(page["back"]["label"])))

    body = "\n    ".join(block_html(b, pfx) for b in page.get("blocks", []))

    ticker, idbar = chrome(profile, doc, pfx)

    site_name = esc(profile.get("name", ""))
    title = esc(page.get("title") or site_name)
    full_title = "%s — %s" % (title, site_name) if slug else site_name
    meta = esc(page.get("metaDescription") or doc.get("metaDescription") or "")
    base = str(doc.get("baseUrl", "")).rstrip("/")
    url = "%s/%s" % (base, slug + "/" if slug else "") if base else ""
    og_img = ""
    if page.get("lead") or page.get("cover"):
        src = page.get("lead") or page.get("cover")
        if str(src).lower().startswith(("http://", "https://")):
            og_img = str(src)
        elif base:
            og_img = "%s/images/%s" % (base, src)

    foot_links = "".join(
        '<a href="%s">%s</a>' % (esc(l.get("url")), esc(l.get("label")))
        for l in profile.get("links", []) if l.get("url"))
    foot_links += '<a href="%s">%s</a>' % (
        esc(doc.get("homeUrl", "/")),
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
%(ogimg)s
<meta name="twitter:card" content="%(card)s">
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
  %(back)s
  <div class="rule">
    <div class="rule-in"><span>%(label)s</span><span class="rule-meta"><span>%(kicker)s</span></span></div>
  </div>
  %(nav)s
  %(lead)s
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
        "ogimg": ('<meta property="og:image" content="%s">' % esc(og_img)) if og_img else "",
        "card": "summary_large_image" if og_img else "summary",
        "fonts": FONTS,
        "css": stylesheet(profile.get("layout", {})) + PROSE_CSS,
        "ticker": ticker,
        "idbar": idbar,
        "back": back,
        "label": esc(page.get("title") or ""),
        "kicker": esc(page.get("kicker") or doc.get("kicker", "Archive")),
        "nav": nav,
        "lead": lead,
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

    # A page marked "hidden" keeps its copy and its images in the repo but is
    # not built, not linked and not redirected to -- the way to shelve one
    # without losing it. Drop the flag to bring it back.
    shelved = [p for p in pages if p.get("hidden")]
    pages = [p for p in pages if not p.get("hidden")]
    if not pages:
        die("every page in pages.json is hidden")
    if profile is None:
        profile = load("profile.json")

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    imgsrc = CONTENT / "archive-images"
    have = set()
    if imgsrc.exists():
        shutil.copytree(imgsrc, OUT / "images")
        have = {f.name for f in (OUT / "images").iterdir() if f.is_file()}

    # Fail loudly on a typo'd filename rather than shipping a broken <img>.
    def check(src_name, where):
        s = str(src_name or "")
        if s and not s.lower().startswith(("http://", "https://")) and s not in have:
            missing.append("%s (%s)" % (s, where))

    missing = []
    for p in pages:
        where = "/" + p.get("slug", "")
        check(p.get("lead"), where)
        check(p.get("cover"), where)
        for b in p.get("blocks", []):
            if not isinstance(b, dict):
                continue
            if b.get("type") == "image":
                check(b.get("src"), where)
            elif b.get("type") == "gallery":
                for i in b.get("items", []):
                    check(i if isinstance(i, str) else i.get("src"), where)
            elif b.get("type") == "cards":
                for i in b.get("items", []):
                    check(i.get("image"), where)
    if missing:
        die("archive images not found in content/archive-images: %s"
            % ", ".join(missing))

    for p in pages:
        slug = p.get("slug", "")
        d = OUT / slug if slug else OUT
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(page_html(p, doc, profile, pages))

    # Old Squarespace paths -> their new homes. Cloudflare's static-asset
    # Worker reads site/_redirects; the file has to sit at the assets root,
    # not inside site/archive/.
    reds = doc.get("redirects") or {}
    if reds:
        lines = ["# generated by archive.py — old Squarespace URLs"]
        lines += ["%s %s 301" % (k, v) for k, v in sorted(reds.items())]
        (SITE / "_redirects").write_text("\n".join(lines) + "\n")

    if not quiet:
        note = ""
        if shelved:
            note = ", %d shelved: %s" % (
                len(shelved), ", ".join(p.get("slug", "?") for p in shelved))
        print("built site/archive/  (%d page%s, %d images, %d redirects%s)"
              % (len(pages), "" if len(pages) == 1 else "s", len(have),
                 len(reds), note))


if __name__ == "__main__":
    build_archive()
