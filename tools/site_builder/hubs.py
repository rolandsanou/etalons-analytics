"""Hub pages: home, squad, players index, matches index, analysis, management,
history, projections, methodology.

Charts and card titles are translated client-side from assets/i18n.js; the copy
the generator writes (heroes, section headings, table headers) is translated here
through ctx.t so each language gets a real static page. See routes.py."""

import unicodedata

from .detail import (POS_LABEL_KEY, POS_ORDER, match_slug, ordinal,
                     _fmt, _int)
from . import seo
from .layout import avatar, card, esc, hero, page, section

CAMPAIGNS = [
    ("CAN 2025", "2025-12-01", "2026-01-31"),
    ("Éliminatoires CM 2026 & amicaux 2025", "2025-02-01", "2025-11-30"),
    ("CAN 2023 & éliminatoires 2024", "2023-06-01", "2024-12-31"),
    ("Éliminatoires CM 2026 (2023)", "2022-06-01", "2023-05-31"),
    ("CAN 2021 (janv. 2022)", "2022-01-01", "2022-05-31"),
]


def search_key(text):
    """Accent-stripped key so "traore" finds "Traoré"."""
    s = unicodedata.normalize("NFD", str(text))
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


def _campaign(date):
    for label, start, end in CAMPAIGNS:
        if start <= date <= end:
            return label
    return "Autres matchs"


def pos_label(ctx, pos):
    return ctx.t(POS_LABEL_KEY.get(pos, pos or "?"))


def _find_event(d, hist_match):
    for e in d.events:
        if e["date"] == hist_match["date"] and e["opponent"] == hist_match["opponent"]:
            return e["event_id"]
    return None


def _match_row(ctx, event, score):
    return f"""<a class="mrow" href="{ctx.url('match', match_slug(event))}">
  <span class="dt">{esc(event['date'])}</span>
  <span class="chip {event['result']}">{ctx.result_letter[event['result']]}</span>
  <span class="opp">{esc(event['opponent'])}</span>
  <span class="sc">{esc(score)}</span>
  <span class="cmp">{esc(event['tournament'])}</span></a>"""


# ------------------------------------------------------------------ home

