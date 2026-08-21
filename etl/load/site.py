from datetime import date, datetime

import pandas as pd

from .. import analytics
from ..config import RAW, SITE_DATA, STAGING, STATS_SINCE, TEAM, WIKI_TEAM_URL
from ..extract.wikipedia import squad_windows
from ..parsers.wikipedia import parse_afcon_record, parse_as_of, parse_leaders
from ..transform import matches as matches_mod
from ..util import read_csv, write_json
from .marts import build_profiles


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


def build_squad_json(today):
    callups = read_csv(STAGING / "callups.csv")
    current = [_callup_to_player(c) for c in callups if c["window_id"] == "current"]
    recent = [_callup_to_player(c) for c in callups if c["window_id"] == "recent"]
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


def build_history_json():
    m = matches_mod.load_staged()
    hist = matches_mod.history_stats(m)
    team_html = (RAW / "wikipedia" / "team_page.html").read_text(encoding="utf-8")
    capped, scorers = parse_leaders(team_html)
    return {
        **hist,
        "most_capped": capped,
        "top_scorers": scorers,
        "afcon_record": parse_afcon_record(team_html),
    }


def build_elo_json():
    tl = pd.read_csv(STAGING / "elo_timeline.csv")
    timeline = [{"date": r.date, "elo": float(r.elo), "opponent": r.opponent}
                for r in tl.itertuples()]
    rk = pd.read_csv(STAGING / "elo_rankings.csv")
    ranked = [{"rank": int(r.rank), "team": r.team, "elo": float(r.elo)}
              for r in rk.itertuples()]
    return analytics.elo_summary(timeline, ranked)


def run():
    today = date.today()
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
