from collections import defaultdict
from datetime import date

from ..analytics import age_on
from ..config import MARTS, STAGING
from ..util import read_csv, write_csv

COHORT_FIELDS = ["window_id", "level", "window_date", "squad_size", "linked",
                 "with_senior_apps", "median_days_to_debut"]


def build_pipeline(today=None):
    today = today or date.today()
    youth = read_csv(STAGING / "youth_callups.csv")
    apps = read_csv(STAGING / "appearances.csv")
    first_app = {}
    for a in apps:
        pid = a["player_id"]
        if pid and (pid not in first_app or a["date"] < first_app[pid]):
            first_app[pid] = a["date"]

    cohorts = defaultdict(list)
    for y in youth:
        cohorts[y["window_id"]].append(y)

    rows, prospects = [], []
    for wid, members in sorted(cohorts.items(), key=lambda kv: kv[1][0]["window_date"]):
        linked = [m for m in members if m["senior_player_id"]]
        debuts = []
        with_apps = 0
        for m in linked:
            d = first_app.get(m["senior_player_id"])
            if d:
                with_apps += 1
                if d >= m["window_date"]:
                    delta = (date.fromisoformat(d) - date.fromisoformat(m["window_date"])).days
                    debuts.append(delta)
        debuts.sort()
        rows.append({
            "window_id": wid, "level": members[0]["level"],
            "window_date": members[0]["window_date"],
            "squad_size": len(members), "linked": len(linked),
            "with_senior_apps": with_apps,
            "median_days_to_debut": debuts[len(debuts) // 2] if debuts else "",
        })
        for m in members:
            if not m["senior_player_id"] and m["dob"]:
                age = age_on(m["dob"], today)
                if age <= 21:
                    prospects.append({"name": m["name"], "pos": m["pos"], "age": age,
                                      "window_id": wid, "level": m["level"],
                                      "club": m["club_at_time"]})
    prospects.sort(key=lambda p: p["age"])
    return rows, prospects


def run():
    rows, _ = build_pipeline()
    write_csv(MARTS / "pipeline.csv", rows, COHORT_FIELDS)
    return rows
