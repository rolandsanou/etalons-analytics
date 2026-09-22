"""Who is new in the latest squad, and who is missing from it.

Two questions everyone asks when a list is announced, answered with evidence
rather than with a story. The site cannot know why a selector picked anyone, and
does not pretend to: what it can do is lay out what was true of each player at
the moment of the call — club form, age, what they have done in a Burkina Faso
shirt already — and let the reader draw the conclusion.

The same applies in reverse. A regular left out may be injured, suspended,
rested, or dropped, and none of those is visible in this data. So an absentee is
reported as a fact with his record beside it, never as a verdict.
"""

from ..config import STAGING
from datetime import date

from ..analytics import age_on
from ..util import as_float, as_int, read_csv

# A player counts as an established regular — and so as news when he is absent —
# once he has been on this many matchday sheets in the study window.
REGULAR_SQUADS = 6
# ... and has actually started a reasonable share of them.
REGULAR_STARTS = 3
# A federation names its squad within about this many days of the match. A list
# older than that, relative to the next fixture, is from a previous camp.
ANNOUNCEMENT_DAYS = 30


def _from_earlier_camp(as_of, next_match):
    if not (as_of and next_match):
        return False
    try:
        gap = (date.fromisoformat(next_match) - date.fromisoformat(as_of)).days
    except ValueError:
        return False
    return gap > ANNOUNCEMENT_DAYS


# "recent" is not a squad. It is the Wikipedia section listing players called up
# in the last twelve months *who are not in the current squad*, so it is disjoint
# from it by construction — comparing the two would report every current player
# as a change. It still counts as evidence a player was around recently.
SUPPLEMENTARY = {"recent"}


def _windows():
    """Announced squads, newest first, and the supplementary lists separately."""
    rows = read_csv(STAGING / "callups.csv")
    seen = {}
    for r in rows:
        seen.setdefault(r["window_id"], r.get("window_date", ""))
    squads = sorted((w for w in seen if w not in SUPPLEMENTARY),
                    key=lambda w: seen[w], reverse=True)
    return squads, rows


def _club_line(form):
    """This season's club record, as the case for or against a call."""
    if not form:
        return None
    apps, minutes = as_int(form["apps"]), as_int(form["minutes"])
    return {
        "competition": form.get("tournament", ""),
        "season": form.get("season_year", ""),
        "apps": apps, "minutes": minutes,
        "per_app": round(minutes / apps, 1) if apps else None,
        "rating": as_float(form["rating"]) or None,
        "prev_minutes": as_int(form["prev_minutes"]) if form.get("prev_minutes") else None,
        "prev_season": form.get("prev_season_year", "") or None,
    }


def build_squad_news():
    order, callups = _windows()
    if len(order) < 2:
        return None
    latest, previous = order[0], order[1]

    members = {}
    for r in callups:
        members.setdefault(r["window_id"], {})[r["player_id"]] = r
    now, before = members.get(latest, {}), members.get(previous, {})
    # every window older than the latest, to tell a debutant from a recall
    ever_before = set()
    for w in list(order[1:]) + sorted(SUPPLEMENTARY):
        ever_before |= set(members.get(w, {}))

    profiles = {p["player_id"]: p for p in read_csv(STAGING / "players.csv")}
    form = {f["player_id"]: f for f in read_csv(STAGING / "club_form.csv")}
    apps = read_csv(STAGING / "appearances.csv")

    played = {}
    for a in apps:
        s = played.setdefault(a["player_id"], {"squads": 0, "starts": 0,
                                               "minutes": 0, "last": ""})
        s["squads"] += 1
        s["starts"] += as_int(a["started"]) if a["played"] == "1" else 0
        s["minutes"] += as_int(a["minutes"])
        s["last"] = max(s["last"], a["date"])

    def card(pid, row):
        p = profiles.get(pid, {})
        rec = played.get(pid, {})
        return {
            "player_id": pid,
            "name": row.get("name") or p.get("name", pid),
            "pos": p.get("pos", ""),
            "age": round(age_on(p["dob"], date.today()), 1) if p.get("dob") else None,
            "club": p.get("club_v") or row.get("club_at_time", ""),
            "league": p.get("league_v", ""),
            "status": p.get("status", ""),
            "caps": as_int(p.get("caps")),
            "window_squads": rec.get("squads", 0),
            "window_starts": rec.get("starts", 0),
            "window_minutes": rec.get("minutes", 0),
            "last_seen": rec.get("last", "") or p.get("last_seen", ""),
            "club_form": _club_line(form.get(pid)),
        }

    newcomers, recalls = [], []
    for pid, row in now.items():
        if pid in before:
            continue
        entry = card(pid, row)
        # never in an earlier list and never on a matchday sheet: a new name.
        # in an earlier list, or capped, and back after an absence: a recall.
        if pid not in ever_before and not entry["window_squads"] and not entry["caps"]:
            newcomers.append(entry)
        else:
            recalls.append(entry)

    absent = []
    for pid, rec in played.items():
        if pid in now:
            continue
        if rec["squads"] < REGULAR_SQUADS or rec["starts"] < REGULAR_STARTS:
            continue
        p = profiles.get(pid, {})
        # a player who has retired from international football is not "missing"
        if p.get("status") == "retired_int" or as_int(p.get("career_retired")):
            continue
        absent.append(card(pid, {"name": p.get("name", pid)}))

    for group in (newcomers, recalls):
        group.sort(key=lambda c: (-(c["club_form"] or {}).get("minutes", 0), c["name"]))
    absent.sort(key=lambda c: -c["window_minutes"])

    # The date the source says this list is current to, and whether that falls
    # before the next scheduled match — i.e. whether a newer squad exists that
    # has not reached our sources yet.
    as_of = next((r.get("window_date", "") for r in callups
                  if r["window_id"] == latest), "")
    fixtures = read_csv(STAGING / "fixtures.csv") if (
        STAGING / "fixtures.csv").exists() else []
    next_match = min((f["date"] or f["window_start"] for f in fixtures),
                     default="")

    return {
        "window_id": latest,
        "compared_with": previous,
        "as_of": as_of,
        "next_match": next_match,
        # A squad is announced days before its window, so simply predating the
        # next fixture proves nothing — that is the normal case. What marks a
        # list as belonging to an EARLIER camp is a long gap: beyond
        # ANNOUNCEMENT_DAYS before the next match, a newer list almost certainly
        # exists and has not reached us.
        "predates_next_match": _from_earlier_camp(as_of, next_match),
        "squad": len(now),
        "newcomers": newcomers,
        "recalls": recalls,
        "absent": absent[:8],
        "rule": {"regular_squads": REGULAR_SQUADS, "regular_starts": REGULAR_STARTS},
    }


# --- registry entry point ---

def squad_news_json():
    return build_squad_news()
