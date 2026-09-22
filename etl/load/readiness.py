"""Is the called-up squad actually playing club football right now?

Raw club minutes cannot be compared across this squad: some play a season that
started six weeks ago, some are mid-season, some are in calendar-year leagues
two thirds of the way through. Minutes *per appearance* is comparable, and it
answers the question that matters before an international window — is this
player starting for his club, or coming off the bench?

There is no composite score here. The band is one stated rule over one measure,
and every component is published beside it so the rule can be argued with.
"""

from .common import latest_squad_window
from ..util import as_int, read_csv
from ..config import STAGING

# A player averaging at least this many minutes per club appearance is starting
# rather than being used off the bench. Two thirds of a match.
STARTER_MINUTES = 60
# A player needs this many club appearances before the average means anything.
MIN_APPS = 3
# Share of the squad starting regularly, banded. Stated on the page.
STRONG, NEUTRAL = 0.65, 0.45


def _band(share):
    if share >= STRONG:
        return "strong"
    return "neutral" if share >= NEUTRAL else "weak"


def build_readiness(window_id=None):
    """Club-match sharpness of the latest called-up squad."""
    rows = read_csv(STAGING / "callups.csv")
    window_id = window_id or latest_squad_window(rows)
    callups = [c for c in rows if c["window_id"] == window_id]
    if not callups:
        return None
    form = {r["player_id"]: r for r in read_csv(STAGING / "club_form.csv")}
    profiles = {r["player_id"]: r for r in read_csv(STAGING / "players.csv")}

    rated, players = [], []
    for c in callups:
        f = form.get(c["player_id"])
        apps, minutes = as_int(f["apps"]) if f else 0, as_int(f["minutes"]) if f else 0
        per_app = round(minutes / apps, 1) if apps else None
        counts = bool(f) and apps >= MIN_APPS
        row = {
            "player_id": c["player_id"], "name": c["name"],
            "pos": profiles.get(c["player_id"], {}).get("pos", ""),
            "club": (f or {}).get("tournament", ""),
            "season": (f or {}).get("season_year", ""),
            "apps": apps, "minutes": minutes, "per_app": per_app,
            "counts": counts,
            "starting": bool(counts and per_app and per_app >= STARTER_MINUTES),
        }
        players.append(row)
        if counts:
            rated.append(row)

    players.sort(key=lambda r: (-(r["per_app"] or -1), r["name"]))
    starting = sum(1 for r in rated if r["starting"])
    share = starting / len(rated) if rated else 0.0
    return {
        "window_id": window_id,
        "squad": len(callups),
        # the denominator is the squad we can actually judge, stated plainly
        "rated": len(rated),
        "no_club_data": sum(1 for r in players if not r["counts"]),
        "starting": starting,
        "share": round(share, 3),
        "band": _band(share) if rated else None,
        "median_per_app": (sorted(r["per_app"] for r in rated)[len(rated) // 2]
                           if rated else None),
        "rule": {"starter_minutes": STARTER_MINUTES, "min_apps": MIN_APPS,
                 "strong": STRONG, "neutral": NEUTRAL},
        "players": players,
    }


# --- registry entry point ---

def readiness_json():
    return build_readiness()
