"""Upcoming matches: whatever the source has scheduled, plus anything seeded.

CAF publishes a calendar well before a stats provider lists the individual
matches — as of August 2026 the source had no 2027 qualifying season at all — so
a maintainer can enter known fixtures in `data/seed/fixtures.csv` and they appear
at once. A seeded row wins over a fetched one on the same date: it was typed
deliberately.

Nothing here invents a fixture. An empty file is a real answer, and the site says
so rather than showing a placeholder.
"""

from datetime import date

from ..config import RAW, SEED, SOFA_TEAM_ID, STAGING
from ..util import read_csv, read_json, write_csv

FIXTURE_FIELDS = ["date", "opponent", "venue", "tournament", "source"]


def _from_source():
    path = RAW / "sofascore" / "fixtures.json"
    if not path.exists():
        return []
    rows = []
    for e in read_json(path).get("events", []):
        at_home = str(e.get("home_id")) == str(SOFA_TEAM_ID)
        rows.append({
            "date": e["date"],
            "opponent": e["away"] if at_home else e["home"],
            # the source only distinguishes home from away; a tournament played
            # on neutral ground still comes through as one or the other
            "venue": "H" if at_home else "A",
            "tournament": e.get("tournament", ""),
            "source": "sofascore",
        })
    return rows


def _from_seed():
    path = SEED / "fixtures.csv"
    if not path.exists():
        return []
    rows = []
    for r in read_csv(path):
        if not (r.get("date") or "").strip():
            continue
        rows.append({
            "date": r["date"].strip(),
            "opponent": (r.get("opponent") or "").strip(),
            "venue": (r.get("venue") or "").strip().upper()[:1] or "N",
            "tournament": (r.get("tournament") or "").strip(),
            "source": "seed",
        })
    return rows


def run(today=None):
    today = (today or date.today()).isoformat()
    by_date = {}
    for row in _from_source() + _from_seed():   # seed second, so it overwrites
        if row["date"] >= today:
            by_date[row["date"]] = row
    rows = sorted(by_date.values(), key=lambda r: r["date"])
    write_csv(STAGING / "fixtures.csv", rows, FIXTURE_FIELDS)
    return rows
