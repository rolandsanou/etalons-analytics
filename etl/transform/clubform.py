from ..config import RAW, STAGING
from ..util import read_json, write_csv

# Two seasons per player: the latest one the source has, and the most recent
# completed one before it. Club leagues restart on different dates, so from
# August the latest season can be a fortnight old for one player and complete for
# another — the earlier season is the settled figure both can be read against. It
# carries its own competition name because a transfer moves the baseline to the
# player's previous league.
CLUB_FORM_FIELDS = ["player_id", "sofa_id", "tournament", "season_year",
                    "apps", "starts", "minutes", "rating",
                    "prev_tournament", "prev_season_year", "prev_apps",
                    "prev_starts", "prev_minutes", "prev_rating", "as_of"]

BLANK = {"apps": "", "starts": "", "minutes": "", "rating": ""}


def _stats(st):
    return {
        "apps": st.get("appearances", 0),
        "starts": st.get("matchesStarted", 0),
        "minutes": st.get("minutesPlayed", 0),
        "rating": round(st["rating"], 2) if st.get("rating") else "",
    }


def run(registry):
    sofa2pid = {str(p["sofa_id"]): pid for pid, p in registry.items() if p["sofa_id"]}
    folder = RAW / "sofascore" / "club_form"
    rows = []
    if folder.exists():
        for f in sorted(folder.glob("*.json")):
            data = read_json(f)
            pick = data.get("pick")
            pid = sofa2pid.get(f.stem, "")
            if not pick or not pid:
                continue
            prev_pick = data.get("pick_prev") or {}
            prev_st = data.get("statistics_prev")
            # blank, not zero, when there is no earlier season: a player in their
            # first campaign at this level has no baseline, and "0" would read as
            # a season spent unused
            prev = _stats(prev_st) if prev_st else dict(BLANK)
            rows.append({
                "player_id": pid, "sofa_id": f.stem,
                "tournament": pick["tournament"], "season_year": pick["year"],
                **_stats(data.get("statistics") or {}),
                "prev_tournament": prev_pick.get("tournament", "") if prev_st else "",
                "prev_season_year": prev_pick.get("year", "") if prev_st else "",
                "prev_apps": prev["apps"], "prev_starts": prev["starts"],
                "prev_minutes": prev["minutes"], "prev_rating": prev["rating"],
                "as_of": data.get("fetched_at", "")[:10],
            })
    rows.sort(key=lambda r: r["player_id"])
    write_csv(STAGING / "club_form.csv", rows, CLUB_FORM_FIELDS)
