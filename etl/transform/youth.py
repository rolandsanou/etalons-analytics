from ..config import STAGING
from ..extract import wikipedia as wiki_extract
from ..parsers.wikipedia import parse_players
from ..util import canonical_name, load_overrides, norm_name, write_csv

YOUTH_FIELDS = ["window_id", "level", "window_date", "name", "pos", "dob",
                "club_at_time", "club_country_at_time", "senior_player_id",
                "link_quality"]


def link_youth(name, dob, senior_by_name):
    """(player_id, quality): exact = name+dob agree, name_only = senior dob missing."""
    candidates = senior_by_name.get(norm_name(name), [])
    for p in candidates:
        if dob and p["dob"] and p["dob"] == dob:
            return p["player_id"], "exact"
    if len(candidates) == 1 and not candidates[0]["dob"]:
        return candidates[0]["player_id"], "name_only"
    return "", ""


def run(registry):
    overrides = load_overrides()
    senior_by_name = {}
    for p in registry.values():
        senior_by_name.setdefault(norm_name(p["name"]), []).append(p)

    rows = []
    for w in wiki_extract.youth_windows():
        path = wiki_extract.raw_path(w)
        if not path.exists():
            continue
        html = path.read_text(encoding="utf-8")
        for r in parse_players(html, w["section_id"]):
            name = canonical_name(r["name"], overrides)
            pid, quality = link_youth(name, r["dob"] or "", senior_by_name)
            rows.append({
                "window_id": w["window_id"], "level": w["level"],
                "window_date": w["window_date"],
                "name": name, "pos": r["pos"], "dob": r["dob"] or "",
                "club_at_time": r["club"],
                "club_country_at_time": r["club_country"] or "",
                "senior_player_id": pid, "link_quality": quality,
            })
    rows.sort(key=lambda r: (r["window_date"], r["name"]))
    write_csv(STAGING / "youth_callups.csv", rows, YOUTH_FIELDS)
