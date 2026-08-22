from collections import defaultdict

from ..analytics import goal_impact
from ..config import RAW, SOFA_TEAM_ID, STAGING
from ..util import read_csv, read_json, write_csv
from .appearances import APPEARANCE_FIELDS
from .incidents import GOAL_FIELDS

GOAL_EXTRA_FIELDS = ["pos", "diff_before", "impact"]

CONCESSION_FIELDS = ["event_id", "date", "pos", "half", "deficit_after",
                     "reply_pos", "reply_minutes", "replied_within_10", "result"]

BIN_LABELS = ["1_15", "16_30", "31_45", "46_60", "61_75", "76_90"]

STATE_FIELDS = (["event_id", "date", "result", "effective_length", "has_et",
                 "first_goal", "min_leading", "min_level", "min_trailing",
                 "trailed", "led"]
                + [f"gf_{b}" for b in BIN_LABELS] + ["gf_et", "gf_s45", "gf_s90"]
                + [f"ga_{b}" for b in BIN_LABELS] + ["ga_et", "ga_s45", "ga_s90"])

PRESENCE_FIELDS = ["entry_min", "exit_min", "gf_on", "ga_on", "entry_state"]


def state_at(goals, pos):
    diff = sum(1 if is_bf else -1 for p, is_bf in goals if p <= pos)
    return "leading" if diff > 0 else ("trailing" if diff < 0 else "level")


def _num(x, default=0):
    try:
        return int(float(x))
    except (TypeError, ValueError):
        return default


def build_injury_map(injury_rows, incidents=()):
    """Stoppage length per period end; extended by any incident deeper into stoppage.

    Fallback when nothing was recorded: +2/+3 (≈ the plan's +5 on 90)."""
    inj = {}
    for r in injury_rows:
        end = _num(r.get("period_end"))
        inj[end] = max(inj.get(end, 0), _num(r.get("length")))
    for minute, added in incidents:
        m, a = _num(minute), _num(added)
        if a and m in (45, 90, 105, 120):
            inj[m] = max(inj.get(m, 0), a)
    if not inj:
        inj = {45: 2, 90: 3}
    return inj


def clock_pos(minute, added, inj):
    m, a = _num(minute), _num(added)
    i45, i90 = inj.get(45, 0), inj.get(90, 0)
    if m <= 45:
        return m + a
    if m <= 90:
        return 45 + i45 + (m - 45) + a
    if m <= 105:
        return 90 + i45 + i90 + (m - 90) + a
    return 105 + i45 + i90 + inj.get(105, 0) + (m - 105) + a


def effective_length(inj, has_et):
    base = 90 + inj.get(45, 0) + inj.get(90, 0)
    if has_et:
        base += 30 + inj.get(105, 0) + inj.get(120, 0)
    return base


def bin_goal(minute, added):
    """(bin key, is_stoppage) — stoppage folds into 31_45 / 76_90."""
    m, a = _num(minute), _num(added)
    if m > 90:
        return "et", False
    if m >= 76:
        return "76_90", m == 90 and a > 0
    if m >= 61:
        return "61_75", False
    if m >= 46:
        return "46_60", False
    if m >= 31:
        return "31_45", m == 45 and a > 0
    if m >= 16:
        return "16_30", False
    return "1_15", False


def state_minutes(goals, effective):
    """goals: [(pos, is_bf)] sorted by pos. Minutes leading/level/trailing (BF view)."""
    sums = {"leading": 0.0, "level": 0.0, "trailing": 0.0}
    diff, prev = 0, 0.0
    trailed = led = False
    first_goal = ""
    for pos, is_bf in goals:
        key = "leading" if diff > 0 else ("trailing" if diff < 0 else "level")
        sums[key] += max(pos - prev, 0)
        diff += 1 if is_bf else -1
        if not first_goal:
            first_goal = "bf" if is_bf else "opp"
        trailed = trailed or diff < 0
        led = led or diff > 0
        prev = pos
    key = "leading" if diff > 0 else ("trailing" if diff < 0 else "level")
    sums[key] += max(effective - prev, 0)
    return {
        "first_goal": first_goal,
        "min_leading": round(sums["leading"], 1),
        "min_level": round(sums["level"], 1),
        "min_trailing": round(sums["trailing"], 1),
        "trailed": int(trailed),
        "led": int(led),
    }


