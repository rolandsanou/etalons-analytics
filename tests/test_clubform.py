from etl.extract.sofascore import pick_club_seasons


def _ut(name, ut_id, years):
    return {"uniqueTournament": {"name": name, "id": ut_id},
            "seasons": [{"id": 100 + i, "year": y} for i, y in enumerate(years)]}


def test_pick_skips_national_team_competitions():
    data = {"uniqueTournamentSeasons": [
        _ut("Africa Cup of Nations", 656, ["2025"]),
        _ut("World Cup Qual. CAF", 2, ["2026"]),
        _ut("Pro League", 38, ["26/27", "25/26"]),
        _ut("Ligue 1", 34, ["25/26"]),
    ]}
    picks = pick_club_seasons(data)
    assert picks[0]["tournament"] == "Pro League"
    assert picks[0]["year"] == "26/27"
    assert picks[0]["season_id"] == 100
    assert [p["tournament"] for p in picks] == ["Pro League", "Ligue 1"]


def test_pick_leagues_before_cups():
    data = {"uniqueTournamentSeasons": [
        _ut("Türkiye Kupası", 9, ["25/26"]),
        _ut("Süper Lig", 52, ["25/26"]),
        _ut("UEFA Europa League", 679, ["25/26"]),
    ]}
    picks = pick_club_seasons(data)
    assert [p["tournament"] for p in picks] == [
        "Süper Lig", "Türkiye Kupası", "UEFA Europa League"]


def test_pick_none_when_only_national():
    data = {"uniqueTournamentSeasons": [_ut("Int. Friendly Games", 218, ["2026"])]}
    assert pick_club_seasons(data) == []
    assert pick_club_seasons({}) == []
