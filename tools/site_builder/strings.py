"""Translations for the copy the generator writes into the HTML.

Keyed on the French source string, gettext-style: `t("Derniers matchs")`. A key
with no entry falls through to French and is recorded in MISSES, which
build_site reports — so a forgotten string shows up in the build log instead of
silently shipping.

Only the *generated* copy lives here. Chart labels, section titles and card
subtitles are translated client-side from site/assets/i18n.js.
"""

MISSES = set()

EN = {
    # --- navigation -------------------------------------------------------
    "Accueil": "Home",
    "Effectif": "Squad",
    "Joueurs": "Players",
    "Matchs": "Matches",
    "Analyse": "Analysis",
    "Gestion": "Management",
    "Histoire": "History",
    "Projections": "Projections",
    "Méthodologie": "Methodology",

    # --- home -------------------------------------------------------------
    "Analyse de données · Burkina Faso": "Data analysis · Burkina Faso",
    "Les Étalons, chiffres à l'appui": "The Étalons, by the numbers",
    "Un projet ouvert qui suit chaque joueur appelé en sélection depuis la CAN "
    "2021 : temps de jeu, performances, style de jeu, résilience et projections "
    "— avec les sources et les limites de chaque chiffre affichées.":
        "An open project tracking every player called up since AFCON 2021: "
        "playing time, individual performance, style of play, resilience and "
        "projections — with the source and the limits of every number on show.",
    "Analyse de données de l'équipe nationale du Burkina Faso : effectif, "
    "performances individuelles, style de jeu, histoire et projections.":
        "Data analysis of the Burkina Faso national football team: squad, "
        "individual performance, style of play, history and projections.",
    "Rang Elo CAF": "CAF Elo rank",
    "Matchs analysés": "Matches analysed",
    "Dernier match": "Latest match",
    "Âge moyen": "Average age",
    "{rank} mondial · {pts} pts": "{rank} in the world · {pts} pts",
    "depuis janv. 2022 · {n} joueurs suivis": "since Jan 2022 · {n} players tracked",
    "{pct} % en Europe": "{pct}% based in Europe",
    "Derniers matchs": "Latest matches",
    "Cliquez un match pour la composition, les statistiques et la chronologie.":
        "Open a match for the lineup, the statistics and the timeline.",
    "Tous les matchs →": "All matches →",
    "Les plus utilisés": "Most used",
    "Classés par minutes jouées en sélection depuis janvier 2022.":
        "Ranked by international minutes played since January 2022.",
    "Tous les joueurs →": "All players →",
    "Explorer": "Explore",
    "Effectif & répartitions": "Squad & breakdowns",
    "Qui compose le groupe, où jouent les Étalons, comment l'effectif se structure.":
        "Who is in the squad, where the Étalons play, how the group is built.",
    "Analyse de jeu": "Style of play",
    "Style, temps forts, résilience, systèmes et importance des joueurs.":
        "Style, timing, resilience, formations and player importance.",
    "Tous les matchs": "All matches",
    "{n} rencontres détaillées : compositions, statistiques, chronologies.":
        "{n} matches in detail: lineups, statistics, timelines.",
    "Histoire & Elo": "History & Elo",
    "1960 à aujourd'hui : CAN, sélectionneurs, lieux, tirs au but, trajectoire Elo.":
        "1960 to today: AFCON runs, head coaches, venues, shootouts, Elo.",
    "CAN 2027, vivier des jeunes, attentes Elo face aux rivaux africains.":
        "AFCON 2027, the youth pipeline, Elo expectations against African rivals.",
    "Tous les joueurs": "All players",
    "{n} joueurs appelés depuis 2022, avec leur fiche détaillée.":
        "{n} players called up since 2022, each with a full profile.",

    # --- players index ----------------------------------------------------
    "Effectif élargi": "Extended squad",
    "Tous les joueurs depuis 2022": "Every player since 2022",
    "{total} joueurs appelés ou apparus sur une feuille de match depuis la CAN "
    "2021, dont {a_team} avec l'équipe A. Chaque fiche détaille le temps de jeu, "
    "les performances et l'importance dans le groupe.":
        "{total} players called up or named on a matchday sheet since AFCON "
        "2021, {a_team} of them for the senior side. Each profile covers playing "
        "time, performance and importance to the group.",
    "Filtrer par nom…": "Filter by name…",
    "Masquer les joueurs vus uniquement en CHAN": "Hide players seen only at CHAN",
    "Tableau détaillé": "Detailed table",
    "Tableau complet, triable colonne par colonne : minutes, buts, passes, "
    "dribbles, arrêts, note moyenne, club et valeur estimée.":
        "The full table, sortable by any column: minutes, goals, passes, "
        "dribbles, saves, average rating, club and estimated value.",
    "Les {n} joueurs appelés en sélection du Burkina Faso depuis 2022, avec leur "
    "fiche individuelle et un tableau détaillé triable.":
        "The {n} players called up by Burkina Faso since 2022, each with an "
        "individual profile, plus a sortable detailed table.",
    "Gardien": "Goalkeeper", "Défenseur": "Defender",
    "Milieu": "Midfielder", "Attaquant": "Forward",

    # --- matches index ----------------------------------------------------
    "Chaque rencontre, en détail": "Every match, in detail",
    "{n} matchs depuis janvier 2022 avec composition, statistiques d'équipe et "
    "chronologie des buts.":
        "{n} matches since January 2022 with the lineup, team statistics and "
        "the goal timeline.",
    "Les {n} matchs du Burkina Faso depuis 2022 : compositions, statistiques et "
    "chronologies.":
        "Burkina Faso's {n} matches since 2022: lineups, statistics and timelines.",
    "{n} matchs · {w}V {d}N {l}D": "{n} matches · {w}W {d}D {l}L",
    "CAN 2025": "AFCON 2025",
    "Éliminatoires CM 2026 & amicaux 2025": "2026 WC qualifiers & 2025 friendlies",
    "CAN 2023 & éliminatoires 2024": "AFCON 2023 & 2024 qualifiers",
    "Éliminatoires CM 2026 (2023)": "2026 WC qualifiers (2023)",
    "CAN 2021 (janv. 2022)": "AFCON 2021 (Jan 2022)",
    "Autres matchs": "Other matches",

    # --- squad page -------------------------------------------------------
    "Le groupe actuel et sa structure": "The current group and how it is built",
    "Dernière liste connue, pyramide des âges, pays des clubs et type de "
    "championnat.":
        "The latest known squad list, age distribution, club countries and "
        "league types.",
    "Effectif du Burkina Faso : postes, âges, clubs et championnats.":
        "Burkina Faso's squad: positions, ages, clubs and leagues.",

    # --- analysis ---------------------------------------------------------
    "Comment cette équipe joue": "How this team plays",
    "Style de jeu comparé aux adversaires rencontrés, capacité à renverser une "
    "situation, temps forts, systèmes et importance des joueurs.":
        "Style of play measured against the opponents actually faced, the "
        "ability to turn a match around, strong and weak periods, and formations.",
    "Style de jeu du Burkina Faso, résilience, temps forts et systèmes — chaque "
    "métrique avec son échantillon.":
        "Burkina Faso's style of play, resilience, timing and formations — every "
        "metric with its sample size.",

    # --- management -------------------------------------------------------
    "Gestion de l'effectif": "Squad management",
    "Qui pèse, qui tourne, qui entre": "Who matters, who rotates, who comes on",
    "Importance des joueurs, stabilité du onze, associations sur le terrain, "
    "utilisation du banc et effet du calendrier. Chaque mesure est affichée avec "
    "son échantillon et masquée sous son seuil.":
        "Player importance, stability of the eleven, on-pitch partnerships, use "
        "of the bench and the effect of the calendar. Every measure is shown "
        "with its sample and hidden below its threshold.",
    "Importance des joueurs du Burkina Faso, rotation du onze, associations sur "
    "le terrain, utilisation du banc et effet du calendrier.":
        "Player importance for Burkina Faso, rotation of the eleven, on-pitch "
        "partnerships, use of the bench and the effect of the calendar.",

    # --- history ----------------------------------------------------------
    "1960 à aujourd'hui": "1960 to today",
    "Toutes les rencontres officielles depuis l'indépendance : tendances, "
    "parcours en CAN, sélectionneurs, lieux, tirs au but et trajectoire Elo.":
        "Every official match since independence: trends, AFCON runs, head "
        "coaches, venues, shootouts and the Elo trajectory.",
    "Histoire du Burkina Faso depuis 1960 : bilans, CAN, sélectionneurs, lieux, "
    "tirs au but et classement Elo.":
        "Burkina Faso's history since 1960: records, AFCON runs, head coaches, "
        "venues, shootouts and Elo rating.",
    "en cours": "in progress",
    "{n} m · {w}-{d}-{l} · {ppg} pts/m": "{n} m · {w}-{d}-{l} · {ppg} pts/m",

    # --- projections ------------------------------------------------------
    "CAN 2027, CM 2030 et le vivier": "AFCON 2027, WC 2030 and the pipeline",
    "Âge de l'effectif aux prochaines échéances, attentes face aux rivaux "
    "africains et passage des équipes de jeunes vers les A. Modèles simples, "
    "explicitement illustratifs.":
        "Squad age at the next tournaments, expectations against African rivals "
        "and the step up from the youth teams. Simple models, explicitly "
        "illustrative.",
    "Projections du Burkina Faso vers la CAN 2027 et le Mondial 2030 : âges, "
    "vivier des jeunes, attentes Elo et vérification du modèle.":
        "Burkina Faso's projections towards AFCON 2027 and the 2030 World Cup: "
        "ages, youth pipeline, Elo expectations and a model backtest.",

    # --- methodology ------------------------------------------------------
    "Comment ces chiffres sont produits": "How these numbers are produced",
    "Sources, formules, seuils et limites. Tout est reproductible : le code et "
    "les données intermédiaires sont publics.":
        "Sources, formulas, thresholds and limits. All of it is reproducible: "
        "the code and the intermediate data are public.",
    "Sources, formules, seuils et limites du projet Étalons Analytics.":
        "Sources, formulas, thresholds and limits of the Étalons Analytics project.",
    "Crédits photo": "Photo credits",
    "Portraits issus de Wikimedia Commons, sous licence libre. Aucune photo de "
    "presse sous droits n'est republiée ici.":
        "Portraits come from Wikimedia Commons under a free licence. No "
        "copyrighted press photography is republished here.",

    # --- match page -------------------------------------------------------
    "Victoire": "Win", "Match nul": "Draw", "Défaite": "Defeat",
    "à domicile": "at home", "à l'extérieur": "away",
    "terrain neutre": "neutral ground",
    "Prochain match": "Next match",
    ", formation {f}": ", {f} formation",
    "{result} {venue}{formation}.": "{result} {venue}{formation}.",
    "Chronologie": "Timeline",
    "Fiche du match": "Match facts",
    "Statistiques d'équipe": "Team statistics",
    "Composition": "Lineup",
    "Compétition": "Competition", "Date": "Date", "Lieu": "Venue",
    "Système": "Formation", "Système adverse": "Opponent formation",
    "Durée effective": "Effective length", "Minutes en tête": "Minutes leading",
    "Minutes menés": "Minutes trailing",
    "Domicile": "Home", "Extérieur": "Away",
    "Titulaires ({n})": "Starting eleven ({n})",
    "Entrés en jeu ({n})": "Came on ({n})",
    "Non entrés ({n})": "Unused ({n})",
    "Aucun événement enregistré pour ce match.":
        "No events recorded for this match.",
    "Statistiques détaillées non publiées pour ce match.":
        "Detailed statistics were not published for this match.",
    "carton": "card",
    "(blessure)": "(injury)",
    "BUT": "GOAL", "CHG": "SUB",
    "{n} but": "{n} goal", "{n} buts": "{n} goals", "{n} p.d.": "{n} assists",
    "{result} {gf}-{ga} contre {opponent} le {date} ({tournament}) : "
    "composition, statistiques et chronologie des buts.":
        "{result} {gf}-{ga} against {opponent} on {date} ({tournament}): lineup, "
        "statistics and the goal timeline.",
    "Possession": "Possession", "Tirs": "Shots", "Tirs cadrés": "Shots on target",
    "Grosses occasions": "Big chances", "Passes": "Passes",
    "Passes réussies": "Accurate passes", "Corners": "Corners", "Fautes": "Fouls",
    "Tacles": "Tackles", "Interceptions": "Interceptions", "Arrêts": "Saves",

    # --- player page ------------------------------------------------------
    "International actif": "Active international",
    "En marge du groupe": "On the fringe of the squad",
    "Hors du groupe": "Out of the squad",
    "Retraité international": "Retired from internationals",
    "Retraité": "Retired",
    "Identité": "Profile",
    "Bilan depuis janv. 2022": "Record since Jan 2022",
    "Importance": "Importance",
    "En sortie de banc": "Off the bench",
    "Match par match": "Match by match",
    "Poste": "Position", "Âge": "Age", "Club": "Club",
    "Sélections (carrière)": "Caps (career)", "Buts (carrière)": "Goals (career)",
    "Valeur estimée": "Estimated value", "Taille": "Height", "Pied": "Foot",
    "Dernière apparition": "Last appearance",
    "{n} ans": "{n} yrs", "{n} cm": "{n} cm",
    "Matchs dans le groupe": "Matchday squads",
    "Apparitions": "Appearances", "Titularisations": "Starts",
    "Minutes": "Minutes", "Buts": "Goals", "Passes décisives": "Assists",
    "Dribbles réussis": "Dribbles completed", "Note moyenne": "Average rating",
    "Rôle": "Role", "Part des minutes": "Minutes share",
    "On/Off ±/90": "On/Off ±/90",
    "PPM titulaire − remplaçant": "PPG started − not started",
    "Buts+passes /90": "Goals+assists /90",
    "– (échantillon insuffisant)": "– (insufficient sample)",
    "Pilier": "Pillar", "Rotation": "Rotation", "Marge": "Fringe",
    "Pas encore assez de matchs pour situer ce joueur.":
        "Not enough matches yet to place this player.",
    "Entrées": "Sub appearances", "Buts + passes": "Goals + assists",
    "Entrée moyenne": "Average entry",
    "Adversaire": "Opponent", "Score": "Score", "Statut": "Status",
    "Min": "Min", "P. déc.": "Assists", "Note": "Rating",
    "Aucun match programmé dans les sources pour l'instant.":
        "No match scheduled in the sources yet.",
    "Tit.": "Start", "Rempl.": "Sub", "Non entré": "Unused",
    "Photo : {author} · {licence} · ": "Photo: {author} · {licence} · ",
    "{name} ({pos}, {club}) : sélections, minutes, buts et performances avec les "
    "Étalons du Burkina Faso depuis 2022.":
        "{name} ({pos}, {club}): caps, minutes, goals and performance for "
        "Burkina Faso since 2022.",
    "{name} ({pos}, {club}) avec le Burkina Faso depuis 2022 : {apps} apparitions, "
    "{minutes} minutes, {goals} buts. Fiche complète, match par match.":
        "{name} ({pos}, {club}) for Burkina Faso since 2022: {apps} appearances, "
        "{minutes} minutes, {goals} goals. Full match-by-match record.",
    "{name} — statistiques Burkina Faso": "{name} — Burkina Faso stats",

    # --- shared -----------------------------------------------------------
    "Burkina Faso": "Burkina Faso",
}

# result letters differ per language (Victoire/Nul/Défaite vs Win/Draw/Loss)
RESULT_LETTER = {"fr": {"W": "V", "D": "N", "L": "D"},
                 "en": {"W": "W", "D": "D", "L": "L"}}


def translator(lang):
    """Return t(source_french, **vars) for the requested language."""
    if lang == "fr":
        def t_fr(source, **kw):
            return source.format(**kw) if kw else source
        return t_fr

    def t_en(source, **kw):
        target = EN.get(source)
        if target is None:
            # punctuation and placeholders need no translation
            if any(ch.isalpha() for ch in source):
                MISSES.add(source)
            target = source
        return target.format(**kw) if kw else target
    return t_en