def presence(app_row, ins, outs, reds, effective):
    """(entry, exit) clock positions, or (None, None) for an unused sub."""
    pid = app_row["player_id"]
    sid = str(app_row.get("sofa_player_id", ""))
    started = app_row.get("started") in (1, "1", True)
    played = app_row.get("played") in (1, "1", True)
    minutes = _num(app_row.get("minutes"))
    if started:
        entry = 0.0
    elif pid in ins or sid in ins:
        entry = ins.get(pid, ins.get(sid))
    elif played:
        entry = max(effective - minutes, 0.0)
    else:
        return None, None
    exit_ = outs.get(pid, outs.get(sid, effective))
    red = reds.get(pid, reds.get(sid))
    if red is not None:
        exit_ = min(exit_, red)
    return entry, max(exit_, entry)


def annotate_goals(positioned):
    """positioned: [(pos, is_bf, row)] sorted. Adds pos/diff_before/impact in place."""
    diff = 0
    for i, (pos, is_bf, row) in enumerate(positioned):
        before = diff if is_bf else -diff
        row["pos"] = round(pos, 1)
        row["diff_before"] = before
        row["impact"] = goal_impact(before, i == 0)
        diff += 1 if is_bf else -1


def concessions(positioned):
    """One row per conceded goal with the reply that followed (if any)."""
    rows = []
    diff = 0
    for i, (pos, is_bf, row) in enumerate(positioned):
        diff += 1 if is_bf else -1
        if is_bf:
            continue
        reply = next((p for p, b, _ in positioned[i + 1:] if b), None)
        rows.append({
            "pos": round(pos, 1),
            "half": 1 if _num(row.get("minute")) <= 45 else 2,
            "deficit_after": -diff if diff < 0 else 0,
            "reply_pos": round(reply, 1) if reply is not None else "",
            "reply_minutes": round(reply - pos, 1) if reply is not None else "",
            "replied_within_10": (1 if reply is not None and reply - pos <= 10 else 0),
        })
    return rows


def _match_dimension():
    """Every finished match in the window, whether or not lineups were published."""
    rows = []
    for ev in read_json(RAW / "sofascore" / "events_index.json"):
        bf_home = ev["home_id"] == SOFA_TEAM_ID
        gf = ev["home_score"] if bf_home else ev["away_score"]
        ga = ev["away_score"] if bf_home else ev["home_score"]
        bf_pens = ev.get("home_pens" if bf_home else "away_pens", 0)
        opp_pens = ev.get("away_pens" if bf_home else "home_pens", 0)
        rows.append({
            "event_id": str(ev["event_id"]), "date": ev["date"],
            "result": "W" if gf > ga else ("D" if gf == ga else "L"),
            "pens": f"{bf_pens}-{opp_pens}" if (bf_pens or opp_pens) else "",
        })
    rows.sort(key=lambda r: r["date"])
    return rows


