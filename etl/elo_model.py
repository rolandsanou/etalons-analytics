CONT_FINALS = ("african cup of nations", "copa américa", "uefa euro",
               "afc asian cup", "gold cup", "oceania nations cup", "confederations cup")


def k_factor(tournament):
    t = str(tournament).lower()
    if "fifa world cup" in t and "qualification" not in t:
        return 60
    if any(c in t for c in CONT_FINALS) and "qualification" not in t:
        return 50
    if "qualification" in t:
        return 40
    if t == "friendly":
        return 20
    return 30


def gd_multiplier(gd):
    gd = abs(gd)
    if gd <= 1:
        return 1.0
    if gd == 2:
        return 1.5
    return 1.75 + (gd - 3) / 8.0


def expected(diff):
    return 1.0 / (1.0 + 10 ** (-diff / 400.0))


def update(home_elo, away_elo, home_goals, away_goals, tournament, neutral):
    diff = home_elo - away_elo + (0 if neutral else 100)
    e_home = expected(diff)
    if home_goals > away_goals:
        s = 1.0
    elif home_goals == away_goals:
        s = 0.5
    else:
        s = 0.0
    delta = k_factor(tournament) * gd_multiplier(home_goals - away_goals) * (s - e_home)
    return home_elo + delta, away_elo - delta
