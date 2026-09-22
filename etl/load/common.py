"""Helpers shared by the analysis modules in this package.

Keep these public and dependency-free so no analysis module has to import a
private name from a sibling.
"""

from ..util import as_float, as_int  # noqa: F401 (re-exported for analyses)


def points_from(row):
    """Match points from a row carrying gf/ga (an appearance or a match)."""
    gf, ga = as_int(row["gf"]), as_int(row["ga"])
    return 3 if gf > ga else (1 if gf == ga else 0)


def presence_minutes(app_row):
    """Minutes on the pitch, preferring the reconstructed presence window."""
    if app_row.get("entry_min") not in ("", None):
        return max(as_float(app_row["exit_min"]) - as_float(app_row["entry_min"]), 0.0)
    return float(as_int(app_row.get("minutes")))


def record(results):
    """W/D/L counts plus points per game for a list of 'W'/'D'/'L'."""
    w, d, l = results.count("W"), results.count("D"), results.count("L")
    n = len(results)
    return {"n": n, "w": w, "d": d, "l": l,
            "ppg": round((3 * w + d) / n, 2) if n else None}


# Wikipedia's "Recent call-ups" section lists players called in the last twelve
# months who are NOT in the current squad. It is evidence a player was around
# lately, but it is not an announced squad, and treating it as one makes every
# current player look like a change.
SUPPLEMENTARY_WINDOWS = {"recent"}


def latest_squad_window(callups):
    """The newest announced squad, whatever source it came from.

    Nothing may hard-code a window id for this. A federation list typed into
    data/seed/manual_squads.csv is newer than Wikipedia's section for weeks at a
    time, and three separate copies of this rule had already been written — which
    is exactly how a page ends up showing one squad while the section beneath it
    discusses another.
    """
    dated = {}
    for c in callups:
        if c["window_id"] not in SUPPLEMENTARY_WINDOWS:
            dated.setdefault(c["window_id"], c.get("window_date", ""))
    return max(dated, key=lambda w: dated[w]) if dated else None
