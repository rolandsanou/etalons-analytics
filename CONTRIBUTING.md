# Contributing

Contributions are welcome — data fixes, new sources, new analyses, translations.

## Quick start

```
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python -m etl all
.venv\Scripts\python -m pytest -q
```

Work on a branch, never on `main`. Run `python -m etl quality` and the tests before
every commit. Keep commits short, English, imperative ("Add WCQ window", "Fix Yago
name override").

## The easiest contributions: seed files

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

## Layering rules

- `extract` only downloads and snapshots into `data/raw/` (immutable; gitignored).
- `transform` reads only `data/raw/` + `data/seed/`, writes only `data/staging/`.
- `load` reads only `data/staging/` (+ raw HTML for record tables), writes
  `data/marts/` and `site/data/`.
- Never hand-edit anything under `data/staging/`, `data/marts/` or `site/data/` —
  they are generated. Hand-maintained data lives in `data/seed/`.

## Ideas / roadmap

- FBref per-tournament tables as a second stats source (blocked for plain HTTP
  clients; needs a browser-assisted or Playwright extractor).
- Cards and substitution timelines from Sofascore incidents endpoint.
- Player detail pages on the dashboard.
- WCQ 2023–2025 squad lists (no Wikipedia squad pages; needs a curated seed).

## Licensing

Code is MIT. Wikipedia content is CC BY-SA 4.0; martj42 results are CC0; Sofascore
data is used non-commercially with attribution and is not redistributed in bulk —
keep raw snapshots out of git.
