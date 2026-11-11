# withgreenwood.com

The founder's portfolio: a 4:5 grid, `/archive` and `/monza`. Plain static HTML built by Python. See `README.md` for the workflow.

## Check your work
Run `python3 build.py`, then preview with `python3 -m http.server 8747 --directory site`. There are no tests, so look at the pages you changed at phone and desktop width.

## Traps
- Every push to `main` deploys straight to the live site, so get the founder's go-ahead before pushing.
- `site/` is built and committed, and Cloudflare serves it with no build step. Change `content/` or the Python files, rebuild, and commit both.
- Without Pillow, the build copies full-size originals instead of resized images. Run `pip install -r requirements.txt` first on a new computer.
- Don't re-run `mkpages.py`: it was a one-time generator for `content/pages.json`.
- The `name` in `wrangler.jsonc` must match the Cloudflare Worker, or a deploy creates a second one.
- Velvit work never belongs in this repo, even though the shared project memory sits under this folder's name.

## Labels and subtitles
On a new page, a small label over a heading, or a subtitle under one, stays only when it says something the heading doesn't, such as a case study's client name. A label on every heading and subtext under everything is the default AI look that reviewers now spot.

## Matching a reference
When the founder gives a reference site or image to match, pull its exact colours, fonts and spacing into named values in the site's styles, with a comment saying where they came from, instead of working from a written description of the look, so the match holds across pages.
