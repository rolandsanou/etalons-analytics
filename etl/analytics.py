from datetime import date

import numpy as np

from .config import AFCON_2027, WC_2030, PEAK_WINDOW, TOP5_LEAGUES, TEAM
from .elo_model import expected

CAF = {
    "Algeria", "Angola", "Benin", "Botswana", "Burkina Faso", "Burundi", "Cameroon",
    "Cape Verde", "Central African Republic", "Chad", "Comoros", "Congo", "DR Congo",
    "Djibouti", "Egypt", "Equatorial Guinea", "Eritrea", "Eswatini", "Ethiopia", "Gabon",
    "Gambia", "Ghana", "Guinea", "Guinea-Bissau", "Ivory Coast", "Kenya", "Lesotho",
    "Liberia", "Libya", "Madagascar", "Malawi", "Mali", "Mauritania", "Mauritius",
    "Morocco", "Mozambique", "Namibia", "Niger", "Nigeria", "Rwanda",
    "São Tomé and Príncipe", "Senegal", "Seychelles", "Sierra Leone", "Somalia",
    "South Africa", "South Sudan", "Sudan", "Tanzania", "Togo", "Tunisia", "Uganda",
    "Zambia", "Zimbabwe",
}

EUROPE = {
    "England", "Spain", "Italy", "Germany", "France", "Portugal", "Netherlands",
    "Belgium", "Turkey", "Switzerland", "Austria", "Denmark", "Sweden", "Norway",
    "Poland", "Czech Republic", "Croatia", "Serbia", "Greece", "Scotland", "Russia",
    "Ukraine", "Romania", "Bulgaria", "Hungary", "Slovakia", "Slovenia", "Cyprus",
    "Israel", "Azerbaijan", "Kazakhstan", "Belarus", "Bosnia and Herzegovina",
    "Albania", "North Macedonia", "Moldova", "Luxembourg", "Republic of Ireland",
    "Ireland", "Wales", "Finland", "Iceland", "Estonia", "Latvia", "Lithuania",
    "Armenia", "Georgia", "Malta", "Northern Ireland",
}

RIVALS = ["Morocco", "Senegal", "Egypt", "Nigeria", "Algeria", "Ivory Coast",
          "Cameroon", "Mali", "Ghana", "Tunisia"]

BUCKETS = [(0, 20, "≤20"), (21, 23, "21–23"), (24, 26, "24–26"),
           (27, 29, "27–29"), (30, 32, "30–32"), (33, 99, "33+")]


def age_on(dob, on):
    d = date.fromisoformat(dob)
    return round((on - d).days / 365.25, 1)


def bucket(age):
    a = int(age)
    for lo, hi, label in BUCKETS:
        if lo <= a <= hi:
            return label
    return "33+"


def peak_phase(pos, age):
    lo, hi = PEAK_WINDOW.get(pos, (24, 29))
    if age < lo:
        return "before"
    if age > hi:
        return "after"
    return "peak"


def league_group(country):
    if not country:
        return "unknown"
    if country == "Burkina Faso":
        return "home"
    if country in TOP5_LEAGUES:
        return "top5"
    if country in EUROPE:
        return "europe_other"
    if country in CAF:
        return "africa"
    return "world_other"


def enrich_players(players, today):
    out = []
    for p in players:
        q = dict(p)
        if p.get("dob"):
            q["age"] = age_on(p["dob"], today)
            q["age_afcon27"] = age_on(p["dob"], AFCON_2027)
            q["age_wc30"] = age_on(p["dob"], WC_2030)
            q["phase_now"] = peak_phase(p["pos"], q["age"])
            q["phase_afcon27"] = peak_phase(p["pos"], q["age_afcon27"])
        q["league_group"] = league_group(p.get("club_country"))
        out.append(q)
    return out


def _count(values):
    counts = {}
    for v in values:
        counts[v] = counts.get(v, 0) + 1
    return counts


