"""Upcoming fixtures: the merge rules, and how an empty calendar is recorded."""

from datetime import date
from unittest import mock

from etl.extract import sofascore
from etl.transform import fixtures


def _rows(**kw):
    row = {"date": "2026-09-05", "opponent": "Ghana", "venue": "A",
           "tournament": "WCQ", "source": "sofascore"}
    row.update(kw)
    return row


def test_a_seeded_fixture_wins_over_a_fetched_one_on_the_same_date():
    """A maintainer types a fixture because the source is wrong or silent, so it
    is the deliberate answer."""
    src = [_rows(), _rows(date="2026-10-10", opponent="Mali")]
    seed = [_rows(venue="N", tournament="AFCON Q. 2027", source="seed")]
    with mock.patch.object(fixtures, "_from_source", return_value=src), \
         mock.patch.object(fixtures, "_from_seed", return_value=seed), \
         mock.patch.object(fixtures, "write_csv"):
        rows = fixtures.run(today=date(2026, 8, 23))
    assert [r["date"] for r in rows] == ["2026-09-05", "2026-10-10"]
    assert rows[0]["source"] == "seed"
    assert rows[0]["venue"] == "N"          # a neutral ground the source cannot express


def test_matches_already_played_are_not_fixtures():
    src = [_rows(date="2026-08-01"), _rows(date="2026-08-23"), _rows(date="2026-09-05")]
    with mock.patch.object(fixtures, "_from_source", return_value=src), \
         mock.patch.object(fixtures, "_from_seed", return_value=[]), \
         mock.patch.object(fixtures, "write_csv"):
        rows = fixtures.run(today=date(2026, 8, 23))
    # today counts: a match kicking off later today has not been played yet
    assert [r["date"] for r in rows] == ["2026-08-23", "2026-09-05"]


def test_no_scheduled_matches_is_recorded_as_an_answer_not_a_failure():
    """The endpoint 404s when a team has nothing upcoming. That must read as an
    empty calendar, so the site can say so, rather than as an outage."""
    with mock.patch.object(sofascore, "get_sofa_json",
                           side_effect=RuntimeError("HTTP 404 for /events/next/0")), \
         mock.patch.object(sofascore, "write_json") as w, \
         mock.patch.object(sofascore, "OUT", mock.MagicMock()):
        sofascore.fetch_fixtures(force=True)
    payload = w.call_args.args[1]
    assert payload["events"] == []
    assert "error" not in payload


def test_a_real_outage_is_kept_as_an_error():
    with mock.patch.object(sofascore, "get_sofa_json",
                           side_effect=RuntimeError("HTTP 503 for /events/next/0")), \
         mock.patch.object(sofascore, "write_json") as w, \
         mock.patch.object(sofascore, "OUT", mock.MagicMock()):
        sofascore.fetch_fixtures(force=True)
    payload = w.call_args.args[1]
    assert payload["events"] == []
    assert "503" in payload["error"]
