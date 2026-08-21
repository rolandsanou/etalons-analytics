from etl.transform.timeline import (bin_goal, build_injury_map, clock_pos,
                                    effective_length, presence, state_minutes)


def test_injury_map_records_and_extends():
    inj = build_injury_map([{"period_end": 45, "length": 3}, {"period_end": 90, "length": 4}])
    assert inj == {45: 3, 90: 4}
    inj = build_injury_map([{"period_end": 90, "length": 4}], incidents=[(90, 7), (45, 2)])
    assert inj[90] == 7 and inj[45] == 2


def test_injury_map_fallback():
    assert build_injury_map([]) == {45: 2, 90: 3}


def test_clock_pos_continuous():
    inj = {45: 3, 90: 5}
    assert clock_pos(20, 0, inj) == 20
    assert clock_pos(45, 2, inj) == 47
    assert clock_pos(46, 0, inj) == 49          # H2 starts after H1 stoppage
    assert clock_pos(90, 4, inj) == 97
    assert clock_pos(91, 0, inj) == 99          # ET1 starts after H2 stoppage
    assert effective_length(inj, has_et=False) == 98
    assert effective_length(inj, has_et=True) == 128


def test_bin_goal_folding():
    assert bin_goal(7, 0) == ("1_15", False)
    assert bin_goal(45, 0) == ("31_45", False)
    assert bin_goal(45, 3) == ("31_45", True)
    assert bin_goal(76, 0) == ("76_90", False)
    assert bin_goal(90, 5) == ("76_90", True)
    assert bin_goal(101, 0) == ("et", False)


def test_state_minutes_and_flags():
    # BF scores at 10', concedes 30' and 60', match ends 2-1 down? -> goals BF,opp,opp
    goals = [(10, True), (30, False), (60, False)]
    st = state_minutes(goals, 95)
    assert st["first_goal"] == "bf"
    assert st["min_level"] == 10 + 30           # 0-10 and 30-60
    assert st["min_leading"] == 20              # 10-30
    assert st["min_trailing"] == 35             # 60-95
    assert st["led"] == 1 and st["trailed"] == 1


def test_state_minutes_goalless():
    st = state_minutes([], 93)
    assert st["min_level"] == 93
    assert st["first_goal"] == ""
    assert st["led"] == 0 and st["trailed"] == 0


def _app(pid, started, played, minutes, sid="99"):
    return {"player_id": pid, "sofa_player_id": sid,
            "started": started, "played": played, "minutes": minutes}


def test_presence_windows():
    eff = 97
    ins = {"sub-in": 60.0}
    outs = {"starter-off": 75.0}
    reds = {"sent-off": 50.0}
    e, x = presence(_app("starter", "1", "1", 90), ins, outs, reds, eff)
    assert (e, x) == (0.0, 97)
    e, x = presence(_app("starter-off", "1", "1", 75), ins, outs, reds, eff)
    assert (e, x) == (0.0, 75.0)
    e, x = presence(_app("sub-in", "0", "1", 37), ins, outs, reds, eff)
    assert (e, x) == (60.0, 97)
    e, x = presence(_app("sent-off", "1", "1", 50), ins, outs, reds, eff)
    assert (e, x) == (0.0, 50.0)
    e, x = presence(_app("bench", "0", "0", 0), ins, outs, reds, eff)
    assert (e, x) == (None, None)
    # sub-in with no incident record falls back to effective - minutes
    e, x = presence(_app("ghost", "0", "1", 20), ins, outs, reds, eff)
    assert (e, x) == (77, 97)
