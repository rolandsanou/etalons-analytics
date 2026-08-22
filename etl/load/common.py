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