def home_page(d, ctx):
    t = ctx.t
    elo, hist, team = d.elo, d.history, d.team
    stats = d.squad["stats"]
    last = hist["last10"][0]
    top = [p for p in d.profiles if _int(p["minutes"]) > 0][:6]

    tiles = [
        (t("Rang Elo CAF"), f"#{elo['caf_rank']}",
         t("{rank} mondial · {pts} pts",
           rank=ordinal(elo["world_rank"], ctx.lang),
           pts=_fmt(elo["current"]))),
        (t("Matchs analysés"), str(team["coverage"]["events"]),
         t("depuis janv. 2022 · {n} joueurs suivis", n=d.pool["n_players"])),
        (t("Dernier match"), last["score"],
         f"{esc(last['opponent'])} · {esc(last['date'])}"),
        (t("Âge moyen"), _fmt(stats["avg_age"], 1),
         t("{pct} % en Europe", pct=_fmt(stats["pct_europe"], 0))),
    ]
    tile_html = "".join(
        f'<div class="tile"><div class="label">{esc(a)}</div>'
        f'<div class="value">{b}</div><div class="sub">{c}</div></div>'
        for a, b, c in tiles)

    recent = "".join(
        _match_row(ctx, d.event_by[_find_event(d, m)], m["score"])
        for m in hist["last10"][:6] if _find_event(d, m))

    cards_html = "".join(f"""<a class="pcard" href="{ctx.url('player', p['player_id'])}">
  {avatar(ctx.asset(d.photo('player', p['player_id']) or ''), p['name'], 'pic')
   if d.photo('player', p['player_id']) else avatar(None, p['name'], 'pic')}
  <span><span class="nm">{esc(p['name'])}</span>
    <span class="rl">{esc(pos_label(ctx, p['pos']))}</span>
    <span class="stat">{_fmt(p['minutes'])} min</span></span>
</a>""" for p in top)

    tiles_nav = [
        ("squad", t("Effectif & répartitions"),
         t("Qui compose le groupe, où jouent les Étalons, comment l'effectif se structure.")),
        ("analysis", t("Analyse de jeu"),
         t("Style, temps forts, résilience, systèmes et importance des joueurs.")),
        ("matches", t("Tous les matchs"),
         t("{n} rencontres détaillées : compositions, statistiques, chronologies.",
           n=team["coverage"]["events"])),
        ("history", t("Histoire & Elo"),
         t("1960 à aujourd'hui : CAN, sélectionneurs, lieux, tirs au but, trajectoire Elo.")),
        ("projections", t("Projections"),
         t("CAN 2027, vivier des jeunes, attentes Elo face aux rivaux africains.")),
        ("players", t("Tous les joueurs"),
         t("{n} joueurs appelés depuis 2022, avec leur fiche détaillée.",
           n=d.pool["n_players"])),
    ]
    nav_cards = "".join(
        f"""<a class="card w4" href="{ctx.url(route)}">
  <h3>{esc(title)}</h3><p class="sub">{esc(sub)}</p></a>"""
        for route, title, sub in tiles_nav)

    body = f"""<div class="hero-band"><div class="inner">
  <p class="eyebrow">{esc(t("Analyse de données · Burkina Faso"))}</p>
  <h1>{esc(t("Les Étalons, chiffres à l'appui"))}</h1>
  <p>{esc(t("Un projet ouvert qui suit chaque joueur appelé en sélection depuis la CAN 2021 : temps de jeu, performances, style de jeu, résilience et projections — avec les sources et les limites de chaque chiffre affichées."))}</p>
</div></div>
<main>
  <div class="tiles">{tile_html}</div>

  <section id="derniers">
    <h2>{esc(t("Derniers matchs"))}</h2>
    <p class="lead">{esc(t("Cliquez un match pour la composition, les statistiques et la chronologie."))}</p>
    <div class="mlist">{recent}</div>
    <p class="sub"><a href="{ctx.url('matches')}">{esc(t("Tous les matchs →"))}</a></p>
  </section>

  <section id="cadres">
    <h2>{esc(t("Les plus utilisés"))}</h2>
    <p class="lead">{esc(t("Classés par minutes jouées en sélection depuis janvier 2022."))}</p>
    <div class="roster feature">{cards_html}</div>
    <p class="sub"><a href="{ctx.url('players')}">{esc(t("Tous les joueurs →"))}</a></p>
  </section>

  <section id="explorer">
    <h2>{esc(t("Explorer"))}</h2>
    <div class="grid">{nav_cards}</div>
  </section>
</main>"""
    description = t("Analyse de données de l'équipe nationale du Burkina Faso : effectif, performances individuelles, style de jeu, histoire et projections.")
    return page(ctx, title=t("Accueil"), description=description,
                structured=(seo.website(ctx.lang, description),),
                body=body, needs=("meta",))


# ------------------------------------------------------------------ players index

def players_index(d, ctx):
    t = ctx.t
    groups = {}
    for p in d.profiles:
        groups.setdefault(p["pos"] or "?", []).append(p)
    blocks = []
    for pos in sorted(groups, key=lambda k: POS_ORDER.get(k, 9)):
        entries = sorted(groups[pos], key=lambda p: -_int(p["minutes"]))
        cards_html = "".join(f"""<a class="pcard" href="{ctx.url('player', p['player_id'])}"
   data-name="{esc(search_key(p['name']))}" data-chan="{p.get('chan_only', '0')}">
  {avatar(ctx.asset(d.photo('player', p['player_id'])) if d.photo('player', p['player_id']) else None, p['name'], 'pic')}
  <span><span class="nm">{esc(p['name'])}</span>
    <span class="rl">{esc((p.get('club_v') or p.get('club') or '—')[:20])}</span>
    <span class="stat">{p['apps']} m · {_fmt(p['minutes'])} min</span></span>
</a>""" for p in entries)
        blocks.append(f"""<section data-pos="{esc(pos)}">
  <h2>{esc(pos_label(ctx, pos))}
    <span style="color:var(--muted);font-weight:400">{len(entries)}</span></h2>
  <div class="roster">{cards_html}</div>
</section>""")

    a_team = sum(1 for p in d.profiles if p.get("chan_only") != "1")
    chan_only = len(d.profiles) - a_team
    filters = f"""<div class="filters">
  <input type="search" id="roster_search" placeholder="{esc(t("Filtrer par nom…"))}">
  <label><input type="checkbox" id="hide_chan">
    {esc(t("Masquer les joueurs vus uniquement en CHAN"))} ({chan_only})</label>
  <span class="count" id="roster_count"></span>
</div>"""

    body = f"""{hero(t("Effectif élargi"), t("Tous les joueurs depuis 2022"),
        t("{total} joueurs appelés ou apparus sur une feuille de match depuis la CAN 2021, dont {a_team} avec l'équipe A. Chaque fiche détaille le temps de jeu, les performances et l'importance dans le groupe.",
          total=len(d.profiles), a_team=a_team))}
<main>
  {filters}
  {''.join(blocks)}
  <section id="tableau">
    <h2>{esc(t("Tableau détaillé"))}</h2>
    <p class="lead">{esc(t("Tableau complet, triable colonne par colonne : minutes, buts, passes, dribbles, arrêts, note moyenne, club et valeur estimée."))}</p>
    <div class="grid">
      {card(width="w12", extra='<input type="search" id="pool_search" class="search">'
            '<div class="tablewrap pool"><table id="pool_table"></table></div>'
            '<p class="sub" id="pool_note"></p>')}
    </div>
  </section>
</main>"""
    return page(ctx, title=t("Joueurs"),
                description=t("Les {n} joueurs appelés en sélection du Burkina Faso depuis 2022, avec leur fiche individuelle et un tableau détaillé triable.",
                              n=len(d.profiles)),
                body=body, needs=("pool", "meta"), scripts=("players", "roster"))


