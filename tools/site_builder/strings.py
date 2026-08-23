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

    # --- plain notes on the detail pages -----------------------------------
    # Written into the HTML on these pages rather than swapped in by script, so
    # they read without JavaScript like the rest of a match or player page.
    "L'ordre des événements du match : buts, changements, cartons. "
    "Les minutes comptent les arrêts de jeu, donc un but à 90+3 "
    "apparaît après la 90e.":
        "The order of what happened: goals, substitutions, cards. Minutes "
        "include stoppage time, so a goal at 90+3 appears after the 90th.",
    "« Durée effective » est le temps réellement joué, arrêts de "
    "jeu inclus : elle dépasse presque toujours 90 minutes. Les "
    "minutes passées en tête ou menés disent comment le match s'est "
    "déroulé, pas seulement comment il s'est terminé.":
        "“Effective length” is the time actually played, stoppage included — it "
        "almost always exceeds 90 minutes. The minutes spent leading or trailing "
        "say how the match went, not just how it ended.",
    "Le Burkina à gauche, l'adversaire à droite. Comparez les deux "
    "colonnes plutôt qu'un chiffre seul : dominer la possession ou "
    "les tirs n'a jamais gagné un match à lui tout seul.":
        "Burkina Faso on the left, the opponent on the right. Compare the two "
        "columns rather than one figure alone: winning possession or shots has "
        "never won a match on its own.",
    "Le onze de départ, les entrants, et ceux restés sur le banc. "
    "La note est celle du fournisseur de données pour ce match ; "
    "elle manque sur les rencontres les moins couvertes.":
        "The starting eleven, who came on, and who stayed on the bench. The "
        "rating is the data provider's for that match; it is missing on the "
        "least-covered fixtures.",
    "Club, valeur et contrat viennent du profil du joueur chez le "
    "fournisseur de données et changent avec les transferts. Les "
    "sélections et buts de carrière couvrent toute la carrière, pas "
    "seulement la période étudiée ici.":
        "Club, value and contract come from the player's profile at the data "
        "provider and change with transfers. Career caps and goals cover the "
        "whole career, not only the window studied here.",
    "Uniquement depuis janvier 2022 : ce n'est pas le bilan d'une "
    "carrière. « Matchs dans le groupe » compte les feuilles de "
    "match, y compris celles où le joueur n'est pas entré.":
        "Since January 2022 only — this is not a career record. “Matchday "
        "squads” counts every team sheet, including those where the player did "
        "not come on.",
    "La place du joueur dans le groupe, mesure par mesure, sans "
    "note unique : chacune se lit à part. Un tiret veut dire trop "
    "peu de matchs pour le situer honnêtement.":
        "Where the player sits in the group, measure by measure, with no single "
        "score: each one is read on its own. A dash means too few matches to "
        "place them honestly.",
    "Ce que le joueur produit en entrant en cours de match. Sur "
    "aussi peu de minutes, un seul but change tout : à lire comme "
    "une indication, pas comme une preuve.":
        "What the player produces when coming on. Over so few minutes a single "
        "goal changes everything: read it as an indication, not as proof.",
    "Chaque feuille de match depuis 2022. « Non entré » veut dire "
    "convoqué mais resté sur le banc, ce qui est aussi une "
    "information. Une note absente veut dire que le match n'a pas "
    "de statistiques détaillées.":
        "Every team sheet since 2022. “Unused” means named in the squad but left "
        "on the bench, which is information too. A missing rating means the "
        "match has no detailed statistics.",

    # --- computed facts ----------------------------------------------------
    "Le saviez-vous ?": "Did you know?",
    "Des faits tirés directement des données — recalculés à chaque mise à jour, "
    "jamais écrits à la main.":
        "Facts taken straight from the data — recomputed on every update, never "
        "written by hand.",
    "Voir l'analyse complète →": "See the full analysis →",

    "Mené de deux buts ou plus, le Burkina Faso n'a encore jamais gagné : "
    "{w}V-{d}N-{l}D en {n} matchs depuis 2022, soit {ppg} point par match.":
        "Two goals down, Burkina Faso has never yet won: {w}W-{d}D-{l}L in {n} "
        "matches since 2022 — {ppg} points per match.",
    "Mené de deux buts ou plus depuis 2022 : {w}V-{d}N-{l}D en {n} matchs, "
    "soit {ppg} point par match.":
        "Two goals down since 2022: {w}W-{d}D-{l}L in {n} matches — {ppg} points "
        "per match.",
    "Quand l'équipe ne se fait jamais mener, elle ne perd pratiquement pas : "
    "{w}V-{d}N-{l}D en {n} matchs, soit {ppg} points par match.":
        "When the team never falls behind, it barely loses: {w}W-{d}D-{l}L in "
        "{n} matches — {ppg} points per match.",
    "Sur {total} buts encaissés depuis 2022, {never} n'ont jamais reçu de "
    "réponse dans le même match — soit {pct} %.":
        "Of {total} goals conceded since 2022, {never} were never answered in "
        "the same match — {pct}%.",
    "Le premier but décide presque tout : {sf_ppg} points par match en "
    "marquant d'abord ({sf_n} matchs), {cf_ppg} en encaissant d'abord "
    "({cf_n} matchs, {cf_w} victoires pour {cf_l} défaites).":
        "The first goal decides almost everything: {sf_ppg} points per match "
        "when scoring first ({sf_n} matches), {cf_ppg} when conceding first "
        "({cf_n} matches, {cf_w} wins against {cf_l} defeats).",
    "Le Burkina marque nettement moins dans le premier quart d'heure "
    "({bin} minutes) que dans le reste du match — un écart trop net pour "
    "être le simple hasard.":
        "Burkina Faso scores markedly less in the opening quarter-hour "
        "({bin} minutes) than in the rest of the match — a gap too wide to be "
        "chance alone.",
    "Le Burkina marque nettement plus dans la tranche {bin} minutes que "
    "dans le reste du match — un écart trop net pour être le simple hasard.":
        "Burkina Faso scores markedly more in the {bin} minute band than in the "
        "rest of the match — a gap too wide to be chance alone.",
    "{name} a joué {min} minutes en sélection depuis 2022, l'équivalent de "
    "{matches} matchs complets.":
        "{name} has played {min} international minutes since 2022 — the "
        "equivalent of {matches} full matches.",
    "{name} a marqué {goals} des {total} buts de l'équipe depuis 2022, "
    "soit {pct} % à lui seul.":
        "{name} has scored {goals} of the team's {total} goals since 2022 — "
        "{pct}% on his own.",
    "En {best} : {best_ppg} points par match. En {worst} : {worst_ppg}. "
    "Mais les adversaires n'étaient pas les mêmes — Elo moyen {best_elo} "
    "contre {worst_elo}.":
        "In {best}: {best_ppg} points per match. In {worst}: {worst_ppg}. But "
        "the opponents were not the same — average Elo {best_elo} against "
        "{worst_elo}.",
    "Recevoir loin de chez soi coûte peu, mais coûte : {home_ppg} points par "
    "match au Burkina, {delo_ppg} sur les {delo_n} matchs « à domicile » "
    "joués à l'étranger.":
        "Hosting away from home costs little, but it costs: {home_ppg} points "
        "per match in Burkina Faso, {delo_ppg} across the {delo_n} “home” "
        "matches played abroad.",
    "Au classement Elo, le Burkina est {caf} d'Afrique sur {n_caf} nations, "
    "et {world} au monde, avec {pts} points.":
        "On Elo, Burkina Faso is {caf} in Africa out of {n_caf} nations, and "
        "{world} in the world, on {pts} points.",
    "Depuis 1960 : {pld} matchs, {w} victoires, {d} nuls, {l} défaites — "
    "{pct} % de victoires.":
        "Since 1960: {pld} matches, {w} wins, {d} draws, {l} defeats — {pct}% "
        "won.",

    # --- plain-language glossary -------------------------------------------
    "Comment lire ces chiffres": "How to read these numbers",
    "Pas besoin d'être statisticien. Voici ce que veut dire chaque mesure du "
    "site — et surtout ce qu'elle ne dit pas.":
        "You do not need to be a statistician. Here is what each measure on the "
        "site means — and, more to the point, what it does not.",
    "Nouveau sur ces chiffres ? Commencez ici →":
        "New to these numbers? Start here →",
    "La méthode en détail": "The method in detail",

    "Points par match": "Points per match",
    "Une victoire vaut 3 points, un nul 1, une défaite 0. On additionne, "
    "on divise par le nombre de matchs. 2,43 veut dire une équipe qui "
    "gagne presque à chaque fois ; 0,07 une équipe qui n'y arrive "
    "pratiquement jamais.":
        "A win is worth 3 points, a draw 1, a defeat 0. Add them up and divide "
        "by matches played. 2.43 means a team winning nearly every time; 0.07 a "
        "team that almost never manages it.",

    "Par 90 minutes": "Per 90 minutes",
    "Un remplaçant qui joue 20 minutes ne peut pas être comparé à un "
    "titulaire qui joue 90. On ramène donc tout à un match complet : "
    "2 buts en 180 minutes, c'est 1 but par 90 minutes.":
        "A substitute who plays 20 minutes cannot be compared with a starter who "
        "plays 90. So everything is scaled to a full match: 2 goals in 180 "
        "minutes is 1 goal per 90 minutes.",

    "Minutes jouées": "Minutes played",
    "La mesure la plus honnête de la confiance d'un sélectionneur. Une "
    "sélection peut se discuter ; les minutes sur le terrain sont un "
    "choix répété match après match.":
        "The most honest measure of a head coach's trust. A call-up can be "
        "argued about; minutes on the pitch are a choice repeated match after "
        "match.",

    "Pourquoi un tiret au lieu d'un chiffre": "Why a dash instead of a number",
    "Sur 4 matchs, un seul match chanceux change tout. Quand "
    "l'échantillon est trop petit pour vouloir dire quelque chose, on "
    "affiche « – » plutôt qu'un chiffre qui tromperait.":
        "Over 4 matches, one lucky game changes everything. When the sample is "
        "too small to mean anything we show “–” rather than a number that would "
        "mislead.",

    "Le classement Elo": "The Elo rating",
    "Un seul nombre pour situer la force d'une équipe, emprunté aux "
    "échecs. Battre un adversaire plus fort en rapporte beaucoup ; "
    "perdre contre un plus faible en coûte beaucoup. Il dit où en est "
    "une équipe par rapport aux autres, pas son palmarès.":
        "A single number placing a team's strength, borrowed from chess. Beating "
        "a stronger opponent earns a lot; losing to a weaker one costs a lot. It "
        "says where a team stands against the rest, not what it has won.",

    "La possession": "Possession",
    "La part du temps où l'équipe a le ballon. Seule, elle ne dit pas "
    "grand-chose : on peut dominer le ballon et perdre. C'est pourquoi "
    "chaque chiffre est présenté à côté du même chiffre pour les "
    "adversaires réellement rencontrés.":
        "The share of the time the team had the ball. On its own it says little: "
        "you can dominate the ball and lose. That is why every figure sits "
        "beside the same figure for the opponents actually faced.",

    "« Descriptif, pas causal »": "“Descriptive, not causal”",
    "On peut constater que deux choses vont ensemble. On ne peut pas "
    "dire que l'une cause l'autre. Peu de repos semble être le meilleur "
    "repos — jusqu'à ce qu'on voie que ces matchs étaient joués contre "
    "les adversaires les plus faibles.":
        "We can observe that two things go together. We cannot say one causes "
        "the other. Little rest looks like the best rest — until you notice "
        "those matches were played against the weakest opponents.",

    "Pourquoi on montre toujours le compte": "Why the count is always shown",
    "« 67 % » peut vouloir dire 2 sur 3. Le nombre brut est toujours "
    "affiché à côté du pourcentage, pour que vous puissiez juger "
    "vous-même de ce qu'il vaut.":
        "“67%” can mean 2 out of 3. The raw count is always shown beside the "
        "percentage, so you can judge for yourself what it is worth.",

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
