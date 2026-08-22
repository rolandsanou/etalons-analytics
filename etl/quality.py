import json

from .config import MARTS, SEED, SITE_DATA, STAGING
from .util import read_csv


def _minutes_by_player():
    path = MARTS / "player_profile.csv"
    if not path.exists():
        return {}
    return {p["player_id"]: int(p["minutes"] or 0) for p in read_csv(path)}


def _check_players(report):
    players = read_csv(STAGING / "players.csv")
    ids = [p["player_id"] for p in players]
    dup = len(ids) - len(set(ids))
    report.append(("players: unique player_id", "FAIL" if dup else "PASS",
                   f"{len(ids)} players, {dup} duplicate ids"))
    noname = sum(1 for p in players if not p["name"].strip())
    report.append(("players: name present", "FAIL" if noname else "PASS", f"{noname} empty"))
    minutes = _minutes_by_player()
    sofa_only = sorted((p for p in players if p["source"] == "sofascore"),
                       key=lambda p: -minutes.get(p["player_id"], 0))
    report.append(("players: sofascore-only entries", "WARN" if len(sofa_only) > 12 else "PASS",
                   f"{len(sofa_only)} players never matched a Wikipedia call-up "
                   f"(possible name variants -> data/seed/name_overrides.csv), by minutes: "
                   + ", ".join(f"{p['name']} ({minutes.get(p['player_id'], 0)}')"
                               for p in sofa_only[:8])))
    verified = sum(1 for p in players if p.get("club_v"))
    pct_v = round(100 * verified / len(players), 1) if players else 0
    report.append(("players: verified club coverage", "WARN" if pct_v < 60 else "PASS",
                   f"{pct_v}% have a Sofascore-verified club ({verified}/{len(players)})"))
    unresolved = [p["name"] for p in players if not p.get("sofa_id")]
    report.append(("players: sofa_id resolution", "WARN" if unresolved else "PASS",
                   f"{len(unresolved)} without sofa_id"
                   + (": " + ", ".join(unresolved[:6]) + " -> data/seed/sofa_ids.csv"
                      if unresolved else "")))
    from .util import norm_name
    mismatch = [f"{p['name']}: {p['club']} -> {p['club_v']}"
                for p in players
                if p.get("club") and p.get("club_v")
                and norm_name(p["club"]) != norm_name(p["club_v"])]
    report.append(("players: wiki vs sofascore club", "INFO",
                   f"{len(mismatch)} players whose verified club differs from the "
                   "Wikipedia list (transfer or naming) — "
                   + "; ".join(mismatch[:6]) + ("…" if len(mismatch) > 6 else "")))
    statuses = {}
    for p in players:
        statuses[p.get("status", "?")] = statuses.get(p.get("status", "?"), 0) + 1
    report.append(("players: status distribution", "INFO",
                   ", ".join(f"{k}={v}" for k, v in sorted(statuses.items()))))
    return {p["player_id"] for p in players}


def _check_callups(report, ids):
    callups = read_csv(STAGING / "callups.csv")
    orphan = sum(1 for c in callups if c["player_id"] not in ids)
    report.append(("callups: referential integrity", "FAIL" if orphan else "PASS",
                   f"{len(callups)} call-ups, {orphan} orphans"))


def _check_appearances(report, ids):
    apps = read_csv(STAGING / "appearances.csv")
    if not apps:
        report.append(("appearances: rows", "FAIL", "no rows"))
        return
    orphan = sum(1 for a in apps if a["player_id"] not in ids)
    report.append(("appearances: referential integrity", "FAIL" if orphan else "PASS",
                   f"{len(apps)} rows, {orphan} orphans"))
    bad_min = sum(1 for a in apps if not (0 <= int(a["minutes"] or 0) <= 130))
    report.append(("appearances: minutes in [0,130]", "FAIL" if bad_min else "PASS",
                   f"{bad_min} out of range"))
    played = [a for a in apps if a["played"] == "1"]
    detailed = sum(1 for a in played if a["has_detailed_stats"] == "1")
    pct = round(100 * detailed / len(played), 1) if played else 0
    report.append(("appearances: detailed-stats coverage", "WARN" if pct < 80 else "PASS",
                   f"{pct}% of played appearances have detailed stats"))
    by_event = {}
    for a in apps:
        e = by_event.setdefault(a["event_id"], {"gf": int(a["gf"] or 0), "goals": 0})
        e["goals"] += int(a["goals"] or 0)
    mismatch = sum(1 for e in by_event.values() if e["goals"] > e["gf"])
    report.append(("appearances: player goals vs team goals", "FAIL" if mismatch else "PASS",
                   f"{mismatch} events where player goals exceed team goals "
                   "(own goals can make player sum lower, never higher)"))


def _check_staging_present(report):
    for name in ("players.csv", "callups.csv", "matches.csv", "appearances.csv",
                 "events.csv", "elo_timeline.csv", "elo_rankings.csv"):
        path = STAGING / name
        ok = path.exists() and path.stat().st_size > 50
        report.append((f"staging: {name}", "PASS" if ok else "FAIL",
                       "present" if ok else "missing or empty"))


