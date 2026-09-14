#!/usr/bin/env python3
"""Build the archive pages (site/archive/...) from content/pages.json.

These are the prose and case-study pages that used to live on the Squarespace
site, rebuilt in the same "full flip" treatment as the grid. They are served
from the same Worker as the grid, at /archive/*.

Images and the two h.264 loops open in a lightbox — the one part of the
archive that needs JavaScript. Without it the page still reads; the images
just don't open, and the loops fall back to their poster frame.

Page slugs may nest: a slug of "work/trillectro" builds
site/archive/work/trillectro/index.html and links back up two levels. Only
pages with "nav": true appear in the page nav.

Run directly (`python3 archive.py`) or let build.py call it after the grid.
"""
import shutil
import sys
from pathlib import Path

from build import (CONTENT, FONTS, SITE, die, esc, load, rule_toggle,
                   stylesheet)

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
/* "reading": true in pages.json. A page that is one long piece of prose --
   Story is the only one -- next to a full-width band of photographs leaves a
   lot of empty column beside 68ch of 16px text. The fix is bigger type, not a
   longer line: 20px carries the same ~79 characters a line the site sets
   everywhere else while occupying ~150px more width. Widening the measure
   instead would have put 102 characters on a line, which is a worse read than
   the white space it tidied away. */
/* Wide screens only: on a phone there is no empty column to answer and
   20px would just make the page longer. */
@media(min-width:620px){.prose.read>p{font-size:1.25em;line-height:1.62}}
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

/* ---- lead image, side variant ----
   story-01.jpg is only 540px wide at source, so the full-bleed treatment above
   stretched it to ~1180px and it went soft. A page with "leadSide" in
   pages.json drops the image into the prose as a float instead: it renders
   around 320px, well inside the source width, and the opening paragraphs run
   up beside it. Headings, galleries and cells clear the float so nothing
   collides with it, and below 620px it unwraps to a full-width block. */
.prose .lead-side{float:right;width:min(42%,320px);
  margin:.3em 0 1.3em 26px}
.prose .lead-side img{display:block;width:100%;height:auto;
  border:1px solid var(--line)}
.prose h2,.prose .gal,.prose .cells,.prose .cards{clear:both}
@media(max-width:619px){
  .prose .lead-side{float:none;width:100%;margin:0 0 1.4em}
}

/* ---- gallery: justified rows ----
   These photographs are 3:2, 2:3, 4:3, square and 16:9 all mixed together, so
   a fixed column grid leaves every short image sitting in a pocket of white --
   which, in a layout made of flush hairlines, reads as broken.

   archive.py packs them into rows at build time and gives each figure a
   percentage width proportional to its aspect ratio. Every row therefore
   spans the full width exactly, the last one included, and every image in a
   row lands on the same height. Nothing is cropped and no white shows.
   Because the widths are percentages, the rows rescale with the container.

   Under 620px the rows unwrap: one image per line, full width. Three
   landscape shots sharing a phone screen are 80px tall and worth nothing. */
.gal{display:flex;flex-direction:column;gap:1px;max-width:none;
  background:var(--bg);padding:1px;margin:0 0 1.8em}
.gal-row{display:flex;gap:1px;min-width:0}
.gal figure{margin:0;min-width:0;background:var(--bg);
  box-shadow:0 0 0 1px var(--line);flex-grow:0;flex-shrink:1}
.gal img,.gal .mov{display:block;width:100%;height:auto;border:0;
  aspect-ratio:var(--r)}
.gal .mov{background:var(--panel)}
.gal figcaption{padding:0 12px 12px}
@media(max-width:619px){
  .gal-row{flex-direction:column;gap:1px}
  .gal figure{flex-basis:auto !important;width:100%}
}

/* ---- index cards (the projects page) ----
   Same treatment as the grid tiles in build.py -- image fills the cell, slow
   zoom on hover, the label riding up over it, and the corner badge fading in.
   The one difference is the crop: these keep 4/3 rather than the grid's 4/5.
   Timings and easings are copied verbatim so the two read as one system. */
.cards{display:grid;grid-template-columns:repeat(1,1fr);gap:1px;
  max-width:none;background:var(--bg);padding:1px;margin:0 0 1.8em}
