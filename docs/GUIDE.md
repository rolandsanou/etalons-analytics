# Guide: run it, understand it, change it

This walks from an empty folder to a running copy of the site, then through the
changes people actually want to make. Every command here has been run on a clean
checkout, and the output shown is what you should see.

If something does not match, jump to [When it goes wrong](#when-it-goes-wrong).

- [1. What you need](#1-what-you-need)
- [2. Get it running](#2-get-it-running)
- [3. What just happened](#3-what-just-happened)
- [4. Rebuild the published site exactly](#4-rebuild-the-published-site-exactly)
- [5. Make a change](#5-make-a-change)
- [6. Refresh the data](#6-refresh-the-data)
- [7. Check your work](#7-check-your-work)
- [8. Publish](#8-publish)
- [When it goes wrong](#when-it-goes-wrong)

---

## 1. What you need

| | |
|---|---|
| Python | 3.12 or newer (`python --version`) |
| Git | any recent version |
| Disk | ~350 MB, most of it the cached source snapshots |
| Network | only to fetch data. The site rebuilds fully offline — see §4 |

No database, no Node, no build step. If you have Python and Git you have
everything.

---

## 2. Get it running

```bash
git clone https://github.com/rolandsanou/etalons-analytics.git
cd etalons-analytics
python -m venv .venv
```

Activate it — `.venv\Scripts\activate` on Windows, `source .venv/bin/activate`
elsewhere — then:

```bash
pip install -r requirements.txt
```

Now build everything from the data already in the repository:

```bash
python -m etl load
```

```
wrote .../data/marts/player_profile.csv (129 rows)
wrote .../data/marts/formations.csv (3 rows)
...
wrote .../site/data/meta.json (0 KB)
```

Generate the pages:

```bash
python tools/build_site.py
```

```
built 392 pages (fr: 196, en: 196 — 129 players, 58 matches per language)
sitemap lists 392 URLs with language alternates; 404.html written
every generated string is translated
```

Serve it:

```bash
python -m http.server 8123 --directory site
```

Open <http://localhost:8123>. You should see the French site; English is at
`/en/`. **You have not touched the network yet** — that is the point of §4.

---

## 3. What just happened

Data moves in one direction through four folders, and each step reads only from
the one above it:

```
etl/extract   →  data/raw/       immutable API + page snapshots   (gitignored)
etl/transform →  data/staging/   typed, clean tables              (committed)
etl/load      →  data/marts/     analysis-ready aggregates        (committed)
                 site/data/*.json  what the browser fetches       (committed)
tools/build_site.py → site/**.html   392 pages                    (committed)
```

`data/seed/` sits alongside as the fifth input: hand-maintained CSVs holding
things no API knows — coach tenure dates, name variants, announced fixtures.

Two consequences worth internalising:

- **`etl/load/` must never read `data/raw/`.** Because staging is committed, you
  can rebuild every number and every page with no network access and no API key.
  That is what makes contribution and CI possible. If you catch yourself reaching
  for `data/raw` inside `load`, the logic belongs in `transform`.
- **Generated files are not source.** Never hand-edit `data/marts/`,
  `site/data/`, or the generated `.html`. Change the code that writes them and
  re-run.

Each step also runs alone:

```bash
python -m etl transform   # re-derive staging from the raw snapshots
python -m etl load        # rebuild marts + JSON from staging
python -m etl pages       # regenerate the HTML
python -m etl quality     # just the checks
```

---

## 4. Rebuild the published site exactly

This is the reproducibility check. It proves the site is a function of the
committed data and nothing else:

```bash
python -m etl load && python tools/build_site.py && git status --short
```

If `git status` comes back empty, your machine produced byte-identical output to
what is published. Two known exceptions will show as changes:

- `site/data/meta.json` — carries `generated_at`, so it moves every run.
- Anything whose figures depend on today's date (ages, "days since").

Everything else should be identical. If a mart differs, that is a real finding —
open an issue.

---

## 5. Make a change

Five recipes, smallest first. Each ends with the command that shows your change.

### 5a. Change wording or a label

Copy lives in two places depending on who writes it:

| What | Where |
|---|---|
| Text the generator writes into HTML | `tools/site_builder/strings.py` |
| Text the browser writes (charts, tables, section leads) | `site/assets/i18n.js` |

`strings.py` is keyed on **the French source string**, gettext-style:

```python
EN = {
    "Derniers matchs": "Latest matches",
}
```

So French is edited at the call site and English in this dictionary. Forget an
English entry and the build tells you rather than silently shipping French:

```
WARNING: 1 strings have no English translation:
  - Prochain match
```

Rebuild with `python tools/build_site.py` and the report must read
`every generated string is translated`.

### 5b. Add a column to the players table

The table is client-side, fed by `site/data/pool.json`, which comes from the
`player_profile` mart. Three edits:

1. **`etl/load/profiles.py`** — add the field name to `PROFILE_FIELDS`, and the
   value to the `row` dict.
2. **`tools/gen_data_model.py`** — nothing to do; just re-run it, since CI fails
   if the data dictionary is stale.
3. **`site/assets/sections/players.js`** — add an entry to the `COLUMNS` list
   with a `label` key pointing at an `i18n.js` string.

```bash
python -m etl load && python tools/gen_data_model.py && python tools/build_site.py
```

Sorting reads the underlying value, not the rendered cell, so a formatted or
suffixed cell still sorts correctly.

### 5c. Add a whole analysis

The long version is in [ARCHITECTURE.md](ARCHITECTURE.md); the shape is:

1. Write the computation in `etl/load/<your_analysis>.py`, taking staging tables
   and returning rows. Keep the arithmetic in `etl/analytics.py` if it is a
   formula worth testing on its own.
2. Register it **once** in `etl/load/registry.py`, declaring the marts it writes
   and the JSON fragments it contributes. `marts.py` and `site.py` iterate the
   registry — you do not edit them.
3. Add a chart or table in `site/assets/sections/`, and the anchor element in the
   relevant page builder in `tools/site_builder/hubs.py`.
4. Add a check to `etl/quality.py`. An analysis without a check is a guess.

### 5d. Change the design

All colour, type and spacing decisions are CSS custom properties at the top of
`site/assets/style.css`. Change the token, not the usages:

```css
--s1: #c0142b;      /* the Burkina Faso accent */
--paper: #f5f3ef;
--ink: #1b1a17;
```

Two rules that will bite you:

- **Dark mode is two synced blocks.** A token overridden for dark must be set in
  both `@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) }`
  and `:root[data-theme="dark"]`, or the manual toggle and the OS preference
  disagree.
- **Inside the masthead, never take a colour from `--ink` or `--paper`.** Those
  invert with the theme while the masthead stays dark in both, which is how the
  selected language chip once ended up white-on-white. Use `--masthead` and
  `--masthead-ink`.

Chart colours are read from these same tokens at render time
(`readThemeTokens()` in `core.js`), so a token change repaints the charts too.

### 5e. Redraw the icons or social cards

Both are committed images, drawn by hand-run scripts so that Pillow never becomes
a dependency of the build or of CI:

```bash
pip install pillow
python tools/make_icons.py       # favicon.svg + .ico + apple-touch-icon.png
python tools/make_og_image.py    # og-fr.png + og-en.png
```

Icons are drawn from geometry, never set as a character. A glyph renders only if
the reader's system carries a font for it — the reason the favicon used to be an
emoji that looked different on every platform.

---

## 6. Refresh the data

Everything above works from committed data. To pull new data you need the network
and a little care, because the source is an unofficial API.

```bash
python -m etl all                   # incremental: fetches only what is missing
python -m etl all --force-profiles  # + re-read clubs, values, contracts
python -m etl all --force           # + re-read Wikipedia, results, Commons
```

What is cached and for how long:

| Data | Refetched when |
|---|---|
| Lineups, incidents, match statistics | **never** — a played match cannot change |
| Player profiles, club form | older than 30 days, or a force flag |
| Fixtures | older than 1 day |
| Wikipedia pages, results dataset, portraits | `--force` |

Reach for `--force-profiles` after a transfer window: it is about 200 requests
and roughly four minutes at the built-in 1.3 s pacing. Avoid `--force` unless you
mean it.

The one thing you cannot get from the network is a squad announcement in a form
this pipeline reads. Those go in `data/seed/wiki_squads.csv`, and they are the
most valuable contribution anyone can make.

---

## 7. Check your work

Run all four before you open a pull request:

```bash
python -m pytest -q            # 116 passed in 1.01s
python -m etl quality          # quality: 49 checks, 0 failures
python tools/check_links.py    # checked 393 pages, 0 broken internal links
python tools/check_seo.py      # audited 393 pages: 0 failures, 0 warnings
```

The test suite is fast because `etl/analytics.py` and `etl/parsers/` are pure
functions with no I/O — keep them that way and testing stays cheap.

The quality gate is a gate: it exits non-zero and fails the build. A red run is a
finding to fix, not an obstacle to route around.

`check_seo.py` also scans the CSS and JS for stray control characters. That check
exists because a mangled escape sequence has twice reached a committed asset —
once silently disabling all of `core.js`, once printing a control character where
an icon should have been. Neither showed up as a broken link.

**How numbers must be presented.** These are enforced in review:

- Show the numerator and denominator, not just the rate.
- Gate a small sample — render `–` and grey the row. Never hide it, never show it
  as if it were solid.
- Pool ratios (sum ÷ sum). Never average percentages.
- Compare like with like: style against the opponents actually faced, formations
  against opponent Elo.
- No composite indexes. A single invented score cannot be argued with.
- Descriptive, never causal.

---

## 8. Publish

```bash
bash tools/deploy.sh
```

That rebuilds, runs the link and SEO checks, commits, pushes `main`, and pushes
`site/` to the `gh-pages` branch with `git subtree push`.

GitHub Pages serves the **`gh-pages` branch**, not Actions, because the workflows
on this account are blocked by a billing lock. `ci.yml` and `pages.yml` are
written and correct; when the lock clears, switch Pages back to "GitHub Actions"
and they take over.

---

## When it goes wrong

**`ModuleNotFoundError: No module named 'curl_cffi'`**
You skipped `pip install -r requirements.txt`, or the venv is not active. The
Sofascore extractor needs `curl_cffi` for browser impersonation; plain `requests`
gets a 403.

**`python -m etl load` fails on a missing staging file**
You are on a checkout where staging is incomplete. `python -m etl transform`
rebuilds staging from `data/raw`, but only if you have the snapshots. Without
them, pull the committed staging back: `git checkout -- data/staging`.

**Build reports untranslated strings**
Expected, and the point. Add the English to `tools/site_builder/strings.py`
keyed on the exact French source string, including punctuation.

**The site looks unstyled, or a deploy seems not to have landed**
A stale cache. Every stylesheet and script URL carries `?v=<hash>` of the asset
contents, so a real deploy busts it — but the HTML itself can be held by the CDN
for a few minutes. Hard-refresh before debugging.

**Charts missing on a page you edited**
The charting library is only loaded on pages whose markup contains a chart
container, and `boot.js` only runs a renderer whose anchor id exists. If you
added a chart, add its container via the `card(chart="…")` helper so both checks
see it.

**A quality check fails after a data refresh**
Read the message before changing the check. The gate has caught real source
problems, including shootout goals being folded into the match score.
