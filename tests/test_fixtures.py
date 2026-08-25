"""Upcoming fixtures: the merge rules, and how a half-announced match is held.

CAF publishes a qualifying campaign in stages — the draw, then the windows, then
the exact dates. These tests pin the behaviour that matters: a fixture with no
confirmed date is still shown, and it is never given one it does not have.
"""

from datetime import date
from unittest import mock

from etl.extract import sofascore
from etl.transform import fixtures


def _row(**kw):
    row = {f: "" for f in fixtures.FIXTURE_FIELDS}
    row.update({"date": "2026-09-25", "date_confirmed": "1",
                "window_start": "2026-09-25", "window_end": "2026-09-25",
                "matchday": "1", "opponent": "Benin", "venue": "H",
                "tournament": "WCQ", "source": "sofascore"})
    row.update(kw)
    return row


def _run(src, seed, today=(2026, 8, 23)):
    with mock.patch.object(fixtures, "_from_source", return_value=src), \
         mock.patch.object(fixtures, "_from_seed", return_value=seed), \
         mock.patch.object(fixtures, "write_csv"):
        return fixtures.run(today=date(*today))


def test_a_seeded_fixture_wins_over_a_fetched_one_on_the_same_matchday():
    """A maintainer types a fixture because the source is wrong or silent, so it
    is the deliberate answer."""
    src = [_row(), _row(matchday="2", opponent="Mali")]
    seed = [_row(venue="N", tournament="AFCON Q. 2027", source="seed")]
    rows = _run(src, seed)
    assert [r["matchday"] for r in rows] == ["1", "2"]
    assert rows[0]["source"] == "seed"
    assert rows[0]["venue"] == "N"      # a neutral ground the source cannot express


def test_an_unscheduled_fixture_keeps_its_window_and_says_so():
    seed = [_row(date="", date_confirmed="0",
                 window_start="2026-09-21", window_end="2026-10-06")]
    row = _run([], seed)[0]
    assert row["date"] == ""            # never invented
    assert row["date_confirmed"] == "0"
    assert (row["window_start"], row["window_end"]) == ("2026-09-21", "2026-10-06")


def test_a_fixture_survives_until_its_window_closes():
    """Mid-window, with no date set, the match has probably not been played —
    dropping it the moment the window opened would hide the whole campaign."""
    seed = [_row(date="", date_confirmed="0",
                 window_start="2026-09-21", window_end="2026-10-06")]
    assert len(_run([], seed, today=(2026, 9, 30))) == 1   # window still open
    assert len(_run([], seed, today=(2026, 10, 7))) == 0   # window closed


def test_matches_already_played_are_not_fixtures():
    src = [_row(date=d, window_start=d, window_end=d, matchday=str(i))
           for i, d in enumerate(("2026-08-01", "2026-08-23", "2026-09-05"))]
    rows = _run(src, [])
    # today counts: a match kicking off later today has not been played yet
    assert [r["date"] for r in rows] == ["2026-08-23", "2026-09-05"]


def test_fixtures_are_ordered_by_window_then_matchday():
    seed = [_row(date="", date_confirmed="0", matchday="2",
                 window_start="2026-09-21", window_end="2026-10-06"),
            _row(date="", date_confirmed="0", matchday="1",
                 window_start="2026-09-21", window_end="2026-10-06"),
            _row(date="", date_confirmed="0", matchday="3",
                 window_start="2026-11-09", window_end="2026-11-17")]
    assert [r["matchday"] for r in _run([], seed)] == ["1", "2", "3"]


def test_a_fetched_fixture_is_always_marked_confirmed():
    """The source only ever publishes matches with a real kick-off date."""
    payload = {"events": [{"date": "2026-09-25", "home_id": "4749",
                           "home": "Burkina Faso", "away": "Benin",
                           "tournament": "WCQ"}]}
    with mock.patch.object(fixtures, "read_json", return_value=payload), \
         mock.patch.object(fixtures, "RAW", mock.MagicMock()):
        row = fixtures._from_source()[0]
    assert row["date_confirmed"] == "1"
    assert row["venue"] == "H"          # team id matches the home side
    assert row["opponent"] == "Benin"


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
