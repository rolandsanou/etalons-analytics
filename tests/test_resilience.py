from etl.analytics import goal_impact
from etl.load.style import compute_axis
from etl.transform.timeline import annotate_goals, concessions


def test_goal_impact_classes():
    assert goal_impact(0, True) == "opener"
    assert goal_impact(0, False) == "go_ahead"
    assert goal_impact(-1, False) == "equalizer"
    assert goal_impact(1, False) == "extender"
    assert goal_impact(-2, False) == "consolation"


def _g(minute):
    return {"minute": minute}


def test_annotate_goals_sequence():
    # opp scores, BF equalizes, BF goes ahead, opp replies, BF extends
    seq = [(10, False, _g(10)), (20, True, _g(20)), (30, True, _g(30)),
           (40, False, _g(40)), (50, True, _g(50))]
    annotate_goals(seq)
    impacts = [row["impact"] for _, _, row in seq]
    assert impacts == ["opener", "equalizer", "go_ahead", "equalizer", "go_ahead"]
    diffs = [row["diff_before"] for _, _, row in seq]
    assert diffs == [0, -1, 0, -1, 0]


def test_annotate_goals_extender_and_consolation():
    seq = [(10, True, _g(10)), (20, True, _g(20)), (30, False, _g(30)), (40, False, _g(40))]
    annotate_goals(seq)
    assert [r["impact"] for _, _, r in seq] == [
        "opener", "extender", "consolation", "equalizer"]


def test_concessions_reply_tracking():
    seq = [(10, False, _g(10)), (18, True, _g(18)), (70, False, _g(70))]
    annotate_goals(seq)
    rows = concessions(seq)
    assert len(rows) == 2
    first, second = rows
    assert first["deficit_after"] == 1
    assert first["reply_minutes"] == 8 and first["replied_within_10"] == 1
    assert first["half"] == 1
    assert second["reply_pos"] == "" and second["replied_within_10"] == 0
    assert second["half"] == 2


def test_concessions_no_deficit_when_ahead():
    seq = [(10, True, _g(10)), (20, True, _g(20)), (30, False, _g(30))]
    annotate_goals(seq)
    rows = concessions(seq)
    assert len(rows) == 1
    assert rows[0]["deficit_after"] == 0


def _row(**kw):
    return {k: str(v) for k, v in kw.items()}


def test_compute_axis_kinds():
    rows = [_row(possession_pct=60, passes=400, passes_accurate=320),
            _row(possession_pct=40, passes=200, passes_accurate=140)]
    assert compute_axis(rows, "avg", "possession_pct", None) == (50.0, 2)
    assert compute_axis(rows, "per_match", "passes", None) == (300.0, 2)
    # pooled ratio, not a mean of ratios
    assert compute_axis(rows, "pct", "passes_accurate", "passes") == (76.7, 2)


def test_compute_axis_ignores_missing():
    rows = [_row(shots=10), {"shots": ""}, {}]
    assert compute_axis(rows, "per_match", "shots", None) == (10.0, 1)
    assert compute_axis([], "per_match", "shots", None) == (None, 0)
