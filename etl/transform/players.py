from collections import defaultdict

from ..config import STAGING
from ..extract import wikipedia as wiki_extract
from ..parsers.wikipedia import parse_players
from ..util import canonical_name, load_overrides, norm_name, slugify, write_csv

CALLUP_FIELDS = ["player_id", "window_id", "window_date", "name", "pos", "dob",
                 "caps_at_time", "goals_at_time", "club_at_time",
                 "club_country_at_time", "note", "source"]

PLAYER_FIELDS = ["player_id", "name", "pos", "dob", "club", "club_country",
                 "caps", "goals", "first_window", "last_window", "n_windows",
                 "sofa_id", "source"]


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
                "sofa_id": "",
                "source": "wikipedia",
            }
            for r in group:
                r["player_id"] = pid
    return registry, callups


def write(registry, callups):
    players = sorted(registry.values(), key=lambda p: p["player_id"])
    write_csv(STAGING / "players.csv", players, PLAYER_FIELDS)
    callups.sort(key=lambda c: (c["window_date"], c["name"]))
    write_csv(STAGING / "callups.csv", callups, CALLUP_FIELDS)
