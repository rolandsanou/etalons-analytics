from etl.analytics import calibrate_draw_rate, wdl_from_elo

PEAK, WIDTH = 0.28, 680.0


def test_probabilities_sum_to_one():
    for diff in (-600, -300, -50, 0, 50, 300, 600):
        p = wdl_from_elo(diff, PEAK, WIDTH)
        assert abs(p["win"] + p["draw"] + p["loss"] - 1.0) < 0.002
        assert all(v >= 0 for v in p.values())


def test_even_matchup_is_symmetric():
    p = wdl_from_elo(0, PEAK, WIDTH)
    assert abs(p["win"] - p["loss"]) < 0.002
    assert abs(p["draw"] - PEAK) < 0.002


def test_expected_score_is_preserved():
    # win + draw/2 must equal the Elo expectation
    from etl.elo_model import expected
    for diff in (-400, -120, 0, 250):
        p = wdl_from_elo(diff, PEAK, WIDTH)
        assert abs((p["win"] + p["draw"] / 2) - expected(diff)) < 0.003


def test_heavy_underdog_keeps_a_win_chance():
    p = wdl_from_elo(-376, PEAK, WIDTH)
    assert p["win"] > 0.01, "a 376-point underdog should not be at exactly zero"
    assert p["loss"] > p["draw"] > p["win"]


def test_draw_share_decays_with_the_gap():
    close = wdl_from_elo(0, PEAK, WIDTH)["draw"]
    far = wdl_from_elo(500, PEAK, WIDTH)["draw"]
    assert far < close


def test_calibration_from_samples():
    samples = ([(10, "D")] * 30 + [(10, "W")] * 40 + [(10, "L")] * 30
               + [(300, "D")] * 10 + [(300, "W")] * 60 + [(300, "L")] * 30)
    peak, width, n = calibrate_draw_rate(samples)
    assert n == 100
    assert abs(peak - 0.30) < 0.01
    assert 150 <= width <= 800


def test_calibration_falls_back_on_thin_data():
    peak, width, n = calibrate_draw_rate([(0, "W")] * 5)
    assert (peak, width) == (0.27, 380.0)
    assert n == 5
