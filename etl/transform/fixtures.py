"""Upcoming matches: whatever the source has scheduled, plus anything seeded.

CAF publishes a calendar in stages. The draw and the pairings come first, then the
international windows, and only later the exact date and venue of each match. So a
fixture here may carry a confirmed date, or only the window it falls in — and the
site says which. Inventing a date to fill the column would be worse than leaving
it open, because a wrong date on a public page is read as fact.

A seeded row wins over a fetched one on the same matchday: it was typed
deliberately.
"""

from datetime import date

from ..config import RAW, SEED, SOFA_TEAM_ID, STAGING
from ..util import read_csv, read_json, write_csv

FIXTURE_FIELDS = ["date", "date_confirmed", "window_start", "window_end",
                  "matchday", "opponent", "venue", "tournament", "source"]


def _blank():
    return {f: "" for f in FIXTURE_FIELDS}


def _from_source():
    """Scheduled matches the stats source has published — always exact dates."""
    path = RAW / "sofascore" / "fixtures.json"
    if not path.exists():
        return []
    rows = []
    for e in read_json(path).get("events", []):
        at_home = str(e.get("home_id")) == str(SOFA_TEAM_ID)
        row = _blank()
        row.update({
            "date": e["date"], "date_confirmed": "1",
            "window_start": e["date"], "window_end": e["date"],
            "opponent": e["away"] if at_home else e["home"],
            # the source only distinguishes home from away; a tournament played
            # on neutral ground still comes through as one or the other
            "venue": "H" if at_home else "A",
            "tournament": e.get("tournament", ""),
            "source": "sofascore",
        })
        rows.append(row)
    return rows


def _from_seed():
    """Hand-entered fixtures. `date` may be blank when CAF has announced the
    pairing and the window but not yet the day."""
    path = SEED / "fixtures.csv"
    if not path.exists():
        return []
    rows = []
    for r in read_csv(path):
        start = (r.get("window_start") or r.get("date") or "").strip()
        if not start:
            continue
        exact = (r.get("date") or "").strip()
        row = _blank()
        row.update({
            "date": exact,
            "date_confirmed": "1" if exact else "0",
            "window_start": start,
            "window_end": (r.get("window_end") or exact or start).strip(),
            "matchday": (r.get("matchday") or "").strip(),
            "opponent": (r.get("opponent") or "").strip(),
            "venue": (r.get("venue") or "").strip().upper()[:1],
            "tournament": (r.get("tournament") or "").strip(),
            "source": "seed",
        })
        rows.append(row)
    return rows


def _key(row):
    """What identifies the same fixture across sources: the matchday if there is
    one, otherwise the date."""
    return row["matchday"] or row["date"] or row["window_start"]


def run(today=None):
    today = (today or date.today()).isoformat()
    by_key = {}
    for row in _from_source() + _from_seed():   # seed second, so it overwrites
        # a fixture stays listed until its window has closed, not just its date,
        # so an unscheduled match does not vanish the day the window opens
        if (row["window_end"] or row["window_start"]) >= today:
            by_key[_key(row)] = row
    rows = sorted(by_key.values(),
                  key=lambda r: (r["window_start"], int(r["matchday"] or 0)))
    write_csv(STAGING / "fixtures.csv", rows, FIXTURE_FIELDS)
    return rows
