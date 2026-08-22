# Étalons Analytics

Open data project on the **Burkina Faso senior national football team** (Les Étalons):
an ETL pipeline and a bilingual (FR/EN) analytics dashboard following **every player
called up since AFCON 2021 (January 2022)** — who they are, where they play (verified),
how much they actually play and produce for the national team, and how the team itself
performs (history since 1960, Elo, formations, projections to AFCON 2027 / WC 2030).

The analysis is designed to evolve with time and contributions: sources are snapshotted,
transforms are deterministic, every metric is gated by sample size, and hand-maintained
knowledge lives in small seed files anyone can extend — see [CONTRIBUTING.md](CONTRIBUTING.md).

**Live site: https://rolandsanou.github.io/etalons-analytics/**

**Docs:** [Architecture](docs/ARCHITECTURE.md) · [Data model](docs/DATA_MODEL.md) ·
[Contributing](CONTRIBUTING.md) · [Roadmap](ROADMAP.md)

## Deploying

The site is served from the `gh-pages` branch (the contents of `site/` at its
root). To publish an update:

```bash
bash tools/deploy.sh
```

`.github/workflows/pages.yml` does the same job automatically on every push to
`main`; it is in place but idle while GitHub Actions is unavailable on the
account. When Actions runs again, set Pages back to "GitHub Actions" in the
repository settings and the script becomes unnecessary.

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
| `matches.csv` | match (1960→) | all-time results with competition classification, **venue class** (home / delocalized home / neutral / away) and **head coach** |
| `elo_timeline.csv` / `elo_rankings.csv` | match / team | BF Elo after every match (+ opponent pre-match Elo), current world ratings |
| `goal_events.csv` / `substitutions.csv` / `cards.csv` / `injury_times.csv` | incident | goal timings with running scores, subs, cards, stoppage lengths |
| `match_states.csv` | match | effective length, goal bins, minutes leading/level/trailing, comeback flags |
| `penalties.csv` / `shootouts_alltime.csv` | attempt / shootout | in-game and shootout penalty attempts per taker; all-time shootout record |
| `youth_callups.csv` | player × youth squad | U-17/U-20 AFCON squads linked to the senior registry (name + DOB) |
| `club_form.csv` | player | latest club season: apps, starts, minutes, rating (30-day refresh) |
| `team_match_stats.csv` | match × period × side | possession, big chances, shots, passes, duels, dribbles, defensive actions (ALL / 1st / 2nd half, BF and opponent) |
| `concessions.csv` | goal conceded | deficit depth, reply time, replied-within-10 flag |

Marts (`data/marts/`, committed): `player_profile.csv`, `player_importance.csv`,
`bench_impact.csv`, `formations.csv`, `team_timeline.csv`, `captains.csv`,
`goalkeepers.csv`, `coach_eras.csv`, `pipeline.csv`, `team_form_yearly.csv`,
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
| `data/seed/coach_tenures.csv` | head-coach tenures (year precision; refine dates freely) |
| `data/seed/youth_squads.csv` | youth tournament squad pages (U-17/U-20 AFCON editions) |

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
- **Venue classes** — "delocalized home" = BF designated host but playing abroad
  (stadium homologation), classified by listing + host country because the source
  flags the Marrakech-era homes as neutral; final tournaments count as neutral.
- **Coach eras** — tenures from a hand-verifiable seed (year precision, initially
  parsed from Wikipedia); records per tenure of ≥10 matches, rest pooled; Elo Δ =
  first to last match of the tenure.
- **Captains & goalkeepers** — kick-off captain from lineups; GK save% =
  saves / (saves + goals conceded while on pitch), clean sheet = full presence with
  zero conceded, rates gated at 270'.
- **Penalties & shootouts** — per-taker in-game conversion and per-attempt shootout
  record from incidents (cross-checked against recorded shootout scores);
  all-time shootout list from martj42.
- **Youth pipeline** — youth squads linked to the senior registry only on
  name + date-of-birth agreement; "graduated" means appearing on a senior matchday
  sheet; prospects = not yet called up, aged ≤21.
- **Club readiness** — latest club season (apps, minutes, rating) per active/fringe
  player, refreshed every 30 days and stamped with its as-of date.
- **Playing style** — averages computed only over matches whose feed includes passing
  data (a reduced feed would distort the denominator); an axis appears only above 75%
  coverage of that sample, always beside the opponents actually faced. Ratios are
  pooled (sum/sum), never averages of percentages; per-match volume is indexed with
  opponents = 100 so different scales share one axis. Terciles use the opponent's
  pre-match Elo. xG is null at source for CAF matches and is excluded.
- **Resilience** — every goal is classified by what it changed (opener / equalizer /
  go-ahead / extender / consolation; own goals credited to the benefiting side).
  Response time is measured in real playing minutes including stoppage; output by
  game state is normalized by minutes actually spent in that state; the late swing
  compares the points implied by the score at 75' with the final result.

## Roadmap

- [x] Goal timelines & substitutions from the incidents endpoint
- [x] Player importance profiles (gated components, no composite index)
- [x] Bench impact
- [x] **v3** — team playing style (possession, directness, big chances, duels; 1st/2nd-half
      splits; style vs opponent strength) and resilience (deficit ladder, reply time
      after conceding, output by game state, clutch scorers)
- [x] **v4** — coach eras, penalties & shootouts, captains & GK deep-dive, the
      "home away from home" cost, club-readiness indicator, youth pipeline (U17/U20 → senior)
- [ ] U-20 AFCON 2027 squads (Ghana; qualifiers run through 2026 — add the squad list
      to `data/seed/youth_squads.csv` when published)
- [ ] Qualifier-window squad lists (curated seed)
- [ ] Player detail pages, match detail pages
- [ ] Automation: scheduled ETL refresh + deploy
- [ ] xG (no free CAF source today), Transfermarkt values (blocked)

## Sources & licensing

- Squad lists, call-ups, records: Wikipedia (CC BY-SA 4.0)
- Results since 1960: [martj42/international_results](https://github.com/martj42/international_results) (CC0)
- Per-player match stats, profiles, market values: Sofascore (unofficial API; cached
  raw, non-commercial use with attribution; this project is not affiliated with
  Sofascore; raw snapshots are not redistributed)
- Elo: computed by this pipeline (eloratings.net formula)

Code is MIT — see [LICENSE](LICENSE).
