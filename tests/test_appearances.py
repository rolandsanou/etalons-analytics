from etl.transform.appearances import POS_MAP, STATS_MAP, _dob_from_ts, _match_player


def test_pos_map():
    assert POS_MAP["G"] == "GK"
    assert POS_MAP["F"] == "FW"


def test_stats_map_covers_requested_metrics():
    cols = set(STATS_MAP.values())
    for needed in ("goals", "assists", "passes", "passes_accurate",
                   "dribbles_attempted", "dribbles_won", "saves"):
        assert needed in cols


def test_dob_from_ts():
    assert _dob_from_ts(None) == ""
    assert _dob_from_ts(820454400) == "1996-01-01"


def _entry(name, dob_ts=None, pid=1):
    player = {"name": name, "id": pid}
    if dob_ts:
        player["dateOfBirthTimestamp"] = dob_ts
    return {"player": player}


def test_match_player_unique_name():
    registry = {"herve-koffi": {"name": "Hervé Koffi", "dob": "1996-10-16"}}
    idx = {"herve koffi": ["herve-koffi"]}
    assert _match_player(_entry("Herve Koffi"), idx, registry, {}) == "herve-koffi"


def test_match_player_homonym_resolved_by_dob():
    registry = {
        "x-1998": {"name": "X", "dob": "1998-01-01"},
        "x-2003": {"name": "X", "dob": "2003-06-22"},
    }
    idx = {"x": ["x-1998", "x-2003"]}
    ts_2003 = 1056240000  # 2003-06-22 UTC
    assert _match_player(_entry("X", ts_2003), idx, registry, {}) == "x-2003"
    assert _match_player(_entry("X"), idx, registry, {}) is None


def test_match_player_override():
    registry = {"steeve-yago": {"name": "Steeve Yago", "dob": ""}}
    idx = {"steeve yago": ["steeve-yago"]}
    overrides = {"steve yago": "Steeve Yago"}
    assert _match_player(_entry("Steve Yago"), idx, registry, overrides) == "steeve-yago"
