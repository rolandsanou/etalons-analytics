# Étalons Analytics

Open data project on the **Burkina Faso senior national football team** (Les Étalons):
an ETL pipeline and a bilingual (FR/EN) analytics dashboard following **every player
called up since AFCON 2021 (January 2022)** — who they are, where they play (verified),
how much they actually play and produce for the national team, and how the team itself
performs (history since 1960, Elo, formations, projections to AFCON 2027 / WC 2030).

The analysis is designed to evolve with time and contributions: sources are snapshotted,
transforms are deterministic, every metric is gated by sample size, and hand-maintained
knowledge lives in small seed files anyone can extend — see [CONTRIBUTING.md](CONTRIBUTING.md).

## Architecture

```
        EXTRACT                    TRANSFORM                     LOAD
  sources -> data/raw/       raw -> data/staging/       staging -> data/marts/
  (immutable snapshots)      (typed, clean tables)      (analysis-ready CSVs)
                                                        + site/data/*.json (dashboard)
```

```
python -m etl all            # extract -> transform -> load -> quality
python -m etl all --force    # refresh volatile sources (new matches, new call-ups)
python -m etl quality        # data-quality report only
```

- **Extract** (`etl/extract/`) — one module per source. Finished matches never change,
  so Sofascore lineups and incidents are fetched once and cached forever; player
  profiles refresh when older than 30 days; Wikipedia pages and the results dataset
  refresh with `--force`.
- **Transform** (`etl/transform/`) — parses raw snapshots into typed staging tables
  (schemas below). Player identity is resolved here: normalized names + homonym
  splitting by date of birth + manual overrides.
- **Load** (`etl/load/`) — computes the marts and the dashboard JSONs. Formulas live
  in `etl/analytics.py`.
- **Quality** (`etl/quality.py`) — a gate, not an afterthought: uniqueness, referential
  integrity, bounds, player-vs-team goal consistency, coverage rates, club-change
  audit, unresolved identities. `FAIL` breaks the build; `WARN`/`INFO` guide contributors.

## Data model

Staging (`data/staging/`, committed):

| table | grain | key content |
|---|---|---|
| `players.csv` | player | registry: stable `player_id`, position, DOB, career caps/goals (Wikipedia), **verified club/league/country + market value + contract (Sofascore)**, activity `status`, `sofa_id` |
| `callups.csv` | player × window | squad lists (AFCON 2021/2023/2025, current, recent) with club/caps at the time |
| `appearances.csv` | player × match | minutes, goals, assists, shots, passes (total/accurate), key passes, crosses, long balls, dribbles won/attempted, tackles, interceptions, clearances, recoveries, duels, aerials, fouls, touches, GK saves, rating |
| `events.csv` | match | opponent, score, result, competition, **starting formations (both teams)**, stats coverage |
| `matches.csv` | match (1960→) | all-time results with competition classification |
| `elo_timeline.csv` / `elo_rankings.csv` | match / team | BF Elo after every match (+ opponent pre-match Elo), current world ratings |

Marts (`data/marts/`, committed): `player_profile.csv` (per-player aggregates over the
study window + identity/status/verified club), `formations.csv`, `team_form_yearly.csv`,
`afcon_editions.csv`, `elo_yearly.csv`.

## Metric definitions & gates

Every rate on the dashboard shows its raw numerator/denominator, and small samples are
flagged rather than hidden. Claims are descriptive, never causal.

- **Elo** — recomputed over ~49k internationals since 1872 (martj42): K = 60 World Cup,
  50 continental finals, 40 qualifiers, 30 other, 20 friendlies; goal-difference
  multiplier (1.5 / 1.75 / +1/8 per extra goal); +100 home advantage. Projection =
  linear trend on year-end Elo since 2010 with an ≈80% band from year-on-year
  volatility — illustrative, not a prediction.
- **Formations** — starting formation from matchday lineups; systems with **< 8 matches
  are pooled** into "Other" (samples too small to compare); each row carries the average
  **opponent pre-match Elo** so records aren't read against unequal schedules.
- **Player status** — precedence: seeded international retirement
  (`data/seed/int_retirements.csv`, verified announcements only) → career retirement
  (Sofascore) → recency heuristic: *active* = on a squad list or matchday sheet in the
  last 12 months, *fringe* = 12–18 months, *out of the group* = longer (never labeled
  "retired" by inference).
- **Verified club/league** — from each player's Sofascore profile
  (`team.primaryUniqueTournament` = league), stamped `sofascore@date`; Wikipedia squad
  lists freeze the club at call-up time, so the two are audited against each other in
  the quality report. Market value is Sofascore's proposed value (EUR) and is labeled
  as such.
- **Age & peak windows** — indicative peak: GK 26–33, DF 25–30, MF/FW 24–29;
  AFCON 2027 assumed mid-2027 (dates not final), WC 2030 in June 2030.

Known limitations: ~24% of appearances (minor friendlies) carry minutes only, no
detailed stats; career caps/goals are as of the latest Wikipedia update; no complete
squad lists for qualifier-only windows yet.

## Quickstart

```
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python -m etl all
.venv\Scripts\python -m pytest -q
python -m http.server 8123 --directory site
```

`site/` is fully static — deployable as-is on Vercel or GitHub Pages.

## Seed files (hand-maintained knowledge)

| file | purpose |
|---|---|
| `data/seed/wiki_squads.csv` | call-up windows: one row per Wikipedia squad list |
| `data/seed/name_overrides.csv` | name variant → canonical (the quality report suggests candidates) |
| `data/seed/sofa_ids.csv` | manual player ↔ Sofascore id links when auto-search can't |
| `data/seed/int_retirements.csv` | verified international-retirement announcements |

- **Goal timing & game states** — a per-match timeline rebuilt from incidents
  (stoppage time included; extra time detected even when the source logs ET events as
  "90+X", via the shootout marker). Goals in six 15-minute bins with the
  stoppage share split out; a bin is flagged strong/weak only when the χ² across the
  six regulation bins is significant (p < 0.05). Minutes leading/level/trailing,
  scored-first vs conceded-first records, comebacks and blown leads all derive from
  the same timeline.
- **Player importance** — no composite index. Gated components: minutes share of team
  minutes in the player's own window; on/off GD per 90 (≥900' on AND ≥450' off);
  PPG started vs not started (≥10 starts AND ≥8 non-started squad matches); G+A per 90
  (≥450'); minutes-weighted rating (≥5 rated apps AND ≥300'). Roles: Pillar ≥60%
  minutes AND ≥66% of squad matches started; Rotation ≥25%; otherwise Fringe.
  Percentiles are computed among qualified peers only.
- **Bench impact** — raw sub G+A with minutes; per-90 gated (≥5 sub apps, ≥150');
  GD after entry (≥8 sub apps) read against the team's own post-60' baseline.

## Roadmap

- [x] Goal timelines & substitutions from the incidents endpoint
- [x] Player importance profiles (gated components, no composite index)
- [x] Bench impact
- [ ] Qualifier-window squad lists (curated seed)
- [ ] Player detail pages
- [ ] xG (no free CAF source today), Transfermarkt values (blocked)

## Sources & licensing

- Squad lists, call-ups, records: Wikipedia (CC BY-SA 4.0)
- Results since 1960: [martj42/international_results](https://github.com/martj42/international_results) (CC0)
- Per-player match stats, profiles, market values: Sofascore (unofficial API; cached
  raw, non-commercial use with attribution; this project is not affiliated with
  Sofascore; raw snapshots are not redistributed)
- Elo: computed by this pipeline (eloratings.net formula)

Code is MIT — see [LICENSE](LICENSE).
