from etl.analytics import classify_sofa_tournament, formation_table


def _e(formation, result, gf, ga, date="2024-01-01", tournament="Friendly Games"):
    return {"bf_formation": formation, "result": result, "gf": gf, "ga": ga,
            "date": date, "tournament": tournament}


def test_classify_sofa_tournament():
    assert classify_sofa_tournament("Africa Cup of Nations, Qualification, Group L") == "afcon_qual"
    assert classify_sofa_tournament("Africa Cup of Nations, Group E") == "afcon"
    assert classify_sofa_tournament("World Cup Qualification, CAF") == "wc_qual"
    assert classify_sofa_tournament("Int. Friendly Games") == "friendly"
    assert classify_sofa_tournament("WAFU Cup") == "other"


def test_formation_table_pools_small_groups():
    events = ([_e("4-3-3", "W", 2, 0)] * 9
              + [_e("4-2-3-1", "D", 1, 1)] * 3
              + [_e("5-4-1", "L", 0, 1)] * 2
              + [_e("", "W", 1, 0)])
    rows = formation_table(events, lambda d: 1700, min_n=8)
    names = [r["formation"] for r in rows]
    assert names == ["4-3-3", "others"]
    main = rows[0]
    assert main["matches"] == 9
    assert main["w"] == 9
    assert main["ppg"] == 3.0
    assert main["opp_elo_avg"] == 1700
    others = rows[1]
    assert others["matches"] == 6
    assert sorted(others["pooled_from"]) == ["4-2-3-1", "5-4-1"]


def test_formation_table_elo_lookup_missing():
    rows = formation_table([_e("4-3-3", "W", 1, 0)] * 8, lambda d: None, min_n=8)
    assert rows[0]["opp_elo_avg"] is None
    assert rows[0]["n_elo"] == 0
