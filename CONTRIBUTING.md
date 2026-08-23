# Contributing

Contributions are welcome — data fixes, new sources, new analyses, translations.
Start with **[docs/GUIDE.md](docs/GUIDE.md)** — it walks from a clone to a
running copy and then through the changes people actually make. Then
[ROADMAP.md](ROADMAP.md) for what needs doing (items tagged **good first
issue** need no prior knowledge of the codebase) and
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for how the pieces fit.

## Quick start

```
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python -m etl load       # rebuilds everything from committed data
.venv\Scripts\python -m pytest -q
python -m http.server 8123 --directory site
```

**You do not need to download anything to contribute.** `data/staging/` is
committed, so `etl load` rebuilds every mart and the whole dashboard offline.
Run the full `etl all` only when you are refreshing the sources themselves.

Work on a branch, never on `main`. Before every commit:

```bash
python -m pytest -q && python -m etl quality && python tools/check_links.py && python tools/check_seo.py
```

All four must pass. The quality gate exits non-zero on a real problem, so a red
run is a finding to fix rather than an obstacle to route around.

Keep commits short, English and imperative ("Add WCQ window", "Fix Yago
name override").

## Where things live

| I want to… | Go to |
|---|---|
| fix a name, club, coach date, retirement | `data/seed/*.csv` — no code needed |
| add a call-up window or youth squad | `data/seed/wiki_squads.csv`, `data/seed/youth_squads.csv` |
| add an announced fixture | `data/seed/fixtures.csv` — appears on the site at once |
| change generated copy, or translate it | the call site, then `tools/site_builder/strings.py` |
| add a metric or analysis | one new module in `etl/load/` + one entry in `etl/load/registry.py` |
| change a formula or threshold | `etl/analytics.py` (pure functions, unit-tested) |
| add a chart or section | `tools/site_builder/hubs.py` (the anchor) + `site/assets/sections/` + `site/assets/i18n.js` |
| add a data-quality check | `etl/quality.py` |
| understand a column | [docs/DATA_MODEL.md](docs/DATA_MODEL.md) (generated) |

The four-step recipe for adding an analysis is in
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md#adding-an-analysis-the-four-step-recipe).

## The rules that keep numbers defensible

Burkina Faso plays roughly 15 matches a year, so samples are small by nature:

- show the raw numerator and denominator beside every rate;
- gate small samples (render `–`, grey the row) instead of hiding them;
- no composite indexes — show components side by side;
- pool ratios (`sum/sum`), never average percentages;
- compare like with like (style vs opponents faced, formations vs opponent Elo);
- stay descriptive, never causal.

Never hand-edit anything under `data/staging/`, `data/marts/` or `site/data/` —
they are generated. Hand-maintained data lives in `data/seed/`.

## The easiest contributions: seed files

Ranked by how much each would improve the site today:

| # | file | why it matters |
|---|---|---|
| 1 | `wiki_squads.csv` | the largest gap by far. 58 matches are covered in detail but only a handful of squad announcements, so "called up but did not play" is mostly invisible |
| 2 | `fixtures.csv` | the stats source publishes a calendar late — as of Aug 2026 it had no 2027 qualifying season at all. A seeded row shows up immediately |
| 3 | `coach_tenures.csv` | still year-precision in places, which blurs the boundary between coaching eras |
| 4 | `int_retirements.csv` | only announcements with a public source. A player going uncalled is not a retirement |
| 5 | `sofa_ids.csv` | two players are absent from the source's index and are deliberately left unlinked rather than guessed |
| 6 | portraits | 104 of 129 players have none. Upload under a free licence to Wikimedia Commons and the extractor picks it up; press photos are never used |

- `data/seed/name_overrides.csv` — maps a name variant to its canonical form
  (`variant,canonical`). The quality report lists players that exist only via
  Sofascore: most are spelling differences with Wikipedia. Add a line, re-run
  `python -m etl transform load quality`, and the player's stats merge into the
  right profile.
- `data/seed/wiki_squads.csv` — call-up windows. Each row points at a Wikipedia
  page + section listing a squad. To add a window (a new tournament squad page,
  or the current squad after a new call-up), add a row and run
  `python -m etl all --force`.
- `data/seed/sofa_ids.csv` — manual `player_id,sofa_id` links for players the
  automatic search can't resolve (the quality report lists them). Find the id in
  the player's Sofascore URL.
- `data/seed/int_retirements.csv` — international retirements
  (`player_id,date,source,note`). Only add entries backed by a public announcement;
  the pipeline never infers retirement, it only labels long absences "out of the group".
- `data/seed/coach_tenures.csv` — head-coach tenures at year precision (generated
  from Wikipedia's coaching history, then hand-verified). Refining a start/end to the
  real month/day improves match attribution around coaching changes.
- `data/seed/youth_squads.csv` — youth tournament squad pages (same format as
  `wiki_squads.csv` plus a `level` column). Add a row when a new U-17/U-20 squad
  list is published (next expected: U-20 AFCON 2027, qualifiers through 2026).

## Layering rules

- `extract` only downloads and snapshots into `data/raw/` (immutable; gitignored).
- `transform` reads only `data/raw/` + `data/seed/`, writes only `data/staging/`.
- `load` reads only `data/staging/` + `data/seed/`, writes `data/marts/` and
  `site/data/`. It must never touch `data/raw/` — that is what keeps CI and
  offline contribution possible.

Each layer reads only from the layer above. If a transform wants to read a mart,
the logic belongs in `load` instead.

## Ideas and open work

See [ROADMAP.md](ROADMAP.md).

## Licensing

Code is MIT. Wikipedia content is CC BY-SA 4.0; martj42 results are CC0; Sofascore
data is used non-commercially with attribution and is not redistributed in bulk —
keep raw snapshots out of git.
