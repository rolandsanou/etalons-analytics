from collections import defaultdict

from ..analytics import chi_square_uniform, importance_tier, percentile_among
from ..config import MARTS, STAGING
from ..transform.timeline import BIN_LABELS
from ..util import read_csv, write_csv
from .common import as_float, as_int, points_from, presence_minutes, record

# short aliases kept for the dense aggregation code below
_f, _i, _pts, _presence_minutes, _record = (as_float, as_int, points_from,
                                            presence_minutes, record)


# ---------- team timeline ----------

TIMELINE_FIELDS = ["bin", "gf", "ga", "gf_stoppage", "ga_stoppage"]


def build_team_timeline():
    states = read_csv(STAGING / "match_states.csv")
    bins = []
    for b in BIN_LABELS + ["et"]:
        row = {"bin": b,
               "gf": sum(_i(s[f"gf_{b}"]) for s in states),
               "ga": sum(_i(s[f"ga_{b}"]) for s in states),
               "gf_stoppage": 0, "ga_stoppage": 0}
        if b == "31_45":
            row["gf_stoppage"] = sum(_i(s["gf_s45"]) for s in states)
            row["ga_stoppage"] = sum(_i(s["ga_s45"]) for s in states)
        if b == "76_90":
            row["gf_stoppage"] = sum(_i(s["gf_s90"]) for s in states)
            row["ga_stoppage"] = sum(_i(s["ga_s90"]) for s in states)
        bins.append(row)

    reg = bins[:6]
    def chi(side):
        counts = [r[side] for r in reg]
        stat, sig = chi_square_uniform(counts)
        if not sig:
            return {"stat": stat, "significant": False, "bin": None, "direction": None}
        e = sum(counts) / 6
        extreme = max(reg, key=lambda r: abs(r[side] - e))
        return {"stat": stat, "significant": True, "bin": extreme["bin"],
                "direction": "high" if extreme[side] > e else "low"}

    lead = sum(_f(s["min_leading"]) for s in states)
    level = sum(_f(s["min_level"]) for s in states)
    trail = sum(_f(s["min_trailing"]) for s in states)
    total = lead + level + trail

    late_min = sum(max(_f(s["effective_length"]) - 60, 0) for s in states)
    late_gf = sum(_i(s["gf_61_75"]) + _i(s["gf_76_90"]) + _i(s["gf_et"]) for s in states)
    late_ga = sum(_i(s["ga_61_75"]) + _i(s["ga_76_90"]) + _i(s["ga_et"]) for s in states)

    summary = {
        "matches": len(states),
        "minutes": {
            "leading": round(lead), "level": round(level), "trailing": round(trail),
            "pct_leading": round(100 * lead / total, 1) if total else None,
            "pct_level": round(100 * level / total, 1) if total else None,
            "pct_trailing": round(100 * trail / total, 1) if total else None,
        },
        "scored_first": _record([s["result"] for s in states if s["first_goal"] == "bf"]),
        "conceded_first": _record([s["result"] for s in states if s["first_goal"] == "opp"]),
        "goalless": sum(1 for s in states if s["first_goal"] == ""),
        "comeback_wins": sum(1 for s in states if s["trailed"] == "1" and s["result"] == "W"),
        "rescued_draws": sum(1 for s in states if s["trailed"] == "1" and s["result"] == "D"),
        "blown_leads": sum(1 for s in states if s["led"] == "1" and s["result"] == "L"),
        "dropped_leads": sum(1 for s in states if s["led"] == "1" and s["result"] == "D"),
        "chi2": {"gf": chi("gf"), "ga": chi("ga")},
        "post60": {"gf": late_gf, "ga": late_ga, "minutes": round(late_min),
                   "gd90": round(90 * (late_gf - late_ga) / late_min, 2) if late_min else None},
    }
    return bins, summary


# ---------- player importance ----------

IMPORTANCE_FIELDS = [
    "player_id", "name", "pos", "tier", "window_start", "window_matches",
    "team_min_window", "squad_matches", "starts", "start_share",
    "on_min", "minutes_share", "off_min",
    "on_gd90", "off_gd90", "onoff_diff", "gate_onoff",
    "starts_ppg", "nonstart_ppg", "ppg_diff", "gate_ppg",
    "goals", "assists", "pens", "ga90", "gate_ga90",
    "rating_avg", "rated_apps", "rated_min", "gate_rating",
    "pct_minutes_share", "pct_onoff", "pct_ppg", "pct_ga90", "pct_rating",
]