def squad_stats(players):
    with_age = [p for p in players if "age" in p]
    ages = [p["age"] for p in with_age]
    caps = [p["caps"] for p in with_age]
    total_caps = sum(caps)
    return {
        "n": len(players),
        "avg_age": round(float(np.mean(ages)), 1) if ages else None,
        "median_age": round(float(np.median(ages)), 1) if ages else None,
        "caps_weighted_age": round(float(np.average(ages, weights=caps)), 1) if total_caps else None,
        "avg_age_afcon27": round(float(np.mean([p["age_afcon27"] for p in with_age])), 1) if ages else None,
        "total_caps": total_caps,
        "pct_abroad": round(100 * sum(1 for p in players if p["league_group"] != "home") / len(players), 1) if players else None,
        "pct_europe": round(100 * sum(1 for p in players if p["league_group"] in ("top5", "europe_other")) / len(players), 1) if players else None,
        "by_pos": _count(p["pos"] for p in players),
        "by_bucket": _count(bucket(p["age"]) for p in with_age),
        "by_club_country": _count(p["club_country"] or "?" for p in players),
        "by_league_group": _count(p["league_group"] for p in players),
        "phase_afcon27": _count(p["phase_afcon27"] for p in with_age),
    }


def core_generation(players):
    core = [p for p in players if "age" in p and p["caps"] >= 15]
    if not core:
        return None
    return {
        "n": len(core),
        "names": [p["name"] for p in sorted(core, key=lambda x: -x["caps"])],
        "avg_age_now": round(float(np.mean([p["age"] for p in core])), 1),
        "avg_age_afcon27": round(float(np.mean([p["age_afcon27"] for p in core])), 1),
        "in_peak_afcon27": sum(1 for p in core if p["phase_afcon27"] == "peak"),
    }


def elo_forecast(timeline):
    if len(timeline) < 20:
        return None
    yearly = {}
    for p in timeline:
        yearly[int(p["date"][:4])] = p["elo"]
    years = sorted(y for y in yearly if y >= 2010)
    xs = np.array(years, dtype=float)
    ys = np.array([yearly[y] for y in years])
    slope, intercept = np.polyfit(xs, ys, 1)
    changes = np.diff(ys)
    sigma = float(np.std(changes)) if len(changes) > 2 else 30.0
    last_year = xs[-1]

    def point(target):
        h = max(target - last_year, 0.5)
        mid = slope * target + intercept
        band = 1.28 * sigma * float(np.sqrt(h))
        return {"year": target, "mid": round(mid, 0), "lo": round(mid - band, 0), "hi": round(mid + band, 0)}

    return {
        "slope_per_year": round(float(slope), 1),
        "history_years": [{"year": int(x), "elo": float(y)} for x, y in zip(xs, ys)],
        "targets": [point(2027.5), point(2030.5)],
    }


def win_expectancy(ranked, team=TEAM):
    elos = {r["team"]: r["elo"] for r in ranked}
    mine = elos.get(team)
    if mine is None:
        return []
    out = []
    for op in RIVALS:
        if op in elos:
            out.append({
                "opponent": op,
                "opp_elo": elos[op],
                "expected": round(expected(mine - elos[op]), 2),
            })
    return out


def player_status(retired_int, career_retired, last_seen, today):
    """Precedence: seeded international retirement > career retirement > recency."""
    if retired_int:
        return "retired_int"
    if career_retired:
        return "retired_career"
    if not last_seen:
        return "out"
    months = (today - date.fromisoformat(last_seen)).days / 30.44
    if months <= 12:
        return "active"
    if months <= 18:
        return "fringe"
    return "out"


def goal_impact(diff_before, is_first_goal):
    """Classify a goal by what it changed, from the scoring side's view."""
    if diff_before == 0:
        return "opener" if is_first_goal else "go_ahead"
    if diff_before == -1:
        return "equalizer"
    if diff_before > 0:
        return "extender"
    return "consolation"


