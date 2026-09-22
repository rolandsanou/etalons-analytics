"""What one match says, once its feed has been read.

Three questions a reader asks after a game, answered from what the match
actually produced rather than from a narrative:

  - how it went in each half, and when the goals landed
  - which parts of the game the team won and lost — building, progressing,
    finishing, contesting — as attempts completed out of attempts made
  - what each player did with the ball and without it

Nothing here scores a performance. There is no man of the match and no
composite index: a leader is the player with the largest count in one stated
category, always printed with that count beside him, and a phase is the raw
made/attempted pair the feed published. A reader who disagrees with the
emphasis can still see every number it was drawn from.

Coverage is the thing to be honest about. Sofascore publishes this depth for
competitive matches and often not for friendlies — 33 of the 58 matches in the
study window carry it — so every function here returns None rather than a
half-empty section, and the page says the feed did not cover the match instead
of showing blanks.
"""

# Half-by-half: the measures that mean something when a match turns, in the
# order a reader scans them. Percentages are marked so they are never summed.
HALF_ROWS = [
    ("possession_pct", "Possession", True),
    ("shots", "Tirs", False),
    ("shots_on_target", "Tirs cadrés", False),
    ("big_chances", "Grosses occasions", False),
    ("final_third_entries", "Entrées dans le dernier tiers", False),
    ("corners", "Corners", False),
    ("fouls", "Fautes", False),
]

# Each phase is made/attempted pairs, never a score. The pairs come straight
# from the feed's own ratio statistics, so "69 %" always has its 66/95 beside it.
PHASES = [
    ("Construction", [
        ("passes_accurate", "passes", "Passes"),
        ("long_balls", "long_balls_att", "Longs ballons"),
    ]),
    ("Progression", [
        ("final_third_phase", "final_third_phase_att", "Jeu dans le dernier tiers"),
        ("dribbles", "dribbles_att", "Dribbles"),
        ("crosses", "crosses_att", "Centres"),
    ]),
    ("Finition", [
        ("shots_on_target", "shots", "Tirs cadrés"),
        ("big_chances_scored", "big_chances", "Grosses occasions converties"),
    ]),
    ("Duels", [
        ("ground_duels", "ground_duels_att", "Duels au sol"),
        ("aerial_duels", "aerial_duels_att", "Duels aériens"),
        ("tackles_won", "tackles", "Tacles"),
    ]),
]

GOAL_BANDS = [("1_15", "1-15"), ("16_30", "16-30"), ("31_45", "31-45"),
              ("46_60", "46-60"), ("61_75", "61-75"), ("76_90", "76-90"),
              ("et", "Prol.")]

# What a reader wants to see for an outfield player, and what for a keeper.
# Pairs are (made, attempted); a lone key is a plain count.
OUTFIELD_COLS = [
    ("touches", None, "Ballons touchés"),
    (("passes_accurate", "passes"), None, "Passes"),
    ("key_passes", None, "Passes clés"),
    (("duels_won", "_duels_total"), None, "Duels gagnés"),
    ("shots", None, "Tirs"),
    (("tackles_won", "tackles"), None, "Tacles"),
    ("interceptions", None, "Interceptions"),
    ("recoveries", None, "Ballons récupérés"),
]
KEEPER_COLS = [
    ("saves", None, "Arrêts"),
    ("high_claims", None, "Sorties aériennes"),
    ("punches", None, "Dégagements du poing"),
    (("passes_accurate", "passes"), None, "Passes"),
    ("recoveries", None, "Ballons récupérés"),
]

# A category is only worth calling out when somebody clearly led it, so a
# leader needs this many and needs to be alone at the top.
LEADER_MIN = {"touches": 40, "duels_won": 4, "key_passes": 2, "tackles_won": 3,
              "recoveries": 5, "interceptions": 3, "saves": 3, "shots": 3}
# Saves are a keeper's category and nobody else's; the rest are compared among
# outfield players, because a keeper collecting crosses would otherwise lead
# "recoveries" in most matches and the line would say nothing about the game.
KEEPER_CATEGORIES = {"saves"}
LEADER_LABEL = {
    "touches": "le plus de ballons touchés", "duels_won": "le plus de duels gagnés",
    "key_passes": "le plus de passes clés", "tackles_won": "le plus de tacles réussis",
    "recoveries": "le plus de ballons récupérés",
    "interceptions": "le plus d'interceptions", "saves": "le plus d'arrêts",
    "shots": "le plus de tirs",
}


def _n(value):
    """A feed number, or None when the feed did not carry one."""
    if value in ("", None):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _i(value):
    n = _n(value)
    return int(n) if n is not None else None


def _ratio(row, made_key, att_key):
    """made/attempted, with the percentage, or None if either side is missing."""
    made, att = _n(row.get(made_key)), _n(row.get(att_key))
    if made is None or att is None or att <= 0:
        return None
    return {"made": int(made), "att": int(att), "pct": round(100 * made / att, 1)}


# --- how the match went, half by half -------------------------------------

def half_split(first, second):
    """Both halves side by side, for whichever measures the feed carried.

    `first` and `second` are each {"bf": row, "opp": row}. A measure absent from
    both halves is dropped rather than printed empty; a measure present in one
    half only is kept, because "no shots in the second half" is itself the
    finding and blanking it would hide it.
    """
    if not (first and second):
        return None
    out = []
    for key, label, is_pct in HALF_ROWS:
        cells = {}
        for name, half in (("h1", first), ("h2", second)):
            cells[name] = {side: _n((half.get(side) or {}).get(key))
                           for side in ("bf", "opp")}
        if all(v is None for c in cells.values() for v in c.values()):
            continue
        out.append({"key": key, "label": label, "pct": is_pct, **cells})
    return out or None


