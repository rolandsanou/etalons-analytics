"""Elo-based expectations against African rivals, with a CAF-calibrated draw rate.

The draw parameters are fitted on real CAF matches rather than assumed, and the
whole block is labelled illustrative: it is a rating model, not a forecast that
accounts for squad availability, venue or form.
"""

from ..config import STAGING, TEAM
from ..elo_model import HOME_ADVANTAGE
from ..analytics import (CAF, calibrate_draw_rate, fit_scoreline,
                         likely_scorelines, wdl_from_elo)
from ..transform.matches import classify_tournament, load_results, team_matches
from ..util import as_float, as_int, norm_name, read_csv

RIVALS = ["Morocco", "Senegal", "Egypt", "Algeria", "Nigeria", "Ivory Coast",
          "Cameroon", "Mali", "Tunisia", "Ghana", "DR Congo", "Cape Verde"]


def caf_samples():
    """(elo_diff, result) for CAF-vs-CAF matches, using pre-match ratings."""
    tl = read_csv(STAGING / "elo_timeline.csv")
    matches = {m["date"]: m for m in read_csv(STAGING / "matches.csv")}
    samples = []
    prev_elo = None
    for row in tl:
        elo = float(row["elo"])
        opp = row.get("opp_elo")
        m = matches.get(row["date"])
        if prev_elo is not None and opp and m and m["opponent"] in CAF:
            samples.append((prev_elo - float(opp), m["result"]))
        prev_elo = elo
    return samples


def build_predictions():
    samples = caf_samples()
    peak, width, n_close = calibrate_draw_rate(samples)
    ranked = {r["team"]: float(r["elo"]) for r in read_csv(STAGING / "elo_rankings.csv")}
    mine = ranked.get(TEAM)
    rows = []
    if mine:
        for opponent in RIVALS:
            if opponent not in ranked:
                continue
            diff = mine - ranked[opponent]
            probs = wdl_from_elo(diff, peak, width)
            rows.append({"opponent": opponent, "opp_elo": round(ranked[opponent]),
                         "diff": round(diff), **probs})
        rows.sort(key=lambda r: -r["win"])
    return {
        "team_elo": round(mine) if mine else None,
        "calibration": {"draw_peak": peak, "draw_width": width,
                        "n_close_matches": n_close, "n_samples": len(samples)},
        "matchups": rows,
        "fixtures": upcoming_fixtures(),
        "outlook": fixture_outlook(mine, ranked, peak, width),
    }


# Half-width, in Elo points, of the rating gap counted as "a match like this".
SIMILAR_BAND = 150
# Below this many comparable matches the base rate is not stated at all.
MIN_SIMILAR = 5


def _venue_swing(venue):
    return {"H": HOME_ADVANTAGE, "A": -HOME_ADVANTAGE}.get(venue, 0)


def head_to_head(matches, opponent):
    """The whole record against this opponent since 1960 — a real count, not a
    model. Returns None when they have never met."""
    played = [m for m in matches
              if norm_name(m["opponent"]) == norm_name(opponent)]
    if not played:
        return None
    return {
        "pld": len(played),
        "w": sum(1 for m in played if m["result"] == "W"),
        "d": sum(1 for m in played if m["result"] == "D"),
        "l": sum(1 for m in played if m["result"] == "L"),
        "gf": sum(as_int(m["gf"]) for m in played),
        "ga": sum(as_int(m["ga"]) for m in played),
        "last": max(m["date"] for m in played),
    }


def _pre_match_gaps(timeline):
    """{date: our pre-match Elo minus the opponent's} for every rated match.

    The rating carried on a row is the one *after* that match, so the pre-match
    figure is the previous row's — the same convention caf_samples uses.
    """
    gaps = {}
    prev = None
    for row in timeline:
        opp = row.get("opp_elo")
        if prev is not None and opp:
            gaps[row["date"]] = prev - as_float(opp)
        prev = as_float(row["elo"])
    return gaps


def against_similar(matches, timeline, target_gap):
    """What the team has actually done in matches as lopsided as this one.

    Not a forecast: a base rate. The band is on the *rating gap*, not on the
    opponent's absolute strength, because that is what makes two matches
    comparable. Banding on the opponent alone would pool a 1980s match where
    Burkina Faso were the underdogs against a 1500-rated side with a 2026 match
    where they are the favourites against the same rating — the same opponent
    strength, opposite situations.

    Withheld entirely when too few comparable matches exist to mean anything.
    """
    gaps = _pre_match_gaps(timeline)
    rows = [m for m in matches
            if m["date"] in gaps and abs(gaps[m["date"]] - target_gap) <= SIMILAR_BAND]
    if len(rows) < MIN_SIMILAR:
        return None
    n = len(rows)
    dates = sorted(m["date"] for m in rows)
    return {
        "n": n,
        "w": sum(1 for m in rows if m["result"] == "W"),
        "d": sum(1 for m in rows if m["result"] == "D"),
        "l": sum(1 for m in rows if m["result"] == "L"),
        "gf_pm": round(sum(as_int(m["gf"]) for m in rows) / n, 2),
        "ga_pm": round(sum(as_int(m["ga"]) for m in rows) / n, 2),
        "clean_sheets": sum(1 for m in rows if as_int(m["ga"]) == 0),
        "failed_to_score": sum(1 for m in rows if as_int(m["gf"]) == 0),
        "band": SIMILAR_BAND,
        "from_year": dates[0][:4],
        "to_year": dates[-1][:4],
    }


def fixture_outlook(mine, ranked, peak, width):
    """One expectation per upcoming fixture, each carrying what it rests on."""
    fixtures = upcoming_fixtures()
    if not fixtures or not mine:
        return []
    matches = read_csv(STAGING / "matches.csv")
    timeline = read_csv(STAGING / "elo_timeline.csv")
    out = []
    for f in fixtures:
        opp_elo = ranked.get(f["opponent"])
        row = {k: f.get(k, "") for k in
               ("date", "date_confirmed", "window_start", "window_end",
                "matchday", "opponent", "venue", "tournament")}
        row["h2h"] = head_to_head(matches, f["opponent"])
        if opp_elo is None:
            # the opponent is not in the rating table: say so rather than guess
            row.update(opp_elo=None, probs=None, similar=None)
            out.append(row)
            continue
        diff = mine - opp_elo + _venue_swing(f.get("venue"))
        probs = wdl_from_elo(diff, peak, width)
        similar = against_similar(matches, timeline, diff)
        row.update(
            opp_elo=round(opp_elo),
            elo_diff=round(diff),
            venue_swing=_venue_swing(f.get("venue")),
            probs=probs,
            xpts=round(3 * probs["win"] + probs["draw"], 2),
            similar=similar,
        )
        # A scoreline needs a goal total, and the only honest source for one is
        # what matches against this calibre of opponent have actually contained.
        # Without that sample there is no scoreline — a rating gap alone cannot
        # say whether a match finishes 1-0 or 3-2.
        if similar:
            total = similar["gf_pm"] + similar["ga_pm"]
            lam_for, lam_against = fit_scoreline(total, probs["win"])
            row["scoreline"] = {
                "goals_for": lam_for,
                "goals_against": lam_against,
                "total": round(total, 2),
                "from_n": similar["n"],
                "scores": likely_scorelines(lam_for, lam_against, top=6),
            }
        out.append(row)
    return out


def upcoming_fixtures():
    """Scheduled matches, when the source has published any."""
    path = STAGING / "fixtures.csv"
    if not path.exists():
        return []
    return read_csv(path)


# --- registry entry point ---

def predictions_json():
    return build_predictions()
