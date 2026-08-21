from datetime import date, datetime, timezone
from urllib.parse import quote

from ..config import (PROFILE_MAX_AGE_DAYS, RAW, SEED, SOFA_BASE, SOFA_TEAM_ID,
                      STAGING, STATS_SINCE)
from ..http import get_sofa_json
from ..util import norm_name, read_csv, read_json, write_json

OUT = RAW / "sofascore"
LINEUPS = OUT / "lineups"
PLAYERS_DIR = OUT / "players"
SEARCH_DIR = OUT / "search"


def _event_row(e):
    ts = e["startTimestamp"]
    return {
        "event_id": e["id"],
        "date": datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d"),
        "ts": ts,
        "tournament": e["tournament"]["name"],
        "home_id": e["homeTeam"]["id"],
        "home": e["homeTeam"]["name"],
        "away_id": e["awayTeam"]["id"],
        "away": e["awayTeam"]["name"],
        "home_score": e.get("homeScore", {}).get("current"),
        "away_score": e.get("awayScore", {}).get("current"),
        "status": e.get("status", {}).get("type"),
    }


def fetch_events_index(force=False):
    index_path = OUT / "events_index.json"
    if index_path.exists() and not force:
        return read_json(index_path)
    since_ts = int(datetime(STATS_SINCE.year, STATS_SINCE.month, STATS_SINCE.day,
                            tzinfo=timezone.utc).timestamp())
    rows = []
    page = 0
    while True:
        data = get_sofa_json(f"{SOFA_BASE}/team/{SOFA_TEAM_ID}/events/last/{page}")
        events = data.get("events", [])
        if not events:
            break
        rows.extend(_event_row(e) for e in events)
        oldest = min(e["startTimestamp"] for e in events)
        if oldest < since_ts or not data.get("hasNextPage"):
            break
        page += 1
    rows = [r for r in rows
            if r["ts"] >= since_ts and r["status"] == "finished"
            and r["home_score"] is not None]
    rows.sort(key=lambda r: r["ts"])
    write_json(index_path, rows)
    return rows


def search_match(search_data, name):
    """Auto-accept only an exact normalized-name match on a Burkinabè player."""
    for r in search_data.get("results", []):
        if r.get("type") != "player":
            continue
        ent = r.get("entity", {})
        country = (ent.get("country") or {}).get("alpha2")
        if norm_name(ent.get("name", "")) == norm_name(name) and country == "BF":
            return ent.get("id")
    return None


def _profile_targets():
    ids, unlinked = set(), []
    players_path = STAGING / "players.csv"
    if players_path.exists():
        for r in read_csv(players_path):
            if r.get("sofa_id"):
                ids.add(str(r["sofa_id"]))
            else:
                unlinked.append((r["player_id"], r["name"]))
    seed_path = SEED / "sofa_ids.csv"
    if seed_path.exists():
        for r in read_csv(seed_path):
            if r.get("sofa_id"):
                ids.add(str(r["sofa_id"]))
    return ids, unlinked


def resolve_sofa_ids(unlinked, force=False):
    SEARCH_DIR.mkdir(parents=True, exist_ok=True)
    accepted = set()
    for pid, name in unlinked:
        dest = SEARCH_DIR / f"{pid}.json"
        if not dest.exists() or force:
            try:
                data = get_sofa_json(f"{SOFA_BASE}/search/all?q={quote(name)}")
            except Exception as e:
                data = {"error": str(e)}
            write_json(dest, {"fetched_at": datetime.now().isoformat(timespec="seconds"),
                              "data": data})
        cached = read_json(dest)
        sid = search_match(cached.get("data", {}), name)
        if sid:
            accepted.add(str(sid))
    return accepted


def fetch_player_profiles(ids, force=False):
    PLAYERS_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today()
    fetched = 0
    for sid in sorted(ids):
        dest = PLAYERS_DIR / f"{sid}.json"
        if dest.exists() and not force:
            stamp = read_json(dest).get("fetched_at", "")[:10]
            try:
                if (today - date.fromisoformat(stamp)).days <= PROFILE_MAX_AGE_DAYS:
                    continue
            except ValueError:
                pass
        try:
            data = get_sofa_json(f"{SOFA_BASE}/player/{sid}")
        except Exception as e:
            data = {"error": str(e)}
        write_json(dest, {"fetched_at": datetime.now().isoformat(timespec="seconds"),
                          "data": data})
        fetched += 1
    return fetched


def run(force=False):
    OUT.mkdir(parents=True, exist_ok=True)
    LINEUPS.mkdir(parents=True, exist_ok=True)
    index = fetch_events_index(force=force)
    fetched = 0
    for ev in index:
        dest = LINEUPS / f"{ev['event_id']}.json"
        if dest.exists():
            continue
        try:
            data = get_sofa_json(f"{SOFA_BASE}/event/{ev['event_id']}/lineups")
        except Exception as e:
            data = {"error": str(e)}
        write_json(dest, data)
        fetched += 1
    ids, unlinked = _profile_targets()
    ids |= resolve_sofa_ids(unlinked, force=force)
    n_profiles = fetch_player_profiles(ids, force=False)
    print(f"sofascore: {len(index)} events in window, {fetched} lineups fetched, "
          f"{n_profiles} player profiles fetched/refreshed, "
          f"{len(unlinked)} players searched")
