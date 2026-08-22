from collections import defaultdict

from ..config import MARTS, STAGING
from ..util import read_csv, write_csv
from .marts import opp_elo_lookup

MIN_COVERAGE = 0.75
MIN_MATCHES = 8

# axis -> (label key, kind, numerator, denominator)
#   per_match : sum(num) / matches
#   pct       : sum(num) / sum(den) * 100
#   avg       : mean of num
AXES = [
    ("possession", "avg", "possession_pct", None),
    ("pass_accuracy", "pct", "passes_accurate", "passes"),
    ("passes_per_match", "per_match", "passes", None),
    ("long_ball_share", "pct", "long_balls_att", "passes"),
    ("long_ball_accuracy", "pct", "long_balls", "long_balls_att"),
    ("shots_per_match", "per_match", "shots", None),
    ("shots_on_target_share", "pct", "shots_on_target", "shots"),
    ("shots_inside_box_share", "pct", "shots_inside_box", "shots"),
    ("big_chances_per_match", "per_match", "big_chances", None),
    ("crosses_per_match", "per_match", "crosses_att", None),
    ("dribbles_per_match", "per_match", "dribbles_att", None),
    ("dribble_success", "pct", "dribbles", "dribbles_att"),
    ("aerial_win", "pct", "aerial_duels", "aerial_duels_att"),
    ("ground_duel_win", "pct", "ground_duels", "ground_duels_att"),
    ("tackles_per_match", "per_match", "tackles", None),
    ("interceptions_per_match", "per_match", "interceptions", None),
    ("recoveries_per_match", "per_match", "recoveries", None),
    ("clearances_per_match", "per_match", "clearances", None),
    ("corners_per_match", "per_match", "corners", None),
    ("fouls_per_match", "per_match", "fouls", None),
]

STYLE_FIELDS = ["scope", "scope_value", "side", "matches", "axis", "value",
                "n", "coverage_pct"]


def _f(row, col):
    v = row.get(col, "")
    if v in ("", None):
        return None
    try:
        return float(v)
    except ValueError:
        return None


def compute_axis(rows, kind, num_col, den_col):
    """(value, n) where n = matches contributing; None when coverage is thin."""
    if kind == "avg":
        vals = [v for v in (_f(r, num_col) for r in rows) if v is not None]
        if not vals:
            return None, 0
        return round(sum(vals) / len(vals), 1), len(vals)
    if kind == "per_match":
        vals = [v for v in (_f(r, num_col) for r in rows) if v is not None]
        if not vals:
            return None, 0
        return round(sum(vals) / len(vals), 1), len(vals)
    pairs = [(_f(r, num_col), _f(r, den_col)) for r in rows]
    pairs = [(n, d) for n, d in pairs if n is not None and d]
    if not pairs:
        return None, 0
    num = sum(n for n, _ in pairs)
    den = sum(d for _, d in pairs)
    return round(100 * num / den, 1), len(pairs)


def full_feed_events(stats):
    """Matches whose statistics block carries passing data (a real Opta feed).

    Thin blocks (possession/shots/corners only) would otherwise inflate the
    denominator and gate out the very axes they lack."""
    return {s["event_id"] for s in stats
            if s["period"] == "ALL" and s["side"] == "bf" and s.get("passes")}


def build_style():
    all_rows = read_csv(STAGING / "team_match_stats.csv")
    full = full_feed_events(all_rows)
    stats = [s for s in all_rows
             if s["period"] == "ALL" and s["event_id"] in full]
    if not stats:
        return []
    elo = opp_elo_lookup()
    matches = sorted({s["event_id"] for s in stats})
    match_elo = {}
    for s in stats:
        e = elo(s["date"])
        if e:
            match_elo[s["event_id"]] = e
    ranked = sorted(match_elo.items(), key=lambda kv: kv[1])
    third = max(len(ranked) // 3, 1)
    tercile = {}
    for i, (eid, _) in enumerate(ranked):
        tercile[eid] = ("weak" if i < third
                        else ("strong" if i >= len(ranked) - third else "mid"))

    formations = {e["event_id"]: e.get("bf_formation", "")
                  for e in read_csv(STAGING / "events.csv")}

    groups = defaultdict(lambda: defaultdict(list))
    for s in stats:
        side = s["side"]
        groups[("overall", "all")][side].append(s)
        groups[("year", s["date"][:4])][side].append(s)
        if s["event_id"] in tercile:
            groups[("opp_elo", tercile[s["event_id"]])][side].append(s)
        f = formations.get(s["event_id"], "")
        if f:
            groups[("formation", f)][side].append(s)

    rows = []
    for (scope, value), sides in groups.items():
        for side, srows in sides.items():
            n_matches = len({r["event_id"] for r in srows})
            if scope != "overall" and n_matches < MIN_MATCHES:
                continue
            for axis, kind, num_col, den_col in AXES:
                val, n = compute_axis(srows, kind, num_col, den_col)
                coverage = n / n_matches if n_matches else 0
                if val is None or coverage < MIN_COVERAGE:
                    continue
                rows.append({
                    "scope": scope, "scope_value": value, "side": side,
                    "matches": n_matches, "axis": axis, "value": val,
                    "n": n, "coverage_pct": round(100 * coverage, 1),
                })
    order = {"overall": 0, "opp_elo": 1, "formation": 2, "year": 3}
    rows.sort(key=lambda r: (order.get(r["scope"], 9), r["scope_value"], r["side"]))
    return rows


def half_split():
    """Possession / shots / passes, first half vs second (BF only)."""
    stats = read_csv(STAGING / "team_match_stats.csv")
    full = full_feed_events(stats)
    out = []
    for period, label in (("1ST", "first"), ("2ND", "second")):
        rows = [s for s in stats if s["period"] == period and s["side"] == "bf"
                and s["event_id"] in full]
        if not rows:
            continue
        entry = {"half": label, "matches": len({r["event_id"] for r in rows})}
        for axis, kind, num_col, den_col in AXES:
            if axis not in ("possession", "shots_per_match", "passes_per_match",
                            "big_chances_per_match", "dribbles_per_match"):
                continue
            val, n = compute_axis(rows, kind, num_col, den_col)
            if val is not None and n / max(entry["matches"], 1) >= MIN_COVERAGE:
                entry[axis] = val
                entry[axis + "_n"] = n
        out.append(entry)
    return out


def run():
    rows = build_style()
    write_csv(MARTS / "team_style.csv", rows, STYLE_FIELDS)
    return rows
