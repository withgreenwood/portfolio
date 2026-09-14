#!/usr/bin/env python3
"""Build site/monza/ from content/monza.json + content/monza-images/.

A single-event sub-page in the same grid language as the homepage. The tiles
are not our own photography -- they are what other accounts posted about the
activation, newest first, each linking back to its source post. Nothing on the
homepage links here; it is reached by its URL.

The chrome (ticker, identity bar, rules, footer, grid) is imported wholesale
from build.py so the two pages can never drift apart stylistically.

Usage:  python3 monza.py        (or just python3 build.py, which chains it)
"""
import json
import math
import shutil
from datetime import datetime, timezone
from pathlib import Path

from build import CONTENT, FONTS, SITE, TICKER_MIN_PX, TICKER_SPAN_PAD, \
    TICKER_SPEED, die, esc, load, stylesheet

OUT = SITE / "monza"

# One extra rule for this page only: the standfirst. Everything else is
# inherited, so this stays a few lines rather than a second stylesheet.
EXTRA_CSS = """
.lede{padding:clamp(18px,2.4vw,26px) var(--pad) 0;max-width:62ch}
.lede p{margin:0;font:400 12px/1.75 var(--mono);letter-spacing:.045em;
  text-transform:none}
.backlink{font:500 11px/1 var(--mono);letter-spacing:.12em;text-decoration:none;
  border-bottom:1px solid transparent;padding-bottom:2px;
  transition:color .15s,border-color .15s}
.backlink:hover{color:var(--accent);border-bottom-color:var(--accent)}
.wordmark a{text-decoration:none}
"""


def ticker_html(phrases, speed):
    """Same geometry as build.py: repeat the run until one half clears the
    widest display, then scale the duration so the on-screen speed is fixed."""
    phrases = [p for p in phrases if str(p).strip()]
    if not phrases:
        return "", 34
    one = "".join(f'<span>{esc(p)}</span><span class="dot">&bull;</span>'
                  for p in phrases)
    per_char = 11 * (0.6 + 0.14)
    half_px = sum(len(str(p)) * per_char + 2 * TICKER_SPAN_PAD + per_char
                  for p in phrases)
    reps = max(2, math.ceil(TICKER_MIN_PX / half_px))
    half_px *= reps
    dur = round(half_px / float(speed), 1)
    half = one * reps
    return f'<div class="ticker"><div class="ticker-run">{half}{half}</div></div>', dur


def date_span(items):
    ts = [i.get("takenAt") for i in items if i.get("takenAt")]
    if not ts:
        return ""
    lo = datetime.fromtimestamp(min(ts), timezone.utc)
    hi = datetime.fromtimestamp(max(ts), timezone.utc)
    if lo.year == hi.year and lo.month == hi.month:
        return "%d&ndash;%d %s %d" % (lo.day, hi.day, hi.strftime("%b"), hi.year)
    if lo.year == hi.year:
        return "%d %s &ndash; %d %s %d" % (lo.day, lo.strftime("%b"),
                                           hi.day, hi.strftime("%b"), hi.year)
    return "%s &ndash; %s" % (lo.strftime("%b %Y"), hi.strftime("%b %Y"))


