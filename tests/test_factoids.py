"""Computed facts. The point of these tests is that a claim retracts itself.

"Burkina Faso has never won from two goals down" is only publishable while it is
true. If one such match is ever won, the sentence has to change on its own — a
hand-written fact would sit on the home page being wrong.
"""

from etl.load.factoids import _wdl, build_factoids


def _team(deficit_detail="0W-1D-13L", deficit_n=14):
    return {
        "resilience": {"metrics": [
            {"metric": "deficit", "scope": "trailed_2plus", "n": deficit_n,
             "value": 0.07, "detail": deficit_detail},
            {"metric": "deficit", "scope": "never_trailed", "n": 35,
             "value": 2.43, "detail": "25W-10D-0L"},
            {"metric": "reply", "scope": "never", "n": 54, "value": 69.2,
             "detail": "54 of 78"},
            {"metric": "reply", "scope": "within_10", "n": 8, "value": 10.3, "detail": ""},
        ]},
        "timeline": {"summary": {
            "scored_first": {"n": 34, "w": 25, "d": 7, "l": 2, "ppg": 2.41},
            "conceded_first": {"n": 27, "w": 4, "d": 4, "l": 19, "ppg": 0.59},
            "chi2": {"gf": {"stat": 15.5, "significant": True, "bin": "1_15",
                            "direction": "low"}},
        }},
        "formations": [
            {"formation": "4-3-3", "matches": 20, "ppg": 1.8, "opp_elo_avg": 1579.0,
             "pooled_from": ""},
            {"formation": "4-2-3-1", "matches": 18, "ppg": 1.61,
             "opp_elo_avg": 1599.0, "pooled_from": ""},
        ],
    }


HISTORY = {"venues": {"all_time": [
    {"venue_class": "home_bf", "pld": 144, "ppg": 1.93},
    {"venue_class": "home_delocalized", "pld": 46, "ppg": 1.85}]},
    "all_time": {"pld": 464, "w": 164, "d": 123, "l": 177, "win_pct": 35.3}}

ELO = {"caf_rank": 14, "n_caf": 53, "world_rank": 81, "current": 1652.4}

PROFILES = [{"name": "A B", "minutes": "2985", "goals": "3"},
            {"name": "C D", "minutes": "1200", "goals": "11"},
            {"name": "E F", "minutes": "0", "goals": "0"}]


def _keys(**kw):
    return [f["key"] for f in build_factoids(_team(**kw), HISTORY, ELO, PROFILES)]


def test_never_won_claim_is_made_only_while_it_is_true():
    assert "fact_two_down_never_won" in _keys()


def test_the_claim_retracts_itself_after_a_single_win():
    keys = _keys(deficit_detail="1W-1D-13L", deficit_n=15)
    assert "fact_two_down_never_won" not in keys
    assert "fact_two_down" in keys


def test_wdl_parsing():
    assert _wdl("0W-1D-13L") == (0, 1, 13)
    assert _wdl("25W-10D-0L") == (25, 10, 0)
    assert _wdl("nonsense") is None
    assert _wdl(None) is None


def test_the_reply_fact_counts_every_conceded_goal():
    fact = next(f for f in build_factoids(_team(), HISTORY, ELO, PROFILES)
                if f["key"] == "fact_no_reply")
    # 54 never answered + 8 answered within 10 min = 62 conceded in this fixture
    assert fact["vals"]["total"] == 62
    assert fact["vals"]["answered"] == 8


def test_most_minutes_and_top_scorer_are_different_measures():
    facts = {f["key"]: f["vals"] for f in build_factoids(_team(), HISTORY, ELO, PROFILES)}
    assert facts["fact_most_minutes"]["name"] == "A B"      # most minutes
    assert facts["fact_top_scorer_share"]["name"] == "C D"  # most goals
    assert facts["fact_top_scorer_share"]["total"] == 14


def test_formation_fact_always_carries_the_schedule_it_faced():
    """A formation record without the opponent strength beside it invites exactly
    the causal reading the project refuses to make."""
    vals = next(f["vals"] for f in build_factoids(_team(), HISTORY, ELO, PROFILES)
                if f["key"] == "fact_formation")
    assert vals["best_elo"] and vals["worst_elo"]


def test_a_formation_below_the_gate_is_not_compared():
    team = _team()
    team["formations"][1]["matches"] = 3      # too few to state a record
    assert "fact_formation" not in [f["key"] for f
                                    in build_factoids(team, HISTORY, ELO, PROFILES)]


def test_bin_fact_is_dropped_when_the_test_is_not_significant():
    team = _team()
    team["timeline"]["summary"]["chi2"]["gf"]["significant"] = False
    keys = [f["key"] for f in build_factoids(team, HISTORY, ELO, PROFILES)]
    assert "fact_bin_low" not in keys
