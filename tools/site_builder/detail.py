"""Match and player detail pages.

Rendered as static HTML — tables, timelines and CSS comparison bars — so they are
readable without JavaScript and indexable by search engines. That is also why the
copy is translated here at build time rather than swapped in by JS: each language
gets a real, crawlable page.
"""

import re
import unicodedata

from . import layout, seo
from .layout import avatar, card, esc, page

# French source strings double as the translation keys (see strings.py)
POS_LABEL_KEY = {"GK": "Gardien", "DF": "Défenseur", "MF": "Milieu", "FW": "Attaquant"}
POS_LABEL = POS_LABEL_KEY          # kept for callers that only need French
POS_ORDER = {"GK": 0, "DF": 1, "MF": 2, "FW": 3}
RESULT_WORD = {"W": "Victoire", "D": "Match nul", "L": "Défaite"}

STATUS_WORD = {
    "active": "International actif",
    "fringe": "En marge du groupe",
    "out": "Hors du groupe",
    "retired_int": "Retraité international",
    "retired_career": "Retraité",
}

# (column, French label, unit)
STAT_ROWS = [
    ("possession_pct", "Possession", "%"),
    ("shots", "Tirs", ""),
    ("shots_on_target", "Tirs cadrés", ""),
    ("big_chances", "Grosses occasions", ""),
    ("passes", "Passes", ""),
    ("passes_accurate", "Passes réussies", ""),
    ("corners", "Corners", ""),
    ("fouls", "Fautes", ""),
    ("tackles", "Tacles", ""),
    ("interceptions", "Interceptions", ""),
    ("saves", "Arrêts", ""),
]


def slugify(text):
    s = unicodedata.normalize("NFD", str(text))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", s.lower())).strip("-")


def match_slug(event):
    return f"{event['date']}-{slugify(event['opponent'])}"


def _num(x, default=0):
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def _int(x, default=0):
    return int(_num(x, default))


# Number formatting differs by language: French groups with a space and uses a
# comma for decimals, English groups with a comma and uses a point. The build
# renders one language at a time, so a module-level locale is safe and keeps the
# call sites (_fmt is used in dozens of f-strings) unchanged.
_LOCALE = "fr"


def set_locale(lang):
    global _LOCALE
    _LOCALE = lang
    # these pages write their notes into the HTML, so the label is resolved
    # here rather than left to the i18n script
    layout.PLAIN_LABEL = "En clair" if lang == "fr" else "In plain terms"


def _fmt(x, dec=0):
    if x in ("", None):
        return "–"
    grouped = f"{_num(x):,.{dec}f}"
    if _LOCALE == "en":
        return grouped
    return grouped.replace(",", " ").replace(".", ",")


def ordinal(n, lang):
    """81 -> "81st" in English, "81e" in French."""
    n = int(n)
    if lang != "en":
        return f"{n}e"
    if n % 100 in (11, 12, 13):
        return f"{n}th"
    return f"{n}{ {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th') }"


def _kv(pairs):
    return "".join(f"<dt>{esc(k)}</dt><dd>{esc(v)}</dd>" for k, v in pairs)


# ---------------------------------------------------------------- match page

def stat_bars(ctx, bf, opp):
    if not bf or not opp:
        return ('<p class="sub">'
                + esc(ctx.t("Statistiques détaillées non publiées pour ce match."))
                + "</p>")
    out = []
    for key, label, unit in STAT_ROWS:
        a, b = bf.get(key, ""), opp.get(key, "")
        if a in ("", None) and b in ("", None):
            continue
        av, bv = _num(a), _num(b)
        total = av + bv
        pa = 100 * av / total if total else 50
        out.append(f"""<div class="statrow">
  <div class="lbl"><span>{_fmt(a, 0)}{unit}</span><span>{esc(ctx.t(label))}</span>
    <span>{_fmt(b, 0)}{unit}</span></div>
  <div class="bar"><i style="width:{pa:.1f}%"></i></div>
</div>""")
    return '<div class="statbars">' + "".join(out) + "</div>"


