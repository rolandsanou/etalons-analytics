"""How settled is the team?

Two measures per head-coach era:

* churn — how much the starting eleven changes from one match to the next
  (Jaccard overlap of consecutive starting sets, reported as players changed);
* concentration — how much of the available pitch time goes to a small core
  (share taken by the eleven most-used players).

Both are descriptive. A high-churn era is not automatically worse: it can mean
experimentation, injuries or a deliberately wide pool.
"""

from collections import defaultdict
from datetime import date, timedelta

from ..config import MARTS, STAGING
from ..util import read_csv, write_csv
from .common import presence_minutes


def coach_on(date_str, by_date):
    """Coach in charge, tolerating the one-day offset between sources."""
    if date_str in by_date:
        return by_date[date_str]
    base = date.fromisoformat(date_str)
    for delta in (1, -1):
        key = (base + timedelta(days=delta)).isoformat()
        if key in by_date:
            return by_date[key]
    return ""

STABILITY_FIELDS = ["coach", "first_match", "last_match", "matches", "matches_with_xi",
                    "players_used", "avg_changes", "churn_pct", "top11_share",
                    "unique_xis", "gated"]

MIN_MATCHES = 4


def starters_by_event(apps):
    out = defaultdict(set)
    for a in apps:
        if a["started"] == "1" and a["played"] == "1":
            out[a["event_id"]].add(a["player_id"])
    return out


def churn(sequences):
    """Mean number of starters changed between consecutive matches."""
    changes = []
    for prev, cur in zip(sequences, sequences[1:]):
        if not prev or not cur:
            continue
        changes.append(len(cur - prev))
    if not changes:
        return None, None
    avg = sum(changes) / len(changes)
    return round(avg, 2), round(100 * avg / 11, 1)


def build_stability():
    apps = read_csv(STAGING / "appearances.csv")
    # CHAN is a separate squad of home-based players: it would look like extreme
    # churn against the A team it never overlaps with
    events = {e["event_id"]: e for e in read_csv(STAGING / "events.csv")
              if e.get("comp_class") != "chan"}
    coach_by_date = {m["date"]: m.get("coach", "")
                     for m in read_csv(STAGING / "matches.csv")}
    starters = starters_by_event(apps)

    # attribute each event to the coach in charge on that date
    by_coach = defaultdict(list)
    for eid, event in events.items():
        by_coach[coach_on(event["date"], coach_by_date) or "inconnu"].append(event)

    minutes_by_event = defaultdict(lambda: defaultdict(float))
    for a in apps:
        if a["played"] == "1":
            minutes_by_event[a["event_id"]][a["player_id"]] += presence_minutes(a)

    seen_before = set()
    rows = []
    for coach, evs in by_coach.items():
        evs.sort(key=lambda e: e["date"])
        sequences = [starters.get(e["event_id"], set()) for e in evs]
        avg_changes, churn_pct = churn(sequences)

        minutes = defaultdict(float)
        for e in evs:
            for pid, mins in minutes_by_event.get(e["event_id"], {}).items():
                minutes[pid] += mins
        total = sum(minutes.values())
        top11 = sorted(minutes.values(), reverse=True)[:11]
        share = round(100 * sum(top11) / total, 1) if total else None

        used = set()
        for s in sequences:
            used |= s
        for e in evs:
            used |= set(minutes_by_event.get(e["event_id"], {}))

        # only matches with a published starting eleven can inform these measures
        with_xi = sum(1 for s in sequences if s)
        gated = with_xi >= MIN_MATCHES
        rows.append({
            "coach": coach,
            "first_match": evs[0]["date"], "last_match": evs[-1]["date"],
            "matches": len(evs), "matches_with_xi": with_xi,
            "players_used": len(used),
            "avg_changes": avg_changes if gated else "",
            "churn_pct": churn_pct if gated else "",
            "top11_share": share if gated else "",
            "unique_xis": len({frozenset(s) for s in sequences if s}),
            "gated": int(gated),
        })
    rows.sort(key=lambda r: r["first_match"], reverse=True)
    return rows


def run():
    rows = build_stability()
    write_csv(MARTS / "squad_stability.csv", rows, STABILITY_FIELDS)
    return rows


# --- registry entry point ---

def stability_json():
    return build_stability()