# ------------------------------------------------------------------ matches index

def matches_index(d, ctx):
    t = ctx.t
    by_campaign = {}
    for e in sorted(d.events, key=lambda e: e["date"], reverse=True):
        by_campaign.setdefault(_campaign(e["date"]), []).append(e)
    blocks = []
    for label, events in by_campaign.items():
        w = sum(1 for e in events if e["result"] == "W")
        dd = sum(1 for e in events if e["result"] == "D")
        l = sum(1 for e in events if e["result"] == "L")
        rows = "".join(_match_row(ctx, e, f"{e['gf']}–{e['ga']}") for e in events)
        blocks.append(f"""<section>
  <h2>{esc(t(label))}</h2>
  <p class="lead">{esc(t("{n} matchs · {w}V {d}N {l}D", n=len(events), w=w, d=dd, l=l))}</p>
  <div class="mlist">{rows}</div>
</section>""")
    body = f"""{hero(t("Matchs"), t("Chaque rencontre, en détail"),
        t("{n} matchs depuis janvier 2022 avec composition, statistiques d'équipe et chronologie des buts.", n=len(d.events)))}
<main>{''.join(blocks)}</main>"""
    return page(ctx, title=t("Matchs"),
                description=t("Les {n} matchs du Burkina Faso depuis 2022 : compositions, statistiques et chronologies.", n=len(d.events)),
                body=body, needs=("meta",))


# ------------------------------------------------------------------ squad

def squad_page(d, ctx):
    t = ctx.t
    body = f"""{hero(t("Effectif"), t("Le groupe actuel et sa structure"),
        t("Dernière liste connue, pyramide des âges, pays des clubs et type de championnat."))}
<main>
  {section("effectif", "s_squad", None, cards=(
      card(chart="c_pos", title_key="c_pos", sub_key="c_pos_sub", card_id="card_pos",
           height="short")
      + card(chart="c_age", title_key="c_age", sub_key="c_age_sub", card_id="card_age",
             height="short")
      + card(width="w12", title_key="t_squad", table_id="squad_table",
             extra='<details class="tv"><summary data-i18n="t_callups"></summary>'
                   '<div class="tablewrap"><table id="callups_table"></table></div></details>')))}
  {section("repartitions", "s_break", "s_break_lead", cards=(
      card(chart="c_clubs", title_key="c_clubs", sub_key="c_clubs_sub",
           card_id="card_clubs", height="tall")
      + card(title_key="c_leagues", sub_key="c_leagues_sub", card_id="card_leagues",
             extra='<div class="league-bar" id="league_bar"></div>'
                   '<div class="league-legend" id="league_legend"></div>')))}
</main>"""
    return page(ctx, title=t("Effectif"),
                description=t("Effectif du Burkina Faso : postes, âges, clubs et championnats."),
                body=body, needs=("squad", "meta"),
                scripts=("overview", "breakdowns"))


# ------------------------------------------------------------------ analysis

