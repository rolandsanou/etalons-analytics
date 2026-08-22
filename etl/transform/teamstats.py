from ..config import RAW, SOFA_TEAM_ID, STAGING
from ..parsers.statistics import VALUE_COLS, parse_event_statistics
from ..util import read_json, write_csv

STATS_FIELDS = ["event_id", "date", "period", "side", "opponent", "venue",
                "result", "gf", "ga"] + VALUE_COLS


def run():
    events = read_json(RAW / "sofascore" / "events_index.json")
    rows = []
    for ev in events:
        path = RAW / "sofascore" / "statistics" / f"{ev['event_id']}.json"
        if not path.exists():
            continue
        data = read_json(path)
        if "error" in data or not data.get("statistics"):
            continue
        bf_home = ev["home_id"] == SOFA_TEAM_ID
        gf = ev["home_score"] if bf_home else ev["away_score"]
        ga = ev["away_score"] if bf_home else ev["home_score"]
        base = {
            "event_id": ev["event_id"], "date": ev["date"],
            "opponent": ev["away"] if bf_home else ev["home"],
            "venue": "H" if bf_home else "A",
            "result": "W" if gf > ga else ("D" if gf == ga else "L"),
            "gf": gf, "ga": ga,
        }
        for period, sides in parse_event_statistics(data, bf_home).items():
            for side, values in sides.items():
                if not values:
                    continue
                rows.append({**base, "period": period, "side": side, **values})
    rows.sort(key=lambda r: (r["date"], r["period"], r["side"]))
    write_csv(STAGING / "team_match_stats.csv", rows, STATS_FIELDS)
