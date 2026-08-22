"""Which players actually play together, and what happens while they are on.

Minutes together come from the reconstructed presence windows: two players
overlap for the intersection of their time on the pitch. Goals are attributed to
a pairing only when they fall inside that overlap, so a pair is never credited
with a goal scored after one of them left.

Descriptive only: a pairing's goal difference reflects the whole team and the
opponents faced, not the pair in isolation.
"""

from collections import defaultdict
from itertools import combinations

from ..config import MARTS, STAGING
from ..util import read_csv, write_csv
from .common import as_float, as_int

PAIR_FIELDS = ["player_a", "name_a", "pos_a", "player_b", "name_b", "pos_b",
               "pair_type", "matches", "minutes", "gf", "ga", "gd", "gd90",
               "gated"]

MIN_MINUTES = 270          # three full matches together
MIN_MATCHES = 4
POS_RANK = {"GK": 0, "DF": 1, "MF": 2, "FW": 3}


def overlap(a, b):
    """Minutes both players were on the pitch, 0 when they never overlapped."""
    start = max(as_float(a["entry_min"]), as_float(b["entry_min"]))
    end = min(as_float(a["exit_min"]), as_float(b["exit_min"]))
    return max(end - start, 0.0)


def pair_type(pos_a, pos_b):
    pair = tuple(sorted((pos_a or "?", pos_b or "?"), key=lambda p: POS_RANK.get(p, 9)))
    return "-".join(pair)


def build_partnerships():
    apps = read_csv(STAGING / "appearances.csv")
    goals = read_csv(STAGING / "goal_events.csv")
    chan = {e["event_id"] for e in read_csv(STAGING / "events.csv")
            if e.get("comp_class") == "chan"}

    goals_by_event = defaultdict(list)
    for g in goals:
        if g["pos"] not in ("", None):
            goals_by_event[g["event_id"]].append((as_float(g["pos"]), g["is_bf"] == "1"))

    on_pitch = defaultdict(list)
    meta = {}
    for a in apps:
        if a["event_id"] in chan or a["played"] != "1" or a["entry_min"] in ("", None):
            continue
        on_pitch[a["event_id"]].append(a)
        meta[a["player_id"]] = (a["name"], a["pos"])

    agg = defaultdict(lambda: {"matches": 0, "minutes": 0.0, "gf": 0, "ga": 0})
    for event_id, players in on_pitch.items():
        event_goals = goals_by_event.get(event_id, [])
        for a, b in combinations(sorted(players, key=lambda x: x["player_id"]), 2):
            mins = overlap(a, b)
            if mins <= 0:
                continue
            key = (a["player_id"], b["player_id"])
            entry = agg[key]
            entry["matches"] += 1
            entry["minutes"] += mins
            start = max(as_float(a["entry_min"]), as_float(b["entry_min"]))
            end = min(as_float(a["exit_min"]), as_float(b["exit_min"]))
            for pos, is_bf in event_goals:
                if start < pos <= end:
                    entry["gf" if is_bf else "ga"] += 1

    rows = []
    for (pid_a, pid_b), v in agg.items():
        name_a, pos_a = meta.get(pid_a, (pid_a, ""))
        name_b, pos_b = meta.get(pid_b, (pid_b, ""))
        gated = v["minutes"] >= MIN_MINUTES and v["matches"] >= MIN_MATCHES
        gd = v["gf"] - v["ga"]
        rows.append({
            "player_a": pid_a, "name_a": name_a, "pos_a": pos_a,
            "player_b": pid_b, "name_b": name_b, "pos_b": pos_b,
            "pair_type": pair_type(pos_a, pos_b),
            "matches": v["matches"], "minutes": round(v["minutes"]),
            "gf": v["gf"], "ga": v["ga"], "gd": gd,
            "gd90": round(90 * gd / v["minutes"], 2) if gated and v["minutes"] else "",
            "gated": int(gated),
        })
    rows.sort(key=lambda r: -r["minutes"])
    return rows


def top_pairs(limit=14):
    return [r for r in build_partnerships() if r["gated"]][:limit]


# --- registry entry points ---

def partnerships_json():
    rows = build_partnerships()
    qualified = [r for r in rows if r["gated"]]
    return {
        "min_minutes": MIN_MINUTES, "min_matches": MIN_MATCHES,
        "qualified": len(qualified), "pairs_seen": len(rows),
        "most_used": qualified[:14],
        "best_gd": sorted(qualified, key=lambda r: -r["gd90"])[:8],
        "worst_gd": sorted(qualified, key=lambda r: r["gd90"])[:8],
    }