def analysis_page(d, ctx):
    t = ctx.t
    body = f"""{hero(t("Analyse"), t("Comment cette équipe joue"),
        t("Style de jeu comparé aux adversaires rencontrés, capacité à renverser une situation, temps forts, systèmes et importance des joueurs."))}
<main>
  {section("style", "s_style", None, extra_head='<p class="lead" id="lead_style"></p>',
    cards=(card(chart="c_style_pct", title_key="c_style_pct", sub_key="c_style_pct_sub",
                card_id="card_style_pct", height="tall")
           + card(chart="c_style_vol", title_key="c_style_vol", sub_key="c_style_vol_sub",
                  card_id="card_style_vol", height="tall")
           + card(chart="c_style_terc", title_key="c_style_terc",
                  sub_key="c_style_terc_sub", card_id="card_style_terc",
                  width="w8", height="short")
           + card(width="w4", title_key="c_style_half", sub_key="c_style_half_sub",
                  card_id="card_style_half", table_id="half_table")))}
  {section("resilience", "s_res", None, extra_head='<p class="lead" id="lead_res"></p>',
    cards=(card(width="w4", title_key="c_deficit", sub_key="c_deficit_sub",
                card_id="card_deficit",
                extra='<div class="mini-tiles" id="deficit_tiles"></div>'
                      '<p class="sub" id="late_swing_note"></p>')
           + card(width="w4", chart="c_reply", card_id="card_reply", height="short",
                  extra='<p class="sub" id="reply_median"></p>',
                  title_html='<h3 data-i18n="c_reply"></h3><p class="sub" id="reply_sub"></p>')
           + card(width="w4", chart="c_state_out", title_key="c_state_out",
                  sub_key="c_state_out_sub", card_id="card_state_out", height="short")
           + card(width="w12", title_key="c_clutch", sub_key="c_clutch_sub",
                  card_id="card_clutch", table_id="clutch_table")))}
  {section("tempo", "s_tempo", None, extra_head='<p class="lead" id="lead_tempo"></p>',
    cards=(card(width="w8", chart="c_bins", title_key="c_bins", sub_key="c_bins_sub",
                card_id="card_bins", extra='<p class="sub" id="chi_note"></p>')
           + card(width="w4", title_key="c_gamestate", sub_key="c_gamestate_sub",
                  card_id="card_gamestate",
                  extra='<div class="mini-tiles" id="tempo_tiles"></div>'
                        '<div class="league-bar" id="state_bar"></div>'
                        '<div class="league-legend" id="state_legend"></div>')))}
  {section("systemes", "s_forms", "s_forms_lead",
    cards=card(width="w12", chart="c_forms", title_key="c_forms", sub_key="c_forms_sub",
               card_id="card_forms", height="short"))}
</main>"""
    return page(ctx, title=t("Analyse de jeu"),
                description=t("Style de jeu du Burkina Faso, résilience, temps forts et systèmes — chaque métrique avec son échantillon."),
                body=body, needs=("team", "pool", "meta"),
                scripts=("style", "tempo", "breakdowns"))


# ------------------------------------------------------------------ management

def management_page(d, ctx):
    t = ctx.t
    body = f"""{hero(t("Gestion de l'effectif"), t("Qui pèse, qui tourne, qui entre"),
        t("Importance des joueurs, stabilité du onze, associations sur le terrain, utilisation du banc et effet du calendrier. Chaque mesure est affichée avec son échantillon et masquée sous son seuil."))}
<main>
  {section("importance", "s_imp", "s_imp_lead",
    cards=(card(width="w12", title_key="c_imp_table", sub_key="c_imp_table_sub",
                card_id="card_imp", table_id="imp_table",
                extra='<p class="sub" id="pilier_note"></p>')
           + card(chart="c_prof", title_key="c_imp_prof", sub_key="c_imp_prof_sub",
                  card_id="card_prof", height="short",
                  extra='<div class="pickrow"><label for="imp_picker" data-i18n="imp_picker">'
                        '</label><select id="imp_picker"></select></div>')
           + card(chart="c_bench", title_key="c_bench", sub_key="c_bench_sub",
                  card_id="card_bench", height="short",
                  extra='<p class="sub" id="bench_note"></p>')))}
  {section("stabilite", "s_stab", "s_stab_lead",
    cards=card(width="w12", title_key="c_stab", sub_key="c_stab_sub",
               card_id="card_stab", table_id="stability_table"))}
  {section("associations", "s_pairs", "s_pairs_lead",
    cards=(card(width="w8", title_key="c_pairs", sub_key="c_pairs_sub",
                card_id="card_pairs", table_id="pairs_table",
                extra='<p class="sub" id="pairs_note"></p>')
           + card(width="w4", title_key="c_pairs_extremes",
                  sub_key="c_pairs_extremes_sub",
                  extra='<div class="tablewrap"><table id="pairs_extremes"></table></div>')))}
  {section("remplacements", "s_subs", "s_subs_lead",
    cards=(card(width="w8", title_key="c_subs", sub_key="c_subs_sub",
                card_id="card_subs", table_id="subs_table")
           + card(width="w4", chart="c_subs_dist", title_key="c_subs_dist",
                  sub_key="c_subs_dist_sub", card_id="card_subs_dist",
                  height="short")))}
  {section("calendrier", "s_rest", "s_rest_lead",
    cards=card(width="w12", title_key="c_rest", sub_key="c_rest_sub",
               card_id="card_rest", table_id="rest_table",
               extra='<p class="sub" id="rest_note"></p>'))}
</main>"""
    return page(ctx, title=t("Gestion de l'effectif"),
                description=t("Importance des joueurs du Burkina Faso, rotation du onze, associations sur le terrain, utilisation du banc et effet du calendrier."),
                body=body, needs=("team", "pool", "meta"),
                scripts=("importance", "model", "mgmt"))


