from datetime import date, datetime

import pandas as pd

from .. import analytics
from ..config import SEED, SITE_DATA, STAGING, STATS_SINCE, TEAM, WIKI_TEAM_URL
from ..transform import matches as matches_mod
from ..util import read_csv, read_json, write_json
from .formations import build_formations
from .profiles import build_profiles
from .registry import site_fragments
from .style import full_feed_events


def reference():
    """Wikipedia-derived reference tables, staged by transform/records.py."""
    return read_json(STAGING / "reference.json")


def squad_windows():
    return read_csv(SEED / "wiki_squads.csv")


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
    return {
        "as_of": reference()["as_of"],
        "players": squad,
        "callups": pool,
        "stats": analytics.squad_stats(squad),
        "core_generation": analytics.core_generation(
            squad + [p for p in pool if p["name"] not in seen]),
    }


def build_pool_json(today):
    profiles = build_profiles(today)
    events = read_csv(STAGING / "events.csv")
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
    ref = reference()
    return {
        **hist,
        "most_capped": ref["most_capped"],
        "top_scorers": ref["top_scorers"],
        "afcon_record": ref["afcon_record"],
        "shootouts": build_shootouts_json(),
    }


def build_elo_json():
    tl = pd.read_csv(STAGING / "elo_timeline.csv")
    timeline = [{"date": r.date, "elo": float(r.elo), "opponent": r.opponent}
                for r in tl.itertuples()]
    rk = pd.read_csv(STAGING / "elo_rankings.csv")
    ranked = [{"rank": int(r.rank), "team": r.team, "elo": float(r.elo)}
              for r in rk.itertuples()]
    return analytics.elo_summary(timeline, ranked)


def _stats_coverage():
    path = STAGING / "team_match_stats.csv"
    if not path.exists():
        return {"with_stats": 0, "with_full_stats": 0}
    rows = read_csv(path)
    return {"with_stats": len({r["event_id"] for r in rows}),
            "with_full_stats": len(full_feed_events(rows))}


def build_team_json():
    events = read_csv(STAGING / "events.csv")
    return {
        "formations": build_formations(),
        "penalties": build_penalties_json(),
        "coverage": {
            "events": len(events),
            "with_formation": sum(1 for e in events if e.get("bf_formation")),
            **_stats_coverage(),
        },
    }


def _with_fragments(document, base):
    """Merge every registry-declared fragment for this document."""
    for key, builder in site_fragments(document).items():
        base[key] = builder()
    return base


def run():
    today = date.today()
    write_json(SITE_DATA / "team.json", _with_fragments("team", build_team_json()))
    write_json(SITE_DATA / "squad.json", _with_fragments("squad", build_squad_json(today)))
    write_json(SITE_DATA / "pool.json", _with_fragments("pool", build_pool_json(today)))
    write_json(SITE_DATA / "history.json",
               _with_fragments("history", build_history_json()))
    write_json(SITE_DATA / "elo.json", _with_fragments("elo", build_elo_json()))
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
