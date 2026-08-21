from collections import defaultdict

from ..config import RAW, SOFA_TEAM_ID, STAGING
from ..util import load_overrides, norm_name, read_json, write_csv
from .appearances import _match_player

GOAL_FIELDS = ["event_id", "date", "minute", "added_time", "class", "is_bf",
               "scorer_sofa_id", "scorer_name", "scorer_player_id",
               "assist_sofa_id", "assist_name", "assist_player_id",
               "bf_score_after", "opp_score_after"]

SUB_FIELDS = ["event_id", "date", "minute", "added_time", "is_bf",
              "in_sofa_id", "in_name", "in_player_id",
              "out_sofa_id", "out_name", "out_player_id", "injury"]

CARD_FIELDS = ["event_id", "date", "minute", "added_time", "is_bf", "card",
               "sofa_id", "name", "player_id", "reason", "rescinded"]

INJURY_FIELDS = ["event_id", "period_end", "length"]


def parse_event_incidents(data, bf_home):
    """Split one raw incidents payload into goal/sub/card/injury-time rows.

    Player-id joining happens later; rows carry raw sofascore player dicts.
    """
    goals, subs, cards, injuries = [], [], [], []
    for inc in data.get("incidents", []):
        t = inc.get("incidentType")
        minute = inc.get("time")
        added = inc.get("addedTime") or 0
        if t == "goal":
            credited_bf = bool(inc.get("isHome")) == bf_home
            goals.append({
                "minute": minute, "added_time": added,
                "class": inc.get("incidentClass", "regular"),
                "is_bf": credited_bf,
                "scorer": inc.get("player") or {},
                "assist": inc.get("assist1") or {},
                "bf_score_after": inc.get("homeScore") if bf_home else inc.get("awayScore"),
                "opp_score_after": inc.get("awayScore") if bf_home else inc.get("homeScore"),
            })
        elif t == "substitution":
            subs.append({
                "minute": minute, "added_time": added,
                "is_bf": bool(inc.get("isHome")) == bf_home,
                "in": inc.get("playerIn") or {},
                "out": inc.get("playerOut") or {},
                "injury": bool(inc.get("injury")),
            })
        elif t == "card":
            cards.append({
                "minute": minute, "added_time": added,
                "is_bf": bool(inc.get("isHome")) == bf_home,
                "card": inc.get("incidentClass", ""),
                "player": inc.get("player") or {"name": inc.get("playerName", "")},
                "reason": inc.get("reason", ""),
                "rescinded": bool(inc.get("rescinded")),
            })
        elif t == "injuryTime":
            injuries.append({"period_end": minute, "length": inc.get("length") or 0})
    return goals, subs, cards, injuries


def _pid(player, on_bf_side, name_index, registry, overrides, sofa2pid):
    if not on_bf_side or not player:
        return ""
    sid = str(player.get("id", ""))
    if sid and sid in sofa2pid:
        return sofa2pid[sid]
    if player.get("name"):
        return _match_player({"player": player}, name_index, registry, overrides) or ""
    return ""


def run(registry):
    overrides = load_overrides()
    sofa2pid = {str(p["sofa_id"]): pid for pid, p in registry.items() if p["sofa_id"]}
    name_index = defaultdict(list)
    for pid, p in registry.items():
        name_index[norm_name(p["name"])].append(pid)

    events = read_json(RAW / "sofascore" / "events_index.json")
    goal_rows, sub_rows, card_rows, injury_rows = [], [], [], []
    for ev in events:
        path = RAW / "sofascore" / "incidents" / f"{ev['event_id']}.json"
        if not path.exists():
            continue
        data = read_json(path)
        if "error" in data:
            continue
        bf_home = ev["home_id"] == SOFA_TEAM_ID
        base = {"event_id": ev["event_id"], "date": ev["date"]}
        goals, subs, cards, injuries = parse_event_incidents(data, bf_home)
        for g in goals:
            scorer_is_bf = g["is_bf"] if g["class"] != "ownGoal" else not g["is_bf"]
            goal_rows.append({
                **base, "minute": g["minute"], "added_time": g["added_time"],
                "class": g["class"], "is_bf": int(g["is_bf"]),
                "scorer_sofa_id": g["scorer"].get("id", ""),
                "scorer_name": g["scorer"].get("name", ""),
                "scorer_player_id": _pid(g["scorer"], scorer_is_bf, name_index,
                                         registry, overrides, sofa2pid),
                "assist_sofa_id": g["assist"].get("id", ""),
                "assist_name": g["assist"].get("name", ""),
                "assist_player_id": _pid(g["assist"], g["is_bf"], name_index,
                                         registry, overrides, sofa2pid),
                "bf_score_after": g["bf_score_after"],
                "opp_score_after": g["opp_score_after"],
            })
        for s in subs:
            sub_rows.append({
                **base, "minute": s["minute"], "added_time": s["added_time"],
                "is_bf": int(s["is_bf"]),
                "in_sofa_id": s["in"].get("id", ""),
                "in_name": s["in"].get("name", ""),
                "in_player_id": _pid(s["in"], s["is_bf"], name_index,
                                     registry, overrides, sofa2pid),
                "out_sofa_id": s["out"].get("id", ""),
                "out_name": s["out"].get("name", ""),
                "out_player_id": _pid(s["out"], s["is_bf"], name_index,
                                      registry, overrides, sofa2pid),
                "injury": int(s["injury"]),
            })
        for c in cards:
            card_rows.append({
                **base, "minute": c["minute"], "added_time": c["added_time"],
                "is_bf": int(c["is_bf"]), "card": c["card"],
                "sofa_id": c["player"].get("id", ""),
                "name": c["player"].get("name", ""),
                "player_id": _pid(c["player"], c["is_bf"], name_index,
                                  registry, overrides, sofa2pid),
                "reason": c["reason"], "rescinded": int(c["rescinded"]),
            })
        for i in injuries:
            injury_rows.append({**base, "period_end": i["period_end"],
                                "length": i["length"]})

    for rows in (goal_rows, sub_rows, card_rows):
        rows.sort(key=lambda r: (r["date"], r["minute"] or 0, r["added_time"] or 0))
    write_csv(STAGING / "goal_events.csv", goal_rows, GOAL_FIELDS)
    write_csv(STAGING / "substitutions.csv", sub_rows, SUB_FIELDS)
    write_csv(STAGING / "cards.csv", card_rows, CARD_FIELDS)
    write_csv(STAGING / "injury_times.csv", injury_rows, INJURY_FIELDS)