def _check_goal_events(report):
    path = STAGING / "goal_events.csv"
    if not path.exists():
        report.append(("goal_events: staged", "FAIL", "missing"))
        return
    goals = read_csv(path)
    events = {e["event_id"]: e for e in read_csv(STAGING / "events.csv")}
    final = {}
    for g in goals:
        final[g["event_id"]] = g
    bad = []
    for eid, g in final.items():
        ev = events.get(eid)
        if not ev:
            continue
        if (g["bf_score_after"], g["opp_score_after"]) != (ev["gf"], ev["ga"]):
            bad.append(f"{ev['date']} vs {ev['opponent']} "
                       f"({g['bf_score_after']}-{g['opp_score_after']} != {ev['gf']}-{ev['ga']})")
    report.append(("goal_events: final running score == match score",
                   "FAIL" if bad else "PASS",
                   f"{len(final)} scoring matches checked"
                   + ("; MISMATCH: " + "; ".join(bad[:4]) if bad else "")))
    bf_goals = [g for g in goals if g["is_bf"] == "1"]
    unattributed = sum(1 for g in bf_goals
                       if g["class"] != "ownGoal" and not g["scorer_player_id"])
    report.append(("goal_events: BF scorer attribution",
                   "WARN" if unattributed else "PASS",
                   f"{len(bf_goals)} BF goals, {unattributed} scorers not matched to registry"))


def _check_coaches(report):
    from datetime import date, timedelta
    matches = read_csv(STAGING / "matches.csv")
    modern = [m for m in matches if m["date"] >= "2000-01-01"]
    with_coach = sum(1 for m in modern if m.get("coach"))
    pct = round(100 * with_coach / len(modern), 1) if modern else 0
    report.append(("matches: coach coverage since 2000", "WARN" if pct < 90 else "PASS",
                   f"{pct}% assigned ({with_coach}/{len(modern)})"))
    seed = read_csv(SEED / "coach_tenures.csv") if (SEED / "coach_tenures.csv").exists() else []
    spans = []
    for r in seed:
        start = date.fromisoformat(r["start"])
        end = date.fromisoformat(r["end"]) if r["end"] else date.today()
        spans.append((r["coach"], start, end))
    bad = []
    for i in range(len(spans)):
        for j in range(i + 1, len(spans)):
            a, b = spans[i], spans[j]
            overlap = (min(a[2], b[2]) - max(a[1], b[1])).days
            if overlap > 366:
                bad.append(f"{a[0]} / {b[0]}")
    report.append(("seed: coach tenures non-conflicting", "FAIL" if bad else "PASS",
                   f"{len(spans)} tenures"
                   + ("; >1y overlap: " + "; ".join(bad[:3]) if bad else "")))


def _check_captains(report):
    apps = read_csv(STAGING / "appearances.csv")
    per_event = {}
    for a in apps:
        if a.get("captain") == "1":
            per_event[a["event_id"]] = per_event.get(a["event_id"], 0) + 1
    n_events = len({a["event_id"] for a in apps})
    odd = [e for e, n in per_event.items() if n != 1]
    report.append(("appearances: one captain per match",
                   "WARN" if (odd or len(per_event) < n_events) else "PASS",
                   f"{len(per_event)}/{n_events} matches with a captain flag, "
                   f"{len(odd)} with more than one"))


def _check_penalties(report):
    path = STAGING / "penalties.csv"
    if not path.exists():
        report.append(("penalties: staged", "FAIL", "missing"))
        return
    pens = read_csv(path)
    odd = [p for p in pens if p["outcome"] not in ("scored", "missed")]
    report.append(("penalties: outcomes classified", "WARN" if odd else "PASS",
                   f"{len(pens)} rows, {len(odd)} with unexpected outcome"))
    events = {e["event_id"]: e for e in read_csv(STAGING / "events.csv") if e.get("pens")}
    so = {}
    for p in pens:
        if p["kind"] != "shootout":
            continue
        s = so.setdefault(p["event_id"], {"bf": 0, "opp": 0})
        if p["outcome"] == "scored":
            s["bf" if p["is_bf"] == "1" else "opp"] += 1
    mismatch, no_cov = [], 0
    for eid, ev in events.items():
        bf_p, opp_p = ev["pens"].split("-")
        if eid not in so:
            no_cov += 1
            continue
        if (str(so[eid]["bf"]), str(so[eid]["opp"])) != (bf_p, opp_p):
            mismatch.append(f"{ev['date']} vs {ev['opponent']}")
    report.append(("penalties: shootout attempts == recorded pens",
                   "FAIL" if mismatch else "PASS",
                   f"{len(events)} shootout matches, {no_cov} without attempt incidents"
                   + ("; MISMATCH: " + "; ".join(mismatch) if mismatch else "")))


