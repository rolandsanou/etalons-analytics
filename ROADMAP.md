# Roadmap

What this project is aiming at, what is already there, and where help is most
useful. Items marked **good first issue** need no prior knowledge of the codebase.

Scope reminder: the senior men's national team of Burkina Faso, every player
called up since AFCON 2021, with public sources only and every metric gated by
sample size. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for how the pipeline
fits together and [CONTRIBUTING.md](CONTRIBUTING.md) for the workflow.

## Done

- **Pipeline** — extract / transform / load layers, 47-check quality gate,
  77 unit tests, incremental and cached extraction.
- **Squad & players** — 129-player registry since January 2022, verified clubs and
  leagues, market values, activity status, per-match performance (minutes, goals,
  assists, passes, dribbles, duels, saves).
- **Team analysis** — history since 1960, Elo with projections, formations,
  goal timing and game states, playing style vs opponents faced, resilience,
  penalties and shootouts, captains, goalkeepers, coach eras, venue effects,
  youth pipeline, club readiness.
- **Dashboard** — bilingual FR/EN static site, 22 charts, table view under every
  chart, full methodology section.

## Now: make it public and self-updating

- [ ] **Publish the repository** and deploy `site/` (GitHub Pages or Vercel — the
      site is static with no build step).
- [ ] **Scheduled refresh** — a GitHub Action running `python -m etl all --force`
      weekly, committing refreshed staging/marts/site data. This is what makes the
      analysis live rather than a snapshot.
- [ ] **Reproducible builds** — allow a `REFERENCE_DATE` override in `etl/config.py`
      so age-dependent outputs are deterministic, then have CI verify that
      regenerated marts match the committed ones byte for byte.

## Data coverage

- [ ] **Qualifier-window squad lists** — Wikipedia has no squad pages for
      World Cup / AFCON qualifier windows. Needs a curated seed in
      `data/seed/`, sourced from FBF announcements. **good first issue**
- [ ] **U-20 AFCON 2027 squad** (Ghana; qualifiers run through 2026) — one row in
      `data/seed/youth_squads.csv` once published. **good first issue**
- [ ] **Two unlinked players** — Elohim Kaboré and Hassane Rachid Traoré are absent
      from Sofascore's index; add their ids to `data/seed/sofa_ids.csv` if they
      ever appear. Never guess a link: the rule is exact name **and** date of
      birth. **good first issue**
- [ ] **Retirement sources** — `data/seed/int_retirements.csv` currently carries
      maintainer-reported entries for Steeve Yago and Issoufou Dayo; add the public
      announcement links. **good first issue**
- [ ] **Coach tenure precision** — tenures are stored at year precision. Refining
      start/end to real dates improves attribution around handovers.
      **good first issue**
- [ ] **Pre-2022 performance data** — extend the appearance-level window backwards
      (AFCON 2017 run, the 2013 final) where Sofascore has coverage.

## Analysis

- [x] **Match detail pages** — 58 static pages: lineups, statistics comparison,
      goal/card/substitution timeline, previous-next navigation.
- [x] **Player detail pages** — 129 pages: identity, window record, importance
      components, bench output and full match-by-match history.
- [x] **Fixture predictions** — W/D/L probabilities from Elo with a draw rate
      calibrated on 441 real CAF matches (27.9% between close sides).
- [ ] **AFCON 2027 qualifying tracker** — blocked on data, not on code: the source
      publishes **no 2027 qualifying season and no scheduled fixtures** yet (checked
      2026-08-22). The fixtures block on `projections.html` already degrades to an
      explanatory note and will populate automatically once
      `staging/fixtures.csv` exists. Remaining work when the calendar lands: a
      fixtures extractor, group standings, and a Monte-Carlo over the remaining
      games ("BF needs X points"), labelled illustrative.
- [ ] **Market-value time series** — profiles already refresh every 30 days; append
      each snapshot to a history table so squad value over time becomes visible.
- [ ] **Set-piece and cards analysis** — cards are already staged and unused
      (`data/staging/cards.csv`). **good first issue**
- [ ] **Opponent-formation matrix** — blocked today: sample per pairing is far too
      small to report responsibly. Revisit as matches accumulate.

## Platform and quality

- [x] **Multi-page structure** — 195 generated pages with a shared shell, hero
      bands, breadcrumbs, sitemap and robots.txt.
- [x] **Motion** — scroll reveals, staggered entrances and hover states that never
      gate visibility and collapse under `prefers-reduced-motion`.
- [x] **Photos** — Wikimedia Commons portraits (25 players, 7 coaches) with
      per-image licence and author credited; initials avatars otherwise.
- [ ] **More portraits** — 104 of 129 players have no free portrait. Uploading
      own photographs to Commons under CC BY-SA is the way to close the gap.
      **good first issue**
- [ ] **English pages** — the generated page copy (hero text, table headers on
      detail pages) is French-only; the charts and hub sections are bilingual.
- [ ] **Accessibility pass** — keyboard navigation for chart tooltips, contrast
      audit on photo cards.
- [ ] **Dark mode** — the palette is defined but the site ships light only.
- [ ] **Data dictionary descriptions** — `tools/gen_data_model.py` documents every
      column name; per-column descriptions are still missing. **good first issue**
- [ ] **Second team: Les Étalonnes** — the women's national team, as a parallel
      pipeline reusing the same layers.

## Deliberately out of scope

- **xG** — the source reports zeros for CAF matches; showing them would be
  misleading.
- **Transfermarkt values** — blocked to scrapers; Sofascore's proposed value is
  used instead and labelled as such.
- **FBref as a second stats source** — blocked to non-browser clients (403).
- **Positional / tracking data** (pressing, PPDA, pass networks) — no free source
  covers CAF.
- **Composite player ratings** — indefensible at ~15 matches a year; components
  are shown side by side instead.
