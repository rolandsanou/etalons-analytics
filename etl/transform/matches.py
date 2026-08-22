import numpy as np
import pandas as pd

from ..config import RAW, STAGING, TEAM


def load_results():
    df = pd.read_csv(RAW / "martj42" / "results.csv", parse_dates=["date"])
    df = df.dropna(subset=["home_score", "away_score"]).copy()
    df["home_score"] = df["home_score"].astype(int)
    df["away_score"] = df["away_score"].astype(int)
    fn = pd.read_csv(RAW / "martj42" / "former_names.csv")
    mapping = dict(zip(fn["former"], fn["current"]))
    df["home_team"] = df["home_team"].replace(mapping)
    df["away_team"] = df["away_team"].replace(mapping)
    return df.sort_values("date").reset_index(drop=True)


def team_matches(df, team):
    m = df[(df.home_team == team) | (df.away_team == team)].copy()
    m["is_home"] = m.home_team == team
    m["gf"] = np.where(m.is_home, m.home_score, m.away_score)
    m["ga"] = np.where(m.is_home, m.away_score, m.home_score)
    m["opponent"] = np.where(m.is_home, m.away_team, m.home_team)
    m["venue"] = np.where(m.neutral, "N", np.where(m.is_home, "H", "A"))
    # delocalized homes (e.g. the Marrakech era) are often flagged neutral,
    # so classify by listing + host country, not by the neutral flag
    m["venue_class"] = np.select(
        [m.is_home & (m.country == team), m.is_home & (m.country != team),
         ~m.is_home & m.neutral.astype(bool)],
        ["home_bf", "home_delocalized", "neutral"], default="away")
    m["result"] = np.select([m.gf > m.ga, m.gf == m.ga], ["W", "D"], default="L")
    return m


def classify_tournament(name):
    t = str(name).lower()
    if "african cup of nations" in t or "africa cup of nations" in t:
        return "afcon_qual" if "qualification" in t else "afcon"
    if "fifa world cup" in t:
        return "wc_qual" if "qualification" in t else "wc"
    if t == "friendly":
        return "friendly"
    return "other"


def _record(g):
    return {
        "pld": int(len(g)),
        "w": int((g.result == "W").sum()),
        "d": int((g.result == "D").sum()),
        "l": int((g.result == "L").sum()),
        "gf": int(g.gf.sum()),
        "ga": int(g.ga.sum()),
        "win_pct": round(100 * (g.result == "W").mean(), 1) if len(g) else 0.0,
    }


# editions officially named for a year but played later (COVID-delayed)
EDITION_YEAR = {2022: 2021, 2024: 2023}


def afcon_editions(m):
    a = m[m.comp == "afcon"].sort_values("date")
    groups, current, last = [], [], None
    for idx, d in zip(a.index, a.date):
        if last is not None and (d - last).days > 45:
            groups.append(current)
            current = []
        current.append(idx)
        last = d
    if current:
        groups.append(current)
    out = []
    for idx in groups:
        g = a.loc[idx]
        start = g.date.min()
        year = EDITION_YEAR.get(start.year, start.year)
        out.append({"year": int(year), **_record(g)})
    return out


def history_stats(m):
    m = m.copy()
    m["year"] = m.date.dt.year
    m["decade"] = (m.year // 10) * 10

    by_decade = [{"decade": int(d), **_record(g)} for d, g in m.groupby("decade")]
    by_year = [{"year": int(y), **_record(g)} for y, g in m.groupby("year")]
    by_comp = {c: _record(g) for c, g in m.groupby("comp")}

    m["margin"] = m.gf - m.ga

    def top(rows):
        return [{
            "date": r.date.strftime("%Y-%m-%d"),
            "opponent": r.opponent,
            "score": f"{int(r.gf)}-{int(r.ga)}",
            "tournament": r.tournament,
            "venue": r.venue,
        } for r in rows.itertuples()]

    biggest_wins = top(m.nlargest(5, "margin"))
    heaviest_losses = top(m.nsmallest(5, "margin"))

    opp = [{"opponent": o, **_record(g)} for o, g in m.groupby("opponent") if len(g) >= 10]
    opp.sort(key=lambda r: -r["pld"])

    last10 = top(m.tail(10).iloc[::-1])
    for row, r in zip(last10, m.tail(10).iloc[::-1].itertuples()):
        row["result"] = r.result

    return {
        "all_time": _record(m),
        "by_decade": by_decade,
        "by_year": by_year,
        "by_comp": by_comp,
        "biggest_wins": biggest_wins,
        "heaviest_losses": heaviest_losses,
        "top_opponents": opp[:8],
        "last10": last10,
        "afcon_editions": afcon_editions(m),
        "first_match": m.date.min().strftime("%Y-%m-%d"),
        "last_match": m.date.max().strftime("%Y-%m-%d"),
    }


def run():
    df = load_results()
    m = team_matches(df, TEAM)
    m["comp"] = m.tournament.map(classify_tournament)
    out = m[["date", "opponent", "venue", "gf", "ga", "result",
             "tournament", "comp", "neutral", "city", "country"]].copy()
    out["date"] = out.date.dt.strftime("%Y-%m-%d")
    STAGING.mkdir(parents=True, exist_ok=True)
    out.to_csv(STAGING / "matches.csv", index=False)
    print(f"wrote {STAGING / 'matches.csv'} ({len(out)} rows)")


def load_staged():
    m = pd.read_csv(STAGING / "matches.csv", parse_dates=["date"])
    return m