def build_monza(quiet=False):
    src = CONTENT / "monza.json"
    if not src.exists():
        return  # no-op, exactly like archive.py without pages.json

    doc = load("monza.json")
    if not isinstance(doc, dict) or "items" not in doc:
        die("monza.json must be an object with an 'items' array")
    items = doc["items"]
    if not items:
        die("monza.json has no items")

    profile = load("profile.json")
    imgdir = CONTENT / "monza-images"

    missing = [i.get("image") for i in items
               if not i.get("image") or not (imgdir / i["image"]).exists()]
    if missing:
        die("monza images not found in content/monza-images: %s"
            % ", ".join(map(str, missing[:6])))

    # Newest first. The JSON is written in order, but sorting here means a
    # hand-added tile does not have to be inserted in the right place.
    items = sorted(items, key=lambda i: i.get("takenAt") or 0, reverse=True)

    OUT.mkdir(parents=True, exist_ok=True)
    dest = OUT / "images"
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    used = {i["image"] for i in items}
    for f in sorted(imgdir.iterdir()):
        if f.name in used:
            shutil.copy2(f, dest / f.name)

    lay = profile.get("layout", {})
    ticker, tick_dur = ticker_html(doc.get("ticker", profile.get("ticker", [])),
                                   lay.get("tickerSpeed", TICKER_SPEED))

    tiles = []
    for it in items:
        t, s = esc(it.get("title")), esc(it.get("source"))
        typ = "tt" if it.get("type") == "tt" else "ig"
        plat = "TikTok" if typ == "tt" else "Instagram"
        alt = esc("%s post by %s" % (plat, it.get("title") or "an attendee"))
        ov = ""
        if t or s:
            ov = ('<span class="pgf-ov">'
                  + (f'<span class="pgf-t">{t}</span>' if t else "")
                  + (f'<span class="pgf-s">{s}</span>' if s else "")
                  + "</span>")
        tiles.append(
            f'<a class="pgf-i" data-t="{typ}" href="{esc(it.get("url"))}" '
            f'target="_blank" rel="noopener noreferrer">'
            f'<img src="images/{esc(it["image"])}" alt="{alt}" '
            f'width="720" height="900" loading="lazy" decoding="async">'
            f'<span class="pgf-a" aria-hidden="true">&#8599;</span>{ov}</a>')
    grid = '<main class="pgf-grid">\n    ' + "\n    ".join(tiles) + "\n  </main>"

    name = esc(profile.get("name", "Portfolio"))
    title = esc(doc.get("title", "Monza"))
    subtitle = esc(doc.get("subtitle", ""))
    standfirst = esc(doc.get("standfirst", ""))
    count_label = "%d Posts" % len(items)
    span = date_span(items)
    meta = doc.get("metaDescription") or profile.get("metaDescription", "")
    site_url = str(profile.get("siteUrl", "")).rstrip("/")
    og = esc(site_url + "/monza/images/" + str(items[0]["image"])) if site_url else ""

    prof_links = [l for l in profile.get("links", []) if l.get("url")]
    links = "".join(
        f'<li><a href="{esc(l.get("url"))}">{esc(l.get("label"))}</a></li>'
        for l in prof_links)
    links_html = f'<ul class="links">{links}</ul>' if links else ""
    foot_links = "".join(
        f'<a href="{esc(l.get("url"))}">{esc(l.get("label"))}</a>'
        for l in prof_links)

    css = stylesheet(lay, tick_dur) + EXTRA_CSS

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} &mdash; {name}</title>
<meta name="description" content="{esc(meta)}">
<meta property="og:title" content="{title} &mdash; {name}">
<meta property="og:description" content="{esc(meta)}">
<meta property="og:type" content="article">
{f'<meta property="og:url" content="{esc(site_url)}/monza/">' if site_url else ''}
<meta name="twitter:card" content="summary_large_image">
{f'<meta property="og:image" content="{og}">' if og else ''}
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'><text y='13' font-size='14'>&#9724;</text></svg>">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<style>{css}</style>
</head>
<body>
{ticker}
<header class="idbar">
  <div class="idcell idcell-name"><span class="wordmark"><a href="/">{name}</a></span></div>
  <div class="idcell idcell-links">{links_html}</div>
</header>
<div class="wrap">
  <div class="rule">
    <div class="rule-in"><span>{title}{f' &mdash; {subtitle}' if subtitle else ''}</span><span>{count_label} &middot; {span}</span></div>
  </div>
  {f'<div class="lede"><p>{standfirst}</p></div>' if standfirst else ''}
  {grid}
</div>
<footer>
  <div class="foot-in">
    <a class="backlink" href="/">&larr; All Work</a>
    {foot_links}
    <span class="push">{esc(profile.get("footer", ""))}</span>
  </div>
</footer>
</body>
</html>
"""
    (OUT / "index.html").write_text(page)
    if not quiet:
        kb = len(page.encode()) / 1024
        print("built site/monza/  (%d tiles, %.1f KB, %d images)"
              % (len(items), kb, len(used)))


if __name__ == "__main__":
    build_monza()
