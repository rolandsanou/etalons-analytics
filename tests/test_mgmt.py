from etl.load.partnerships import overlap, pair_type
from etl.load.rest import band as rest_band
from etl.load.rest import rest_days
from etl.load.subpatterns import band as sub_band
from etl.load.subpatterns import _median, _state_at


def _app(entry, exit_):
    return {"entry_min": str(entry), "exit_min": str(exit_)}


def test_overlap_shared_minutes():
    # a starter and a substitute who came on at 60'
    assert overlap(_app(0, 95), _app(60, 95)) == 35
    # both starters, one off at 70'
    assert overlap(_app(0, 70), _app(0, 95)) == 70
    # never on the pitch together
    assert overlap(_app(0, 60), _app(75, 95)) == 0
    # touching windows do not overlap
    assert overlap(_app(0, 60), _app(60, 95)) == 0


def test_pair_type_is_order_independent():
    assert pair_type("DF", "GK") == pair_type("GK", "DF") == "GK-DF"
    assert pair_type("MF", "FW") == "MF-FW"
    assert pair_type("DF", "DF") == "DF-DF"


def test_sub_band_edges():
    assert sub_band(45) == "1_45"
    assert sub_band(46) == "46_60"
    assert sub_band(70) == "61_70"
    assert sub_band(80) == "71_80"
    assert sub_band(90) == "81_plus"
    assert sub_band(120) == "81_plus"


def test_median():
    assert _median([60]) == 60
    assert _median([50, 70]) == 60
    assert _median([50, 60, 70]) == 60
    assert _median([]) is None


def test_state_at_uses_goals_before_the_minute():
    goals = [(10, True), (40, False), (75, False)]
    assert _state_at(5, goals) == "level"
    assert _state_at(20, goals) == "leading"
    assert _state_at(50, goals) == "level"
    assert _state_at(80, goals) == "trailing"
    assert _state_at(40, goals) == "level"  # the goal at 40' counts


def test_rest_band_edges():
    assert rest_band(0) == "0_3"
    assert rest_band(3) == "0_3"
    assert rest_band(4) == "4_5"
    assert rest_band(5) == "4_5"
    assert rest_band(9) == "6_9"
    assert rest_band(10) == "10_plus"
    assert rest_band(300) == "10_plus"


def test_rest_days_sequence():
    matches = [{"date": "2026-03-31"}, {"date": "2026-03-28"}, {"date": "2026-06-05"}]
    out = rest_days(matches)
    assert [m["date"] for m, _ in out] == ["2026-03-28", "2026-03-31", "2026-06-05"]
    assert [d for _, d in out] == [None, 3, 66]