def build_importance(players):
    apps = read_csv(STAGING / "appearances.csv")
    events = read_csv(STAGING / "events.csv")
    states = {s["event_id"]: _f(s["effective_length"], 95)
              for s in read_csv(STAGING / "match_states.csv")}
    callups = read_csv(STAGING / "callups.csv")
    goals = read_csv(STAGING / "goal_events.csv")

    eff = lambda eid: states.get(eid, 95.0)
    events_by_date = sorted((e for e in events), key=lambda e: e["date"])
    first_window = {}
    for c in callups:
        cur = first_window.get(c["player_id"])
        if cur is None or c["window_date"] < cur:
            first_window[c["player_id"]] = c["window_date"]
    pens_by_pid = defaultdict(int)
    for g in goals:
        if g["class"] == "penalty" and g["scorer_player_id"]:
            pens_by_pid[g["scorer_player_id"]] += 1

    by_pid = defaultdict(list)
    for a in apps:
        by_pid[a["player_id"]].append(a)

    names = {p["player_id"]: p for p in players}
    rows = []
    for pid, squad_rows in by_pid.items():
        p = names.get(pid, {})
        first_app = min(a["date"] for a in squad_rows)
        window_start = min(first_window.get(pid, first_app), first_app)
        team_evs = [e for e in events_by_date if e["date"] >= window_start]
        team_min = sum(eff(e["event_id"]) for e in team_evs)
        window_matches = len(team_evs)

        played = [a for a in squad_rows if a["played"] == "1"]
        started = [a for a in squad_rows if a["started"] == "1" and a["played"] == "1"]
        nonstarted = [a for a in squad_rows if a["started"] != "1" or a["played"] != "1"]
        on_min = sum(_presence_minutes(a) for a in played)
        off_min = sum(eff(a["event_id"]) for a in squad_rows) - on_min
        minutes_share = on_min / team_min if team_min else 0.0
        start_share = len(started) / len(squad_rows) if squad_rows else 0.0

        on_gd = sum(_i(a["gf_on"]) - _i(a["ga_on"]) for a in played)
        off_gf = sum(_i(a["gf"]) - _i(a["gf_on"]) for a in squad_rows)
        off_ga = sum(_i(a["ga"]) - _i(a["ga_on"]) for a in squad_rows)
        gate_onoff = on_min >= 900 and off_min >= 450
        gate_ppg = len(started) >= 10 and len(nonstarted) >= 8

        g = sum(_i(a["goals"]) for a in played)
        ast = sum(_i(a["assists"]) for a in played)
        gate_ga90 = on_min >= 450

        rated = [a for a in played if _f(a["rating"]) > 0]
        rated_min = sum(_i(a["minutes"]) for a in rated)
        gate_rating = len(rated) >= 5 and rated_min >= 300

        rows.append({
            "player_id": pid, "name": p.get("name", squad_rows[0]["name"]),
            "pos": p.get("pos", squad_rows[0]["pos"]),
            "tier": importance_tier(minutes_share, start_share, window_matches),
            "window_start": window_start, "window_matches": window_matches,
            "team_min_window": round(team_min),
            "squad_matches": len(squad_rows), "starts": len(started),
            "start_share": round(start_share, 2),
            "on_min": round(on_min), "minutes_share": round(minutes_share, 3),
            "off_min": round(off_min),
            "on_gd90": round(90 * on_gd / on_min, 2) if gate_onoff else "",
            "off_gd90": round(90 * (off_gf - off_ga) / off_min, 2) if gate_onoff else "",
            "onoff_diff": (round(90 * on_gd / on_min - 90 * (off_gf - off_ga) / off_min, 2)
                           if gate_onoff else ""),
            "gate_onoff": int(gate_onoff),
            "starts_ppg": (round(sum(_pts(a) for a in started) / len(started), 2)
                           if gate_ppg else ""),
            "nonstart_ppg": (round(sum(_pts(a) for a in nonstarted) / len(nonstarted), 2)
                             if gate_ppg else ""),
            "ppg_diff": "", "gate_ppg": int(gate_ppg),
            "goals": g, "assists": ast, "pens": pens_by_pid.get(pid, 0),
            "ga90": round(90 * (g + ast) / on_min, 2) if gate_ga90 else "",
            "gate_ga90": int(gate_ga90),
            "rating_avg": (round(sum(_f(a["rating"]) * _i(a["minutes"]) for a in rated)
                                 / rated_min, 2) if gate_rating and rated_min else ""),
            "rated_apps": len(rated), "rated_min": rated_min,
            "gate_rating": int(gate_rating),
        })

    for r in rows:
        if r["gate_ppg"] and r["starts_ppg"] != "" and r["nonstart_ppg"] != "":
            r["ppg_diff"] = round(r["starts_ppg"] - r["nonstart_ppg"], 2)

    def add_percentiles(metric, gate, out):
        qualified = [r for r in rows if (not gate or r[gate] == 1) and r[metric] != ""]
        values = [r[metric] for r in qualified]
        for r in rows:
            r[out] = (percentile_among(r[metric], values)
                      if r in qualified else "")

    eligible = [r for r in rows if r["window_matches"] >= 8]
    share_values = [r["minutes_share"] for r in eligible]
    for r in rows:
        r["pct_minutes_share"] = (percentile_among(r["minutes_share"], share_values)
                                  if r in eligible else "")
    add_percentiles("onoff_diff", "gate_onoff", "pct_onoff")
    add_percentiles("ppg_diff", "gate_ppg", "pct_ppg")
    add_percentiles("ga90", "gate_ga90", "pct_ga90")
    add_percentiles("rating_avg", "gate_rating", "pct_rating")

    rows.sort(key=lambda r: -r["minutes_share"])
    return rows


