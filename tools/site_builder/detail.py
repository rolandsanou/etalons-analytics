"""Match and player detail pages.

Rendered as static HTML — tables, timelines and CSS comparison bars — so they
are readable without JavaScript and indexable by search engines.
"""

import re
import unicodedata

from .layout import avatar, card, esc, page

POS_LABEL = {"GK": "Gardien", "DF": "Défenseur", "MF": "Milieu", "FW": "Attaquant"}
POS_ORDER = {"GK": 0, "DF": 1, "MF": 2, "FW": 3}
RESULT_WORD = {"W": "Victoire", "D": "Match nul", "L": "Défaite"}


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


def _fmt(x, dec=0):
    if x in ("", None):
        return "–"
    v = _num(x)
    return f"{v:,.{dec}f}".replace(",", " ").replace(".", ",")


# ---------------------------------------------------------------- match page

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


def stat_bars(bf, opp):
    if not bf or not opp:
        return ('<p class="sub">Statistiques détaillées non publiées pour ce match.</p>')
    out = []
    for key, label, unit in STAT_ROWS:
        a, b = bf.get(key, ""), opp.get(key, "")
        if a in ("", None) and b in ("", None):
            continue
        av, bv = _num(a), _num(b)
        total = av + bv
        pa = 100 * av / total if total else 50
        out.append(f"""<div class="statrow">
  <div class="lbl"><span>{_fmt(a, 0)}{unit}</span><span>{esc(label)}</span>
    <span>{_fmt(b, 0)}{unit}</span></div>
  <div class="bar"><i style="width:{pa:.1f}%"></i></div>
</div>""")
    return '<div class="statbars">' + "".join(out) + "</div>"


def goal_timeline(goals, subs, cards, opponent):
    events = []
    for g in goals:
        minute = _int(g["minute"])
        added = _int(g["added_time"])
        label = f"{minute}'" + (f"+{added}" if added else "")
        kind = "bf" if g["is_bf"] == "1" else "opp"
        who = g["scorer_name"] or "?"
        extra = {"penalty": " (pen.)", "ownGoal": " (csc)"}.get(g["class"], "")
        assist = f" · passe {esc(g['assist_name'])}" if g["assist_name"] else ""
        side = "Burkina Faso" if kind == "bf" else opponent
        events.append((minute + added / 100, f"""<div class="tevent {kind}">
  <span class="min">{label}</span><span class="mark">BUT</span>
  <span><span class="who">{esc(who)}</span>{extra}
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
    <span class="what"> — {esc(c['reason'] or 'carton')}</span></span></div>"""))
    for s in subs:
        if s["is_bf"] != "1":
            continue
        minute = _int(s["minute"])
        events.append((minute + 0.5, f"""<div class="tevent bf">
  <span class="min">{minute}'</span><span class="mark">CHG</span>
  <span><span class="who">{esc(s['in_name'])}</span>
    <span class="what"> pour {esc(s['out_name'])}
    {'(blessure)' if s['injury'] == '1' else ''}</span></span></div>"""))
    if not events:
        return '<p class="sub">Aucun événement enregistré pour ce match.</p>'
    events.sort(key=lambda e: e[0])
    return '<div class="timeline">' + "".join(html for _, html in events) + "</div>"


