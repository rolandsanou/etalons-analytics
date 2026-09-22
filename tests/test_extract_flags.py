import pathlib
"""What the force flags are allowed to re-download.

These guard a wiring bug rather than a formula: `fetch_player_profiles` and
`fetch_club_form` both took a `force` argument that the caller hardcoded to
False, so `--force` silently could not refresh a player's club.
"""

import inspect
from unittest import mock

from etl import extract
from etl.extract import sofascore


def _forces_seen(**kwargs):
    """Run the extractor with every request and directory write stubbed, and
    report the force flag each mutable cache actually received."""
    with mock.patch.object(sofascore, "OUT", mock.MagicMock()), \
         mock.patch.object(sofascore, "LINEUPS", mock.MagicMock()), \
         mock.patch.object(sofascore, "fetch_events_index", return_value=[]), \
         mock.patch.object(sofascore, "fetch_fixtures", return_value=0), \
         mock.patch.object(sofascore, "fetch_incidents", return_value=0), \
         mock.patch.object(sofascore, "fetch_statistics", return_value=0), \
         mock.patch.object(sofascore, "resolve_sofa_ids", return_value=set()), \
         mock.patch.object(sofascore, "_profile_targets", return_value=(set(), [])), \
         mock.patch.object(sofascore, "fetch_player_profiles", return_value=0) as prof, \
         mock.patch.object(sofascore, "fetch_club_form", return_value=0) as club:
        sofascore.run(**kwargs)
        return {"profiles": prof.call_args.kwargs.get("force"),
                "club_form": club.call_args.kwargs.get("force")}


def test_force_profiles_refreshes_club_and_market_value():
    assert _forces_seen(force_profiles=True) == {"profiles": True, "club_form": True}


def test_plain_force_refreshes_them_too():
    # --force means every source that can change, and a club can change
    assert _forces_seen(force=True) == {"profiles": True, "club_form": True}


def test_an_ordinary_run_keeps_the_cache():
    assert _forces_seen() == {"profiles": False, "club_form": False}


def test_a_played_match_is_never_refetched():
    """Incidents and statistics take no force flag at all: once a match has been
    played they cannot change, and re-pulling 64 of each wastes requests against
    an unofficial API."""
    for fn in (sofascore.fetch_incidents, sofascore.fetch_statistics):
        assert "force" not in inspect.signature(fn).parameters


def test_extract_run_passes_the_flag_down():
    with mock.patch.object(extract.wikipedia, "run"), \
         mock.patch.object(extract.martj42, "run"), \
         mock.patch.object(extract.commons, "run"), \
         mock.patch.object(extract.sofascore, "run") as sofa:
        extract.run(force_profiles=True)
    assert sofa.call_args.kwargs["force_profiles"] is True
    assert sofa.call_args.kwargs["force"] is False


# --- a match fetched too early must not stay broken ------------------------

def test_a_cached_error_is_retried_while_the_match_is_recent():
    """Run the pipeline at full time and the feed can answer 404 for a match
    whose statistics appear an hour later. Caching that 404 for good would
    leave the match page permanently without its report."""
    import tempfile
    from datetime import date, timedelta
    from etl.extract.sofascore import _needs_event_fetch
    from etl.util import write_json

    dest = pathlib.Path(tempfile.mkdtemp()) / "16205035.json"
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    long_ago = (date.today() - timedelta(days=400)).isoformat()

    # nothing cached yet
    assert _needs_event_fetch(dest, yesterday)

    write_json(dest, {"error": "HTTP 404"})
    assert _needs_event_fetch(dest, yesterday)        # still worth asking again
    assert not _needs_event_fetch(dest, long_ago)     # that 404 is settled

    write_json(dest, {"statistics": [{"period": "ALL"}]})
    assert not _needs_event_fetch(dest, yesterday)    # a real answer is kept
    assert _needs_event_fetch(dest, yesterday, force=True)


def test_an_undated_event_never_loops_on_a_cached_error():
    import tempfile
    from etl.extract.sofascore import _needs_event_fetch
    from etl.util import write_json
    dest = pathlib.Path(tempfile.mkdtemp()) / "x.json"
    write_json(dest, {"error": "HTTP 404"})
    assert not _needs_event_fetch(dest, None)
    assert not _needs_event_fetch(dest, "not-a-date")
