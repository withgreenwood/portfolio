# Portfolio Grid

A curated Instagram-style grid for Squarespace: selected Instagram posts and article
links in one 4:5 feed with All / Instagram / Writing filter tabs.

Two pieces:

| File | Runs | Purpose |
|---|---|---|
| `admin.html` | On your machine | Add, edit, reorder, crop, preview. Generates the embed. |
| *(the embed)* | On Squarespace | Pure HTML + CSS. Pasted into a Code block. |

Open `admin.html` by double-clicking it. It needs no server, no install, no account.
Your work autosaves in that browser.

---

## Two constraints that shaped this

**1. Squarespace only allows JavaScript in Code blocks on Core plans and above.**
So the generated embed contains **zero JavaScript**. The filter tabs are hidden radio
inputs driven by CSS sibling selectors. This runs on *every* Squarespace plan,
including Basic, and can't break from a script error on someone's phone.

**2. A Squarespace Code block is capped at 400 KB.**
That cap decides where your images live — see below.

---

## Where images live

The admin has a **Hosted / Embedded** switch. This is the one real decision.

### Hosted (recommended)

Images are uploaded to Squarespace and served from its CDN. The embed carries only
URLs, so it stays around **10 KB regardless of item count** — unlimited posts, and
full Instagram-grade quality with a retina `srcset` at 300/500/750/1000w.

1. **Download thumbnails** in the admin — each saves as a 1080×1350 JPEG, pre-cropped.
2. Upload them to Squarespace. Either drop them in any gallery, or use
   **Link → Files** in any link editor, which accepts an upload and returns a URL.
3. Copy each image's URL, then **Paste URLs in bulk** — one per line, in grid order.

To get a URL from an uploaded image: view the live page, right-click the image,
*Copy Image Address*.

**Strip any `?format=` already on the URL you copy** — paste the bare path. The tool
adds its own sizing. This matters: a bare Squarespace CDN URL serves the *full-size
original*. Tested against a live CDN image, `?format=500w` returns 500px at 11 KB
while the bare URL returns 2500px at 200 KB, so the grid pins every tile to an explicit
width and offers 300/500/750/1000/1500w via `srcset`. Those are real supported sizes;
anything else snaps up to the next one.

### Embedded

Images are baked into the code block as data URIs. Nothing to upload — paste and done.
But the 400 KB cap binds hard. Measured against real photographs:

| Quality | Size | Items that fit |
|---|---|---|
| Small | 320×400 | ~16 |
| Medium | 400×500 | ~10 |
| Large | 480×600 | ~6 |
| Instagram retina | 640×800 | ~4 |

Detailed, high-contrast photos cost 2–3× more than soft ones, so these are averages.
**The meter under the embed code is the truth** — it measures your actual bytes and
tells you how many more will fit.

Embedded mode is good for a small, fixed grid or for trying the design out. Anything
larger, or anything where you want Instagram-matching sharpness, wants Hosted.

---

## Installing on Squarespace

1. Edit the page, add a **Code** block.
2. Paste the embed. Leave **Display Source** unchecked.
3. Save.

The grid inherits your site's font and text colour by default, so it should sit
naturally in your existing design. *Text colour* in Appearance overrides that if the
section background needs it.

---

## About the Instagram API

There's no auto-sync, deliberately. Instagram's Basic Display API was shut down in
December 2024. Pulling posts now requires the Graph API with a Business or Creator
account, a linked Facebook Page, and a token refreshed every 60 days — and it would
need server-side code Squarespace can't host.

Instagram's own CDN URLs are signed and expire, so they can't be hotlinked either.
For a curated portfolio you're hand-picking anyway, uploading your own image gives
better quality than Instagram's compressed copy.

---

## Hosting the images somewhere other than Squarespace

Squarespace is a perfectly good image host, but its URLs are opaque hashes you must
copy one at a time off the live page. A plain static host gives *predictable* URLs,
which is faster to set up and much faster to maintain.

**Recommended: Cloudflare Pages or Netlify.** Both are free, both accept a
drag-and-dropped folder, and both serve from a global CDN.

1. **Download thumbnails** — you get `01-morning-light.jpg`, `02-studio-detail.jpg`, …
2. Drag that folder onto Cloudflare Pages or Netlify Drop. You get a URL like
   `https://your-grid.pages.dev`.
3. Paste that one URL into **Folder base URL** and hit **Apply**.

Every item is filled at once from its filename — no per-image copying. Adding a post
later means uploading one more file and clicking Apply again.

Caveat: filenames are derived from the item's title and position. If you rename or
reorder items after uploading, re-export and re-upload so the names still match.

**If you want on-the-fly resizing** the way Squarespace does it, use Cloudinary's free
tier — its URLs take transform segments (`w_500,c_fill,ar_4:5`). That only matters for
very large grids; a 1080×1350 JPEG served lazily is fine for a portfolio.

Non-Squarespace URLs get no `srcset` (those hosts don't resize by URL), so the exported
1080×1350 file is what loads. That's sharper than Instagram serves and still lazy-loaded.

## Moving the whole site off Squarespace

Different question, and usually not worth it for a grid. The same static hosts will
serve a complete site free, and you could point a subdomain like
`work.yourdomain.com` at it via a DNS record while Squarespace keeps the main site.

But you'd be maintaining two sites with two designs, and your Squarespace styling,
navigation, and fonts wouldn't carry across — the grid is built to inherit them. Only
worth considering if you already have other reasons to leave.

## Going native instead

If you'd trade the filter tabs for zero code, Squarespace's own **Gallery section**
covers most of this: up to 250 images, grid layout with column and spacing controls,
and per-image clickthrough URLs to external links — supported on *any* plan. Set
**Lightbox off**, or the links won't fire.

What you lose: the All / Instagram / Writing tabs (there's no native filtering), the
hover caption with a separate source line, and the article badge. What you gain: no
embed to regenerate when you add a post.

**Upgrading your Squarespace plan does not help here.** Core and above unlock
JavaScript in Code blocks, but the 400 KB block cap is not plan-dependent — it applies
on every tier. Don't upgrade for this; use hosted images instead.

## Notes

- **Back up before switching machines.** *Export project* writes a `.json` holding your
  full-resolution originals; *Import project* restores it. Browser storage alone is not
  a backup.
- **Re-cropping is lossless-ish.** Originals are kept, so changing quality or aspect
  re-encodes from the source rather than from a compressed copy.
- **Tabs auto-hide** if you only have one kind of item.
- **Article tiles** show a small document badge, and on touch devices their titles stay
  visible — there's no hover on a phone. Instagram tiles stay clean.
- **Accessibility**: tabs are keyboard-navigable with arrow keys (they're real radio
  inputs), focus rings are visible, and the grid respects `prefers-reduced-motion`.

### Local preview server

Optional — `admin.html` works fine opened directly. If you want it served:

```bash
python3 -m http.server 8747 --directory /Users/sg/Claude/portfolio-grid
```

Then visit `http://localhost:8747/admin.html`. Note that the browser keeps separate
storage for `file://` and `localhost`, so items added in one won't appear in the other.