/* Written as `a.card`, not `.card`: `.prose a` further up gives every link in
   the prose an accent underline, and at equal specificity it would win and
   draw a 1px orange rule across the bottom of every tile. */
.prose a.card{position:relative;display:block;aspect-ratio:4/3;max-width:100%;
  overflow:hidden;background:var(--panel);box-shadow:0 0 0 1px var(--line);
  text-decoration:none;color:inherit;border:0}
.prose a.card:hover{border:0}
.card-img{display:block;width:100%;height:100%;object-fit:cover;background:var(--panel);
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

/* ---- lightbox ----
   Every lead and gallery image opens full screen, with arrows, keys and
   swipe to move through the set. This is the one piece of the archive that
   needs JavaScript; without it the images still sit on the page as before,
   the buttons just do nothing. */
.zoom{display:block;width:100%;padding:0;border:0;background:none;
  color:inherit;font:inherit;cursor:zoom-in}
.zoom:focus-visible{outline:2px solid var(--accent);outline-offset:-3px}
/* The side padding is a gutter for the arrows: on a phone they would
   otherwise sit on top of the photograph. */
.lb{position:fixed;inset:0;z-index:100;background:rgba(0,0,0,.94);
  display:flex;align-items:center;justify-content:center;padding:56px 46px}
.lb[hidden]{display:none}
.lb-stage{display:flex;align-items:center;justify-content:center;
  max-width:100%;max-height:100%}
.lb-img,.lb-vid{display:block;width:auto;height:auto;
  max-width:100%;max-height:calc(100vh - 120px);object-fit:contain}
.lb-stage [hidden]{display:none}
.lb-btn{position:absolute;background:none;border:0;padding:12px;color:#fff;
  cursor:pointer;font:500 20px/1 var(--mono);transition:color .15s}
.lb-btn:hover{color:var(--accent)}
.lb-btn:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.lb-x{top:6px;right:8px;font-size:24px}
.lb-prev{left:2px;top:50%;transform:translateY(-50%)}
.lb-next{right:2px;top:50%;transform:translateY(-50%)}
.lb-count{position:absolute;left:0;right:0;bottom:16px;text-align:center;
  color:#fff;font:500 11px/1 var(--mono);letter-spacing:.14em}
@media(min-width:620px){
  .lb{padding:64px 68px}
  .lb-prev{left:12px}
  .lb-next{right:12px}
}
@media(prefers-reduced-motion:reduce){.lb-btn{transition:none}}

/* ---- back link ---- */
.back{padding:22px var(--pad) 0;font:500 11px/1 var(--mono);
  letter-spacing:.14em}
.back a{text-decoration:none;border-bottom:1px solid transparent}
.back a:hover{color:var(--accent);border-bottom-color:var(--accent)}

/* ---- the rule's right-hand slot, when it is a link back to the grid ----
   Matches .back: no underline at rest, accent rule on hover. The arrow is a
   separate span so it can be nudged without letter-spacing pushing it away
   from the word. */
.rule-meta a{color:inherit;text-decoration:none;
  border-bottom:1px solid transparent}
.rule-meta a:hover{color:var(--accent);border-bottom-color:var(--accent)}
"""


CARD_MOTION = """
<script>
/* The cards page carries no lightbox, so the reduced-motion guard the
   galleries get from that script has to travel with the cards themselves.
   Freeze each looping tile on its poster frame if the OS asks for less
   motion. Without JS the tiles simply keep playing, as before. */
(function(){
  if (!window.matchMedia ||
      !window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  [].forEach.call(document.querySelectorAll("video.card-img"), function(v){
    v.autoplay = false; v.loop = false;
    try { v.pause(); v.removeAttribute("autoplay"); } catch (e) {}
  });
})();
</script>
"""


LIGHTBOX = """
<div class="lb" id="lb" hidden role="dialog" aria-modal="true" aria-label="Image viewer">
  <div class="lb-stage">
    <img class="lb-img" alt="">
    <video class="lb-vid" loop muted playsinline hidden></video>
  </div>
  <button type="button" class="lb-btn lb-x" data-act="close" aria-label="Close">&times;</button>
  <button type="button" class="lb-btn lb-prev" data-act="prev" aria-label="Previous image">&larr;</button>
  <button type="button" class="lb-btn lb-next" data-act="next" aria-label="Next image">&rarr;</button>
  <div class="lb-count"><span class="lb-i">1</span> / <span class="lb-t">1</span></div>
</div>
<script>
(function(){
  var imgs = [].slice.call(document.querySelectorAll(".zoom img, .zoom video"));
  if (!imgs.length) return;
  var lb = document.getElementById("lb"),
      big = lb.querySelector(".lb-img"),
      vid = lb.querySelector(".lb-vid"),
      stage = lb.querySelector(".lb-stage"),
      cur = lb.querySelector(".lb-i"),
      reduce = window.matchMedia &&
               window.matchMedia("(prefers-reduced-motion: reduce)").matches,
      i = 0, opener = null;
  lb.querySelector(".lb-t").textContent = imgs.length;

  if (reduce) {                             // honour the OS setting
    [].forEach.call(document.querySelectorAll(".gal .mov"), function(v){
      v.autoplay = false;
      v.pause();
    });
  }

  function stopVideo(){
    vid.pause();
    vid.removeAttribute("src");
    vid.innerHTML = "";
    vid.load();
    vid.hidden = true;
  }
  function show(n){
    i = (n + imgs.length) % imgs.length;
    var el = imgs[i];
    cur.textContent = i + 1;
    if (el.tagName === "VIDEO") {
      big.hidden = true;
      big.removeAttribute("src");
      vid.poster = el.getAttribute("poster") || "";
      vid.innerHTML = el.innerHTML;          // carry every <source> across
      vid.load();
      vid.hidden = false;
      if (!reduce) { var p = vid.play(); if (p) p.catch(function(){}); }
      return;
    }
    stopVideo();
    big.hidden = false;
    big.src = el.currentSrc || el.src;
    big.alt = el.alt || "";
    [1, -1].forEach(function(d){            // warm the neighbours
      var nb = imgs[(i + d + imgs.length) % imgs.length];
      if (nb.tagName === "IMG") { var a = new Image(); a.src = nb.src; }
    });
  }
  function open(n, from){
    opener = from;
    show(n);
    lb.hidden = false;
    document.documentElement.style.overflow = "hidden";
    lb.querySelector(".lb-next").focus();
  }
  function close(){
    lb.hidden = true;
    document.documentElement.style.overflow = "";
    big.removeAttribute("src");
    stopVideo();
    if (opener) opener.focus();
  }

  imgs.forEach(function(im, n){
    im.parentNode.addEventListener("click", function(e){
      e.preventDefault();
      open(n, im.parentNode);
    });
  });
  lb.addEventListener("click", function(e){
    var b = e.target.closest ? e.target.closest("[data-act]") : null;
    if (b) {
      var a = b.getAttribute("data-act");
      if (a === "prev") show(i - 1);
      else if (a === "next") show(i + 1);
      else close();
      return;
    }
    if (e.target === lb || e.target === stage) close();   // click the ground
  });
  document.addEventListener("keydown", function(e){
    if (lb.hidden) return;
    if (e.key === "Escape") close();
    else if (e.key === "ArrowRight") show(i + 1);
    else if (e.key === "ArrowLeft") show(i - 1);
    else if (e.key === "Tab") {                            // keep focus inside
      var f = lb.querySelectorAll(".lb-btn"), first = f[0], last = f[f.length - 1];
      if (e.shiftKey && document.activeElement === first) { last.focus(); e.preventDefault(); }
      else if (!e.shiftKey && document.activeElement === last) { first.focus(); e.preventDefault(); }
    }
  });
  var x0 = null;
  lb.addEventListener("touchstart", function(e){ x0 = e.changedTouches[0].clientX; }, {passive:true});
  lb.addEventListener("touchend", function(e){
    if (x0 === null) return;
    var dx = e.changedTouches[0].clientX - x0;
    x0 = null;
    if (Math.abs(dx) > 40) show(dx < 0 ? i + 1 : i - 1);
  }, {passive:true});
})();
</script>
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


def video_sources(name, pfx):
    """<source> tags for a clip: the named file, plus a .webm sibling if present.

    h.264 is first because it is both smaller here and understood everywhere;
    the WebM only gets picked up by a build without the proprietary codec.
    A browser downloads the first source it can play, never both.
    """
    out = ['<source src="%s" type="video/mp4">' % esc(img_src(name, pfx))]
    alt = str(name)[:-4] + ".webm"
    if (CONTENT / "archive-images" / alt).exists():
        out.append('<source src="%s" type="video/webm">' % esc(img_src(alt, pfx)))
    return "".join(out)


def img_src(src, pfx):
    src = str(src or "")
    if src.lower().startswith(("http://", "https://")):
        return src
    return pfx + "images/" + src


# Justified-row packing. TARGET is the sum of aspect ratios a row aims for:
# at a 1180px content width that lands rows around 250px tall. A row closes
# when the next image would overshoot, or at MAXN images. A thin final row is
# folded back into the one before it rather than left as an orphan -- without
# that, five of the ten galleries would end on a single image stretched to the
# full width and three times the height of everything above it.
GAL_TARGET = 4.6
GAL_MAXN = 5


def gallery_rows(ratios, target=GAL_TARGET, maxn=GAL_MAXN):
    rows, cur, total = [], [], 0.0
    for r in ratios:
        if cur and (total + r > target or len(cur) >= maxn):
            rows.append(cur)
            cur, total = [r], r
        else:
            cur.append(r)
            total += r
    if cur:
        rows.append(cur)
    if len(rows) > 1 and sum(rows[-1]) < target * 0.6:
        rows[-2].extend(rows.pop())
    return rows


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
        # the images' own shapes decide how many share a row.
        items = [{"src": i} if isinstance(i, str) else i
                 for i in b.get("items", [])]
        if not items:
            return ""
        ratios = [ratio(i.get("src")) for i in items]

        out, n = [], 0
        for row in gallery_rows(ratios):
            total = sum(row)
            cells = []
            for r in row:
                i = items[n]
                n += 1
                cap = i.get("caption")
                if i.get("video"):
                    # Poster is the first frame, so the cell looks right before
                    # the video has loaded and if it never plays at all.
                    f = ('<button type="button" class="zoom">'
                         '<video class="mov" poster="%s" autoplay loop muted '
                         'playsinline preload="metadata" aria-label="%s">'
                         '%s</video>'
                         '</button>' % (
                             esc(img_src(i.get("src"), pfx)),
                             esc(i.get("alt") or cap or "Animation"),
                             video_sources(i.get("video"), pfx)))
                else:
                    f = ('<button type="button" class="zoom">'
                         '<img src="%s" alt="%s" loading="lazy" decoding="async">'
                         '</button>' % (
                             esc(img_src(i.get("src"), pfx)),
                             esc(i.get("alt") or cap or "")))
                if cap:
                    f += "<figcaption>%s</figcaption>" % esc(cap)
                # The row's 1px gaps come out of the 100% before it is split,
                # so the widths still add up to the full width exactly.
                cells.append(
                    '<figure style="--r:%g;flex-basis:calc((100%% - %dpx) * %.5f)">'
                    '%s</figure>' % (r, len(row) - 1, r / total, f))
            out.append('<div class="gal-row">%s</div>' % "".join(cells))
        return '<div class="gal">%s</div>' % "".join(out)
    if t == "cards":
        cs = []
        for i in b.get("items", []):
            # Title only in the overlay -- the client sits on the case study
            # itself, as its kicker, and a second line here was noise.
            # The badge is an arrow, not the grid's diagonal: these go to
            # another page on this site, not off it.
            # A card can carry motion. Squarespace used animated GIFs for two
            # of these tiles; they come over as h.264 + WebM, same as the
            # gallery loops, with the poster carrying the still frame so the
            # tile is never empty and never regresses to a flat image.
            if i.get("video"):
                media = ('<video class="card-img" poster="%s" autoplay loop muted '
                         'playsinline preload="metadata" width="1200" height="900" '
                         'aria-label="%s">%s</video>' % (
                             esc(img_src(i.get("image"), pfx)),
                             esc(i.get("title")),
                             video_sources(i.get("video"), pfx)))
            else:
                media = ('<img class="card-img" src="%s" alt="%s" '
                         'width="1200" height="900" loading="lazy" '
                         'decoding="async">' % (
                             esc(img_src(i.get("image"), pfx)),
                             esc(i.get("title"))))
            cs.append(
                '<a class="card" href="%s">'
                '%s'
                '<span class="card-a" aria-hidden="true">&#8594;</span>'
                '<span class="card-ov"><span class="card-t">%s</span></span>'
                '</a>' % (
                    esc(pfx + str(i.get("href", "")).lstrip("/")),
                    media, esc(i.get("title"))))
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

    lead = side_lead = ""
    if page.get("lead"):
        lead_img = ('<button type="button" class="zoom">'
                    '<img src="%s" alt="%s" decoding="async">'
                    '</button>' % (
                        esc(img_src(page["lead"], pfx)),
                        esc(page.get("leadAlt") or page.get("title") or "")))
        if page.get("leadSide"):
            # Floated inside the prose rather than full-bleed above it. It has
            # to be the first node in the article for the text to wrap.
            side_lead = '<figure class="lead-side">%s</figure>' % lead_img
        else:
            lead = '<div class="lead">%s</div>' % lead_img

    back = ""
    if page.get("back"):
        back = ('<div class="back"><a href="%s">&larr; %s</a></div>' % (
            esc(pfx + str(page["back"]["href"]).lstrip("/")),
            esc(page["back"]["label"])))

    body = "\n    ".join(block_html(b, pfx) for b in page.get("blocks", []))
    if side_lead:
        body = side_lead + "\n    " + body

    ticker, idbar = chrome(profile, doc, pfx)

    # A page that sets its own kicker (the case studies name their client)
    # keeps it as plain text. A page inheriting the section kicker gets the
    # grid/archive toggle instead.
    if "kicker" in page:
        kicker_html = ('<span class="rule-meta"><span>%s</span></span>'
                       % esc(page["kicker"])) if page["kicker"] else ""
    else:
        kicker_html = '<span class="rule-meta">%s</span>' % rule_toggle(
            doc.get("kicker", "Recent Work"), doc.get("kickerHref", "/"),
            doc.get("archiveLabel", "More"), doc.get("archiveHref", "/archive/"),
            "archive")

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
    <div class="rule-in"><span>%(label)s</span>%(kickerhtml)s</div>
  </div>
  %(nav)s
  %(lead)s
  <article class="prose%(proseclass)s">
    %(body)s
  </article>
</div>
<footer>
  <div class="foot-in">
    %(foot)s
    <span class="push">%(copy)s</span>
  </div>
</footer>
%(lightbox)s
</body>
</html>
""" % {
        "full_title": full_title,
        "meta": meta,
        "ogurl": ('<meta property="og:url" content="%s">' % esc(url)) if url else "",
        "ogimg": ('<meta property="og:image" content="%s">' % esc(og_img)) if og_img else "",
        "card": "summary_large_image" if og_img else "summary",
        "proseclass": " read" if page.get("reading") else "",
        "fonts": FONTS,
        "css": stylesheet(profile.get("layout", {})) + PROSE_CSS,
        "ticker": ticker,
        "idbar": idbar,
        "back": back,
        "label": esc(page.get("title") or ""),
        # An explicit "kicker": "" in pages.json suppresses the block entirely;
        # a missing key still falls back to the section kicker.
        "kickerhtml": kicker_html,
        "nav": nav,
        "lead": lead,
        "body": body,
        "foot": foot_links,
        "copy": esc(profile.get("footer", "")),
        # Only pages that actually carry images pay for the viewer.
        "lightbox": (LIGHTBOX if ("zoom" in lead or 'class="zoom"' in body)
                     else "") + (CARD_MOTION if '<video class="card-img"' in body
                                 else ""),
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
                    if isinstance(i, str):
                        check(i, where)
                    else:
                        check(i.get("src"), where)
                        check(i.get("video"), where)
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