def lineup_block(apps, players_with_pages):
    starters = [a for a in apps if a["started"] == "1"]
    subs = [a for a in apps if a["started"] != "1" and a["played"] == "1"]
    unused = [a for a in apps if a["played"] != "1"]

    def rows(entries):
        entries = sorted(entries, key=lambda a: (POS_ORDER.get(a["pos"], 9),
                                                 -_int(a["minutes"])))
        out = []
        for a in entries:
            name = esc(a["name"])
            if a["player_id"] in players_with_pages:
                name = (f'<a href="../joueurs/{esc(a["player_id"])}.html">{name}</a>')
            bits = []
            if _int(a["goals"]):
                bits.append(f"{_int(a['goals'])} but" + ("s" if _int(a["goals"]) > 1 else ""))
            if _int(a["assists"]):
                bits.append(f"{_int(a['assists'])} p.d.")
            marks = (f' <span class="what">({", ".join(bits)})</span>' if bits else "")
            rating = _num(a["rating"])
            rat = (f'<span class="mins">{_fmt(rating, 2)}</span>' if rating else
                   '<span class="mins">–</span>')
            mins = _int(a["minutes"])
            out.append(f"""<div class="lrow"><span class="pos">{esc(a['pos'])}</span>
  <span>{name}{marks}</span><span class="mins">{mins}'</span>{rat}</div>""")
        return '<div class="lineup">' + "".join(out) + "</div>"

    blocks = [f"<h4>Titulaires ({len(starters)})</h4>{rows(starters)}"]
    if subs:
        blocks.append(f"<h4>Entrés en jeu ({len(subs)})</h4>{rows(subs)}")
    if unused:
        names = ", ".join(esc(a["name"]) for a in unused)
        blocks.append(f'<h4>Non entrés ({len(unused)})</h4><p class="sub">{names}</p>')
    return "".join(blocks)


def match_page(d, event, prev_event, next_event, players_with_pages):
    eid = event["event_id"]
    gf, ga = _int(event["gf"]), _int(event["ga"])
    result = RESULT_WORD[event["result"]]
    venue = {"H": "à domicile", "A": "à l'extérieur"}.get(event["venue"], "")
    state = d.state_by.get(eid, {})
    stats = d.stats_for_event(eid)
    apps = d.apps_for_event(eid)
    goals = d.goals_for_event(eid)
    pens = event.get("pens")
    score = f"{gf} – {ga}" + (f" ({pens} t.a.b.)" if pens else "")

    title = f"Burkina Faso {gf}–{ga} {event['opponent']}"
    desc = (f"{result} {gf}-{ga} contre {event['opponent']} le {event['date']} "
            f"({event['tournament']}) : composition, statistiques et chronologie des buts.")

    head = f"""<div class="hero-band"><div class="inner">
  <p class="eyebrow">{esc(event['tournament'])} · {esc(event['date'])}</p>
  <h1>Burkina Faso <span style="color:var(--muted)">{esc(score)}</span> {esc(event['opponent'])}</h1>
  <p>{esc(result)} {esc(venue)}{', formation ' + esc(event['bf_formation']) if event.get('bf_formation') else ''}.</p>
</div></div>"""

    facts = [("Compétition", event["tournament"]), ("Date", event["date"]),
             ("Lieu", {"H": "Domicile", "A": "Extérieur"}.get(event["venue"], "–")),
             ("Système", event.get("bf_formation") or "–"),
             ("Système adverse", event.get("opp_formation") or "–")]
    if state:
        facts += [("Durée effective", f"{_fmt(state['effective_length'])} min"),
                  ("Minutes en tête", f"{_fmt(state['min_leading'], 0)}"),
                  ("Minutes menés", f"{_fmt(state['min_trailing'], 0)}")]
    kv = "".join(f"<dt>{esc(k)}</dt><dd>{esc(v)}</dd>" for k, v in facts)

    body = f"""{head}
<main>
  <p class="crumb"><a href="../index.html">Accueil</a> ›
     <a href="../matchs.html">Matchs</a> › {esc(event['date'])}</p>
  <div class="grid">
    {card(width="w8", title_html="<h3>Chronologie</h3>",
          extra=goal_timeline(goals, d.subs_for_event(eid), d.cards_for_event(eid),
                              event["opponent"]))}
    {card(width="w4", title_html="<h3>Fiche du match</h3>",
          extra=f'<dl class="kv">{kv}</dl>')}
    {card(width="w6", title_html="<h3>Statistiques d'équipe</h3>",
          extra=stat_bars(stats.get("bf"), stats.get("opp")))}
    {card(width="w6", title_html="<h3>Composition</h3>",
          extra=lineup_block(apps, players_with_pages))}
  </div>
  <div class="pager">
    {f'<a href="{match_slug(prev_event)}.html">← {esc(prev_event["opponent"])} ({prev_event["date"]})</a>' if prev_event else '<span></span>'}
    {f'<a href="{match_slug(next_event)}.html">{esc(next_event["opponent"])} ({next_event["date"]}) →</a>' if next_event else '<span></span>'}
  </div>
</main>"""
    return page(title=title, description=desc, body=body, depth=1,
                active="matches", page_class="match-page")