def goal_windows(state):
    """Goals for and against in each quarter-hour, as the feed's own bands.

    Bands are how a match is normally read back — a side that concedes twice in
    the opening quarter played a different game from one that conceded twice in
    stoppage time, and the scoreline alone cannot tell them apart.
    """
    if not state:
        return None
    bands = []
    for suffix, label in GOAL_BANDS:
        gf, ga = _i(state.get(f"gf_{suffix}")), _i(state.get(f"ga_{suffix}"))
        if gf is None and ga is None:
            continue
        bands.append({"band": label, "gf": gf or 0, "ga": ga or 0})
    if not any(b["gf"] or b["ga"] for b in bands):
        return None
    return bands


def match_shape(state):
    """Minutes spent ahead, level and behind, and who scored first.

    A 2-2 reached from two goals down is not the 2-2 that threw away a two-goal
    lead, and the result column records both identically.
    """
    if not state:
        return None
    lead, level, trail = (_n(state.get("min_leading")), _n(state.get("min_level")),
                          _n(state.get("min_trailing")))
    if lead is None and level is None and trail is None:
        return None
    return {
        "leading": int(lead or 0), "level": int(level or 0),
        "trailing": int(trail or 0),
        "effective_length": _n(state.get("effective_length")),
        "first_goal": state.get("first_goal") or "",
        "led": state.get("led") == "1", "trailed": state.get("trailed") == "1",
    }


# --- which parts of the game were won -------------------------------------

def phase_groups(bf, opp):
    """Build-up, progression, finishing and duels, as made out of attempted.

    Both sides are carried so a number can be read against the only comparison
    that matters — what the opponent managed in the same match, on the same
    pitch, against the same referee.
    """
    if not bf:
        return None
    groups = []
    for label, pairs in PHASES:
        rows = []
        for made_key, att_key, row_label in pairs:
            ours = _ratio(bf, made_key, att_key)
            theirs = _ratio(opp or {}, made_key, att_key)
            if ours is None and theirs is None:
                continue
            rows.append({"label": row_label, "bf": ours, "opp": theirs})
        if rows:
            groups.append({"label": label, "rows": rows})
    return groups or None


# --- what the players did --------------------------------------------------

def _with_totals(app):
    """A copy carrying the derived denominators the columns need."""
    row = dict(app)
    won, lost = _n(app.get("duels_won")), _n(app.get("duels_lost"))
    row["_duels_total"] = (won + lost) if (won is not None and lost is not None) else None
    return row


def _line(app, cols):
    cells = []
    for key, _unused, label in cols:
        if isinstance(key, tuple):
            cells.append({"label": label, "value": _ratio(app, key[0], key[1])})
        else:
            cells.append({"label": label, "value": _i(app.get(key))})
    return {
        "player_id": app.get("player_id", ""),
        "name": app.get("name", ""),
        "pos": app.get("pos", ""),
        "minutes": _i(app.get("minutes")) or 0,
        "rating": _n(app.get("rating")),
        "goals": _i(app.get("goals")) or 0,
        "assists": _i(app.get("assists")) or 0,
        "started": app.get("started") == "1",
        "cells": cells,
    }


def player_lines(apps):
    """Two tables — outfield players and keepers — because the columns differ.

    Saves and claims say everything about a keeper's match and nothing about a
    full-back's, so putting both in one table means half of every row is blank
    by construction. Players the feed did not cover are left out rather than
    shown as a row of dashes: on the matches it covers thinly that would be the
    whole team, and an empty table says less than an honest absence.
    """
    covered = [_with_totals(a) for a in apps
               if a.get("has_detailed_stats") == "1" and a.get("played") == "1"]
    if not covered:
        return None
    order = lambda r: (not r["started"], -r["minutes"], r["name"])  # noqa: E731
    groups = {}
    for name, cols, want_gk in (("outfield", OUTFIELD_COLS, False),
                                ("keepers", KEEPER_COLS, True)):
        rows = sorted((_line(a, cols) for a in covered
                       if (a.get("pos") == "GK") == want_gk), key=order)
        if rows:
            groups[name] = {"columns": [label for _k, _u, label in cols],
                            "rows": rows}
    return groups or None


def standouts(apps):
    """Who led the match in each category, where somebody clearly did.

    Deliberately not a rating. Each entry is one player, one named category and
    the count he reached — a fact the reader can check against the table below
    it — and a category nobody led, or that two players tied, is simply left
    out rather than broken by a tiebreak nobody asked for.
    """
    covered = [_with_totals(a) for a in apps
               if a.get("has_detailed_stats") == "1" and a.get("played") == "1"]
    if not covered:
        return None
    out = []
    for key, floor in LEADER_MIN.items():
        keepers = key in KEEPER_CATEGORIES
        pool = [a for a in covered if (a.get("pos") == "GK") == keepers]
        scored = [(_n(a.get(key)) or 0, a) for a in pool]
        best = max((v for v, _ in scored), default=0)
        if best < floor:
            continue
        leaders = [a for v, a in scored if v == best]
        if len(leaders) != 1:
            continue
        out.append({"key": key, "label": LEADER_LABEL[key],
                    "name": leaders[0].get("name", ""),
                    "player_id": leaders[0].get("player_id", ""),
                    "value": int(best)})
    return out or None
