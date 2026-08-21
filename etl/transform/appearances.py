from collections import defaultdict
from datetime import datetime, timezone

from ..config import RAW, SOFA_TEAM_ID, STAGING
from ..util import load_overrides, canonical_name, norm_name, read_json, slugify, write_csv

POS_MAP = {"G": "GK", "D": "DF", "M": "MF", "F": "FW"}

STATS_MAP = {
    "goals": "goals",
    "goalAssist": "assists",
    "totalShots": "shots",
    "onTargetScoringAttempt": "shots_on_target",
    "totalPass": "passes",
    "accuratePass": "passes_accurate",
    "keyPass": "key_passes",
    "totalCross": "crosses",
    "accurateCross": "crosses_accurate",
    "totalLongBalls": "long_balls",
    "accurateLongBalls": "long_balls_accurate",
    "totalContest": "dribbles_attempted",
    "wonContest": "dribbles_won",
    "totalTackle": "tackles",
    "wonTackle": "tackles_won",
    "interceptionWon": "interceptions",
    "totalClearance": "clearances",
    "ballRecovery": "recoveries",
    "duelWon": "duels_won",
    "duelLost": "duels_lost",
    "aerialWon": "aerials_won",
    "aerialLost": "aerials_lost",
    "fouls": "fouls",
    "wasFouled": "fouled",
    "dispossessed": "dispossessed",
    "touches": "touches",
    "saves": "saves",
    "savedShotsFromInsideTheBox": "saves_inside_box",
    "punches": "punches",
    "goodHighClaim": "high_claims",
}

APPEARANCE_FIELDS = (["event_id", "date", "tournament", "opponent", "venue", "gf", "ga",
                      "player_id", "sofa_player_id", "name", "pos", "started", "played",
                      "minutes", "rating", "has_detailed_stats"]
                     + sorted(set(STATS_MAP.values())))

EVENT_FIELDS = ["event_id", "date", "tournament", "opponent", "venue", "gf", "ga",
                "result", "n_lineup", "n_with_stats"]


def _dob_from_ts(ts):
    if not ts:
        return ""
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")


def _match_player(entry, name_index, registry, overrides):
    raw_name = entry["player"]["name"]
    name = canonical_name(raw_name, overrides)
    key = norm_name(name)
    candidates = name_index.get(key, [])
    if len(candidates) == 1:
        return candidates[0]
    if len(candidates) > 1:
        dob = _dob_from_ts(entry["player"].get("dateOfBirthTimestamp"))
        for pid in candidates:
            if dob and registry[pid]["dob"] == dob:
                return pid
    return None


def _new_player(entry, registry, name_index, used_ids, overrides):
    name = canonical_name(entry["player"]["name"], overrides)
    pid = slugify(name)
    if pid in used_ids:
        dob = _dob_from_ts(entry["player"].get("dateOfBirthTimestamp"))
        pid = f"{pid}-{dob[:4]}" if dob else f"{pid}-sofa"
    used_ids.add(pid)
    registry[pid] = {
        "player_id": pid,
        "name": name,
        "pos": POS_MAP.get(entry.get("position", ""), ""),
        "dob": _dob_from_ts(entry["player"].get("dateOfBirthTimestamp")),
        "club": "",
        "club_country": "",
        "caps": "",
        "goals": "",
        "first_window": "",
        "last_window": "",
        "n_windows": 0,
        "sofa_id": entry["player"]["id"],
        "source": "sofascore",
    }
    name_index[norm_name(name)].append(pid)
    return pid


def run(registry):
    overrides = load_overrides()
    name_index = defaultdict(list)
    for pid, p in registry.items():
        name_index[norm_name(p["name"])].append(pid)
    used_ids = set(registry)

    events = read_json(RAW / "sofascore" / "events_index.json")
    app_rows, event_rows = [], []
    for ev in events:
        lu_path = RAW / "sofascore" / "lineups" / f"{ev['event_id']}.json"
        if not lu_path.exists():
            continue
        lu = read_json(lu_path)
        if "error" in lu or not lu.get("home"):
            continue
        bf_home = ev["home_id"] == SOFA_TEAM_ID
        side = lu["home"] if bf_home else lu["away"]
        gf = ev["home_score"] if bf_home else ev["away_score"]
        ga = ev["away_score"] if bf_home else ev["home_score"]
        base = {
            "event_id": ev["event_id"],
            "date": ev["date"],
            "tournament": ev["tournament"],
            "opponent": ev["away"] if bf_home else ev["home"],
            "venue": "H" if bf_home else "A",
            "gf": gf,
            "ga": ga,
        }
        n_with_stats = 0
        for entry in side.get("players", []):
            st = entry.get("statistics") or {}
            minutes = int(st.get("minutesPlayed", 0) or 0)
            detailed = 1 if ("totalPass" in st or "saves" in st or "touches" in st) else 0
            n_with_stats += detailed
            pid = _match_player(entry, name_index, registry, overrides)
            if pid is None:
                pid = _new_player(entry, registry, name_index, used_ids, overrides)
            p = registry[pid]
            if not p["sofa_id"]:
                p["sofa_id"] = entry["player"]["id"]
            if not p["dob"]:
                p["dob"] = _dob_from_ts(entry["player"].get("dateOfBirthTimestamp"))
            row = dict(base)
            row.update({
                "player_id": pid,
                "sofa_player_id": entry["player"]["id"],
                "name": p["name"],
                "pos": p["pos"] or POS_MAP.get(entry.get("position", ""), ""),
                "started": 0 if entry.get("substitute") else 1,
                "played": 1 if minutes > 0 else 0,
                "minutes": minutes,
                "rating": st.get("rating", ""),
                "has_detailed_stats": detailed,
            })
            for sofa_key, col in STATS_MAP.items():
                row[col] = int(st.get(sofa_key, 0) or 0)
            app_rows.append(row)
        event_rows.append({
            **base,
            "result": "W" if gf > ga else ("D" if gf == ga else "L"),
            "n_lineup": len(side.get("players", [])),
            "n_with_stats": n_with_stats,
        })

    app_rows.sort(key=lambda r: (r["date"], r["name"]))
    write_csv(STAGING / "appearances.csv", app_rows, APPEARANCE_FIELDS)
    write_csv(STAGING / "events.csv", event_rows, EVENT_FIELDS)
