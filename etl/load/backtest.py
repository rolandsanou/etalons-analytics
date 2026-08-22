"""Does the Elo model actually predict Burkina Faso's results?

Scored out of sample: the draw rate is calibrated on matches played *before* the
study window, then evaluated on the window itself. Reported against two honest
baselines — the historical base rates, and a flat one-third guess — because a
Brier score alone means nothing without something to beat.
"""

from ..analytics import CAF, calibrate_draw_rate, wdl_from_elo
from ..config import STAGING, STATS_SINCE
from ..util import read_csv

OUTCOMES = ("win", "draw", "loss")
RESULT_KEY = {"W": "win", "D": "draw", "L": "loss"}


def match_sample():
    """(date, elo_diff, result, opponent) per match, using pre-match ratings."""
    timeline = read_csv(STAGING / "elo_timeline.csv")
    by_date = {}
    for m in read_csv(STAGING / "matches.csv"):
        by_date.setdefault(m["date"], []).append(m)
    rows, prev_elo = [], None
    for entry in timeline:
        opp_elo = entry.get("opp_elo")
        candidates = by_date.get(entry["date"], [])
        match = next((m for m in candidates if m["opponent"] == entry["opponent"]),
                     candidates[0] if candidates else None)
        if prev_elo is not None and opp_elo and match:
            rows.append({"date": entry["date"], "opponent": match["opponent"],
                         "diff": prev_elo - float(opp_elo), "result": match["result"],
                         "caf": match["opponent"] in CAF})
        prev_elo = float(entry["elo"])
    return rows


def brier(probs, result):
    """Multiclass Brier score for one match: 0 is perfect, 2 is worst."""
    return sum((probs[o] - (1.0 if RESULT_KEY[result] == o else 0.0)) ** 2
               for o in OUTCOMES)


def base_rates(rows):
    n = len(rows) or 1
    return {o: sum(1 for r in rows if RESULT_KEY[r["result"]] == o) / n
            for o in OUTCOMES}


def calibration_bins(scored, bins=5):
    """Predicted win probability vs how often a win actually happened."""
    out = []
    for i in range(bins):
        lo, hi = i / bins, (i + 1) / bins
        chunk = [s for s in scored
                 if lo <= s["probs"]["win"] < hi or (i == bins - 1 and s["probs"]["win"] == hi)]
        if not chunk:
            continue
        out.append({
            "band": f"{int(lo * 100)}–{int(hi * 100)} %",
            "n": len(chunk),
            "predicted": round(100 * sum(s["probs"]["win"] for s in chunk) / len(chunk), 1),
            "observed": round(100 * sum(1 for s in chunk if s["result"] == "W") / len(chunk), 1),
        })
    return out


def build_backtest():
    rows = match_sample()
    cutoff = STATS_SINCE.isoformat()
    train = [r for r in rows if r["date"] < cutoff and r["caf"]]
    test = [r for r in rows if r["date"] >= cutoff]
    if len(test) < 10 or len(train) < 30:
        return {"available": False}

    peak, width, n_close = calibrate_draw_rate([(r["diff"], r["result"]) for r in train])
    rates = base_rates(train)

    scored = []
    for r in test:
        probs = wdl_from_elo(r["diff"], peak, width)
        scored.append({**r, "probs": probs, "brier": brier(probs, r["result"]),
                       "predicted": max(OUTCOMES, key=lambda o: probs[o])})

    n = len(scored)
    model = sum(s["brier"] for s in scored) / n
    baseline = sum(brier(rates, s["result"]) for s in scored) / n
    uniform = sum(brier({o: 1 / 3 for o in OUTCOMES}, s["result"]) for s in scored) / n
    hits = sum(1 for s in scored if RESULT_KEY[s["result"]] == s["predicted"])

    worst = sorted(scored, key=lambda s: -s["brier"])[:5]
    best = sorted(scored, key=lambda s: s["brier"])[:5]

    def brief(s):
        return {"date": s["date"], "opponent": s["opponent"], "result": s["result"],
                "win": s["probs"]["win"], "draw": s["probs"]["draw"],
                "loss": s["probs"]["loss"], "brier": round(s["brier"], 3)}

    return {
        "available": True,
        "train": {"matches": len(train), "until": cutoff,
                  "draw_peak": peak, "draw_width": width, "n_close": n_close},
        "test": {"matches": n, "from": cutoff},
        "brier": {"model": round(model, 3), "base_rates": round(baseline, 3),
                  "uniform": round(uniform, 3),
                  "skill_vs_base": round(100 * (1 - model / baseline), 1) if baseline else None},
        "accuracy": {"hits": hits, "n": n, "pct": round(100 * hits / n, 1)},
        "calibration": calibration_bins(scored),
        "biggest_surprises": [brief(s) for s in worst],
        "best_calls": [brief(s) for s in best],
    }


# --- registry entry point ---

def backtest_json():
    return build_backtest()
