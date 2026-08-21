import json

from .config import MARTS, SITE_DATA, STAGING
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
    _check_site(report)
    width = max(len(r[0]) for r in report)
    fails = 0
    for name, level, detail in report:
        if level == "FAIL":
            fails += 1
        print(f"[{level:>4}] {name.ljust(width)}  {detail}")
    print(f"quality: {len(report)} checks, {fails} failures")
    return fails
