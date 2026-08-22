from etl.parsers.statistics import parse_event_statistics, parse_stat_value


def test_parse_stat_value_shapes():
    assert parse_stat_value("58%", "pct") == (58.0, None)
    assert parse_stat_value("21", "count") == (21, None)
    assert parse_stat_value("0.00", "count") == (0, None)
    assert parse_stat_value("22/39 (56%)", "ratio") == (22, 39)
    assert parse_stat_value("76/100 (76%)", "ratio") == (76, 100)
    assert parse_stat_value("", "count") == (None, None)
    assert parse_stat_value("-", "count") == (None, None)
    assert parse_stat_value(None, "count") == (None, None)


PAYLOAD = {"statistics": [
    {"period": "ALL", "groups": [
        {"groupName": "Match overview", "statisticsItems": [
            {"key": "ballPossession", "home": "58%", "away": "42%"},
            {"key": "totalShotsOnGoal", "home": "21", "away": "8"},
            {"key": "unknownKey", "home": "9", "away": "9"},
        ]},
        {"groupName": "Passes", "statisticsItems": [
            {"key": "accurateLongBalls", "home": "22/39 (56%)", "away": "17/42 (40%)"},
            {"key": "passes", "home": "478", "away": "355"},
        ]},
    ]},
    {"period": "1ST", "groups": [
        {"groupName": "Match overview", "statisticsItems": [
            {"key": "ballPossession", "home": "61%", "away": "39%"},
        ]},
    ]},
]}


def test_parse_event_statistics_home():
    out = parse_event_statistics(PAYLOAD, bf_home=True)
    assert set(out) == {"ALL", "1ST"}
    bf = out["ALL"]["bf"]
    opp = out["ALL"]["opp"]
    assert bf["possession_pct"] == 58.0 and opp["possession_pct"] == 42.0
    assert bf["shots"] == 21
    assert bf["long_balls"] == 22 and bf["long_balls_att"] == 39
    assert opp["long_balls"] == 17 and opp["long_balls_att"] == 42
    assert bf["passes"] == 478
    assert "unknownKey" not in bf
    assert out["1ST"]["bf"]["possession_pct"] == 61.0


def test_parse_event_statistics_away_flips():
    out = parse_event_statistics(PAYLOAD, bf_home=False)
    assert out["ALL"]["bf"]["possession_pct"] == 42.0
    assert out["ALL"]["bf"]["long_balls_att"] == 42
    assert out["ALL"]["opp"]["shots"] == 21