def goal_timeline(ctx, goals, subs, cards, opponent):
    t = ctx.t
    events = []
    for g in goals:
        minute, added = _int(g["minute"]), _int(g["added_time"])
        label = f"{minute}'" + (f"+{added}" if added else "")
        kind = "bf" if g["is_bf"] == "1" else "opp"
        extra = {"penalty": " (pen.)", "ownGoal": " (csc)"}.get(g["class"], "")
        assist = (f" · {esc(g['assist_name'])}" if g["assist_name"] else "")
        side = t("Burkina Faso") if kind == "bf" else opponent
        events.append((minute + added / 100, f"""<div class="tevent {kind}">
  <span class="min">{label}</span><span class="mark">{esc(t("BUT"))}</span>
  <span><span class="who">{esc(g['scorer_name'] or '?')}</span>{extra}
    <span class="what"> — {esc(side)}{assist}</span></span></div>"""))
    for c in cards:
        if c["card"] not in ("yellow", "red", "yellowRed"):
            continue
        minute = _int(c["minute"])
        mark = "J" if c["card"] == "yellow" else "R"
        kind = "bf" if c["is_bf"] == "1" else "opp"
        events.append((minute, f"""<div class="tevent {kind}">
  <span class="min">{minute}'</span><span class="mark">{mark}</span>
  <span><span class="who">{esc(c['name'])}</span>
    <span class="what"> — {esc(c['reason'] or t("carton"))}</span></span></div>"""))
    for s in subs:
        if s["is_bf"] != "1":
            continue
        minute = _int(s["minute"])
        injury = f' {esc(t("(blessure)"))}' if s["injury"] == "1" else ""
        events.append((minute + 0.5, f"""<div class="tevent bf">
  <span class="min">{minute}'</span><span class="mark">{esc(t("CHG"))}</span>
  <span><span class="who">{esc(s['in_name'])}</span>
    <span class="what"> ← {esc(s['out_name'])}{injury}</span></span></div>"""))
    if not events:
        return ('<p class="sub">'
                + esc(ctx.t("Aucun événement enregistré pour ce match.")) + "</p>")
    events.sort(key=lambda e: e[0])
    return '<div class="timeline">' + "".join(html for _, html in events) + "</div>"


def lineup_block(ctx, apps, players_with_pages):
    t = ctx.t

    def rows(entries):
        entries = sorted(entries, key=lambda a: (POS_ORDER.get(a["pos"], 9),
                                                 -_int(a["minutes"])))
        out = []
        for a in entries:
            name = esc(a["name"])
            if a["player_id"] in players_with_pages:
                name = f'<a href="{ctx.url("player", a["player_id"])}">{name}</a>'
            bits = []
            if _int(a["goals"]):
                n = _int(a["goals"])
                bits.append(t("{n} but" if n == 1 else "{n} buts", n=n))
            if _int(a["assists"]):
                bits.append(t("{n} p.d.", n=_int(a["assists"])))
            marks = f' <span class="what">({", ".join(bits)})</span>' if bits else ""
            rating = _num(a["rating"])
            out.append(f"""<div class="lrow"><span class="pos">{esc(a['pos'])}</span>
  <span>{name}{marks}</span><span class="mins">{_int(a['minutes'])}'</span>
  <span class="mins">{_fmt(rating, 2) if rating else '–'}</span></div>""")
        return '<div class="lineup">' + "".join(out) + "</div>"

    starters = [a for a in apps if a["started"] == "1" and a["played"] == "1"]
    subs = [a for a in apps if a["started"] != "1" and a["played"] == "1"]
    unused = [a for a in apps if a["played"] != "1"]
    blocks = [f'<h4>{esc(t("Titulaires ({n})", n=len(starters)))}</h4>{rows(starters)}']
    if subs:
        blocks.append(f'<h4>{esc(t("Entrés en jeu ({n})", n=len(subs)))}</h4>{rows(subs)}')
    if unused:
        names = ", ".join(esc(a["name"]) for a in unused)
        blocks.append(f'<h4>{esc(t("Non entrés ({n})", n=len(unused)))}</h4>'
                      f'<p class="sub">{names}</p>')
    return "".join(blocks)


