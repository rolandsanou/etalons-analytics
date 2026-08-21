import pandas as pd

from ..config import STAGING, TEAM
from ..elo_model import expected, gd_multiplier, k_factor, update  # noqa: F401 (re-export)
from . import matches as matches_mod


def run_elo(df, team):
    ratings = {}
    timeline = []
    last_played = {}
    for r in df.itertuples():
        h = ratings.get(r.home_team, 1500.0)
        a = ratings.get(r.away_team, 1500.0)
        h2, a2 = update(h, a, r.home_score, r.away_score, r.tournament, bool(r.neutral))
        ratings[r.home_team] = h2
        ratings[r.away_team] = a2
        last_played[r.home_team] = r.date
        last_played[r.away_team] = r.date
        if team in (r.home_team, r.away_team):
            timeline.append({
                "date": r.date.strftime("%Y-%m-%d"),
                "elo": round(h2 if r.home_team == team else a2, 1),
                "opponent": r.away_team if r.home_team == team else r.home_team,
                "opp_elo": round(a if r.home_team == team else h, 1),
            })
    # only teams active in the last 2 years count for rankings
    cutoff = df.date.max() - pd.Timedelta(days=730)
    ranked = sorted(
        ((t, e) for t, e in ratings.items() if last_played[t] >= cutoff),
        key=lambda kv: -kv[1],
    )
    return timeline, [{"rank": i + 1, "team": t, "elo": round(e, 1)}
                      for i, (t, e) in enumerate(ranked)]


def run():
    df = matches_mod.load_results()
    timeline, ranked = run_elo(df, TEAM)
    STAGING.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(timeline).to_csv(STAGING / "elo_timeline.csv", index=False)
    pd.DataFrame(ranked).to_csv(STAGING / "elo_rankings.csv", index=False)
    print(f"wrote {STAGING / 'elo_timeline.csv'} ({len(timeline)} rows), "
          f"elo_rankings.csv ({len(ranked)} rows)")
