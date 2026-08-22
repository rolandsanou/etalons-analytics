"""Record by starting formation, and the shared opponent-Elo lookup."""

from datetime import date, timedelta

from ..analytics import formation_table
from ..config import STAGING
from ..util import read_csv

FORMATION_FIELDS = ["formation", "matches", "w", "d", "l", "gf", "ga", "gf_pm", "ga_pm",
                    "ppg", "opp_elo_avg", "n_elo", "comp_afcon", "comp_afcon_qual",
                    "comp_wc_qual", "comp_friendly", "comp_other", "pooled_from"]


def opp_elo_lookup():
    """date -> opponent pre-match Elo, tolerating a one-day source discrepancy."""
    tl = read_csv(STAGING / "elo_timeline.csv")
    by_date = {r["date"]: float(r["opp_elo"]) for r in tl if r.get("opp_elo")}

    def lookup(d):
        if d in by_date:
            return by_date[d]
        base = date.fromisoformat(d)
        for delta in (1, -1):
            k = (base + timedelta(days=delta)).isoformat()
            if k in by_date:
                return by_date[k]
        return None
    return lookup


def build_formations():
    events = read_csv(STAGING / "events.csv")
    rows = formation_table(events, opp_elo_lookup())
    out = []
    for r in rows:
        flat = {k: v for k, v in r.items() if k not in ("comps", "pooled_from")}
        for c in ("afcon", "afcon_qual", "wc_qual", "friendly", "other"):
            flat[f"comp_{c}"] = r["comps"].get(c, 0)
        flat["pooled_from"] = ";".join(r.get("pooled_from", []))
        out.append(flat)
    return out