# --------------------------------------------------------------- player page

def player_page(d, profile, players_with_pages):
    pid = profile["player_id"]
    imp = d.importance_by.get(pid, {})
    bench = d.bench_by.get(pid, {})
    apps = sorted(d.apps_for_player(pid), key=lambda a: a["date"], reverse=True)
    photo = d.photo("player", pid)
    if photo:
        photo = "../" + photo  # detail pages live one folder deep
    credit = d.photo_credit("player", pid)
    name = profile["name"]

    club = profile.get("club_v") or profile.get("club") or "–"
    league = profile.get("league_v") or ""
    pos = POS_LABEL.get(profile["pos"], profile["pos"] or "–")
    status_word = {"active": "International actif", "fringe": "En marge du groupe",
                   "out": "Hors du groupe", "retired_int": "Retraité international",
                   "retired_career": "Retraité"}.get(profile.get("status"), "")

    desc = (f"{name} ({pos}, {club}) : sélections, minutes, buts et performances "
            f"avec les Étalons du Burkina Faso depuis 2022.")

    facts = [
        ("Poste", pos),
        ("Âge", f"{_fmt(profile.get('age'), 1)} ans" if profile.get("age") else "–"),
        ("Club", club + (f" · {league}" if league else "")),
        ("Sélections (carrière)", profile.get("caps") or "–"),
        ("Buts (carrière)", profile.get("goals_career") or "–"),
        ("Valeur estimée", (f"{_fmt(_num(profile['market_value_eur']) / 1e6, 1)} M€"
                            if profile.get("market_value_eur") else "–")),
        ("Taille", f"{profile['height']} cm" if profile.get("height") else "–"),
        ("Pied", profile.get("foot") or "–"),
        ("Dernière apparition", profile.get("last_seen") or "–"),
    ]
    kv = "".join(f"<dt>{esc(k)}</dt><dd>{esc(v)}</dd>" for k, v in facts)

    window = [
        ("Matchs dans le groupe", profile.get("matchday_squads")),
        ("Apparitions", profile.get("apps")),
        ("Titularisations", profile.get("starts")),
        ("Minutes", _fmt(profile.get("minutes"))),
        ("Buts", profile.get("goals")),
        ("Passes décisives", profile.get("assists")),
        ("Passes réussies", (f"{_fmt(profile['pass_pct'], 1)} %"
                             if profile.get("pass_pct") else "–")),
        ("Dribbles réussis", f"{profile.get('dribbles_won') or 0}/"
                             f"{profile.get('dribbles_attempted') or 0}"),
        ("Note moyenne", _fmt(profile.get("rating_avg"), 2)
                         if profile.get("rating_avg") else "–"),
    ]
    if profile["pos"] == "GK":
        window.append(("Arrêts", profile.get("saves")))
    wkv = "".join(f"<dt>{esc(k)}</dt><dd>{esc(v)}</dd>" for k, v in window)

    role = {"pilier": "Pilier", "rotation": "Rotation",
            "marge": "Marge"}.get(imp.get("tier", ""), "")
    imp_rows = []
    if imp:
        share = _num(imp.get("minutes_share")) * 100
        imp_rows = [
            ("Rôle", role or "–"),
            ("Part des minutes", f"{_fmt(share, 0)} %"),
            ("Titularisations", f"{imp.get('starts')}/{imp.get('squad_matches')}"),
            ("On/Off ±/90", imp.get("onoff_diff") or "– (échantillon insuffisant)"),
            ("PPM titulaire − remplaçant",
             imp.get("ppg_diff") or "– (échantillon insuffisant)"),
            ("Buts+passes /90", imp.get("ga90") or "– (échantillon insuffisant)"),
        ]
    ikv = "".join(f"<dt>{esc(k)}</dt><dd>{esc(v)}</dd>" for k, v in imp_rows)

    rows = []
    for a in apps[:60]:
        ev = d.event_by.get(a["event_id"], {})
        link = (f'<a href="../matchs/{match_slug(ev)}.html">'
                f'{esc(a["opponent"])}</a>' if ev else esc(a["opponent"]))
        res = a["gf"] and (
            "W" if _int(a["gf"]) > _int(a["ga"]) else
            ("D" if _int(a["gf"]) == _int(a["ga"]) else "L"))
        chip = f'<span class="chip {res}">{ {"W": "V", "D": "N", "L": "D"}[res] }</span>' if res else ""
        played = a["played"] == "1"
        # never claim a start for a player who logged no minutes
        status = ("Tit." if played and a["started"] == "1"
                  else ("Rempl." if played else "Non entré"))
        rows.append(f"""<tr><td>{esc(a['date'])}</td><td>{chip}</td><td>{link}</td>
  <td class="num">{esc(a['gf'])}-{esc(a['ga'])}</td>
  <td class="num">{status}</td>
  <td class="num">{str(_int(a['minutes'])) + "'" if played else '–'}</td>
  <td class="num">{_int(a['goals']) or '–'}</td>
  <td class="num">{_int(a['assists']) or '–'}</td>
  <td class="num">{_fmt(a['rating'], 2) if _num(a['rating']) else '–'}</td></tr>""")
    table = f"""<div class="tablewrap"><table>
  <tr><th>Date</th><th></th><th>Adversaire</th><th class="num">Score</th>
      <th class="num">Statut</th><th class="num">Min</th><th class="num">Buts</th>
      <th class="num">P. déc.</th><th class="num">Note</th></tr>
  {''.join(rows)}</table></div>"""

    bench_block = ""
    if bench and _int(bench.get("sub_apps")) >= 3:
        bench_block = card(width="w4", title_html="<h3>En sortie de banc</h3>", extra=f"""
  <dl class="kv">
    <dt>Entrées</dt><dd>{bench['sub_apps']}</dd>
    <dt>Minutes</dt><dd>{_fmt(bench['sub_min'])}</dd>
    <dt>Buts + passes</dt><dd>{bench['sub_ga']}</dd>
    <dt>Entrée moyenne</dt><dd>{_fmt(bench['entry_avg'], 0)}'</dd>
  </dl>""")

    credit_html = ""
    if credit:
        credit_html = (f'<p class="photo-credit">Photo : {esc(credit["author"])} · '
                       f'{esc(credit["licence"])} · '
                       f'<a href="{esc(credit["credit_url"])}" rel="nofollow">Commons</a></p>')

    head = f"""<div class="hero-band"><div class="inner">
  <div class="entity">
    {avatar(photo, name, "photo")}
    <div class="meta">
      <p class="eyebrow">{esc(status_word)}</p>
      <h1>{esc(name)}</h1>
      <p class="sub">{esc(pos)} · {esc(club)}{' · ' + esc(league) if league else ''}</p>
      {credit_html}
    </div>
  </div>
</div></div>"""

    body = f"""{head}
<main>
  <p class="crumb"><a href="../index.html">Accueil</a> ›
     <a href="../joueurs.html">Joueurs</a> › {esc(name)}</p>
  <div class="grid">
    {card(width="w4", title_html="<h3>Identité</h3>", extra=f'<dl class="kv">{kv}</dl>')}
    {card(width="w4", title_html="<h3>Bilan depuis janv. 2022</h3>",
          extra=f'<dl class="kv">{wkv}</dl>')}
    {card(width="w4", title_html="<h3>Importance</h3>",
          extra=(f'<dl class="kv">{ikv}</dl>' if ikv else
                 '<p class="sub">Pas encore assez de matchs pour situer ce joueur.</p>'))}
    {bench_block}
    {card(width="w12", title_html="<h3>Match par match</h3>", extra=table)}
  </div>
</main>"""
    return page(title=name, description=desc, body=body, depth=1,
                active="players", page_class="player-page")
