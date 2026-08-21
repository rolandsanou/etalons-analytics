from datetime import date

from etl.analytics import player_status
from etl.extract.sofascore import search_match
from etl.transform.players import parse_profile

TODAY = date(2026, 8, 21)


def test_status_precedence():
    assert player_status(True, True, "2026-06-01", TODAY) == "retired_int"
    assert player_status(False, True, "2026-06-01", TODAY) == "retired_career"


def test_status_recency_windows():
    assert player_status(False, False, "2026-06-09", TODAY) == "active"
    assert player_status(False, False, "2025-09-01", TODAY) == "active"
    assert player_status(False, False, "2025-05-01", TODAY) == "fringe"
    assert player_status(False, False, "2024-06-01", TODAY) == "out"
    assert player_status(False, False, "", TODAY) == "out"


def test_parse_profile_normal():
    f = parse_profile({
        "team": {"name": "Union SG", "country": {"name": "Belgium"},
                 "primaryUniqueTournament": {"name": "Pro League"},
                 "tournament": {"name": "Cup"}},
        "retired": False, "height": 187, "preferredFoot": "Right",
        "proposedMarketValueRaw": {"value": 5600000, "currency": "EUR"},
        "contractUntilTimestamp": 1814313600,
    }, "2026-08-21T10:00:00")
    assert f["club_v"] == "Union SG"
    assert f["league_v"] == "Pro League"
    assert f["club_country_v"] == "Belgium"
    assert f["market_value_eur"] == 5600000
    assert f["contract_until"].startswith("2027")
    assert f["club_source"] == "sofascore@2026-08-21"
    assert f["career_retired"] == 0


def test_parse_profile_retired_no_team():
    f = parse_profile({"team": {"name": "No team", "disabled": True}, "retired": True})
    assert f["club_v"] == ""
    assert f["league_v"] == ""
    assert f["career_retired"] == 1


def test_parse_profile_non_eur_value_dropped():
    f = parse_profile({"proposedMarketValueRaw": {"value": 1, "currency": "USD"}})
    assert f["market_value_eur"] == ""


def _search(name, country, type_="player", pid=42):
    return {"results": [{"type": type_,
                         "entity": {"id": pid, "name": name,
                                    "country": {"alpha2": country}}}]}


def test_search_match_exact_bf_accepted():
    assert search_match(_search("Hervé Koffi", "BF"), "Herve Koffi") == 42


def test_search_match_rejections():
    assert search_match(_search("Hervé Koffi", "CI"), "Hervé Koffi") is None
    assert search_match(_search("Hervé Kofi", "BF"), "Hervé Koffi") is None
    assert search_match(_search("Hervé Koffi", "BF", type_="team"), "Hervé Koffi") is None
