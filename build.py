#!/usr/bin/env python3
"""Build site/index.html from content/profile.json + content/items.json.

Layout: the "full flip" treatment — flat white ground, black hairline rules,
one accent colour, a tight uppercase grotesk for the wordmark and a wide
uppercase monospace for everything else. The only JavaScript on the page is the
lightbox: tiles keep their href, so without it every tile still opens the post
on instagram.com.

Usage:  python3 build.py
"""
import html
import json
import re
import math
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).parent
CONTENT = ROOT / "content"
SITE = ROOT / "site"

# Ticker geometry. MIN_PX is how wide one half of the run must be before it
# can loop without a gap — 5200 clears a 5K display at 100% scaling.
TICKER_MIN_PX = 5200
TICKER_SPAN_PAD = 20
TICKER_SPEED = 13.3   # px/sec, matching the original 34s at two copies

FONTS = ("https://fonts.googleapis.com/css2"
         "?family=IBM+Plex+Mono:wght@400;500;600"
         "&family=Inter+Tight:wght@500;600;700&display=swap")


# Post ids, for the lightbox. Instagram: /p/<code>/, /reel/<code>/, /tv/<code>/.
# TikTok: /video/<numeric id>/.
IG_RE = re.compile(r"/(p|reel|tv)/([A-Za-z0-9_-]+)")
TT_RE = re.compile(r"/video/(\d+)")


def embed_src(url, typ):
    """The lightbox iframe src for a tile, or "" if the url carries no post id.

    Both endpoints are public -- no API key, no embed.js. Shared with monza.py
    so the two grids build the same attributes.
    """
    u = str(url or "")
    if typ == "tt":
        m = TT_RE.search(u)
        return "https://www.tiktok.com/embed/v2/%s" % m.group(1) if m else ""
    if typ == "ig":
        m = IG_RE.search(u)
        if m:
            return "https://www.instagram.com/%s/%s/embed/captioned/" % (m.group(1), m.group(2))
    return ""



# Kept out of CSS on purpose: archive.py and monza.py share stylesheet(),
# and those pages have no lightbox.
LIGHTBOX_CSS = """
/* ---- lightbox ---- */
.lbx{position:fixed;inset:0;z-index:60;background:rgba(0,0,0,.93);
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  gap:12px;padding:16px}
.lbx[hidden]{display:none}
.lbx-frame{border:0;display:block;background:#fff;width:400px;height:70vh;max-width:100%}
.lbx-meta{margin:0;color:#fff;text-align:center;max-width:min(92vw,720px);
  font:500 10.5px/1.6 var(--mono);letter-spacing:.12em}
.lbx-meta a{text-decoration:none;border-bottom:1px solid rgba(255,255,255,.35);
  padding-bottom:1px}
.lbx-meta a:hover{color:var(--accent);border-bottom-color:var(--accent)}
.lbx-meta em{font-style:normal;color:var(--accent)}
.lbx-meta .n{display:block;margin-top:4px;opacity:.45;letter-spacing:.18em}
.lbx-btn{position:absolute;appearance:none;background:transparent;border:0;color:#fff;
  cursor:pointer;font:400 38px/1 var(--disp);padding:10px 16px;opacity:.6;
  transition:opacity .15s,color .15s}
.lbx-btn:hover{opacity:1;color:var(--accent)}
.lbx-btn:focus-visible{opacity:1;outline:2px solid var(--accent);outline-offset:2px}
.lbx-prev{left:2px;top:50%;transform:translateY(-50%)}
.lbx-next{right:2px;top:50%;transform:translateY(-50%)}
.lbx-close{top:4px;right:6px;font-size:28px}
.lbx-pre{display:none}
@media(prefers-reduced-motion:reduce){.lbx-btn{transition:none}}
"""

