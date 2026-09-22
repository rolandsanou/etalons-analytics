"""The post-match sections, rendered.

Match pages are static HTML with no JavaScript, so everything here is markup and
CSS — no chart library, no client-side rendering. That is a constraint worth
keeping: these pages are the ones search engines and readers on a slow
connection actually reach, and a bar drawn with a div arrives with the page.

The analysis itself is in matchreport.py, which knows nothing about HTML. This
module knows nothing about where the numbers came from.
"""

from .layout import esc
from .matchreport import (goal_windows, half_split, match_shape, phase_groups,
                          player_lines, standouts)


def _pct_or_dash(fmt, value, unit=""):
    return "–" if value is None else f"{fmt(value, 0)}{unit}"


def _ratio_cell(fmt, r):
    """"66/95" with the share beneath it, so the percentage always shows its work."""
    if not r:
        return '<span class="rr">–</span>'
    return (f'<span class="rr"><b>{fmt(r["made"], 0)}/{fmt(r["att"], 0)}</b>'
            f'<i>{fmt(r["pct"], 0)} %</i></span>')


# --- how the match went ----------------------------------------------------

def unfolding(ctx, state, first, second, fmt):
    """Minutes by game state, goals by quarter-hour, and the two halves."""
    t = ctx.t
    shape, windows, halves = (match_shape(state), goal_windows(state),
                              half_split(first, second))
    if not (shape or windows or halves):
        return None
    out = []

    if shape:
        total = max(shape["leading"] + shape["level"] + shape["trailing"], 1)
        segs = [("lead", shape["leading"], t("en tête")),
                ("level", shape["level"], t("à égalité")),
                ("trail", shape["trailing"], t("menés"))]
        bars = "".join(
            f'<i class="{cls}" style="width:{100 * mins / total:.1f}%" '
            f'title="{esc(label)} : {mins} min"></i>'
            for cls, mins, label in segs if mins)
        legend = " · ".join(f'<span class="{cls}">{esc(label)} {mins} min</span>'
                            for cls, mins, label in segs if mins)
        out.append(f'<div class="shape"><div class="shapebar">{bars}</div>'
                   f'<p class="sub">{legend}</p></div>')

    if windows:
        peak = max(max(w["gf"], w["ga"]) for w in windows) or 1
        cells = "".join(f"""<div class="gw">
  <span class="gf">{"●" * w["gf"] or "&nbsp;"}</span>
  <i style="height:{6 + 14 * max(w["gf"], w["ga"]) / peak:.0f}px"></i>
  <span class="ga">{"●" * w["ga"] or "&nbsp;"}</span>
  <em>{esc(w["band"])}</em></div>""" for w in windows)
        out.append(f'<div class="gwins">{cells}</div>'
                   f'<p class="sub">{esc(t("Buts marqués (haut) et encaissés (bas), "
                                          "par tranche de quinze minutes."))}</p>')

    if halves:
        head = (f'<tr><th></th><th colspan="2">{esc(t("1re mi-temps"))}</th>'
                f'<th colspan="2">{esc(t("2e mi-temps"))}</th></tr>'
                f'<tr><th></th><th class="num">{esc(t("BF"))}</th>'
                f'<th class="num">{esc(t("Adv."))}</th>'
                f'<th class="num">{esc(t("BF"))}</th>'
                f'<th class="num">{esc(t("Adv."))}</th></tr>')
        body = "".join(
            f'<tr><td>{esc(t(r["label"]))}</td>'
            + "".join(f'<td class="num">'
                      f'{_pct_or_dash(fmt, r[half][side], " %" if r["pct"] else "")}</td>'
                      for half in ("h1", "h2") for side in ("bf", "opp"))
            + "</tr>" for r in halves)
        out.append(f'<div class="tablewrap"><table class="halves">{head}{body}</table></div>')

    return "".join(out)


# --- which parts of the game were won --------------------------------------

def phases(ctx, bf, opp, fmt):
    """Build-up, progression, finishing and duels, each as made out of attempted."""
    groups = phase_groups(bf, opp)
    if not groups:
        return None
    t = ctx.t
    blocks = []
    for g in groups:
        rows = []
        for r in g["rows"]:
            ours, theirs = r["bf"], r["opp"]
            share = 50.0
            if ours and theirs:
                total = ours["pct"] + theirs["pct"]
                share = 100 * ours["pct"] / total if total else 50.0
            rows.append(f"""<div class="phaserow">
  <div class="lbl"><span>{_ratio_cell(fmt, ours)}</span>
    <span>{esc(t(r["label"]))}</span><span>{_ratio_cell(fmt, theirs)}</span></div>
  <div class="bar"><i style="width:{share:.1f}%"></i></div>
</div>""")
        blocks.append(f'<h4>{esc(t(g["label"]))}</h4>'
                      f'<div class="phasegrp">{"".join(rows)}</div>')
    return "".join(blocks)


# --- what the players did --------------------------------------------------

def players(ctx, apps, players_with_pages, fmt):
    """A row per covered player, plus the categories somebody clearly led."""
    groups = player_lines(apps)
    if not groups:
        return None
    t = ctx.t
    out = []

    leaders = standouts(apps)
    if leaders:
        items = "".join(
            f'<li><b>{esc(s["name"])}</b> — {esc(t(s["label"]))} '
            f'({fmt(s["value"], 0)})</li>' for s in leaders)
        out.append(f'<ul class="standouts">{items}</ul>')

    def table(block, title):
        head = (f'<tr><th>{esc(t("Joueur"))}</th><th class="num">{esc(t("Min"))}</th>'
                + "".join(f'<th class="num">{esc(t(c))}</th>'
                          for c in block["columns"])
                + f'<th class="num">{esc(t("Note"))}</th></tr>')
        body = []
        for r in block["rows"]:
            name = esc(r["name"])
            if r["player_id"] in players_with_pages:
                name = f'<a href="{ctx.url("player", r["player_id"])}">{name}</a>'
            marks = []
            if r["goals"]:
                marks.append(t("{n} but" if r["goals"] == 1 else "{n} buts", n=r["goals"]))
            if r["assists"]:
                marks.append(t("{n} p.d.", n=r["assists"]))
            mark = f' <span class="what">({esc(", ".join(marks))})</span>' if marks else ""
            cells = "".join(
                f'<td class="num">'
                + (_ratio_cell(fmt, c["value"]) if isinstance(c["value"], dict)
                   else ("–" if c["value"] is None else fmt(c["value"], 0)))
                + "</td>" for c in r["cells"])
            body.append(f'<tr><td>{name}{mark}</td>'
                        f'<td class="num">{r["minutes"]}\'</td>{cells}'
                        f'<td class="num">'
                        f'{fmt(r["rating"], 2) if r["rating"] else "–"}</td></tr>')
        return (f'<h4>{esc(title)}</h4><div class="tablewrap">'
                f'<table class="pstats">{head}{"".join(body)}</table></div>')

    if "outfield" in groups:
        out.append(table(groups["outfield"], t("Joueurs de champ")))
    if "keepers" in groups:
        out.append(table(groups["keepers"], t("Gardien")))
    return "".join(out)