def run():
    events = _match_dimension()
    goals = read_csv(STAGING / "goal_events.csv")
    subs = read_csv(STAGING / "substitutions.csv")
    cards = read_csv(STAGING / "cards.csv")
    injuries = read_csv(STAGING / "injury_times.csv")
    apps = read_csv(STAGING / "appearances.csv")

    by_event = lambda rows: _group(rows, "event_id")
    goals_e, subs_e, cards_e, inj_e, apps_e = (by_event(goals), by_event(subs),
                                               by_event(cards), by_event(injuries),
                                               by_event(apps))
    state_rows, concession_rows = [], []
    for ev in events:
        eid = ev["event_id"]
        ev_goals = goals_e.get(eid, [])
        ev_subs = subs_e.get(eid, [])
        incident_times = ([(g["minute"], g["added_time"]) for g in ev_goals]
                          + [(s["minute"], s["added_time"]) for s in ev_subs])
        inj = build_injury_map(inj_e.get(eid, []), incident_times)
        # a shootout implies extra time was played, even when the source logs
        # every ET event as "90+X"
        has_et = (any(e > 90 for e in inj if isinstance(e, int))
                  or any(_num(m) > 90 for m, _ in incident_times)
                  or bool(ev.get("pens")))
        eff = effective_length(inj, has_et)

        positioned = sorted(
            ((clock_pos(g["minute"], g["added_time"], inj), g["is_bf"] == "1", g)
             for g in ev_goals), key=lambda x: x[0])
        annotate_goals(positioned)
        for c in concessions(positioned):
            concession_rows.append({"event_id": eid, "date": ev["date"],
                                    "result": ev["result"], **c})
        st = state_minutes([(p, b) for p, b, _ in positioned], eff)

        row = {"event_id": eid, "date": ev["date"], "result": ev["result"],
               "effective_length": eff, "has_et": int(has_et), **st}
        for b in BIN_LABELS + ["et"]:
            row[f"gf_{b}"] = row[f"ga_{b}"] = 0
        row["gf_s45"] = row["gf_s90"] = row["ga_s45"] = row["ga_s90"] = 0
        for _, is_bf, g in positioned:
            b, stoppage = bin_goal(g["minute"], g["added_time"])
            side = "gf" if is_bf else "ga"
            row[f"{side}_{b}"] += 1
            if stoppage:
                row[f"{side}_s{'45' if b == '31_45' else '90'}"] += 1
        state_rows.append(row)

        # presence windows for this event's appearances
        ins, outs, reds = {}, {}, {}
        for s in ev_subs:
            if s["is_bf"] != "1":
                continue
            pos = clock_pos(s["minute"], s["added_time"], inj)
            for key in (s["in_player_id"], str(s["in_sofa_id"])):
                if key:
                    ins[key] = pos
            for key in (s["out_player_id"], str(s["out_sofa_id"])):
                if key:
                    outs[key] = pos
        for c in cards_e.get(eid, []):
            if c["is_bf"] == "1" and c["card"] in ("red", "yellowRed"):
                pos = clock_pos(c["minute"], c["added_time"], inj)
                for key in (c["player_id"], str(c["sofa_id"])):
                    if key:
                        reds[key] = pos
        goal_marks = [(p, b) for p, b, _ in positioned]
        for a in apps_e.get(eid, []):
            entry, exit_ = presence(a, ins, outs, reds, eff)
            if entry is None:
                a["entry_min"] = a["exit_min"] = a["entry_state"] = ""
                a["gf_on"] = a["ga_on"] = 0
                continue
            a["entry_min"] = round(entry, 1)
            a["exit_min"] = round(exit_, 1)
            a["entry_state"] = state_at(goal_marks, entry)
            a["gf_on"] = sum(1 for p, b, _ in positioned if b and entry < p <= exit_)
            a["ga_on"] = sum(1 for p, b, _ in positioned if not b and entry < p <= exit_)

    write_csv(STAGING / "match_states.csv", state_rows, STATE_FIELDS)
    write_csv(STAGING / "appearances.csv", apps, APPEARANCE_FIELDS + PRESENCE_FIELDS)
    write_csv(STAGING / "goal_events.csv", goals, GOAL_FIELDS + GOAL_EXTRA_FIELDS)
    concession_rows.sort(key=lambda r: (r["date"], r["pos"]))
    write_csv(STAGING / "concessions.csv", concession_rows, CONCESSION_FIELDS)


def _group(rows, key):
    g = defaultdict(list)
    for r in rows:
        g[r[key]].append(r)
    return g