LIGHTBOX = """
<div class="lbx" id="lbx" hidden role="dialog" aria-modal="true" aria-label="Embedded post">
  <button class="lbx-btn lbx-close" id="lbx-close" type="button" aria-label="Close">&times;</button>
  <button class="lbx-btn lbx-prev" id="lbx-prev" type="button" aria-label="Previous post">&lsaquo;</button>
  <button class="lbx-btn lbx-next" id="lbx-next" type="button" aria-label="Next post">&rsaquo;</button>
  <iframe class="lbx-frame" id="lbx-frame" title="Embedded post"
    allow="autoplay; clipboard-write; encrypted-media; picture-in-picture"></iframe>
  <p class="lbx-meta" id="lbx-meta"></p>
  <iframe class="lbx-pre" id="lbx-pre" tabindex="-1" aria-hidden="true" title=""></iframe>
</div>
<script>
/* Tiles keep their href, so cmd-click, middle-click and no-JS all still open
   the post on instagram.com. A plain left click opens it here instead.

   Geometry, measured on instagram.com and stable at every width tested
   (320/360/400/440/560/640): a 54px header, a media box of exactly
   width x 1.25, then a 45px action row. The caption block below that varies
   with caption length (~1100px total at 400px wide), so the frame is sized to
   the viewport and the caption scrolls inside it. */
(function () {
  var all = [].slice.call(document.querySelectorAll(".pgf-i[data-embed]"));
  if (!all.length) return;
  /* Rebuilt on each open, so prev/next stays inside the active filter. */
  var tiles = all;

  var lbx = document.getElementById("lbx"),
      frame = document.getElementById("lbx-frame"),
      pre = document.getElementById("lbx-pre"),
      meta = document.getElementById("lbx-meta"),
      closeBtn = document.getElementById("lbx-close"),
      idx = 0, opener = null;

  function src(i) { return tiles[i].getAttribute("data-embed"); }
  function isTT(i) { return tiles[i].getAttribute("data-t") === "tt"; }
  function avail() { return Math.max(320, window.innerHeight - 96); }
  function size() {
    var a = avail(), w, hgt;
    if (isTT(idx)) {
      /* TikTok's embed is height-driven, not width-driven: its own box is
         325x738 and the player does not grow with the iframe's width, so a
         wider frame only adds empty margin. */
      w = Math.max(280, Math.min(340, window.innerWidth - 48));
      hgt = Math.min(a, 738);
    } else {
      w = Math.max(280, Math.min(400, window.innerWidth - 48, Math.round((a - 260) / 1.25)));
      hgt = Math.min(a, Math.round(208 + w * 1.25 + 400));
    }
    frame.style.width = w + "px";
    frame.style.height = hgt + "px";
  }
  function show(i) {
    idx = (i + tiles.length) % tiles.length;
    var t = tiles[idx];
    size();
    frame.src = src(idx);
    meta.textContent = "";
    var a = document.createElement("a");
    a.href = t.href; a.target = "_blank"; a.rel = "noopener noreferrer";
    a.textContent = t.getAttribute("data-title") || "View on Instagram";
    meta.appendChild(a);
    var s = t.getAttribute("data-source");
    if (s) {
      meta.appendChild(document.createTextNode(" \u2014 "));
      var em = document.createElement("em");
      em.textContent = s;
      meta.appendChild(em);
    }
    var n = document.createElement("span");
    n.className = "n";
    n.textContent = (idx + 1) + " / " + tiles.length;
    meta.appendChild(n);
    pre.src = src((idx + 1) % tiles.length);
  }
  function open(i, tile) {
    opener = tile;
    lbx.hidden = false;
    document.documentElement.style.overflow = "hidden";
    show(i);
    closeBtn.focus();
  }
  function close() {
    lbx.hidden = true;
    frame.removeAttribute("src");
    pre.removeAttribute("src");
    document.documentElement.style.overflow = "";
    if (opener) { opener.focus(); opener = null; }
  }

  all.forEach(function (t) {
    t.addEventListener("click", function (e) {
      if (e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      e.preventDefault();
      tiles = all.filter(function (x) { return !x.hidden; });
      open(tiles.indexOf(t), t);
    });
  });
  closeBtn.addEventListener("click", close);
  document.getElementById("lbx-prev").addEventListener("click", function () { show(idx - 1); });
  document.getElementById("lbx-next").addEventListener("click", function () { show(idx + 1); });
  lbx.addEventListener("click", function (e) { if (e.target === lbx) close(); });
  document.addEventListener("keydown", function (e) {
    if (lbx.hidden) return;
    if (e.key === "Escape") close();
    else if (e.key === "ArrowLeft") show(idx - 1);
    else if (e.key === "ArrowRight") show(idx + 1);
  });
  window.addEventListener("resize", function () { if (!lbx.hidden) size(); });
  /* If Instagram announces its own height, honour it rather than the estimate. */
  window.addEventListener("message", function (e) {
    if (lbx.hidden || isTT(idx) || e.origin !== "https://www.instagram.com") return;
    var d = e.data;
    try { d = typeof d === "string" ? JSON.parse(d) : d; } catch (err) { return; }
    var hgt = d && d.details && d.details.height;
    if (hgt) frame.style.height = Math.min(avail(), hgt) + "px";
  });
})();
</script>
"""


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
  animation:ticker __TICKDUR__s linear infinite}
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
.idcell+.idcell-links{border-left:0}
.wordmark{font:600 clamp(17px,2.1vw,25px)/1 var(--disp);
  letter-spacing:-.045em;white-space:nowrap}
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

