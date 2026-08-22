import pandas as pd

from etl.transform.matches import afcon_editions, classify_tournament, team_matches


def test_classify_tournament():
    assert classify_tournament("African Cup of Nations") == "afcon"
    assert classify_tournament("African Cup of Nations qualification") == "afcon_qual"
    assert classify_tournament("FIFA World Cup qualification") == "wc_qual"
    assert classify_tournament("Friendly") == "friendly"
    assert classify_tournament("WAFU Cup") == "other"


def _df(rows):
    df = pd.DataFrame(rows, columns=["date", "home_team", "away_team",
                                     "home_score", "away_score", "tournament", "neutral"])
    df["country"] = "Somewhere"
    return df


def test_afcon_edition_clustering_across_new_year():
    df = _df([
        ("2025-12-22", "Burkina Faso", "Ghana", 1, 0, "African Cup of Nations", True),
        ("2026-01-06", "Ivory Coast", "Burkina Faso", 3, 0, "African Cup of Nations", True),
        ("2022-01-10", "Burkina Faso", "Cameroon", 1, 2, "African Cup of Nations", True),
    ])
    df["date"] = pd.to_datetime(df["date"])
    m = team_matches(df, "Burkina Faso")
    m["comp"] = m.tournament.map(classify_tournament)
    editions = afcon_editions(m)
    years = sorted(e["year"] for e in editions)
    assert years == [2021, 2025]
    ed2025 = next(e for e in editions if e["year"] == 2025)
    assert ed2025["pld"] == 2
    assert ed2025["w"] == 1
    assert ed2025["l"] == 1


def test_team_matches_venue_and_result():
    df = _df([("2024-06-01", "Burkina Faso", "Togo", 2, 1, "Friendly", False)])
    df["date"] = pd.to_datetime(df["date"])
    m = team_matches(df, "Burkina Faso")
    r = m.iloc[0]
    assert r.venue == "H"
    assert r.result == "W"
    assert r.gf == 2 and r.ga == 1
    assert r.opponent == "Togo"


def _dfc(rows):
    return pd.DataFrame(rows, columns=["date", "home_team", "away_team", "home_score",
                                       "away_score", "tournament", "neutral", "country"])


def test_venue_class():
    df = _dfc([
        # true home in Ouagadougou
        ("2024-06-01", "Burkina Faso", "Togo", 1, 0, "FIFA World Cup qualification", False, "Burkina Faso"),
        # delocalized home qualifier in Marrakech, flagged neutral by the source
        ("2021-09-01", "Burkina Faso", "Niger", 2, 0, "FIFA World Cup qualification", True, "Morocco"),
        # AFCON final tournament, BF listed home in the host country -> neutral
        ("2024-01-20", "Burkina Faso", "Algeria", 2, 2, "African Cup of Nations", True, "Ivory Coast"),
        # plain away
        ("2024-03-01", "Ghana", "Burkina Faso", 1, 0, "Friendly", False, "Ghana"),
        # away listing at a neutral venue
        ("2025-12-22", "Ghana", "Burkina Faso", 0, 1, "African Cup of Nations", True, "Morocco"),
    ])
    df["date"] = pd.to_datetime(df["date"])
    m = team_matches(df, "Burkina Faso").sort_values("date")
    assert list(m.venue_class) == ["home_delocalized", "neutral", "away", "home_bf", "neutral"]
