from collections import defaultdict
from datetime import date, datetime, timezone

from ..analytics import player_status
from ..config import RAW, SEED, STAGING
from ..extract import wikipedia as wiki_extract
from ..extract.sofascore import search_match
from ..parsers.wikipedia import parse_players
from ..util import canonical_name, load_overrides, norm_name, read_csv, read_json, slugify, write_csv

CALLUP_FIELDS = ["player_id", "window_id", "window_date", "name", "pos", "dob",
                 "caps_at_time", "goals_at_time", "club_at_time",
                 "club_country_at_time", "note", "source"]

PLAYER_FIELDS = ["player_id", "name", "pos", "dob", "club", "club_country",
                 "caps", "goals", "first_window", "last_window", "n_windows",
                 "last_seen", "status", "club_v", "club_country_v", "league_v",
                 "club_source", "contract_until", "height", "foot",
                 "market_value_eur", "career_retired", "sofa_id", "source"]


def _load_callups():
    overrides = load_overrides()
    callups = []
    for w in wiki_extract.squad_windows():
        html = wiki_extract.raw_path(w).read_text(encoding="utf-8")
        for r in parse_players(html, w["section_id"]):
            callups.append({
                "window_id": w["window_id"],
                "window_date": w["window_date"],
                "name": canonical_name(r["name"], overrides),
                "pos": r["pos"],
                "dob": r["dob"] or "",
                "caps_at_time": r["caps"],
                "goals_at_time": r["goals"],
                "club_at_time": r["club"],
                "club_country_at_time": r["club_country"] or "",
                "note": r["note"] or "",
                "source": "wikipedia:" + w["window_id"],
            })
    return callups


def _split_homonyms(rows):
    dobs = sorted({r["dob"] for r in rows if r["dob"]})
    if len(dobs) <= 1:
        return [rows]
    groups = {d: [r for r in rows if r["dob"] == d] for d in dobs}
    nodob = [r for r in rows if not r["dob"]]
    if nodob:
        largest = max(groups, key=lambda d: len(groups[d]))
        groups[largest].extend(nodob)
    return list(groups.values())


def build():
    callups = _load_callups()
    by_name = defaultdict(list)
    for c in callups:
        by_name[norm_name(c["name"])].append(c)

    registry = {}
    used_ids = set()
    for _, rows in sorted(by_name.items()):
        for group in _split_homonyms(rows):
            group.sort(key=lambda r: r["window_date"])
            latest = group[-1]
            dob = next((r["dob"] for r in group if r["dob"]), "")
            pid = slugify(latest["name"])
            if pid in used_ids:
                pid = f"{pid}-{dob[:4]}" if dob else f"{pid}-2"
            used_ids.add(pid)
            windows = sorted({(r["window_date"], r["window_id"]) for r in group})
            registry[pid] = {
                "player_id": pid,
                "name": latest["name"],
                "pos": latest["pos"],
                "dob": dob,
                "club": latest["club_at_time"],
                "club_country": latest["club_country_at_time"],
                "caps": latest["caps_at_time"],
                "goals": latest["goals_at_time"],
                "first_window": windows[0][1],
                "last_window": windows[-1][1],
                "n_windows": len({w for _, w in windows}),
                "last_seen": windows[-1][0],
                "sofa_id": "",
                "source": "wikipedia",
            }
            for r in group:
                r["player_id"] = pid
    return registry, callups


def parse_profile(player, fetched_at=""):
    """Extract the verified-club fields from a cached /player/{id} payload."""
    team = player.get("team") or {}
    club = team.get("name") or ""
    if team.get("disabled") or club.lower() == "no team":
        club = ""
    league = ((team.get("primaryUniqueTournament") or {}).get("name")
              or (team.get("tournament") or {}).get("name") or "")
    mv_raw = player.get("proposedMarketValueRaw") or {}
    ts = player.get("contractUntilTimestamp")
    contract = (datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
                if ts else "")
    dob_ts = player.get("dateOfBirthTimestamp")
    return {
        "club_v": club,
        "club_country_v": (team.get("country") or {}).get("name", "") if club else "",
        "league_v": league if club else "",
        "career_retired": 1 if player.get("retired") else 0,
        "contract_until": contract,
        "height": player.get("height") or "",
        "foot": player.get("preferredFoot") or "",
        "market_value_eur": mv_raw.get("value", "") if mv_raw.get("currency") == "EUR" else "",
        "dob_v": (datetime.fromtimestamp(dob_ts, tz=timezone.utc).strftime("%Y-%m-%d")
                  if dob_ts else ""),
        "club_source": f"sofascore@{fetched_at[:10]}" if fetched_at else "sofascore",
    }


def enrich(registry, today=None):
    today = today or date.today()
    seed_path = SEED / "sofa_ids.csv"
    if seed_path.exists():
        seed_ids = {r["player_id"]: r["sofa_id"] for r in read_csv(seed_path) if r.get("sofa_id")}
        for pid, sid in seed_ids.items():
            if pid in registry and not registry[pid]["sofa_id"]:
                registry[pid]["sofa_id"] = sid
    for pid, p in registry.items():
        if p["sofa_id"]:
            continue
        cached = RAW / "sofascore" / "search" / f"{pid}.json"
        if cached.exists():
            sid = search_match(read_json(cached).get("data", {}), p["name"])
            if sid:
                p["sofa_id"] = sid
    ret_path = SEED / "int_retirements.csv"
    retired_int = ({r["player_id"] for r in read_csv(ret_path)} if ret_path.exists() else set())
    n_verified = 0
    for pid, p in registry.items():
        prof = RAW / "sofascore" / "players" / f"{p['sofa_id']}.json" if p["sofa_id"] else None
        fields = {"club_v": "", "club_country_v": "", "league_v": "", "career_retired": 0,
                  "contract_until": "", "height": "", "foot": "", "market_value_eur": "",
                  "club_source": "wikipedia" if p.get("club") else ""}
        if prof and prof.exists():
            cached = read_json(prof)
            player = (cached.get("data") or {}).get("player")
            if player:
                fields = parse_profile(player, cached.get("fetched_at", ""))
                if not p.get("dob") and fields["dob_v"]:
                    p["dob"] = fields["dob_v"]
                if fields["club_v"]:
                    n_verified += 1
        fields.pop("dob_v", None)
        p.update(fields)
        p["status"] = player_status(pid in retired_int, p.get("career_retired"),
                                    p.get("last_seen", ""), today)
    print(f"enriched: {n_verified} players with a verified club")


def write(registry, callups):
    players = sorted(registry.values(), key=lambda p: p["player_id"])
    write_csv(STAGING / "players.csv", players, PLAYER_FIELDS)
    callups.sort(key=lambda c: (c["window_date"], c["name"]))
    write_csv(STAGING / "callups.csv", callups, CALLUP_FIELDS)
