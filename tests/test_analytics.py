from datetime import date

from etl.analytics import age_on, bucket, league_group, peak_phase


def test_bucket_fractional_ages():
    assert bucket(23.9) == "21–23"
    assert bucket(24.0) == "24–26"
    assert bucket(20.9) == "≤20"
    assert bucket(29.7) == "27–29"
    assert bucket(35.2) == "33+"


def test_peak_phase():
    assert peak_phase("GK", 34.0) == "after"
    assert peak_phase("GK", 26.5) == "peak"
    assert peak_phase("MF", 23.0) == "before"
    assert peak_phase("FW", 27.0) == "peak"
    assert peak_phase("DF", 31.0) == "after"


def test_age_on():
    assert age_on("2000-01-01", date(2026, 1, 1)) == 26.0


def test_league_group():
    assert league_group("France") == "top5"
    assert league_group("Netherlands") == "europe_other"
    assert league_group("Sudan") == "africa"
    assert league_group("Burkina Faso") == "home"
    assert league_group("United States") == "world_other"
    assert league_group(None) == "unknown"


def _p(caps, age=25.0):
    return {"age": age, "caps": caps, "goals": 0, "pos": "MF", "name": f"p{caps}",
            "age_afcon27": age + 0.8, "phase_afcon27": "peak",
            "club_country": "France", "league_group": "top5"}


def test_squad_stats_survives_an_unstated_cap_count():
    """A federation list states no caps, so some players have none recorded.
    Summing them used to raise, which left the whole squad document unwritten
    and every age and cap on the page blank."""
    from etl.analytics import squad_stats
    s = squad_stats([_p(40), _p(None), _p(2)])
    assert s["total_caps"] == 42          # the unknown one contributes nothing
    assert s["caps_unknown"] == 1         # ... and says so
    assert s["n"] == 3
    assert s["avg_age"] == 25.0
    assert sum(s["by_bucket"].values()) == 3


def test_caps_weighted_age_ignores_unknown_counts():
    from etl.analytics import squad_stats
    young, old = _p(0, 20.0), _p(100, 30.0)
    # weighting by caps, the only capped player decides it
    assert squad_stats([young, old])["caps_weighted_age"] == 30.0
    # an unknown count must weigh the same as a zero one, not crash
    assert squad_stats([_p(None, 20.0), old])["caps_weighted_age"] == 30.0


def test_core_generation_excludes_players_with_no_recorded_caps():
    from etl.analytics import core_generation
    core = core_generation([_p(40), _p(None), _p(20)])
    assert core["n"] == 2
    assert core_generation([_p(None), _p(1)]) is None