CHI2_CRIT_DF5 = 11.070  # p = 0.05, df = 5


def chi_square_uniform(counts):
    """(statistic, significant) against a uniform spread across the bins."""
    n = sum(counts)
    k = len(counts)
    if n == 0 or k < 2:
        return 0.0, False
    e = n / k
    stat = sum((o - e) ** 2 / e for o in counts)
    return round(stat, 2), stat > CHI2_CRIT_DF5


def importance_tier(minutes_share, start_share, window_matches, min_matches=8):
    if window_matches < min_matches:
        return ""
    if minutes_share >= 0.60 and start_share >= 0.66:
        return "pilier"
    if minutes_share >= 0.25:
        return "rotation"
    return "marge"


def percentile_among(value, peers):
    """Midrank percentile of value within its peer values (peers include value)."""
    if value is None or len(peers) <= 1:
        return None
    below = sum(1 for v in peers if v < value)
    equal = max(sum(1 for v in peers if v == value) - 1, 0)
    return round(100 * (below + 0.5 * equal) / (len(peers) - 1))


def classify_sofa_tournament(name):
    t = str(name).lower()
    if "friendly" in t:
        return "friendly"
    if "africa cup of nations" in t or "african nations" in t:
        return "afcon_qual" if "quali" in t else "afcon"
    if "world cup" in t or "world championship" in t:
        return "wc_qual" if "quali" in t else "wc"
    return "other"


def _formation_agg(name, rows, elo_lookup):
    n = len(rows)
    w = sum(1 for r in rows if r["result"] == "W")
    d = sum(1 for r in rows if r["result"] == "D")
    l = sum(1 for r in rows if r["result"] == "L")
    gf = sum(int(r["gf"]) for r in rows)
    ga = sum(int(r["ga"]) for r in rows)
    elos = [elo_lookup(r["date"]) for r in rows]
    elos = [e for e in elos if e]
    comps = {}
    for r in rows:
        c = classify_sofa_tournament(r["tournament"])
        comps[c] = comps.get(c, 0) + 1
    return {
        "formation": name,
        "matches": n, "w": w, "d": d, "l": l,
        "gf": gf, "ga": ga,
        "gf_pm": round(gf / n, 2), "ga_pm": round(ga / n, 2),
        "ppg": round((3 * w + d) / n, 2),
        "opp_elo_avg": round(float(np.mean(elos)), 0) if elos else None,
        "n_elo": len(elos),
        "comps": comps,
    }


def formation_table(events, elo_lookup, min_n=8):
    groups = {}
    for e in events:
        f = e.get("bf_formation") or "?"
        groups.setdefault(f, []).append(e)
    main = sorted((f for f in groups
                   if f != "?" and len(groups[f]) >= min_n),
                  key=lambda f: -len(groups[f]))
    rows = [_formation_agg(f, groups[f], elo_lookup) for f in main]
    pooled = [e for f, g in groups.items() if f not in main for e in g]
    if pooled:
        row = _formation_agg("others", pooled, elo_lookup)
        row["pooled_from"] = sorted({f for f in groups if f not in main and f != "?"})
        rows.append(row)
    return rows


def elo_summary(timeline, ranked, team=TEAM):
    world_rank = next((r["rank"] for r in ranked if r["team"] == team), None)
    caf = [r for r in ranked if r["team"] in CAF]
    caf_rank = next((i + 1 for i, r in enumerate(caf) if r["team"] == team), None)
    peak = max(timeline, key=lambda p: p["elo"]) if timeline else None
    return {
        "timeline": timeline,
        "current": timeline[-1]["elo"] if timeline else None,
        "peak": peak,
        "world_rank": world_rank,
        "n_world": len(ranked),
        "caf_rank": caf_rank,
        "n_caf": len(caf),
        "caf_top10": caf[:10],
        "forecast": elo_forecast(timeline),
        "win_expectancy": win_expectancy(ranked, team),
    }
