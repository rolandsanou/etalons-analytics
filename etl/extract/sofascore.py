from datetime import datetime, timezone

from ..config import RAW, SOFA_BASE, SOFA_TEAM_ID, STATS_SINCE
from ..http import get_sofa_json
from ..util import read_json, write_json

OUT = RAW / "sofascore"
LINEUPS = OUT / "lineups"


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
    print(f"sofascore: {len(index)} events in window, {fetched} lineups fetched")
