import pandas as pd

CONT_FINALS = ("african cup of nations", "copa américa", "uefa euro",
               "afc asian cup", "gold cup", "oceania nations cup", "confederations cup")


def k_factor(tournament):
    t = str(tournament).lower()
    if "fifa world cup" in t and "qualification" not in t:
        return 60
    if any(c in t for c in CONT_FINALS) and "qualification" not in t:
        return 50
    if "qualification" in t:
        return 40
    if t == "friendly":
        return 20
    return 30


def gd_multiplier(gd):
    gd = abs(gd)
    if gd <= 1:
        return 1.0
    if gd == 2:
        return 1.5
    return 1.75 + (gd - 3) / 8.0


def expected(diff):
    return 1.0 / (1.0 + 10 ** (-diff / 400.0))


def update(home_elo, away_elo, home_goals, away_goals, tournament, neutral):
    diff = home_elo - away_elo + (0 if neutral else 100)
    e_home = expected(diff)
    if home_goals > away_goals:
        s = 1.0
    elif home_goals == away_goals:
        s = 0.5
    else:
        s = 0.0
    delta = k_factor(tournament) * gd_multiplier(home_goals - away_goals) * (s - e_home)
    return home_elo + delta, away_elo - delta


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
            })
    # only teams active in the last 2 years count for rankings
    cutoff = df.date.max() - pd.Timedelta(days=730)
    ranked = sorted(
        ((t, e) for t, e in ratings.items() if last_played[t] >= cutoff),
        key=lambda kv: -kv[1],
    )
    peak = max(timeline, key=lambda p: p["elo"]) if timeline else None
    return {
        "timeline": timeline,
        "current": timeline[-1]["elo"] if timeline else None,
        "peak": peak,
        "ranked": [{"team": t, "elo": round(e, 1)} for t, e in ranked],
    }