# ---------- bench impact ----------

BENCH_FIELDS = ["player_id", "name", "pos", "sub_apps", "sub_min", "sub_goals",
                "sub_assists", "sub_ga", "sub_ga90", "gate_ga90",
                "sub_gd", "sub_gd90", "gate_gd", "entry_avg",
                "entries_leading", "entries_level", "entries_trailing"]


def build_bench(players):
    apps = read_csv(STAGING / "appearances.csv")
    names = {p["player_id"]: p for p in players}
    by_pid = defaultdict(list)
    for a in apps:
        if a["played"] == "1" and a["started"] != "1":
            by_pid[a["player_id"]].append(a)
    rows = []
    for pid, subs in by_pid.items():
        p = names.get(pid, {})
        sub_min = sum(_presence_minutes(a) for a in subs)
        g = sum(_i(a["goals"]) for a in subs)
        ast = sum(_i(a["assists"]) for a in subs)
        gd = sum(_i(a["gf_on"]) - _i(a["ga_on"]) for a in subs)
        entries = [_f(a["entry_min"]) for a in subs if a["entry_min"] != ""]
        gate_ga = len(subs) >= 5 and sub_min >= 150
        gate_gd = len(subs) >= 8
        states = [a.get("entry_state", "") for a in subs]
        rows.append({
            "player_id": pid, "name": p.get("name", subs[0]["name"]),
            "pos": p.get("pos", subs[0]["pos"]),
            "sub_apps": len(subs), "sub_min": round(sub_min),
            "sub_goals": g, "sub_assists": ast, "sub_ga": g + ast,
            "sub_ga90": round(90 * (g + ast) / sub_min, 2) if gate_ga and sub_min else "",
            "gate_ga90": int(gate_ga),
            "sub_gd": gd,
            "sub_gd90": round(90 * gd / sub_min, 2) if gate_gd and sub_min else "",
            "gate_gd": int(gate_gd),
            "entry_avg": round(sum(entries) / len(entries), 1) if entries else "",
            "entries_leading": states.count("leading"),
            "entries_level": states.count("level"),
            "entries_trailing": states.count("trailing"),
        })
    rows.sort(key=lambda r: (-r["sub_ga"], -r["sub_apps"]))
    return rows


# --- registry entry points (zero-arg, load their own inputs) ---

def _players():
    return read_csv(STAGING / "players.csv")


def timeline_bins():
    return build_team_timeline()[0]


def timeline_json():
    bins, summary = build_team_timeline()
    return {"bins": bins, "summary": summary}


def importance():
    return build_importance(_players())


def bench():
    return build_bench(_players())
