"""Elo-based expectations against African rivals, with a CAF-calibrated draw rate.

The draw parameters are fitted on real CAF matches rather than assumed, and the
whole block is labelled illustrative: it is a rating model, not a forecast that
accounts for squad availability, venue or form.
"""

from ..config import STAGING, TEAM
from ..analytics import CAF, calibrate_draw_rate, wdl_from_elo
from ..transform.matches import classify_tournament, load_results, team_matches
from ..util import read_csv

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
    }


def upcoming_fixtures():
    """Scheduled matches, when the source has published any."""
    path = STAGING / "fixtures.csv"
    if not path.exists():
        return []
    return read_csv(path)


# --- registry entry point ---

def predictions_json():
    return build_predictions()
