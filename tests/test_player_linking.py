"""Linking a published squad list to the profiles behind it.

A federation announces names and clubs. Everything the site says about those
players — age, league, club form — hangs off matching each name to a profile,
and both directions of failure are expensive: an unmatched player shows as a
blank card, a wrongly matched one shows another man's career under his name.
The second is far worse, so these tests fix the real cases both ways.
"""

from etl.extract.sofascore import (_name_compatible, _same_club,
                                   club_backed_match, name_variants)
from etl.transform.players import _latest_known


def _hit(name, club, pid=1):
    return {"type": "player",
            "entity": {"id": pid, "name": name, "country": {"alpha2": "BF"},
                       "team": {"name": club}}}


# --- names -----------------------------------------------------------------

def test_shortened_and_reordered_names_are_the_same_player():
    # Sofascore drops a middle name, or leads with the surname
    assert _name_compatible("Aboubacar Camara", "Aboubacar Sidiki Camara")
    assert _name_compatible("Taonsa Axel", "Axel Sountonoma Taonsa")
    # ... and sometimes simply misspells one part
    assert _name_compatible("Chec Bebel Doumbia", "Cheick Bebel Doumbia")
    # accents must not matter
    assert _name_compatible("Ismael Maiga", "Ismael Maïga")


def test_a_shared_surname_is_not_a_player():
    # the case that prompted the rule: searching for Elohim Kabore at Beveren
    # returns Moise Kabore, who plays for Beveren and is a different man
    assert not _name_compatible("Moise Kaboré", "Élohim Kaboré")
    assert not _name_compatible("Issa Kaboré", "Élohim Kaboré")
    # a surname on its own is never enough, however exactly it matches
    assert not _name_compatible("Camara", "Aboubacar Sidiki Camara")
    assert not _name_compatible("Abdoul Kabore", "Abdel Kabore")


def test_name_variants_shorten_a_full_civil_name():
    assert name_variants("Aboubacar Sidiki Camara") == [
        "aboubacar camara", "sidiki camara", "camara"]
    # nothing to shorten
    assert name_variants("Rachid Kouda") == []


# --- clubs -----------------------------------------------------------------

def test_club_names_match_through_formal_noise():
    assert _same_club("FC Rapid București", "Rapid Bucureşti")
    assert _same_club("Västerås SK", "Västerås SK")
    assert not _same_club("Wrexham", "Mantova")


# --- the two signals together ----------------------------------------------

def test_club_backed_match_needs_both_signals():
    data = {"results": [_hit("Chec Bebel Doumbia", "FC Rapid București", 2369254)]}
    assert club_backed_match(data, "Cheick Bebel Doumbia", "Rapid Bucureşti") == 2369254
    # right club, wrong man
    beveren = {"results": [_hit("Moise Kaboré", "SK Beveren", 1490960)]}
    assert club_backed_match(beveren, "Élohim Kaboré", "SK Beveren") is None
    # right man, wrong club — refuse rather than guess
    assert club_backed_match(data, "Cheick Bebel Doumbia", "Mantova") is None
    # no club recorded means there is no second signal at all
    assert club_backed_match(data, "Cheick Bebel Doumbia", "") is None


def test_only_burkinabe_players_are_considered():
    r = _hit("Chec Bebel Doumbia", "FC Rapid București", 99)
    r["entity"]["country"] = {"alpha2": "CI"}
    assert club_backed_match({"results": [r]},
                             "Cheick Bebel Doumbia", "Rapid Bucureşti") is None


# --- carrying a figure forward ---------------------------------------------

def test_a_silent_squad_list_does_not_erase_a_cap_count():
    """The bug this guards: a federation list carries names and clubs but no
    caps, and reading the newest row blindly reset all 25 players to nothing."""
    group = [{"caps_at_time": "38"}, {"caps_at_time": ""}]
    assert _latest_known(group, "caps_at_time") == "38"


def test_a_stated_figure_still_wins():
    group = [{"caps_at_time": "38"}, {"caps_at_time": "41"}]
    assert _latest_known(group, "caps_at_time") == "41"
    assert _latest_known([{"caps_at_time": ""}], "caps_at_time") == ""
