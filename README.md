# Étalons Analytics

Open data analysis of the Burkina Faso senior national football team (Les Étalons):
squad breakdowns, historical trends, Elo rating, and projections toward AFCON 2027
and the 2030 World Cup. Bilingual FR/EN static dashboard fed by a Python pipeline.

## Structure

- `pipeline/` — Python pipeline: fetch sources, parse, compute analytics, write `site/data/*.json`
- `site/` — static dashboard (no build step; deploy as-is on Vercel / GitHub Pages)
- `tests/` — pytest suite for the analytics/Elo logic
- `data/raw/` — cached downloads (gitignored)

## Run

```
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python -m pipeline.build
```

Then serve the site locally:

```
python -m http.server 8123 --directory site
```

## Sources

- Squad, call-ups and player records: [Wikipedia — Burkina Faso national football team](https://en.wikipedia.org/wiki/Burkina_Faso_national_football_team) (CC BY-SA 4.0)
- Match results since 1960: [martj42/international_results](https://github.com/martj42/international_results) (CC0)
- Elo ratings are computed by this pipeline from the results dataset (eloratings.net formula)

Projections are simple, transparent models (age curves, Elo trend) — see the
methodology section of the dashboard.

## License

MIT — see [LICENSE](LICENSE).
