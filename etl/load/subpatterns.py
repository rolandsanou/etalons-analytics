"""How the bench is actually used.

When the first change comes, how many are made, at what score, and whether the
substitute was forced on by an injury. Per coach era and overall, from the
substitution incidents and the reconstructed match clock.

Descriptive: an early first change can mean a tactical decision, an injury or a
red card, and the sample per coach is small.
"""

from collections import defaultdict

from ..config import MARTS, STAGING
from ..util import read_csv, write_csv
from .common import as_float, as_int
from .stability import coach_on

SUBPATTERN_FIELDS = ["scope", "matches", "subs", "subs_per_match", "first_sub_avg",
                     "first_sub_median", "injury_subs", "entries_leading",
                     "entries_level", "entries_trailing", "late_entries", "gated"]

MIN_MATCHES = 4
BANDS = [(0, 45, "1_45"), (46, 60, "46_60"), (61, 70, "61_70"),
         (71, 80, "71_80"), (81, 200, "81_plus")]


def band(minute):
    for lo, hi, label in BANDS:
        if lo <= minute <= hi:
            return label
    return "81_plus"


def _median(values):
    if not values:
        return None
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return round((ordered[mid - 1] + ordered[mid]) / 2, 1)


def _aggregate(scope, events, subs_by_event, states_by_event):
    subs = [s for e in events for s in subs_by_event.get(e["event_id"], [])]
    firsts = []
    for e in events:
        minutes = [as_int(s["minute"]) for s in subs_by_event.get(e["event_id"], [])]
        if minutes:
            firsts.append(min(minutes))
    n = len(events)
    entries = defaultdict(int)
    for s in subs:
        entries[s.get("state_at_entry") or "unknown"] += 1
    gated = n >= MIN_MATCHES and subs
    return {
        "scope": scope,
        "matches": n,
        "subs": len(subs),
        "subs_per_match": round(len(subs) / n, 2) if n else "",
        "first_sub_avg": round(sum(firsts) / len(firsts), 1) if firsts else "",
        "first_sub_median": _median(firsts) if firsts else "",
        "injury_subs": sum(1 for s in subs if s["injury"] == "1"),
        "entries_leading": entries["leading"],
        "entries_level": entries["level"],
        "entries_trailing": entries["trailing"],
        "late_entries": sum(1 for s in subs if as_int(s["minute"]) >= 81),
        "gated": int(bool(gated)),
    }


def _state_at(minute, goal_marks):
    """Burkina Faso's goal difference at a given minute of the match."""
    diff = sum(1 if is_bf else -1 for m, is_bf in goal_marks if m <= minute)
    return "leading" if diff > 0 else ("trailing" if diff < 0 else "level")


def build_subpatterns():
    events = [e for e in read_csv(STAGING / "events.csv")
              if e.get("comp_class") != "chan"]
    subs = read_csv(STAGING / "substitutions.csv")
    goals = read_csv(STAGING / "goal_events.csv")
    coach_by_date = {m["date"]: m.get("coach", "")
                     for m in read_csv(STAGING / "matches.csv")}

    goal_marks = defaultdict(list)
    for g in goals:
        goal_marks[g["event_id"]].append((as_int(g["minute"]), g["is_bf"] == "1"))

    subs_by_event = defaultdict(list)
    for s in subs:
        if s["is_bf"] != "1":
            continue
        s = dict(s)
        s["state_at_entry"] = _state_at(as_int(s["minute"]),
                                        goal_marks.get(s["event_id"], []))
        subs_by_event[s["event_id"]].append(s)

    rows = [_aggregate("Toutes périodes", events, subs_by_event, {})]
    by_coach = defaultdict(list)
    for e in events:
        by_coach[coach_on(e["date"], coach_by_date) or "inconnu"].append(e)
    for coach, evs in sorted(by_coach.items(),
                             key=lambda kv: min(e["date"] for e in kv[1]),
                             reverse=True):
        rows.append(_aggregate(coach, evs, subs_by_event, {}))

    # entry-minute distribution, all eras pooled
    dist = defaultdict(int)
    for event_subs in subs_by_event.values():
        for s in event_subs:
            dist[band(as_int(s["minute"]))] += 1
    distribution = [{"band": label, "n": dist.get(label, 0)}
                    for _, _, label in BANDS]
    return rows, distribution


def run():
    rows, _ = build_subpatterns()
    write_csv(MARTS / "substitution_patterns.csv", rows, SUBPATTERN_FIELDS)
    return rows


# --- registry entry point ---

def subpatterns_json():
    rows, distribution = build_subpatterns()
    return {"by_scope": rows, "distribution": distribution}
