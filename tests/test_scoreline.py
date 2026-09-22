"""The scoreline model.

Its job is to turn two things that are separately known — roughly how many goals
a match like this contains, and who is likelier to win — into a distribution over
exact scores, without the two contradicting each other.
"""

import pytest

from etl.analytics import (fit_scoreline, likely_scorelines, scoreline_grid,
                           wdl_from_grid)


def test_a_grid_is_a_probability_distribution():
    grid = scoreline_grid(1.6, 1.0)
    assert sum(grid.values()) == pytest.approx(1.0, abs=2e-3)
    assert all(p >= 0 for p in grid.values())


def test_the_split_reproduces_the_win_probability_it_was_given():
    """The whole point of fitting: the scoreline distribution and the win
    probability shown beside it must be the same claim."""
    for target in (0.25, 0.40, 0.52, 0.70, 0.85):
        lf, la = fit_scoreline(2.6, target)
        assert wdl_from_grid(scoreline_grid(lf, la))["win"] == pytest.approx(
            target, abs=0.01)


def test_the_split_preserves_the_goal_total_it_was_given():
    for total in (1.8, 2.6, 3.4):
        lf, la = fit_scoreline(total, 0.5)
        assert lf + la == pytest.approx(total, abs=0.01)


def test_a_stronger_favourite_is_expected_to_score_more():
    weak = fit_scoreline(2.6, 0.30)
    strong = fit_scoreline(2.6, 0.75)
    assert strong[0] > weak[0]      # more goals for
    assert strong[1] < weak[1]      # fewer against


def test_an_even_match_splits_the_goals_about_evenly():
    lf, la = fit_scoreline(2.6, 0.38)      # 0.38 win with draws taking a share
    assert lf == pytest.approx(la, abs=0.35)


def test_the_most_likely_scoreline_is_still_unlikely():
    """The headline number has to carry its own probability. A single scoreline
    rarely clears one chance in seven, and publishing it bare would turn a
    distribution into a prediction."""
    top = likely_scorelines(*fit_scoreline(2.6, 0.52))[0]
    assert 0.05 < top["p"] < 0.25


def test_scorelines_come_back_ordered_and_sized():
    scores = likely_scorelines(1.6, 1.0, top=5)
    assert len(scores) == 5
    assert [s["p"] for s in scores] == sorted((s["p"] for s in scores),
                                              reverse=True)
    assert all(s["gf"] >= 0 and s["ga"] >= 0 for s in scores)


def test_a_goalless_expectation_does_not_explode():
    lf, la = fit_scoreline(0, 0.5)         # clamped, not divided by zero
    assert lf >= 0 and la >= 0
    assert sum(scoreline_grid(lf, la).values()) == pytest.approx(1.0, abs=2e-3)
