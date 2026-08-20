from datetime import date

from pipeline.analytics import age_on, bucket, league_group, peak_phase


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
