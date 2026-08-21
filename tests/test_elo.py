from etl.transform.elo import expected, gd_multiplier, k_factor, update


def test_k_factor():
    assert k_factor("FIFA World Cup") == 60
    assert k_factor("African Cup of Nations") == 50
    assert k_factor("African Cup of Nations qualification") == 40
    assert k_factor("FIFA World Cup qualification") == 40
    assert k_factor("Friendly") == 20
    assert k_factor("African Nations Championship") == 30


def test_gd_multiplier():
    assert gd_multiplier(0) == 1.0
    assert gd_multiplier(1) == 1.0
    assert gd_multiplier(-2) == 1.5
    assert gd_multiplier(3) == 1.75
    assert gd_multiplier(5) == 2.0


def test_expected_symmetry():
    assert expected(0) == 0.5
    assert abs(expected(100) + expected(-100) - 1.0) < 1e-9


def test_update_zero_sum_and_direction():
    h, a = update(1500, 1500, 2, 0, "Friendly", neutral=True)
    assert h > 1500 > a
    assert abs((h - 1500) + (a - 1500)) < 1e-9


def test_update_home_advantage():
    hn, _ = update(1500, 1500, 1, 0, "Friendly", neutral=True)
    hh, _ = update(1500, 1500, 1, 0, "Friendly", neutral=False)
    assert hh < hn