def match_page(d, ctx, event, prev_event, next_event, players_with_pages):
    t = ctx.t
    eid = event["event_id"]
    gf, ga = _int(event["gf"]), _int(event["ga"])
    result = t(RESULT_WORD[event["result"]])
    venue = t({"H": "à domicile", "A": "à l'extérieur"}.get(event["venue"], ""))
    state = d.state_by.get(eid, {})
    stats = d.stats_for_event(eid)
    pens = event.get("pens")
    score = f"{gf} – {ga}" + (f" ({pens} t.a.b.)" if pens else "")

    facts = [(t("Compétition"), event["tournament"]), (t("Date"), event["date"]),
             (t("Lieu"), t({"H": "Domicile", "A": "Extérieur"}.get(event["venue"], "–"))),
             (t("Système"), event.get("bf_formation") or "–"),
             (t("Système adverse"), event.get("opp_formation") or "–")]
    if state:
        facts += [(t("Durée effective"), f"{_fmt(state['effective_length'])} min"),
                  (t("Minutes en tête"), _fmt(state["min_leading"], 0)),
                  (t("Minutes menés"), _fmt(state["min_trailing"], 0))]

    formation = (t(", formation {f}", f=event["bf_formation"])
                 if event.get("bf_formation") else "")
    head = f"""<div class="hero-band"><div class="inner">
  <p class="eyebrow">{esc(event['tournament'])} · {esc(event['date'])}</p>
  <h1>{esc(t("Burkina Faso"))} <span>{esc(score)}</span> {esc(event['opponent'])}</h1>
  <p>{esc(t("{result} {venue}{formation}.", result=result, venue=venue, formation=formation))}</p>
</div></div>"""

    pager_prev = (f'<a href="{ctx.url("match", match_slug(prev_event))}">← '
                  f'{esc(prev_event["opponent"])} ({prev_event["date"]})</a>'
                  if prev_event else "<span></span>")
    pager_next = (f'<a href="{ctx.url("match", match_slug(next_event))}">'
                  f'{esc(next_event["opponent"])} ({next_event["date"]}) →</a>'
                  if next_event else "<span></span>")

    body = f"""{head}
<main>
  <p class="crumb"><a href="{ctx.url('home')}">{esc(t("Accueil"))}</a> ›
     <a href="{ctx.url('matches')}">{esc(t("Matchs"))}</a> › {esc(event['date'])}</p>
  <div class="grid">
    {card(width="w8", title_html=f'<h3>{esc(t("Chronologie"))}</h3>',
          extra=goal_timeline(ctx, d.goals_for_event(eid), d.subs_for_event(eid),
                              d.cards_for_event(eid), event["opponent"]),
          plain_text=t("L'ordre des événements du match : buts, changements, cartons. "
                       "Les minutes comptent les arrêts de jeu, donc un but à 90+3 "
                       "apparaît après la 90e."))}
    {card(width="w4", title_html=f'<h3>{esc(t("Fiche du match"))}</h3>',
          extra=f'<dl class="kv">{_kv(facts)}</dl>',
          plain_text=t("« Durée effective » est le temps réellement joué, arrêts de "
                       "jeu inclus : elle dépasse presque toujours 90 minutes. Les "
                       "minutes passées en tête ou menés disent comment le match s'est "
                       "déroulé, pas seulement comment il s'est terminé."))}
    {card(width="w6", title_html=f'<h3>{esc(t("Statistiques d\'équipe"))}</h3>',
          extra=stat_bars(ctx, stats.get("bf"), stats.get("opp")),
          plain_text=t("Le Burkina à gauche, l'adversaire à droite. Comparez les deux "
                       "colonnes plutôt qu'un chiffre seul : dominer la possession ou "
                       "les tirs n'a jamais gagné un match à lui tout seul."))}
    {card(width="w6", title_html=f'<h3>{esc(t("Composition"))}</h3>',
          extra=lineup_block(ctx, d.apps_for_event(eid), players_with_pages),
          plain_text=t("Le onze de départ, les entrants, et ceux restés sur le banc. "
                       "La note est celle du fournisseur de données pour ce match ; "
                       "elle manque sur les rencontres les moins couvertes."))}
  </div>
  <div class="pager">{pager_prev}{pager_next}</div>
</main>"""
    scoreline = f"Burkina Faso {gf}–{ga} {event['opponent']}"
    spelled_date = seo.long_date(event["date"], ctx.lang)
    return page(ctx,
                title=scoreline,
                full_title=f"{scoreline} — {spelled_date}",
                description=t("{result} {gf}-{ga} contre {opponent} le {date} "
                              "({tournament}) : composition, statistiques et "
                              "chronologie des buts.",
                              result=result, gf=gf, ga=ga,
                              opponent=event["opponent"], date=spelled_date,
                              tournament=event["tournament"]),
                structured=(
                    seo.sports_event(ctx.lang, event, ctx.canonical,
                                     f"{scoreline} ({spelled_date})",
                                     t("Burkina Faso")),
                    seo.breadcrumbs([
                        (t("Accueil"), ctx.abs_url("home")),
                        (t("Matchs"), ctx.abs_url("matches")),
                        (scoreline, None)]),
                ),
                body=body, page_class="match-page")


