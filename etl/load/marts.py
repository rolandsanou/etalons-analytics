"""Writes every analysis mart declared in `registry.ANALYSES`.

This module is orchestration only — no analysis logic lives here. To add a mart,
add an entry to registry.py; nothing in this file needs to change.
"""

from datetime import date

import pandas as pd

from ..config import MARTS, STAGING
from ..transform import matches as matches_mod
from ..util import read_csv, write_csv
from .formations import FORMATION_FIELDS, build_formations
from .profiles import PROFILE_FIELDS, build_profiles
from .registry import ANALYSES


def write_team_tables():
    """Small denormalized tables the dashboard and notebooks both use."""
    m = matches_mod.load_staged()
    hist = matches_mod.history_stats(m)
    pd.DataFrame(hist["by_year"]).to_csv(MARTS / "team_form_yearly.csv", index=False)
    pd.DataFrame(hist["afcon_editions"]).to_csv(MARTS / "afcon_editions.csv", index=False)
    elo_tl = pd.read_csv(STAGING / "elo_timeline.csv", parse_dates=["date"])
    elo_tl["year"] = elo_tl.date.dt.year
    (elo_tl.groupby("year").last().reset_index()[["year", "elo"]]
     .to_csv(MARTS / "elo_yearly.csv", index=False))
    print(f"wrote {MARTS / 'team_form_yearly.csv'}, afcon_editions.csv, elo_yearly.csv")


def run():
    MARTS.mkdir(parents=True, exist_ok=True)
    write_csv(MARTS / "player_profile.csv", build_profiles(date.today()), PROFILE_FIELDS)
    write_csv(MARTS / "formations.csv", build_formations(), FORMATION_FIELDS)
    for entry in ANALYSES:
        for filename, fields, builder in entry["marts"]:
            write_csv(MARTS / filename, builder(), fields)
    write_team_tables()
