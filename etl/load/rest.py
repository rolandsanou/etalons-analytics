"""Does the gap between matches show up in the results?

Rest is the number of days since Burkina Faso's previous match. Tournament
football compresses fixtures to three or four days, so the short-rest band is
mostly AFCON and CHAN matches against stronger opposition — which is why the
average opponent Elo is reported beside every band. Read it as context, not as
a fatigue effect.
"""

from collections import defaultdict
from datetime import date

from ..config import MARTS, STAGING
from ..util import read_csv, write_csv
from .common import as_float, as_int, record
from .formations import opp_elo_lookup

REST_FIELDS = ["band", "matches", "w", "d", "l", "ppg", "gf_pm", "ga_pm",
               "opp_elo_avg", "gated"]

BANDS = [(0, 3, "0_3"), (4, 5, "4_5"), (6, 9, "6_9"), (10, 10_000, "10_plus")]
MIN_MATCHES = 5


def band(days):
    for lo, hi, label in BANDS:
        if lo <= days <= hi:
            return label
    return "10_plus"


def rest_days(matches):
    """(match, days since the previous match) in chronological order."""
    ordered = sorted(matches, key=lambda m: m["date"])
    out = []
    previous = None
    for m in ordered:
        current = date.fromisoformat(m["date"])
        out.append((m, (current - previous).days if previous else None))
        previous = current
    return out


def build_rest():
    matches = [m for m in read_csv(STAGING / "matches.csv")
               if m["date"] >= "2022-01-01"]
    elo = opp_elo_lookup()
    grouped = defaultdict(list)
    for m, days in rest_days(matches):
        if days is None or days > 400:      # skip the first match of the window
            continue
        grouped[band(days)].append((m, days))

    rows = []
    for _, _, label in BANDS:
        entries = grouped.get(label, [])
        if not entries:
            continue
        results = [m["result"] for m, _ in entries]
        rec = record(results)
        elos = [elo(m["date"]) for m, _ in entries]
        elos = [e for e in elos if e]
        rows.append({
            "band": label, "matches": rec["n"], "w": rec["w"], "d": rec["d"],
            "l": rec["l"], "ppg": rec["ppg"],
            "gf_pm": round(sum(as_int(m["gf"]) for m, _ in entries) / rec["n"], 2),
            "ga_pm": round(sum(as_int(m["ga"]) for m, _ in entries) / rec["n"], 2),
            "opp_elo_avg": round(sum(elos) / len(elos)) if elos else None,
            "gated": int(rec["n"] >= MIN_MATCHES),
        })
    return rows


def run():
    rows = build_rest()
    write_csv(MARTS / "rest_days.csv", rows, REST_FIELDS)
    return rows


# --- registry entry point ---

def rest_json():
    return build_rest()
