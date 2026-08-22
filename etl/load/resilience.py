from collections import defaultdict

from ..config import MARTS, STAGING
from ..util import read_csv, write_csv
from .performance import _f, _i

RESILIENCE_FIELDS = ["metric", "scope", "n", "value", "detail"]

CLUTCH_FIELDS = ["player_id", "name", "pos", "goals", "openers", "equalizers",
                 "go_ahead", "extenders", "consolations", "late_goals",
                 "goals_when_trailing", "assists_when_trailing", "as_sub_goals"]


def _record(results):
    w = results.count("W")
    d = results.count("D")
    l = results.count("L")
    n = len(results)
    return {"n": n, "w": w, "d": d, "l": l,
            "ppg": round((3 * w + d) / n, 2) if n else None}


def build_resilience():
    states = read_csv(STAGING / "match_states.csv")
    conc = read_csv(STAGING / "concessions.csv")
    goals = read_csv(STAGING / "goal_events.csv")

    by_event_state = {s["event_id"]: s for s in states}

    # deficit ladder: deepest deficit faced per match
    deepest = defaultdict(int)
    for c in conc:
        deepest[c["event_id"]] = max(deepest[c["event_id"]], _i(c["deficit_after"]))
    ladder = {}
    for eid, depth in deepest.items():
        if depth == 0:
            continue
        key = "trailed_1" if depth == 1 else "trailed_2plus"
        ladder.setdefault(key, []).append(by_event_state[eid]["result"])
    never = [s["result"] for s in states if deepest.get(s["event_id"], 0) == 0]

    # reply behaviour after conceding
    replies = [_f(c["reply_minutes"]) for c in conc if c["reply_pos"]]
    replies.sort()
    buckets = {"within_10": 0, "11_20": 0, "21_plus": 0, "never": 0}
    for c in conc:
        if not c["reply_pos"]:
            buckets["never"] += 1
        else:
            m = _f(c["reply_minutes"])
            buckets["within_10" if m <= 10 else ("11_20" if m <= 20 else "21_plus")] += 1

    # output by game state, normalized by exposure minutes
    exposure = {"leading": 0.0, "level": 0.0, "trailing": 0.0}
    for s in states:
        exposure["leading"] += _f(s["min_leading"])
        exposure["level"] += _f(s["min_level"])
        exposure["trailing"] += _f(s["min_trailing"])
    scored = {"leading": 0, "level": 0, "trailing": 0}
    conceded = {"leading": 0, "level": 0, "trailing": 0}
    for g in goals:
        diff = _i(g["diff_before"])
        # diff_before is from the scoring side's view; convert to BF's view
        bf_diff = diff if g["is_bf"] == "1" else -diff
        state = "leading" if bf_diff > 0 else ("trailing" if bf_diff < 0 else "level")
        (scored if g["is_bf"] == "1" else conceded)[state] += 1

    # late swing: score at 75' vs final
    swing = {"gained": 0, "lost": 0}
    goals_by_event = defaultdict(list)
    for g in goals:
        goals_by_event[g["event_id"]].append(g)
    for eid, gs in goals_by_event.items():
        st = by_event_state.get(eid)
        if not st:
            continue
        diff75 = sum(1 if g["is_bf"] == "1" else -1 for g in gs if _f(g["pos"]) <= 75)
        final = sum(1 if g["is_bf"] == "1" else -1 for g in gs)
        pts = lambda d: 3 if d > 0 else (1 if d == 0 else 0)
        delta = pts(final) - pts(diff75)
        if delta > 0:
            swing["gained"] += 1
        elif delta < 0:
            swing["lost"] += 1

    rows = []

    def add(metric, scope, n, value, detail=""):
        rows.append({"metric": metric, "scope": scope, "n": n,
                     "value": value if value is not None else "", "detail": detail})

    for key in ("trailed_1", "trailed_2plus"):
        r = _record(ladder.get(key, []))
        add("deficit", key, r["n"], r["ppg"], f"{r['w']}W-{r['d']}D-{r['l']}L")
    r = _record(never)
    add("deficit", "never_trailed", r["n"], r["ppg"], f"{r['w']}W-{r['d']}D-{r['l']}L")

    for key, n in buckets.items():
        add("reply", key, n, round(100 * n / len(conc), 1) if conc else None,
            f"{n} of {len(conc)} goals conceded")
    add("reply", "median_minutes", len(replies),
        replies[len(replies) // 2] if replies else None)

    for state in ("leading", "level", "trailing"):
        mins = exposure[state]
        add("scored_per90", state, scored[state],
            round(90 * scored[state] / mins, 2) if mins else None,
            f"{scored[state]} goals in {round(mins)} min")
        add("conceded_per90", state, conceded[state],
            round(90 * conceded[state] / mins, 2) if mins else None,
            f"{conceded[state]} goals in {round(mins)} min")

    add("late_swing", "points_gained", swing["gained"], swing["gained"],
        "matches improved by goals after 75'")
    add("late_swing", "points_lost", swing["lost"], swing["lost"],
        "matches worsened by goals after 75'")
    return rows


def build_clutch():
    goals = read_csv(STAGING / "goal_events.csv")
    apps = read_csv(STAGING / "appearances.csv")
    players = {p["player_id"]: p for p in read_csv(STAGING / "players.csv")}

    sub_events = {(a["player_id"], a["event_id"])
                  for a in apps if a["played"] == "1" and a["started"] != "1"}

    agg = defaultdict(lambda: defaultdict(int))
    for g in goals:
        if g["is_bf"] != "1" or g["class"] == "ownGoal":
            continue
        pid = g["scorer_player_id"]
        if pid:
            a = agg[pid]
            a["goals"] += 1
            a[{"opener": "openers", "equalizer": "equalizers",
               "go_ahead": "go_ahead", "extender": "extenders",
               "consolation": "consolations"}.get(g["impact"], "extenders")] += 1
            if _f(g["pos"]) > 75:
                a["late_goals"] += 1
            if _i(g["diff_before"]) < 0:
                a["goals_when_trailing"] += 1
            if (pid, g["event_id"]) in sub_events:
                a["as_sub_goals"] += 1
        apid = g["assist_player_id"]
        if apid and _i(g["diff_before"]) < 0:
            agg[apid]["assists_when_trailing"] += 1

    rows = []
    for pid, a in agg.items():
        p = players.get(pid, {})
        rows.append({
            "player_id": pid, "name": p.get("name", pid), "pos": p.get("pos", ""),
            "goals": a["goals"], "openers": a["openers"], "equalizers": a["equalizers"],
            "go_ahead": a["go_ahead"], "extenders": a["extenders"],
            "consolations": a["consolations"], "late_goals": a["late_goals"],
            "goals_when_trailing": a["goals_when_trailing"],
            "assists_when_trailing": a["assists_when_trailing"],
            "as_sub_goals": a["as_sub_goals"],
        })
    rows.sort(key=lambda r: (-(r["equalizers"] + r["go_ahead"]), -r["goals"]))
    return rows


def run():
    res = build_resilience()
    clutch = build_clutch()
    write_csv(MARTS / "resilience.csv", res, RESILIENCE_FIELDS)
    write_csv(MARTS / "clutch_players.csv", clutch, CLUTCH_FIELDS)
    return res, clutch