# ------------------------------------------------------------------ history

def _coach_slug(name):
    from .detail import slugify
    return slugify(name.split(" & ")[0])


def history_page(d, ctx):
    t = ctx.t
    coach_cards = "".join(f"""<div class="pcard" style="cursor:default">
  {avatar(ctx.asset(d.photo('coach', _coach_slug(c['coach']))) if d.photo('coach', _coach_slug(c['coach'])) else None, c['coach'], 'pic')}
  <span><span class="nm">{esc(c['coach'])}</span>
    <span class="rl">{esc(c['first_match'][:4])}–{esc(c['last_match'][:4])}
      {'<span class="pill st active">' + esc(t("en cours")) + '</span>' if c.get('current') == '1' else ''}</span>
    <span class="stat">{esc(t("{n} m · {w}-{d}-{l} · {ppg} pts/m", n=c['matches'], w=c['w'], d=c['d'], l=c['l'], ppg=c['ppg']))}</span></span>
</div>""" for c in d.coach_eras
        if (c.get("pooled") != "1" and _int(c["matches"]) >= 10) or c.get("current") == "1")

    body = f"""{hero(t("Histoire"), t("1960 à aujourd'hui"),
        t("Toutes les rencontres officielles depuis l'indépendance : tendances, parcours en CAN, sélectionneurs, lieux, tirs au but et trajectoire Elo."))}
<main>
  {section("histoire", "s_history", None,
    extra_head='<p class="lead" id="lead_history"></p>',
    cards=(card(chart="c_decades", title_key="c_decades", sub_key="c_decades_sub",
                card_id="card_decades", height="short")
           + card(chart="c_form", title_key="c_form", sub_key="c_form_sub", height="short")
           + card(width="w12", chart="c_afcon", title_key="c_afcon", sub_key="c_afcon_sub",
                  card_id="card_afcon")
           + card(width="w4", title_key="t_capped", table_id="capped_table")
           + card(width="w4", title_key="t_scorers", table_id="scorers_table")
           + card(width="w4", title_key="t_last10", table_id="last10_table")
           + card(card_id="card_shootouts", table_id="shootout_table",
                  title_html='<h3 data-i18n="t_shootouts"></h3>'
                             '<p class="sub" id="shootout_rec"></p>')
           + card(title_key="t_pens", sub_key="t_pens_sub", card_id="card_pens",
                  extra='<div class="mini-tiles" id="pens_tiles"></div>'
                        '<div class="tablewrap"><table id="takers_table"></table></div>'
                        '<p class="sub" id="pens_gk_note"></p>')
           + card(width="w12", chart="c_venues", title_key="c_venues",
                  sub_key="c_venues_sub", card_id="card_venues", height="short",
                  extra='<p class="sub" id="venues_note"></p>')))}
  <section id="selectionneurs">
    <h2 data-i18n="c_coaches"></h2>
    <p class="lead" data-i18n="c_coaches_sub"></p>
    <div class="roster" style="margin-bottom:14px">{coach_cards}</div>
    <div class="grid">{card(width="w12", table_id="coaches_table",
                            card_id="card_coaches")}</div>
  </section>
  {section("elo", "s_elo", "s_elo_lead",
    cards=(card(width="w8", chart="c_elo_tl", title_key="c_elo_tl",
                sub_key="c_elo_tl_sub", card_id="card_elo", height="tall")
           + card(width="w4", chart="c_winexp", title_key="c_winexp",
                  sub_key="c_winexp_sub", height="tall",
                  extra='<p class="sub" id="winexp_note"></p>')))}
</main>"""
    return page(ctx, title=t("Histoire"),
                description=t("Histoire du Burkina Faso depuis 1960 : bilans, CAN, sélectionneurs, lieux, tirs au but et classement Elo."),
                body=body, needs=("history", "elo", "team", "meta"),
                scripts=("history", "elo"))