# --------------------------------------------------------------- player page

def player_page(d, ctx, profile, players_with_pages):
    t = ctx.t
    pid = profile["player_id"]
    imp = d.importance_by.get(pid, {})
    bench = d.bench_by.get(pid, {})
    apps = sorted(d.apps_for_player(pid), key=lambda a: a["date"], reverse=True)
    photo = d.photo("player", pid)
    credit = d.photo_credit("player", pid)
    name = profile["name"]

    club = profile.get("club_v") or profile.get("club") or "–"
    league = profile.get("league_v") or ""
    pos = t(POS_LABEL_KEY.get(profile["pos"], profile["pos"] or "–"))
    status = t(STATUS_WORD.get(profile.get("status"), "")) if profile.get("status") else ""

    facts = [
        (t("Poste"), pos),
        (t("Âge"), t("{n} ans", n=_fmt(profile.get("age"), 1))
         if profile.get("age") else "–"),
        (t("Club"), club + (f" · {league}" if league else "")),
        (t("Sélections (carrière)"), profile.get("caps") or "–"),
        (t("Buts (carrière)"), profile.get("goals_career") or "–"),
        (t("Valeur estimée"),
         f"{_fmt(_num(profile['market_value_eur']) / 1e6, 1)} M€"
         if profile.get("market_value_eur") else "–"),
        (t("Taille"), t("{n} cm", n=profile["height"]) if profile.get("height") else "–"),
        (t("Pied"), profile.get("foot") or "–"),
        (t("Dernière apparition"), profile.get("last_seen") or "–"),
    ]

    window = [
        (t("Matchs dans le groupe"), profile.get("matchday_squads")),
        (t("Apparitions"), profile.get("apps")),
        (t("Titularisations"), profile.get("starts")),
        (t("Minutes"), _fmt(profile.get("minutes"))),
        (t("Buts"), profile.get("goals")),
        (t("Passes décisives"), profile.get("assists")),
        (t("Passes réussies"), f"{_fmt(profile['pass_pct'], 1)} %"
         if profile.get("pass_pct") else "–"),
        (t("Dribbles réussis"), f"{profile.get('dribbles_won') or 0}/"
                                f"{profile.get('dribbles_attempted') or 0}"),
        (t("Note moyenne"), _fmt(profile.get("rating_avg"), 2)
         if profile.get("rating_avg") else "–"),
    ]
    if profile["pos"] == "GK":
        window.append((t("Arrêts"), profile.get("saves")))

    gated = t("– (échantillon insuffisant)")
    imp_rows = []
    if imp:
        imp_rows = [
            (t("Rôle"), t({"pilier": "Pilier", "rotation": "Rotation",
                           "marge": "Marge"}.get(imp.get("tier", ""), "–"))),
            (t("Part des minutes"),
             f"{_fmt(_num(imp.get('minutes_share')) * 100, 0)} %"),
            (t("Titularisations"), f"{imp.get('starts')}/{imp.get('squad_matches')}"),
            (t("On/Off ±/90"), imp.get("onoff_diff") or gated),
            (t("PPM titulaire − remplaçant"), imp.get("ppg_diff") or gated),
            (t("Buts+passes /90"), imp.get("ga90") or gated),
        ]

    rows = []
    for a in apps[:60]:
        ev = d.event_by.get(a["event_id"], {})
        link = (f'<a href="{ctx.url("match", match_slug(ev))}">{esc(a["opponent"])}</a>'
                if ev else esc(a["opponent"]))
        res = ("W" if _int(a["gf"]) > _int(a["ga"])
               else ("D" if _int(a["gf"]) == _int(a["ga"]) else "L"))
        chip = f'<span class="chip {res}">{ctx.result_letter[res]}</span>'
        played = a["played"] == "1"
        st = (t("Tit.") if played and a["started"] == "1"
              else (t("Rempl.") if played else t("Non entré")))
        rows.append(f"""<tr><td>{esc(a['date'])}</td><td>{chip}</td><td>{link}</td>
  <td class="num">{esc(a['gf'])}-{esc(a['ga'])}</td><td class="num">{esc(st)}</td>
  <td class="num">{str(_int(a['minutes'])) + "'" if played else '–'}</td>
  <td class="num">{_int(a['goals']) or '–'}</td>
  <td class="num">{_int(a['assists']) or '–'}</td>
  <td class="num">{_fmt(a['rating'], 2) if _num(a['rating']) else '–'}</td></tr>""")
    table = f"""<div class="tablewrap"><table>
  <tr><th>{esc(t("Date"))}</th><th></th><th>{esc(t("Adversaire"))}</th>
      <th class="num">{esc(t("Score"))}</th><th class="num">{esc(t("Statut"))}</th>
      <th class="num">{esc(t("Min"))}</th><th class="num">{esc(t("Buts"))}</th>
      <th class="num">{esc(t("P. déc."))}</th>
      <th class="num">{esc(t("Note"))}</th></tr>
  {''.join(rows)}</table></div>"""

    bench_block = ""
    if bench and _int(bench.get("sub_apps")) >= 3:
        bench_block = card(
            width="w4", title_html=f'<h3>{esc(t("En sortie de banc"))}</h3>',
            extra=f'<dl class="kv">{_kv([(t("Entrées"), bench["sub_apps"]), (t("Minutes"), _fmt(bench["sub_min"])), (t("Buts + passes"), bench["sub_ga"]), (t("Entrée moyenne"), _fmt(bench["entry_avg"], 0) + "'")])}</dl>',
            plain_text=t("Ce que le joueur produit en entrant en cours de match. Sur "
                         "aussi peu de minutes, un seul but change tout : à lire comme "
                         "une indication, pas comme une preuve."))

    credit_html = ""
    if credit:
        credit_html = (f'<p class="photo-credit">'
                       f'{esc(t("Photo : {author} · {licence} · ", author=credit["author"], licence=credit["licence"]))}'
                       f'<a href="{esc(credit["credit_url"])}" rel="nofollow">Commons</a></p>')

    head = f"""<div class="hero-band"><div class="inner">
  <div class="entity">
    {avatar(ctx.asset(photo) if photo else None, name, "photo", eager=True)}
    <div class="meta">
      <p class="eyebrow">{esc(status)}</p>
      <h1>{esc(name)}</h1>
      <p class="sub">{esc(pos)} · {esc(club)}{' · ' + esc(league) if league else ''}</p>
      {credit_html}
    </div>
  </div>
</div></div>"""

    body = f"""{head}
<main>
  <p class="crumb"><a href="{ctx.url('home')}">{esc(t("Accueil"))}</a> ›
     <a href="{ctx.url('players')}">{esc(t("Joueurs"))}</a> › {esc(name)}</p>
  <div class="grid">
    {card(width="w4", title_html=f'<h3>{esc(t("Identité"))}</h3>',
          extra=f'<dl class="kv">{_kv(facts)}</dl>',
          plain_text=t("Club, valeur et contrat viennent du profil du joueur chez le "
                       "fournisseur de données et changent avec les transferts. Les "
                       "sélections et buts de carrière couvrent toute la carrière, pas "
                       "seulement la période étudiée ici."))}
    {card(width="w4", title_html=f'<h3>{esc(t("Bilan depuis janv. 2022"))}</h3>',
          extra=f'<dl class="kv">{_kv(window)}</dl>',
          plain_text=t("Uniquement depuis janvier 2022 : ce n'est pas le bilan d'une "
                       "carrière. « Matchs dans le groupe » compte les feuilles de "
                       "match, y compris celles où le joueur n'est pas entré."))}
    {card(width="w4", title_html=f'<h3>{esc(t("Importance"))}</h3>',
          extra=(f'<dl class="kv">{_kv(imp_rows)}</dl>' if imp_rows else
                 '<p class="sub">'
                 + esc(t("Pas encore assez de matchs pour situer ce joueur.")) + '</p>'),
          plain_text=t("La place du joueur dans le groupe, mesure par mesure, sans "
                       "note unique : chacune se lit à part. Un tiret veut dire trop "
                       "peu de matchs pour le situer honnêtement."))}
    {bench_block}
    {card(width="w12", title_html=f'<h3>{esc(t("Match par match"))}</h3>', extra=table,
          plain_text=t("Chaque feuille de match depuis 2022. « Non entré » veut dire "
                       "convoqué mais resté sur le banc, ce qui est aussi une "
                       "information. Une note absente veut dire que le match n'a pas "
                       "de statistiques détaillées."))}
  </div>
</main>"""
    # A description carrying this player's actual figures is unique per page and
    # tells a searcher something; the generic sentence is only the fallback for
    # players with no appearances in the window.
    if _int(profile.get("apps")):
        description = t("{name} ({pos}, {club}) avec le Burkina Faso depuis 2022 : "
                        "{apps} apparitions, {minutes} minutes, {goals} buts. "
                        "Fiche complète, match par match.",
                        name=name, pos=pos, club=club,
                        apps=profile["apps"], minutes=_fmt(profile.get("minutes")),
                        goals=_int(profile.get("goals")))
    else:
        description = t("{name} ({pos}, {club}) : sélections, minutes, buts "
                        "et performances avec les Étalons du Burkina Faso "
                        "depuis 2022.", name=name, pos=pos, club=club)

    return page(ctx, title=name,
                full_title=t("{name} — statistiques Burkina Faso", name=name),
                description=description,
                og_type="profile",
                # a portrait is tall: the square card crops to the face, where
                # the wide card would letterbox it
                og_image=photo,
                og_card="summary" if photo else "summary_large_image",
                structured=(
                    seo.person(ctx.lang, profile, ctx.canonical,
                               seo.absolute(photo) if photo else None),
                    seo.breadcrumbs([
                        (t("Accueil"), ctx.abs_url("home")),
                        (t("Joueurs"), ctx.abs_url("players")),
                        (name, None)]),
                ),
                body=body, page_class="player-page")
