from collections import defaultdict

from ..config import MARTS, STAGING
from ..util import read_csv, write_csv
from .performance import _f, _i, _presence_minutes, _pts

CAPTAIN_FIELDS = ["player_id", "name", "pos", "matches", "w", "d", "l", "ppg",
                  "minutes", "first_date", "last_date"]

GK_FIELDS = ["player_id", "name", "apps", "starts", "minutes", "ga_on", "ga90",
             "saves", "save_pct", "clean_sheets", "high_claims", "punches",
             "pens_faced", "shootout_saves", "rating_avg", "gated"]

GK_MIN_MINUTES = 270


def build_captains(apps):
    rows = defaultdict(list)
    for a in apps:
        if a.get("captain") == "1" and a["played"] == "1":
            rows[a["player_id"]].append(a)
    out = []
    for pid, matches in rows.items():
        results = [_pts(a) for a in matches]
        out.append({
            "player_id": pid, "name": matches[0]["name"], "pos": matches[0]["pos"],
            "matches": len(matches),
            "w": sum(1 for a in matches if _pts(a) == 3),
            "d": sum(1 for a in matches if _pts(a) == 1),
            "l": sum(1 for a in matches if _pts(a) == 0),
            "ppg": round(sum(results) / len(results), 2),
            "minutes": round(sum(_presence_minutes(a) for a in matches)),
            "first_date": min(a["date"] for a in matches),
            "last_date": max(a["date"] for a in matches),
        })
    out.sort(key=lambda r: -r["matches"])
    return out


def build_goalkeepers(apps, eff_by_event):
    rows = defaultdict(list)
    for a in apps:
        if a["pos"] == "GK" and a["played"] == "1":
            rows[a["player_id"]].append(a)
    out = []
    for pid, matches in rows.items():
        minutes = sum(_presence_minutes(a) for a in matches)
        ga_on = sum(_i(a["ga_on"]) for a in matches)
        saves = sum(_i(a["saves"]) for a in matches)
        cs = 0
        for a in matches:
            if a.get("entry_min") in ("", None):
                continue
            eff = eff_by_event.get(a["event_id"], 95.0)
            full = (_f(a["exit_min"]) - _f(a["entry_min"])) >= eff - 1
            if full and _i(a["ga_on"]) == 0:
                cs += 1
        rated = [a for a in matches if _f(a["rating"]) > 0]
        rated_min = sum(_i(a["minutes"]) for a in rated)
        gated = minutes >= GK_MIN_MINUTES
        out.append({
            "player_id": pid, "name": matches[0]["name"],
            "apps": len(matches),
            "starts": sum(1 for a in matches if a["started"] == "1"),
            "minutes": round(minutes),
            "ga_on": ga_on,
            "ga90": round(90 * ga_on / minutes, 2) if gated and minutes else "",
            "saves": saves,
            "save_pct": (round(100 * saves / (saves + ga_on), 1)
                         if gated and (saves + ga_on) else ""),
            "clean_sheets": cs,
            "high_claims": sum(_i(a["high_claims"]) for a in matches),
            "punches": sum(_i(a["punches"]) for a in matches),
            "pens_faced": sum(_i(a["pens_faced"]) for a in matches),
            "shootout_saves": sum(_i(a["shootout_saves"]) for a in matches),
            "rating_avg": (round(sum(_f(a["rating"]) * _i(a["minutes"]) for a in rated)
                                 / rated_min, 2) if rated_min else ""),
            "gated": int(gated),
        })
    out.sort(key=lambda r: -r["minutes"])
    return out


def run():
    apps = read_csv(STAGING / "appearances.csv")
    eff = {s["event_id"]: _f(s["effective_length"], 95)
           for s in read_csv(STAGING / "match_states.csv")}
    captains = build_captains(apps)
    goalkeepers = build_goalkeepers(apps, eff)
    write_csv(MARTS / "captains.csv", captains, CAPTAIN_FIELDS)
    write_csv(MARTS / "goalkeepers.csv", goalkeepers, GK_FIELDS)
    return captains, goalkeepers