# ------------------------------------------------------------------ projections

def projections_page(d, ctx):
    t = ctx.t
    body = f"""{hero(t("Projections"), t("CAN 2027, CM 2030 et le vivier"),
        t("Âge de l'effectif aux prochaines échéances, attentes face aux rivaux africains et passage des équipes de jeunes vers les A. Modèles simples, explicitement illustratifs."))}
<main>
  {section("projections", "s_proj", "s_proj_lead",
    cards=(card(width="w12", chart="c_proj_age", title_key="c_proj_age",
                sub_key="c_proj_age_sub", card_id="card_proj",
                extra='<p class="core" id="core_box"></p>'
                      '<p class="sub" id="readiness_note"></p>')
           + card(width="w12", title_key="c_pipeline", sub_key="c_pipeline_sub",
                  card_id="card_pipeline", table_id="pipeline_table",
                  extra='<p class="sub" id="prospects_note"></p>')))}
  {section("attentes", "s_pred", "s_pred_lead",
    cards=(card(width="w8", chart="c_pred", title_key="c_pred", sub_key="c_pred_sub",
                card_id="card_pred", height="tall")
           + card(width="w4", title_key="c_pred_note", card_id="card_pred_note",
                  extra='<div id="pred_note"></div>')))}
  {section("modele", "s_model", "s_model_lead",
    extra_head='<p class="sub" id="bt_scope"></p>',
    cards=(card(width="w4", title_key="c_bt", sub_key="c_bt_sub",
                card_id="card_bt", table_id="backtest_table")
           + card(width="w5", chart="c_calibration", title_key="c_calibration",
                  sub_key="c_calibration_sub", card_id="card_calibration",
                  height="short")
           + card(width="w3", title_key="c_bt_surprises", sub_key="c_bt_surprises_sub",
                  extra='<div class="tablewrap"><table id="bt_surprises"></table></div>')))}
</main>"""
    return page(ctx, title=t("Projections"),
                description=t("Projections du Burkina Faso vers la CAN 2027 et le Mondial 2030 : âges, vivier des jeunes, attentes Elo et vérification du modèle."),
                body=body, needs=("squad", "pool", "team", "elo", "meta"),
                scripts=("outlook", "predictions", "model"))


# ------------------------------------------------------------------ methodology

def methodology_page(d, ctx):
    t = ctx.t
    credits = "".join(f"""<div>{esc(p['name'])} — {esc(p['author'])},
  {esc(p['licence'])} (<a href="{esc(p['credit_url'])}" rel="nofollow">Commons</a>)</div>"""
        for p in sorted(d.photos, key=lambda x: (x["kind"], x["name"])))
    body = f"""{hero(t("Méthodologie"), t("Comment ces chiffres sont produits"),
        t("Sources, formules, seuils et limites. Tout est reproductible : le code et les données intermédiaires sont publics."))}
<main>
  <section id="methodologie">
    <div class="methodo" id="methodo"></div>
  </section>
  <section id="credits">
    <h2>{esc(t("Crédits photo"))}</h2>
    <p class="lead">{esc(t("Portraits issus de Wikimedia Commons, sous licence libre. Aucune photo de presse sous droits n'est republiée ici."))}</p>
    <div class="credits">{credits}</div>
  </section>
</main>"""
    return page(ctx, title=t("Méthodologie"),
                description=t("Sources, formules, seuils et limites du projet Étalons Analytics."),
                # the marts are openly licensed, so declare them as a Dataset —
                # this is the page that documents what they contain
                structured=(seo.dataset(ctx.lang, ctx.canonical),),
                body=body, needs=("meta",))
