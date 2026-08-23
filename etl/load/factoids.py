"""Striking facts, computed rather than written down.

Each row is a template key plus the numbers to fill it, so the sentence lives in
the translation files and the figures come from the marts. Nothing here is typed
by hand: if the team draws once from two goals down, the "never won" fact stops
being true and stops being emitted, instead of sitting on the home page as a
stale boast.

Facts are only emitted when their sample is worth stating. A fact that needs a
caveat carries it in its own template — the point is to be surprising and true,
not surprising.
"""

from ..util import as_float, as_int



def _wdl(detail):
    """'0W-1D-13L' -> (0, 1, 13)."""
    try:
        w, d, l = detail.replace("W", "").replace("D", "").replace("L", "").split("-")
        return int(w), int(d), int(l)
    except (ValueError, AttributeError):
        return None


def build_factoids(team, history, elo, profiles):
    """[{key, vals}] — key selects the sentence, vals fills it."""
    facts = []
    res = {(m["metric"], m["scope"]): m for m in team["resilience"]["metrics"]}
    summary = team["timeline"]["summary"]

    # 1. the deficit cliff — only stated as "never won" while that is true
    deep = res.get(("deficit", "trailed_2plus"))
    if deep and (wdl := _wdl(deep["detail"])):
        w, d, l = wdl
        facts.append({
            "key": "fact_two_down_never_won" if w == 0 else "fact_two_down",
            "vals": {"n": deep["n"], "w": w, "d": d, "l": l, "ppg": deep["value"]},
        })

    # 2. never trailed, for contrast with the above
    clean = res.get(("deficit", "never_trailed"))
    if clean and (wdl := _wdl(clean["detail"])):
        w, d, l = wdl
        facts.append({"key": "fact_never_trailed",
                      "vals": {"n": clean["n"], "w": w, "d": d, "l": l,
                               "ppg": clean["value"]}})

    # 3. how rarely a concession is answered at all
    never = res.get(("reply", "never"))
    if never:
        total = never["n"] + sum(res[k]["n"] for k in
                                (("reply", "within_10"), ("reply", "11_20"),
                                 ("reply", "21_plus")) if k in res)
        facts.append({"key": "fact_no_reply",
                      "vals": {"never": never["n"], "total": total,
                               "answered": total - never["n"],
                               "pct": never["value"]}})

    # 4. the first goal decides more than it should
    sf, cf = summary.get("scored_first"), summary.get("conceded_first")
    if sf and cf:
        facts.append({"key": "fact_first_goal",
                      "vals": {"sf_ppg": sf["ppg"], "cf_ppg": cf["ppg"],
                               "sf_n": sf["n"], "cf_n": cf["n"],
                               "cf_w": cf["w"], "cf_l": cf["l"]}})

    # 5. the quietest quarter-hour, only if the test says it is real
    chi = (summary.get("chi2") or {}).get("gf") or {}
    if chi.get("significant") and chi.get("bin"):
        facts.append({"key": f"fact_bin_{chi['direction']}",
                      "vals": {"bin": chi["bin"].replace("_", "–"),
                               "stat": chi["stat"]}})

    # 6. minutes are trust: the most-used player, in whole matches
    played = [p for p in profiles if as_int(p.get("minutes"))]
    if played:
        top = max(played, key=lambda p: as_int(p["minutes"]))
        mins = as_int(top["minutes"])
        facts.append({"key": "fact_most_minutes",
                      "vals": {"name": top["name"], "min": mins,
                               "matches": round(mins / 90, 1)}})

    # 7. one player carrying the scoring
    scored = [p for p in profiles if as_int(p.get("goals"))]
    if scored:
        top = max(scored, key=lambda p: as_int(p["goals"]))
        total = sum(as_int(p.get("goals")) for p in profiles)
        if total:
            facts.append({"key": "fact_top_scorer_share",
                          "vals": {"name": top["name"], "goals": as_int(top["goals"]),
                                   "total": total,
                                   "pct": round(100 * as_int(top["goals"]) / total)}})

    # 8. formations, with the schedule they faced — never one without the other
    forms = [f for f in team["formations"]
             if f.get("formation") and not f.get("pooled_from")
             and as_int(f.get("matches")) >= 8]
    if len(forms) >= 2:
        best, worst = max(forms, key=lambda f: f["ppg"]), min(forms, key=lambda f: f["ppg"])
        if best["formation"] != worst["formation"]:
            facts.append({"key": "fact_formation",
                          "vals": {"best": best["formation"], "best_ppg": best["ppg"],
                                   "best_elo": round(as_float(best["opp_elo_avg"])),
                                   "worst": worst["formation"], "worst_ppg": worst["ppg"],
                                   "worst_elo": round(as_float(worst["opp_elo_avg"]))}})

    # 9. home that is not at home
    venues = {v["venue_class"]: v for v in history["venues"]["all_time"]}
    if "home_bf" in venues and "home_delocalized" in venues:
        facts.append({"key": "fact_delocalized",
                      "vals": {"home_ppg": venues["home_bf"]["ppg"],
                               "delo_ppg": venues["home_delocalized"]["ppg"],
                               "delo_n": venues["home_delocalized"]["pld"]}})

    # 10. where the team actually stands
    facts.append({"key": "fact_elo_rank",
                  "vals": {"caf": elo["caf_rank"], "n_caf": elo["n_caf"],
                           "world": elo["world_rank"], "pts": round(elo["current"])}})

    # 11. the all-time ledger, which is more balanced than people assume
    at = history["all_time"]
    facts.append({"key": "fact_all_time",
                  "vals": {"pld": at["pld"], "w": at["w"], "d": at["d"],
                           "l": at["l"], "pct": at["win_pct"]}})

    return facts
