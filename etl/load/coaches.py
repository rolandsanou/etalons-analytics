import pandas as pd

from ..config import MARTS, STAGING
from ..util import write_csv

ERA_FIELDS = ["coach", "tenure_start", "first_match", "last_match", "matches",
              "w", "d", "l", "ppg", "gf_pm", "ga_pm", "elo_first", "elo_last",
              "elo_delta", "pooled"]

MIN_MATCHES = 10


def build_coach_eras():
    m = pd.read_csv(STAGING / "matches.csv", dtype={"coach": str, "coach_since": str})
    m = m.fillna({"coach": "", "coach_since": ""})
    tl = pd.read_csv(STAGING / "elo_timeline.csv")
    elo_by_date = dict(zip(tl.date, tl.elo))

    def agg(g, coach, tenure_start, pooled):
        n = len(g)
        w = int((g.result == "W").sum())
        d = int((g.result == "D").sum())
        l = int((g.result == "L").sum())
        dates = sorted(g.date)
        return {
            "coach": coach, "tenure_start": tenure_start,
            "first_match": dates[0], "last_match": dates[-1],
            "matches": n, "w": w, "d": d, "l": l,
            "ppg": round((3 * w + d) / n, 2),
            "gf_pm": round(g.gf.sum() / n, 2), "ga_pm": round(g.ga.sum() / n, 2),
            "elo_first": elo_by_date.get(dates[0], ""),
            "elo_last": elo_by_date.get(dates[-1], ""),
            "elo_delta": (round(elo_by_date[dates[-1]] - elo_by_date[dates[0]], 0)
                          if dates[0] in elo_by_date and dates[-1] in elo_by_date else ""),
            "pooled": int(pooled),
        }

    known = m[m.coach != ""]
    eras, small = [], []
    for (coach, since), g in known.groupby(["coach", "coach_since"]):
        if len(g) >= MIN_MATCHES:
            eras.append(agg(g, coach, since, False))
        else:
            small.append(g)
    eras.sort(key=lambda r: r["first_match"], reverse=True)
    if small:
        pooled = pd.concat(small)
        eras.append(agg(pooled, "others", "", True))
    return eras


def run():
    eras = build_coach_eras()
    write_csv(MARTS / "coach_eras.csv", eras, ERA_FIELDS)
    return eras
