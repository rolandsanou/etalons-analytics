# Étalons Analytics

Open data project on the **Burkina Faso senior national football team** (Les Étalons).

The study follows **every player called up since AFCON 2021 (January 2022)** and their
individual performances in national-team matches — matches played, minutes, goals,
assists, passes, dribbles, duels, goalkeeper saves — plus team-level history, an Elo
rating computed from every international since 1960, and projections toward AFCON 2027
and the 2030 World Cup. Results are published as a bilingual (FR/EN) static dashboard.

This analysis is meant to evolve over time and welcomes contributions — see
[CONTRIBUTING.md](CONTRIBUTING.md).

## Architecture (ETL)

```
        EXTRACT                 TRANSFORM                  LOAD
  sources -> data/raw/    raw -> data/staging/    staging -> data/marts/
  (immutable snapshots)   (typed, clean tables)   (analysis-ready) + site/data/ (dashboard JSONs)
```

- `etl/extract/` — one module per source, snapshots into `data/raw/<source>/` (gitignored).
  Finished matches never change, so Sofascore lineups are cached once and the pipeline
  is incremental: re-runs only fetch new matches.
- `etl/parsers/` — HTML parsers (Wikipedia squad tables, records).
- `etl/transform/` — builds the staging layer:
  - `players.csv` — player registry with stable `player_id`, homonym handling by date of birth
  - `callups.csv` — one row per player per call-up window (source: Wikipedia squad lists)
  - `appearances.csv` — one row per player per match with ~30 performance metrics (source: Sofascore)
  - `events.csv`, `matches.csv`, `elo_timeline.csv`, `elo_rankings.csv`
- `etl/load/` — marts (`data/marts/player_profile.csv`, team form, AFCON editions,
  yearly Elo) and the dashboard JSONs in `site/data/`.
- `etl/quality.py` — data-quality gate: uniqueness, referential integrity, minutes
  bounds, player-goals vs team-goals consistency, stats coverage, JSON validity.

Staging and marts are committed so the repo is usable (and reviewable) without
re-running extraction.

## Run

```
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python -m etl all            # extract -> transform -> load -> quality
.venv\Scripts\python -m etl all --force    # refresh sources (new matches, new call-ups)
.venv\Scripts\python -m etl quality        # checks only
.venv\Scripts\python -m pytest -q          # unit tests
```

Serve the dashboard locally:

```
python -m http.server 8123 --directory site
```

`site/` is fully static — deployable as-is on Vercel or GitHub Pages.

## Data sources & licensing

- **Call-up windows and player records**: Wikipedia — the national team page and the
  AFCON 2021/2023/2025 squad pages (CC BY-SA 4.0).
- **Match results since 1960**: [martj42/international_results](https://github.com/martj42/international_results) (CC0).
- **Per-player match statistics**: Sofascore (unofficial API). Cached raw, used for
  non-commercial open analysis with attribution; this project is not affiliated with
  Sofascore.
- **Elo ratings**: computed by this pipeline from the results dataset using the
  eloratings.net formula (K by competition, goal-difference multiplier, +100 home advantage).

Projections are simple, transparent models (age curves, Elo trend with uncertainty
band) — see the methodology section of the dashboard. Code is MIT-licensed
([LICENSE](LICENSE)).
