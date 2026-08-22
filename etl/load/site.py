from datetime import date, datetime

import pandas as pd

from .. import analytics
from ..config import RAW, SITE_DATA, STAGING, STATS_SINCE, TEAM, WIKI_TEAM_URL
from ..extract.wikipedia import squad_windows
from ..parsers.wikipedia import parse_afcon_record, parse_as_of, parse_leaders
from ..transform import matches as matches_mod
from ..util import read_csv, write_json
from .marts import build_formations, build_profiles


def _callup_to_player(c):
    return {
        "player_id": c["player_id"],
        "name": c["name"],
        "pos": c["pos"],
        "dob": c["dob"] or None,
        "caps": int(c["caps_at_time"] or 0),
        "goals": int(c["goals_at_time"] or 0),
        "club": c["club_at_time"],
        "club_country": c["club_country_at_time"] or None,
    }


def _overlay_verified(players):
    registry = {r["player_id"]: r for r in read_csv(STAGING / "players.csv")}
    for p in players:
        r = registry.get(p["player_id"])
        if r and r.get("club_v"):
            p["club"] = r["club_v"]
            p["club_country"] = r["club_country_v"] or p["club_country"]
            p["league"] = r["league_v"]
            p["club_verified"] = True
        else:
            p["club_verified"] = False
    return players


def build_squad_json(today):
    callups = read_csv(STAGING / "callups.csv")
    current = _overlay_verified([_callup_to_player(c) for c in callups if c["window_id"] == "current"])
    recent = _overlay_verified([_callup_to_player(c) for c in callups if c["window_id"] == "recent"])
    squad = analytics.enrich_players(current, today)
    pool = analytics.enrich_players(recent, today)
    seen = {p["name"] for p in squad}
    team_html = (RAW / "wikipedia" / "team_page.html").read_text(encoding="utf-8")
    return {
        "as_of": parse_as_of(team_html),
        "players": squad,
        "callups": pool,
        "stats": analytics.squad_stats(squad),
        "core_generation": analytics.core_generation(
            squad + [p for p in pool if p["name"] not in seen]),
    }


def build_pool_json(today):
    from .performance import build_bench, build_importance
    profiles = build_profiles(today)
    events = read_csv(STAGING / "events.csv")
    players = read_csv(STAGING / "players.csv")
    n_detailed = sum(1 for e in events if int(e["n_with_stats"] or 0) > 0)
    windows = [{"window_id": w["window_id"], "label_fr": w["label_fr"],
                "label_en": w["label_en"], "date": w["window_date"]}
               for w in squad_windows()]
    return {
        "since": STATS_SINCE.isoformat(),
        "windows": windows,
        "n_players": len(profiles),
        "coverage": {
            "events": len(events),
            "events_with_stats": n_detailed,
        },
        "profiles": profiles,
        "importance": build_importance(players),
        "bench": build_bench(players),
    }


def build_shootouts_json():
    rows = read_csv(STAGING / "shootouts_alltime.csv")
    return {
        "w": sum(1 for r in rows if r["winner_is_bf"] == "1"),
        "l": sum(1 for r in rows if r["winner_is_bf"] != "1"),
        "matches": rows,
    }


def build_penalties_json():
    pens = read_csv(STAGING / "penalties.csv")
    apps = read_csv(STAGING / "appearances.csv")
    ingame = [p for p in pens if p["kind"] == "ingame"]
    shootout = [p for p in pens if p["kind"] == "shootout"]

    def _split(rows):
        return {"scored": sum(1 for r in rows if r["outcome"] == "scored"),
                "missed": sum(1 for r in rows if r["outcome"] != "scored")}

    takers = {}
    for p in ingame:
        if p["is_bf"] != "1":
            continue
        key = p["player_id"] or p["name"]
        tk = takers.setdefault(key, {"name": p["name"], "player_id": p["player_id"],
                                     "scored": 0, "missed": 0})
        tk["scored" if p["outcome"] == "scored" else "missed"] += 1
    takers = sorted(takers.values(), key=lambda x: (-x["scored"], x["missed"]))

    return {
        "ingame_for": _split([p for p in ingame if p["is_bf"] == "1"]),
        "ingame_against": _split([p for p in ingame if p["is_bf"] != "1"]),
        "takers": takers,
        "shootout_for": _split([p for p in shootout if p["is_bf"] == "1"]),
        "shootout_against": _split([p for p in shootout if p["is_bf"] != "1"]),
        "gk_shootout_saves": sum(int(a["shootout_saves"] or 0) for a in apps),
    }


def build_history_json():
    m = matches_mod.load_staged()
    hist = matches_mod.history_stats(m)
    team_html = (RAW / "wikipedia" / "team_page.html").read_text(encoding="utf-8")
    capped, scorers = parse_leaders(team_html)
    from .coaches import build_coach_eras
    return {
        **hist,
        "most_capped": capped,
        "top_scorers": scorers,
        "afcon_record": parse_afcon_record(team_html),
        "shootouts": build_shootouts_json(),
        "coaches": build_coach_eras(),
    }


def build_elo_json():
    tl = pd.read_csv(STAGING / "elo_timeline.csv")
    timeline = [{"date": r.date, "elo": float(r.elo), "opponent": r.opponent}
                for r in tl.itertuples()]
    rk = pd.read_csv(STAGING / "elo_rankings.csv")
    ranked = [{"rank": int(r.rank), "team": r.team, "elo": float(r.elo)}
              for r in rk.itertuples()]
    return analytics.elo_summary(timeline, ranked)


def build_team_json():
    from .performance import build_team_timeline
    events = read_csv(STAGING / "events.csv")
    with_formation = sum(1 for e in events if e.get("bf_formation"))
    bins, summary = build_team_timeline()
    from .leadership import build_captains, build_goalkeepers
    from .performance import _f
    apps = read_csv(STAGING / "appearances.csv")
    eff = {s["event_id"]: _f(s["effective_length"], 95)
           for s in read_csv(STAGING / "match_states.csv")}
    return {
        "captains": build_captains(apps),
        "goalkeepers": build_goalkeepers(apps, eff),
        "formations": build_formations(),
        "timeline": {"bins": bins, "summary": summary},
        "penalties": build_penalties_json(),
        "coverage": {"events": len(events), "with_formation": with_formation},
    }


def run():
    today = date.today()
    write_json(SITE_DATA / "team.json", build_team_json())
    write_json(SITE_DATA / "squad.json", build_squad_json(today))
    write_json(SITE_DATA / "pool.json", build_pool_json(today))
    write_json(SITE_DATA / "history.json", build_history_json())
    write_json(SITE_DATA / "elo.json", build_elo_json())
    write_json(SITE_DATA / "meta.json", {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "team": TEAM,
        "stats_since": STATS_SINCE.isoformat(),
        "sources": {
            "squads_callups": WIKI_TEAM_URL,
            "results": "https://github.com/martj42/international_results",
            "player_match_stats": "Sofascore (unofficial API, non-commercial attribution)",
        },
    })
