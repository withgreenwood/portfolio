# Portfolio Grid

withgreenwood.com: a 4:5 grid of selected work, plus the old Squarespace pages
rebuilt as `/archive` and a single-event page at `/monza`. Plain static HTML,
built by Python and served by Cloudflare.

```
admin.html          local editor for the grid: add, crop, reorder, export
build.py            content/ -> site/   (runs archive.py and monza.py too)
archive.py          content/pages.json -> site/archive/ and site/_redirects
monza.py            content/monza.json -> site/monza/
rebuild_monza.py    turns downloaded browser packs into content/monza*
mkpages.py          one-shot generator for pages.json (don't re-run)
publish.sh          collect admin exports from ~/Downloads, then build
content/
  profile.json      name, bio, links, ticker, layout, siteUrl
  items.json        the grid items
  images/           grid images
  pages.json        archive copy, plus the old-URL redirects
  archive-images/   archive photos and video loops
  monza.json        Monza tiles
  monza-images/     Monza images
  fonts/            self-hosted web fonts (IBM Plex Mono, Inter Tight; SIL OFL)
site/               the built site: this is what Cloudflare serves
wrangler.jsonc      Cloudflare config (static assets only, no server code)
```

`site/` is committed, so Cloudflare only serves files and never runs a build.

---

## Everyday workflow

1. Open `admin.html` (double-click it). Add or edit items, drag to reorder.
2. Click **Download thumbnails**, then **Export items.json**. Both land in
   `~/Downloads`.
3. Run `./publish.sh`. It moves those files into `content/`, rebuilds the site,
   and lists any images no longer used.
4. Preview, then push. Every push to `main` deploys.

```bash
python3 -m http.server 8747 --directory site
```

```bash
git add -A && git commit -m "Update grid" && git push
```

If macOS blocks access to `~/Downloads`, drag the files in yourself
(`items.json` → `content/`, `NN-name.jpg` → `content/images/`) and run
`./publish.sh` anyway. It rebuilds regardless.

Edit `content/profile.json` directly for name, bio, links, columns and gap, and
`content/pages.json` for archive copy. Then run `python3 build.py`.

---

## What the build produces

Running `python3 build.py` writes everything under `site/`:

- **Pages**: the grid, every archive page, and `/monza`. Each page gets a
  canonical URL from `siteUrl` in `profile.json` (or `baseUrl` in `pages.json`).
- **Grid images**: needs Pillow (`pip3 install -r requirements.txt`). Each grid
  and Monza image goes out as a JPEG capped at 800px wide, plus WebP copies at
  that size and at 400 and 600px. Tiles are a `<picture>` with a `srcset`, so a
  phone loads the 400px WebP rather than the 800px JPEG. Images that haven't
  changed are skipped, so a rebuild is quick. Without Pillow, images are copied
  at full size and served as a plain `<img>`.
- **`404.html`**: shown for any unknown URL (`not_found_handling` in
  `wrangler.jsonc`).
- **`_redirects`**: old Squarespace URLs → their `/archive` pages, from
  `pages.json`.
- **`_headers`**: browser caching (a week for images, a year for fonts) and
  basic security headers.
- **`robots.txt` and `sitemap.xml`**: the sitemap lists every built page.

The grid's filter links and the lightbox are the only JavaScript. Every tile
keeps its real `href`, so without scripts a tile simply opens the post.

---

## Cloudflare settings that live in the dashboard

Some things can't be set from files in this repo:

- **SSL/TLS → Edge Certificates → Always Use HTTPS**: on, so `http://`
  redirects to `https://`.
- **Rules → Redirect Rules**: `www.withgreenwood.com/*` →
  `https://withgreenwood.com/${1}` (301), so www doesn't serve a duplicate copy
  of the site.

`_headers` sends `Strict-Transport-Security` without `includeSubDomains` or
`preload`, so it only affects this exact hostname.

---

## Updating the fonts

The fonts are the latin subset of Google Fonts' woff2 files, renamed with their
version (for example `ibm-plex-mono-500-v20.woff2`). That's why `_headers` can
cache them as immutable. To change a font, add a file with a new name and update
`FONT_FILES` in `build.py`. Never overwrite a file in place.

---

## About the Instagram API

There's no auto-sync, deliberately. Pulling posts needs the Graph API with a
Business or Creator account, a linked Facebook Page, and a token refreshed every
60 days. Instagram's CDN URLs are signed and expire, so they can't be hotlinked
either. For a hand-picked portfolio, uploading your own image also gives better
quality than Instagram's compressed copy.

## Notes

- **Back up before switching machines.** In `admin.html`, *Export project*
  writes a `.json` holding your full-resolution originals, and *Import project*
  restores it. Browser storage alone is not a backup.
- `admin.html` keeps separate storage for `file://` and `localhost`, so items
  added in one won't appear in the other.
- This repo is public. `.gitignore` keeps DNS exports and credentials out of
  it.