/* The right-hand slot: the grid's filters (All Work, then one per brand)
   followed by MORE, which pages across to the archive. The active entry is
   full ink with no pointer; the rest are dimmed links. */
.rule-tog{display:flex;flex-wrap:wrap;align-items:baseline;gap:4px 10px}
.rule-tog span,.rule-tog a{display:inline-block}
.rule-tog .sep{opacity:.38;letter-spacing:0}
.rule-tog a{color:inherit;text-decoration:none;opacity:.42;
  border-bottom:1px solid transparent;transition:opacity .15s,color .15s}
.rule-tog a:hover{opacity:1;color:var(--accent);border-bottom-color:var(--accent)}
.rule-tog [aria-current]{opacity:1;cursor:default}
.rule-tog a[aria-current]:hover{color:inherit;border-bottom-color:transparent}

/* ---- grid ---- */
/* The hairlines are a 1px shadow on each tile, not a black container showing
   through the gap -- a part-filled last row would leave a black slab. */
.pgf-grid{display:grid;grid-template-columns:repeat(__COLSM__,1fr);
  gap:var(--gap);background:var(--bg);
  margin:18px var(--pad) 0;padding:1px}
.pgf-i[hidden]{display:none}
.pgf-i{position:relative;display:block;aspect-ratio:4/5;max-width:100%;
  overflow:hidden;border-radius:var(--radius);background:var(--panel);
  box-shadow:0 0 0 1px var(--line);text-decoration:none;color:inherit}
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
  .idcell+.idcell-links{border-left:1px solid var(--line);margin-left:auto}
  .pgf-grid{grid-template-columns:repeat(__COLSMID__,1fr)}
  .push{margin-left:auto}
}
@media(min-width:940px){
  .pgf-grid{grid-template-columns:repeat(__COLS__,1fr)}
}
"""


def stylesheet(lay, tick_dur=34):
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
        "__TICKDUR__": "%g" % tick_dur,
    }
    css = CSS
    for k, v in subs.items():
        css = css.replace(k, v)
    return css



DEFAULT_FILTERS = [{"key": "all", "label": "All Work"}]


def rule_toggle(filters, arch_label, arch_url, here):
    """ALL WORK | APPLE MUSIC | APPLE TV | JOOPITER | MORE, right of the rule.

    `filters` comes from profile.json. On the grid (`here` == "work") each
    filter is an in-page link (#key) that FILTER_JS picks up; "All Work"
    starts current. On the archive (`here` == "archive") the same filters
    link back to the grid pre-filtered (/#key) and MORE is current. Used by
    both build.py and archive.py so the control reads identically on both.
    """
    filters = filters or DEFAULT_FILTERS
    parts = []
    for f in filters:
        key, label = str(f.get("key", "all")), esc(f.get("label"))
        if here == "work":
            href = "#" if key == "all" else "#" + key
            cur = ' aria-current="true"' if key == "all" else ""
            parts.append('<a href="%s" data-f="%s"%s>%s</a>'
                         % (esc(href), esc(key), cur, label))
        else:
            href = "/" if key == "all" else "/#" + key
            parts.append('<a href="%s">%s</a>' % (esc(href), label))
    if here == "archive":
        parts.append('<span aria-current="page">%s</span>' % esc(arch_label))
    else:
        parts.append('<a href="%s">%s</a>' % (esc(arch_url), esc(arch_label)))
    sep = '<span class="sep" aria-hidden="true">|</span>'
    return '<nav class="rule-tog" aria-label="Filter work">%s</nav>' % sep.join(parts)


# Filters the grid by each tile's data-b (brand). The choice lives in the URL
# hash so a filtered view can be linked to, and so the archive's filter links
# (/#apple-tv) land already filtered.
FILTER_JS = """
<script>
(function () {
  var links = [].slice.call(document.querySelectorAll(".rule-tog a[data-f]"));
  var tiles = [].slice.call(document.querySelectorAll(".pgf-grid .pgf-i"));
  if (!links.length) return;
  var keys = links.map(function (a) { return a.getAttribute("data-f"); });
  function apply(key) {
    if (keys.indexOf(key) < 0) key = "all";
    links.forEach(function (a) {
      if (a.getAttribute("data-f") === key) a.setAttribute("aria-current", "true");
      else a.removeAttribute("aria-current");
    });
    tiles.forEach(function (t) {
      t.hidden = key !== "all" && t.getAttribute("data-b") !== key;
    });
  }
  function fromHash() { apply(decodeURIComponent(location.hash.slice(1)) || "all"); }
  links.forEach(function (a) {
    a.addEventListener("click", function (e) {
      e.preventDefault();
      var key = a.getAttribute("data-f");
      history.replaceState(null, "", key === "all"
        ? location.pathname + location.search : "#" + key);
      apply(key);
    });
  });
  window.addEventListener("hashchange", fromHash);
  fromHash();
})();
</script>
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
        es = embed_src(it.get("url"), typ)
        data = (f' data-embed="{esc(es)}" data-title="{t}" data-source="{s}"'
                if es else "")
        br = esc(it.get("brand"))
        data += f' data-b="{br}"' if br else ""
        tiles.append(
            f'<a class="pgf-i" data-t="{typ}"{data} href="{esc(it.get("url"))}" '
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
    # The run is two identical halves and the keyframe shifts it by -50%, so the
    # loop is only seamless while one half is at least as wide as the viewport.
    # Two copies of a short phrase list is ~900px, which runs dry on a wide
    # display. The face is monospace, so a half's width is predictable: measure
    # it, repeat until it clears TICKER_MIN_PX, and scale the duration by the
    # same factor so the speed on screen never changes.
    phrases = [p for p in profile.get("ticker", []) if str(p).strip()]
    ticker = ""
    tick_dur = 34
    if phrases:
        one = "".join(f'<span>{esc(p)}</span><span class="dot">&bull;</span>'
                      for p in phrases)
        # 11px IBM Plex Mono advances 0.6em, plus .14em letter-spacing, plus the
        # 20px padding on each side of a phrase span; the bullet spans have none.
        per_char = 11 * (0.6 + 0.14)
        half_px = sum(len(str(p)) * per_char + 2 * TICKER_SPAN_PAD + per_char
                      for p in phrases)
        reps = max(2, math.ceil(TICKER_MIN_PX / half_px))
        half_px *= reps
        tick_dur = round(half_px / float(lay.get("tickerSpeed", TICKER_SPEED)), 1)
        half = one * reps
        ticker = f'<div class="ticker"><div class="ticker-run">{half}{half}</div></div>'

    # The identity bar stays the three profile links. The archive (the old
    # Squarespace pages) is a footer link only -- it is the deeper cut, not a
    # peer of Instagram and LinkedIn, and the bar is meant to stay spare.
    prof_links = [l for l in profile.get("links", []) if l.get("url")]
    arch = profile.get("archive")
    foot_only = prof_links + ([arch] if arch and arch.get("url") else [])

    links = "".join(
        f'<li><a href="{esc(l.get("url"))}">{esc(l.get("label"))}</a></li>'
        for l in prof_links)
    links_html = f'<ul class="links">{links}</ul>' if links else ""

    foot_links = "".join(
        f'<a href="{esc(l.get("url"))}">{esc(l.get("label"))}</a>'
        for l in foot_only)

    has_lbx = any(" data-embed=" in t for t in tiles)

    name = esc(profile.get("name", "Portfolio"))
    tagline = profile.get("tagline")
    rule_tog = rule_toggle(
        profile.get("filters"),
        (arch or {}).get("label", "More"), (arch or {}).get("url", "/archive/"),
        "work")
    untagged = [i.get("title") or i.get("url") for i in items if not i.get("brand")]
    if untagged:
        print("note: %d item(s) have no brand, so show under All Work only: %s"
              % (len(untagged), "; ".join(map(str, untagged))))
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
<style>{stylesheet(lay, tick_dur)}{LIGHTBOX_CSS if has_lbx else ''}</style>
</head>
<body>
{ticker}
<header class="idbar">
  <div class="idcell idcell-name"><span class="wordmark">{name}</span></div>
  <div class="idcell idcell-links">{links_html}</div>
</header>
<div class="wrap">
  <div class="rule">
    <div class="rule-in"><span>{esc(tagline)}</span>{rule_tog}</div>
  </div>
  {grid}
</div>
<footer>
  <div class="foot-in">
    {foot_links}
    <span class="push">{esc(profile.get("footer", ""))}</span>
  </div>
</footer>
{FILTER_JS if tiles else ''}
{LIGHTBOX if has_lbx else ''}
</body>
</html>
"""
    (SITE / "index.html").write_text(page)
    kb = len(page.encode()) / 1024
    print("built site/index.html  (%d items, %.1f KB, %d images)"
          % (len(items), kb, len(used)))


if __name__ == "__main__":
    build()
    # The archive pages (the old Squarespace content) are built from the same
    # profile.json so the chrome stays in sync. Absent pages.json, it no-ops.
    from archive import build_archive
    build_archive(quiet=True)
    # Single-event sub-pages, same deal: absent their content JSON they no-op.
    from monza import build_monza
    build_monza(quiet=True)
