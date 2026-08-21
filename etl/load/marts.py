from collections import defaultdict
from datetime import date

import pandas as pd

from ..analytics import age_on, league_group
from ..config import MARTS, STAGING
from ..transform import matches as matches_mod
from ..util import read_csv, write_csv

SUM_COLS = ["minutes", "goals", "assists", "shots", "shots_on_target", "passes",
            "passes_accurate", "key_passes", "crosses", "crosses_accurate",
            "dribbles_attempted", "dribbles_won", "tackles", "tackles_won",
            "interceptions", "clearances", "recoveries", "duels_won", "duels_lost",
            "aerials_won", "aerials_lost", "fouls", "fouled", "dispossessed",
            "touches", "saves", "saves_inside_box", "punches", "high_claims"]

PROFILE_FIELDS = (["player_id", "name", "pos", "dob", "age", "club", "club_country",
                   "league_group", "caps", "goals_career", "n_windows", "windows",
                   "matchday_squads", "apps", "starts", "detailed_apps", "rating_avg",
                   "pass_pct", "dribble_pct", "minutes_per_app", "goals_per90",
                   "sofa_id", "source"] + SUM_COLS)


def _num(x, cast=int, default=0):
    try:
        return cast(x)
    except (TypeError, ValueError):
        return default


def build_profiles(today):
    players = read_csv(STAGING / "players.csv")
    callups = read_csv(STAGING / "callups.csv")
    apps = read_csv(STAGING / "appearances.csv")

    windows_by_player = defaultdict(set)
    for c in callups:
        windows_by_player[c["player_id"]].add(c["window_id"])

    agg = defaultdict(lambda: defaultdict(float))
    for a in apps:
        pid = a["player_id"]
        g = agg[pid]
        g["matchday_squads"] += 1
        played = _num(a["played"])
        g["apps"] += played
        g["starts"] += _num(a["started"]) if played else 0
        g["detailed_apps"] += _num(a["has_detailed_stats"]) if played else 0
        minutes = _num(a["minutes"])
        rating = _num(a["rating"], float, 0.0)
        if rating > 0 and minutes > 0:
            g["_rating_x_min"] += rating * minutes
            g["_rated_min"] += minutes
        for col in SUM_COLS:
            g[col] += _num(a[col])

    profiles = []
    for p in players:
        g = agg.get(p["player_id"], {})
        minutes = int(g.get("minutes", 0))
        apps_n = int(g.get("apps", 0))
        passes = int(g.get("passes", 0))
        dr_att = int(g.get("dribbles_attempted", 0))
        row = {
            "player_id": p["player_id"],
            "name": p["name"],
            "pos": p["pos"],
            "dob": p["dob"],
            "age": age_on(p["dob"], today) if p["dob"] else "",
            "club": p["club"],
            "club_country": p["club_country"],
            "league_group": league_group(p["club_country"] or None),
            "caps": p["caps"],
            "goals_career": p["goals"],
            "n_windows": len(windows_by_player.get(p["player_id"], ())),
            "windows": ";".join(sorted(windows_by_player.get(p["player_id"], ()))),
            "matchday_squads": int(g.get("matchday_squads", 0)),
            "apps": apps_n,
            "starts": int(g.get("starts", 0)),
            "detailed_apps": int(g.get("detailed_apps", 0)),
            "rating_avg": round(g["_rating_x_min"] / g["_rated_min"], 2)
                          if g.get("_rated_min") else "",
            "pass_pct": round(100 * g.get("passes_accurate", 0) / passes, 1) if passes else "",
            "dribble_pct": round(100 * g.get("dribbles_won", 0) / dr_att, 1) if dr_att else "",
            "minutes_per_app": round(minutes / apps_n, 1) if apps_n else "",
            "goals_per90": round(90 * g.get("goals", 0) / minutes, 2) if minutes >= 180 else "",
            "sofa_id": p["sofa_id"],
            "source": p["source"],
        }
        for col in SUM_COLS:
            row[col] = int(g.get(col, 0))
        profiles.append(row)

    profiles.sort(key=lambda r: (-r["minutes"], r["name"]))
    return profiles


def run():
    today = date.today()
    profiles = build_profiles(today)
    write_csv(MARTS / "player_profile.csv", profiles, PROFILE_FIELDS)

    m = matches_mod.load_staged()
    hist = matches_mod.history_stats(m)
    pd.DataFrame(hist["by_year"]).to_csv(MARTS / "team_form_yearly.csv", index=False)
    pd.DataFrame(hist["afcon_editions"]).to_csv(MARTS / "afcon_editions.csv", index=False)

    elo_tl = pd.read_csv(STAGING / "elo_timeline.csv", parse_dates=["date"])
    elo_tl["year"] = elo_tl.date.dt.year
    yearly = elo_tl.groupby("year").last().reset_index()[["year", "elo"]]
    yearly.to_csv(MARTS / "elo_yearly.csv", index=False)
    print(f"wrote {MARTS / 'team_form_yearly.csv'}, afcon_editions.csv, elo_yearly.csv")
