"""The post-match sections, which have to survive a feed that covers half of them.

Sofascore publishes this depth for competitive matches and often not for
friendlies, so the interesting cases are not the complete ones. Every test here
is about what happens when part of the data is missing: the rule throughout is
that a section disappears rather than printing zeros, because a zero is a claim
and an absent statistic is not.
"""

from tools.site_builder import matchreport as mr


def _app(name, pos="MF", **stats):
    row = {"name": name, "player_id": name.lower(), "pos": pos, "minutes": "90",
           "rating": "7.0", "goals": "0", "assists": "0", "started": "1",
           "played": "1", "has_detailed_stats": "1"}
    row.update({k: str(v) for k, v in stats.items()})
    return row


# --- halves ----------------------------------------------------------------

def test_half_split_keeps_a_measure_present_in_one_half_only():
    """No shots in the second half IS the finding; blanking the row hides it."""
    first = {"bf": {"shots": "6", "corners": "3"}, "opp": {"shots": "2", "corners": "1"}}
    second = {"bf": {"shots": "0"}, "opp": {"shots": "9"}}
    rows = {r["key"]: r for r in mr.half_split(first, second)}
    assert rows["shots"]["h2"]["bf"] == 0
    # corners were carried in the first half only, so the row survives
    assert rows["corners"]["h1"]["bf"] == 3
    assert rows["corners"]["h2"]["bf"] is None


def test_half_split_drops_a_measure_no_half_carried():
    first = {"bf": {"shots": "6"}, "opp": {"shots": "2"}}
    second = {"bf": {"shots": "4"}, "opp": {"shots": "5"}}
    assert [r["key"] for r in mr.half_split(first, second)] == ["shots"]


def test_half_split_needs_both_halves():
    assert mr.half_split({"bf": {"shots": "6"}}, None) is None
    assert mr.half_split(None, None) is None


def test_possession_is_flagged_so_it_is_never_summed():
    first = {"bf": {"possession_pct": "44"}, "opp": {"possession_pct": "56"}}
    second = {"bf": {"possession_pct": "36"}, "opp": {"possession_pct": "64"}}
    assert mr.half_split(first, second)[0]["pct"] is True


# --- shape and goal timing -------------------------------------------------

def test_match_shape_separates_two_identical_scorelines():
    """2-2 from two down and 2-2 from two up are the same result and not the
    same match; only the minutes by state tell them apart."""
    comeback = mr.match_shape({"min_leading": "0", "min_level": "20",
                               "min_trailing": "75", "trailed": "1", "led": "0"})
    collapse = mr.match_shape({"min_leading": "70", "min_level": "20",
                               "min_trailing": "5", "trailed": "1", "led": "1"})
    assert comeback["trailing"] == 75 and not comeback["led"]
    assert collapse["leading"] == 70 and collapse["led"]


def test_goal_windows_disappear_when_nothing_was_scored():
    goalless = {f"{side}_{b}": "0" for b in ("1_15", "16_30", "31_45", "46_60",
                                             "61_75", "76_90", "et")
                for side in ("gf", "ga")}
    assert mr.goal_windows(goalless) is None
    scored = dict(goalless, gf_46_60="2")
    bands = {b["band"]: b for b in mr.goal_windows(scored)}
    assert bands["46-60"]["gf"] == 2 and bands["1-15"]["gf"] == 0


def test_shape_and_windows_need_a_state_row():
    assert mr.match_shape({}) is None and mr.goal_windows({}) is None


# --- phases of play --------------------------------------------------------

def test_a_phase_row_carries_its_counts_not_just_a_percentage():
    bf = {"long_balls": "35", "long_balls_att": "70"}
    opp = {"long_balls": "36", "long_balls_att": "52"}
    row = mr.phase_groups(bf, opp)[0]["rows"][0]
    assert row["bf"] == {"made": 35, "att": 70, "pct": 50.0}
    assert row["opp"]["pct"] == 69.2


def test_a_phase_with_no_attempts_is_dropped_rather_than_shown_as_zero_percent():
    # nobody crossed: 0/0 is not "0 % of crosses completed"
    assert mr.phase_groups({"crosses": "0", "crosses_att": "0"}, {}) is None
    assert mr.phase_groups({}, {}) is None


def test_a_phase_survives_the_opponent_side_being_absent():
    groups = mr.phase_groups({"dribbles": "7", "dribbles_att": "19"}, None)
    assert groups[0]["rows"][0]["bf"]["made"] == 7
    assert groups[0]["rows"][0]["opp"] is None


# --- players ---------------------------------------------------------------

def test_keepers_get_their_own_table():
    apps = [_app("Keeper", "GK", saves=4), _app("Back", "DF", touches=50)]
    groups = mr.player_lines(apps)
    assert [r["name"] for r in groups["keepers"]["rows"]] == ["Keeper"]
    assert [r["name"] for r in groups["outfield"]["rows"]] == ["Back"]
    assert "Arrêts" in groups["keepers"]["columns"]
    assert "Arrêts" not in groups["outfield"]["columns"]


def test_players_the_feed_did_not_cover_are_left_out():
    covered = _app("Covered")
    thin = dict(_app("Thin"), has_detailed_stats="0")
    unused = dict(_app("Unused"), played="0")
    assert [r["name"] for r in mr.player_lines([covered, thin, unused])
            ["outfield"]["rows"]] == ["Covered"]
    assert mr.player_lines([thin, unused]) is None


def test_duels_won_shows_its_own_denominator():
    row = mr.player_lines([_app("A", duels_won=6, duels_lost=6)])["outfield"]["rows"][0]
    duels = next(c for c in row["cells"] if c["label"] == "Duels gagnés")
    assert duels["value"] == {"made": 6, "att": 12, "pct": 50.0}


# --- who led what ----------------------------------------------------------

def test_a_leader_needs_to_be_alone_at_the_top():
    tied = [_app("A", touches=60), _app("B", touches=60)]
    assert mr.standouts(tied) is None
    clear = [_app("A", touches=61), _app("B", touches=60)]
    assert mr.standouts(clear)[0]["name"] == "A"


def test_a_category_nobody_reached_is_not_reported():
    """Leading the match with one key pass is not a fact worth printing."""
    assert mr.standouts([_app("A", key_passes=1), _app("B", key_passes=0)]) is None


def test_a_keeper_does_not_win_an_outfield_category():
    """A keeper collecting crosses would lead recoveries most weeks, and that
    line would say nothing about the game."""
    apps = [_app("Keeper", "GK", recoveries=12, saves=4),
            _app("Back", "DF", recoveries=6)]
    leaders = {s["key"]: s["name"] for s in mr.standouts(apps)}
    assert leaders["recoveries"] == "Back"
    assert leaders["saves"] == "Keeper"
