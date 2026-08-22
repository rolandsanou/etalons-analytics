import csv
from collections import defaultdict

from ..config import RAW, SOFA_TEAM_ID, STAGING, TEAM
from ..util import load_overrides, norm_name, read_json, write_csv
from .appearances import _match_player

PENALTY_FIELDS = ["event_id", "date", "kind", "minute", "added_time", "is_bf",
                  "outcome", "sofa_id", "name", "player_id"]

SHOOTOUT_FIELDS = ["date", "opponent", "venue", "winner_is_bf", "first_shooter_is_bf"]


def parse_penalty_incidents(data, bf_home):
    """In-game penalties (scored/missed) and shootout attempts, taker side view."""
    rows = []
    for inc in data.get("incidents", []):
        t = inc.get("incidentType")
        klass = inc.get("incidentClass", "")
        if t == "goal" and klass == "penalty":
            kind, outcome = "ingame", "scored"
        elif t == "inGamePenalty":
            kind, outcome = "ingame", (klass or "missed")
        elif t == "penaltyShootout":
            kind, outcome = "shootout", (klass or "")
        else:
            continue
        rows.append({
            "kind": kind, "outcome": outcome,
            "minute": inc.get("time"), "added_time": inc.get("addedTime") or 0,
            "is_bf": bool(inc.get("isHome")) == bf_home,
            "player": inc.get("player") or {},
        })
    return rows


def _build_penalties(registry):
    overrides = load_overrides()
    name_index = defaultdict(list)
    for pid, p in registry.items():
        name_index[norm_name(p["name"])].append(pid)
    sofa2pid = {str(p["sofa_id"]): pid for pid, p in registry.items() if p["sofa_id"]}

    events = read_json(RAW / "sofascore" / "events_index.json")
    rows = []
    for ev in events:
        path = RAW / "sofascore" / "incidents" / f"{ev['event_id']}.json"
        if not path.exists():
            continue
        data = read_json(path)
        if "error" in data:
            continue
        bf_home = ev["home_id"] == SOFA_TEAM_ID
        for r in parse_penalty_incidents(data, bf_home):
            player = r.pop("player")
            pid = ""
            if r["is_bf"] and player:
                sid = str(player.get("id", ""))
                pid = sofa2pid.get(sid) or (_match_player({"player": player}, name_index,
                                                          registry, overrides) or "")
            rows.append({
                "event_id": ev["event_id"], "date": ev["date"], **r,
                "is_bf": int(r["is_bf"]),
                "sofa_id": player.get("id", ""), "name": player.get("name", ""),
                "player_id": pid,
            })
    rows.sort(key=lambda r: (r["date"], r["kind"]))
    write_csv(STAGING / "penalties.csv", rows, PENALTY_FIELDS)


def _build_shootouts():
    fn_path = RAW / "martj42" / "former_names.csv"
    mapping = {}
    with fn_path.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            mapping[r["former"]] = r["current"]
    rows = []
    with (RAW / "martj42" / "shootouts.csv").open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            home = mapping.get(r["home_team"], r["home_team"])
            away = mapping.get(r["away_team"], r["away_team"])
            if TEAM not in (home, away):
                continue
            winner = mapping.get(r["winner"], r["winner"])
            first = mapping.get(r.get("first_shooter", ""), r.get("first_shooter", ""))
            rows.append({
                "date": r["date"],
                "opponent": away if home == TEAM else home,
                "venue": "H" if home == TEAM else "A",
                "winner_is_bf": int(winner == TEAM),
                "first_shooter_is_bf": int(first == TEAM) if first else "",
            })
    rows.sort(key=lambda r: r["date"])
    write_csv(STAGING / "shootouts_alltime.csv", rows, SHOOTOUT_FIELDS)


def run(registry):
    _build_penalties(registry)
    _build_shootouts()