def _check_club_form(report):
    path = STAGING / "club_form.csv"
    if not path.exists():
        return
    form = read_csv(path)
    players = read_csv(STAGING / "players.csv")
    targets = [p for p in players if p.get("status") in ("active", "fringe") and p.get("sofa_id")]
    covered = {r["player_id"] for r in form}
    pct = round(100 * sum(1 for p in targets if p["player_id"] in covered)
                / len(targets), 1) if targets else 0
    report.append(("club form: coverage of active pool", "WARN" if pct < 70 else "PASS",
                   f"{pct}% of {len(targets)} active/fringe players have a club season"))
    seasons = {}
    for r in form:
        seasons[r["season_year"]] = seasons.get(r["season_year"], 0) + 1
    report.append(("club form: season labels", "INFO",
                   ", ".join(f"{k or '?'}={v}" for k, v in sorted(seasons.items(), reverse=True))))


def _check_youth(report):
    path = STAGING / "youth_callups.csv"
    if not path.exists():
        return
    youth = read_csv(path)
    if not youth:
        report.append(("youth: rows", "WARN", "no youth call-ups staged"))
        return
    no_dob = sum(1 for y in youth if not y["dob"])
    pct = round(100 * (len(youth) - no_dob) / len(youth), 1)
    report.append(("youth: DOB coverage", "WARN" if pct < 80 else "PASS",
                   f"{pct}% of {len(youth)} youth call-ups have a DOB"))
    weak = [y["name"] for y in youth if y["link_quality"] == "name_only"]
    report.append(("youth: senior links", "INFO",
                   f"{sum(1 for y in youth if y['senior_player_id'])} linked to the senior pool"
                   + (f"; name-only (verify): {', '.join(weak[:4])}" if weak else "")))


def _check_timeline(report):
    path = STAGING / "match_states.csv"
    if not path.exists():
        report.append(("match_states: staged", "FAIL", "missing"))
        return
    states = read_csv(path)
    bad_len = [s for s in states
               if not (85 <= float(s["effective_length"]) <= 135)]
    report.append(("match_states: effective length sane", "FAIL" if bad_len else "PASS",
                   f"{len(states)} matches, {len(bad_len)} outside [85,135]"))
    bad_sum = []
    for s in states:
        total = (float(s["min_leading"]) + float(s["min_level"])
                 + float(s["min_trailing"]))
        if abs(total - float(s["effective_length"])) > 0.5:
            bad_sum.append(s["event_id"])
    report.append(("match_states: state minutes sum to length",
                   "FAIL" if bad_sum else "PASS",
                   f"{len(bad_sum)} mismatches"))
    eff_by_event = {s["event_id"]: float(s["effective_length"]) for s in states}
    apps = read_csv(STAGING / "appearances.csv")
    played = [a for a in apps if a["played"] == "1" and a.get("entry_min") != ""]
    off = []
    for a in played:
        # minutesPlayed is capped at 90/120 while the clock includes stoppage,
        # so allow each match's own stoppage plus a small margin
        eff = eff_by_event.get(a["event_id"], 95)
        reg = 120 if eff > 110 else 90
        allowance = max(eff - reg, 0) + 3
        delta = abs((float(a["exit_min"]) - float(a["entry_min"])) - int(a["minutes"]))
        if delta > allowance:
            off.append(a)
    pct = round(100 * len(off) / len(played), 1) if played else 0
    report.append(("appearances: presence vs minutes", "WARN" if pct > 10 else "PASS",
                   f"{pct}% of {len(played)} presences deviate beyond stoppage allowance"))


def _check_events(report):
    events = read_csv(STAGING / "events.csv")
    if not events:
        return
    n = sum(1 for e in events if e.get("bf_formation"))
    pct = round(100 * n / len(events), 1)
    report.append(("events: formation coverage", "WARN" if pct < 70 else "PASS",
                   f"{pct}% of matches have a starting formation ({n}/{len(events)})"))


def _check_site(report):
    for name in ("team.json", "squad.json", "pool.json", "history.json", "elo.json", "meta.json"):
        path = SITE_DATA / name
        try:
            json.loads(path.read_text(encoding="utf-8"))
            report.append((f"site: {name}", "PASS", "valid json"))
        except Exception as e:
            report.append((f"site: {name}", "FAIL", str(e)[:80]))


def run():
    report = []
    _check_staging_present(report)
    ids = _check_players(report)
    _check_callups(report, ids)
    _check_appearances(report, ids)
    _check_events(report)
    _check_goal_events(report)
    _check_penalties(report)
    _check_captains(report)
    _check_coaches(report)
    _check_youth(report)
    _check_club_form(report)
    _check_timeline(report)
    _check_site(report)
    width = max(len(r[0]) for r in report)
    fails = 0
    for name, level, detail in report:
        if level == "FAIL":
            fails += 1
        print(f"[{level:>4}] {name.ljust(width)}  {detail}")
    print(f"quality: {len(report)} checks, {fails} failures")
    return fails
