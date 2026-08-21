from etl.analytics import chi_square_uniform, importance_tier, percentile_among


def test_chi_square_uniform_flat_not_significant():
    stat, sig = chi_square_uniform([10, 11, 9, 10, 10, 10])
    assert not sig
    assert stat < 1


def test_chi_square_concentrated_significant():
    stat, sig = chi_square_uniform([2, 3, 2, 3, 2, 24])
    assert sig
    assert stat > 11.07


def test_chi_square_empty():
    assert chi_square_uniform([0, 0, 0, 0, 0, 0]) == (0.0, False)


def test_importance_tier_rules():
    assert importance_tier(0.65, 0.70, 40) == "pilier"
    assert importance_tier(0.65, 0.50, 40) == "rotation"   # starts too few
    assert importance_tier(0.30, 0.20, 40) == "rotation"
    assert importance_tier(0.10, 0.05, 40) == "marge"
    assert importance_tier(0.90, 1.00, 3) == ""             # window too small


def test_percentile_among():
    peers = [1, 2, 3, 4, 5]
    assert percentile_among(5, peers) == 100
    assert percentile_among(1, peers) == 0
    assert percentile_among(3, peers) == 50
    assert percentile_among(3, [3]) is None
