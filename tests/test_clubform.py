from etl.extract.sofascore import (pick_baseline_season, pick_club_seasons,
                                   season_start_year)


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


def test_season_start_year_sorts_both_label_shapes():
    assert season_start_year("25/26") == 2025      # split-year leagues
    assert season_start_year("2026") == 2026       # calendar-year leagues
    assert season_start_year("18/19") == 2018
    for junk in ("", None, "abc", "20xx/21"):
        assert season_start_year(junk) == -1       # sorts behind real seasons


def test_baseline_follows_a_transfer_into_the_old_league():
    """The point of searching every competition: a player in their first season
    at a new club has nothing behind them there, but their last real campaign is
    sitting in the league they left."""
    data = {"uniqueTournamentSeasons": [
        _ut("Premier League", 17, ["26/27"]),
        _ut("Ligue 1", 34, ["25/26", "24/25"]),
    ]}
    base = pick_baseline_season(data, 2026, exclude={(17, 100)})
    assert (base["tournament"], base["year"]) == ("Ligue 1", "25/26")


def test_baseline_prefers_a_league_over_a_cup_in_the_same_year():
    data = {"uniqueTournamentSeasons": [
        _ut("Premier League", 17, ["26/27"]),
        _ut("Coupe de France", 9, ["25/26"]),
        _ut("Ligue 1", 34, ["25/26"]),
    ]}
    base = pick_baseline_season(data, 2026, exclude={(17, 100)})
    assert base["tournament"] == "Ligue 1"


def test_baseline_is_never_the_current_season_in_another_competition():
    """Only seasons starting strictly earlier qualify — that is what makes them
    completed. A second 26/27 entry is the same campaign, not a baseline."""
    data = {"uniqueTournamentSeasons": [
        _ut("Premier League", 17, ["26/27"]),
        _ut("EFL Cup", 21, ["26/27"]),
    ]}
    assert pick_baseline_season(data, 2026, exclude={(17, 100)}) is None


def test_baseline_ignores_national_team_seasons():
    data = {"uniqueTournamentSeasons": [
        _ut("Premier League", 17, ["26/27"]),
        _ut("Africa Cup of Nations", 656, ["2025"]),
    ]}
    assert pick_baseline_season(data, 2026, exclude={(17, 100)}) is None


def test_transform_leaves_an_absent_baseline_blank():
    """Blank, never 0 — "0" would read as a season spent unused."""
    from etl.transform.clubform import CLUB_FORM_FIELDS, _stats
    for field in ("prev_tournament", "prev_season_year", "prev_apps",
                  "prev_minutes", "prev_rating"):
        assert field in CLUB_FORM_FIELDS
    assert _stats({}) == {"apps": 0, "starts": 0, "minutes": 0, "rating": ""}
    assert _stats({"appearances": 3, "minutesPlayed": 210, "rating": 6.9312}) == {
        "apps": 3, "starts": 0, "minutes": 210, "rating": 6.93}
