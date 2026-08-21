const I18N = {
  fr: {
    tagline: "Analyse de données de l'équipe nationale senior du Burkina Faso — effectif, performances individuelles depuis la CAN 2021, histoire et projections.",
    nav_squad: "Effectif", nav_pool: "Joueurs", nav_breakdowns: "Répartitions",
    nav_forms: "Systèmes",
    nav_history: "Histoire", nav_elo: "Elo", nav_proj: "Projections", nav_method: "Méthodologie",
    tile_caf: "Rang Elo CAF", tile_caf_sub: "{world}e mondial · {n} équipes CAF",
    tile_elo: "Points Elo", tile_elo_sub: "pic {peak} ({year})",
    tile_age: "Âge moyen (effectif)", tile_age_sub: "médiane {median} ans",
    tile_europe: "En Europe", tile_europe_sub: "{top5} joueurs en top 5 européen",
    tile_record: "Matchs depuis 1960", tile_record_sub: "{w}% de victoires",
    tile_pool: "Joueurs utilisés (4 ans)", tile_pool_sub: "{events} matchs analysés",
    s_squad: "Effectif actuel", s_squad_lead: "Dernière liste connue ({asof_short}) — âges, clubs et profil de la sélection.",
    s_pool: "Les joueurs — 4 dernières années", s_pool_lead: "Tous les joueurs appelés depuis la CAN 2021 (janv. 2022) : temps de jeu et performances individuelles en sélection, match par match.",
    s_break: "Répartitions", s_break_lead: "Où jouent les Étalons et comment l'effectif se structure.",
    s_history: "Histoire (1960–{last_year})", s_history_lead: "{pld} matchs officiels depuis {first_year} : tendances, CAN et légendes.",
    s_elo: "Classement Elo", s_elo_lead: "Elo calculé sur l'intégralité des matchs internationaux depuis 1960 (formule eloratings.net).",
    s_proj: "Projections CAN 2027 & CM 2030", s_proj_lead: "Âge de l'effectif aux prochaines échéances et trajectoire Elo — modèles simples et transparents.",
    s_method: "Méthodologie & sources",
    c_pos: "Répartition par poste", c_pos_sub: "Effectif actuel",
    c_age: "Pyramide des âges", c_age_sub: "Effectif actuel, par tranche",
    c_minutes: "Temps de jeu en sélection", c_minutes_sub: "Top 15 minutes jouées depuis janv. 2022",
    c_goals: "Buteurs & passeurs", c_goals_sub: "Buts + passes décisives depuis janv. 2022",
    c_clubs: "Pays des clubs", c_clubs_sub: "Effectif actuel",
    c_leagues: "Type de championnat", c_leagues_sub: "Effectif actuel",
    nav_tempo: "Temps forts", nav_imp: "Importance",
    s_tempo: "Temps forts, temps faibles", s_tempo_lead: "Quand les Étalons marquent et encaissent depuis janv. 2022, et ce que devient un match selon qui ouvre le score. Comptages bruts — {n} matchs.",
    c_bins: "Buts par période de jeu", c_bins_sub: "Segments clairs = part inscrite dans les arrêts de jeu (45+ / 90+) · Prol. à part",
    c_gamestate: "Physionomie des matchs", c_gamestate_sub: "Minutes passées en tête, à égalité, menés — et l'impact du premier but",
    bin_1_15: "1–15", bin_16_30: "16–30", bin_31_45: "31–45+", bin_46_60: "46–60",
    bin_61_75: "61–75", bin_76_90: "76–90+", bin_et: "Prol.",
    legend_gf: "Buts marqués", legend_ga: "Buts encaissés",
    legend_gf_stop: "Marqués (arrêts de jeu)", legend_ga_stop: "Encaissés (arrêts de jeu)",
    chi_none: "Aucune période statistiquement atypique (χ², p ≥ 0,05).",
    chi_low: "Période statistiquement atypique ({side}) : {bin} — anormalement peu (χ² = {stat}, p < 0,05).",
    chi_high: "Période statistiquement atypique ({side}) : {bin} — anormalement beaucoup (χ² = {stat}, p < 0,05).",
    side_gf: "buts marqués", side_ga: "buts encaissés",
    t_scored_first: "Ouvre le score", t_conceded_first: "Encaisse en premier",
    t_comebacks: "Mené, puis…", t_blown: "En tête, puis…",
    st_leading: "En tête", st_level: "À égalité", st_trailing: "Mené",
    pts_per_match: "pts/m",
    s_imp: "Importance des joueurs & banc", s_imp_lead: "Qui pèse vraiment sur les résultats depuis janv. 2022 — sans indice composite : chaque composante est affichée avec son échantillon, et masquée sous son seuil (« – »). Fenêtre = depuis la première convocation du joueur.",
    c_imp_table: "Composantes d'importance", c_imp_table_sub: "Joueurs avec ≥ 8 matchs d'équipe dans leur fenêtre, classés par part des minutes · « – » = échantillon insuffisant",
    c_imp_prof: "Profil percentile", c_imp_prof_sub: "Position du joueur parmi les pairs qualifiés pour chaque composante (points gris = pairs)",
    c_bench: "Impact du banc", c_bench_sub: "Buts + passes en sortie de banc (bruts) · /90 seulement si ≥ 5 entrées et ≥ 150 min",
    h_tier: "Rôle", h_share: "Part min.", h_onoff: "On/Off ±/90", h_ppgdiff: "PPM tit.−remp.",
    h_ga90: "B+P /90", h_subs: "Entrées", h_entry: "Entrée moy.",
    tier_pilier: "Pilier", tier_rotation: "Rotation", tier_marge: "Marge",
    comp_share: "Part des minutes", comp_onoff: "On/Off (±/90)", comp_ppg: "PPM tit. vs remp.",
    comp_ga90: "Buts+passes /90", comp_rating: "Note moyenne",
    imp_picker: "Joueur :",
    bench_baseline: "Référence équipe après la 60e : {gd90} but(s) d'écart /90 ({gf} marqués, {ga} encaissés en {min} min).",
    bench_bar_label: "{ga} B+P · {min} min",
    c_strip: "Dernière apparition par joueur", c_strip_sub: "Chaque point = un joueur, positionné à sa dernière convocation ou feuille de match, coloré par statut",
    no_pilier_note: "Aucun joueur n'atteint le seuil « Pilier » (≥ 60 % des minutes ET ≥ 66 % de titularisations) — l'effectif tourne beaucoup.",
    s_forms: "Systèmes de jeu", s_forms_lead: "Bilan par système de départ depuis janv. 2022. Les systèmes utilisés moins de 8 fois sont regroupés — les effectifs restent trop petits pour des conclusions causales.",
    c_forms: "Résultats par formation", c_forms_sub: "V / N / D par système de départ · le détail (buts, Elo moyen des adversaires) est dans l'infobulle et les données",
    forms_other: "Autres ({n} systèmes)",
    legend_w: "Victoires", legend_d: "Nuls", legend_l: "Défaites",
    forms_tip: "{n} matchs · {ppg} pts/m<br/>BM {gf} ({gfpm}/m) · BE {ga} ({gapm}/m)<br/>Elo moyen adv. {elo} (sur {nelo} matchs)",
    c_decades: "Taux de victoire par décennie", c_decades_sub: "Matchs officiels (2020s en cours)",
    c_form: "Forme sur 5 ans glissants", c_form_sub: "% de victoires, moyenne mobile pondérée",
    c_afcon: "Parcours en CAN", c_afcon_sub: "Stade atteint par édition — finaliste 2013, 3e en 2017",
    c_elo_tl: "Elo depuis 1960", c_elo_tl_sub: "Avec projection 2027–2030 (bande ≈ 80 %)",
    c_winexp: "Résultat attendu vs rivaux CAF", c_winexp_sub: "Score Elo attendu (victoire + ½ nul), terrain neutre",
    c_proj_age: "Âges à la CAN 2027", c_proj_age_sub: "Effectif actuel projeté — bande = fenêtre de pic par poste",
    t_squad: "Liste (dernier rassemblement)", t_callups: "Autres convocations récentes (12 mois)",
    t_capped: "Recordmen de sélections", t_scorers: "Meilleurs buteurs",
    t_last10: "10 derniers matchs",
    h_player: "Joueur", h_pos: "P.", h_age: "Âge", h_caps: "Sél.", h_goals: "Buts",
    h_club: "Club", h_country: "Pays", h_age27: "Âge CAN 27", h_career: "Carrière",
    h_rank: "#", h_windows: "Fenêtres", h_sheets: "Feuilles", h_apps: "Matchs", h_starts: "Tit.",
    h_min: "Min", h_assists: "P. déc.", h_passes: "Passes", h_passpct: "Passes %",
    h_dribbles: "Dribbles", h_tackles: "Tacles", h_inter: "Int.", h_saves: "Arrêts",
    h_rating: "Note", h_date: "Date", h_opp: "Adversaire", h_score: "Score", h_comp: "Compétition",
    pos_GK: "Gardiens", pos_DF: "Défenseurs", pos_MF: "Milieux", pos_FW: "Attaquants",
    lg_top5: "Top 5 européen", lg_europe_other: "Reste de l'Europe", lg_africa: "Afrique",
    lg_home: "Burkina Faso", lg_world_other: "Autres", lg_unknown: "Inconnu",
    round_1: "Groupes", round_2: "8es", round_3: "Quarts", round_4: "Demies / 4e",
    round_5: "3e place", round_6: "Finale", round_7: "Champion",
    phase_before: "avant pic", phase_peak: "dans le pic", phase_after: "après pic",
    st_active: "Actif", st_fringe: "En marge", st_out: "Hors du groupe",
    st_retired_int: "Retraite int.", st_retired_career: "Retraité (car.)",
    h_status: "Statut", h_league: "Championnat", h_mv: "VM",
    club_verified_tip: "Club vérifié (Sofascore)", club_wiki_tip: "Dernier club connu (Wikipedia, peut être obsolète)",
    peak_band: "Fenêtre de pic",
    elo_hist: "Historique", elo_proj: "Projection", elo_peak: "Pic",
    goals_g: "Buts", goals_a: "Passes décisives",
    gf_per_match: "Buts marqués / match", ga_per_match: "Buts encaissés / match",
    winexp_note: "0,5 = adversaire de force égale. Calculé à partir des Elo actuels.",
    pool_search: "Filtrer par nom…", pool_min_note: "Couverture : {pct} % des apparitions avec statistiques détaillées ({events_stats}/{events} matchs). Les amicaux mineurs n'ont parfois que les minutes.",
    show_data: "Voir les données", core_title: "Génération clé",
    core_text: "{n} joueurs à 15 sélections ou plus : âge moyen {age_now} ans aujourd'hui, {age_27} ans à la CAN 2027 — {in_peak} seront dans leur fenêtre de pic.",
    win_result: "V", draw_result: "N", loss_result: "D",
    method_html: `
      <h3>Pipeline ouvert (ETL)</h3>
      <p>Extraction : instantanés bruts des sources (Wikipedia, martj42, Sofascore) → <code>data/raw/</code>.
      Transformation : registre des joueurs (homonymes résolus par date de naissance), convocations, apparitions match par match → <code>data/staging/</code>.
      Chargement : agrégats analytiques → <code>data/marts/</code> + les JSON de ce tableau de bord. Contrôles qualité à chaque exécution (unicité, intégrité référentielle, bornes, cohérence buts joueurs/équipe).</p>
      <h3>Périmètre joueurs</h3>
      <p>Tout joueur appelé depuis la CAN 2021 (janv. 2022) : listes CAN 2021/2023/2025, effectif actuel et convocations récentes (Wikipedia), plus tout joueur apparu sur une feuille de match (Sofascore). Les statistiques individuelles (minutes, passes, dribbles, arrêts…) proviennent des feuilles de match Sofascore — projet non affilié, usage non commercial avec attribution.</p>
      <h3>Elo</h3>
      <p>Recalculé sur ~49 000 matchs internationaux depuis 1872 (données martj42, CC0) : K = 60 (CM), 50 (CAN), 40 (qualifs), 30 (autres), 20 (amicaux) ; multiplicateur d'écart de buts ; +100 d'avantage à domicile. La projection est une tendance linéaire sur les Elo de fin d'année depuis 2010, bande ≈ 80 % basée sur la volatilité annuelle — un modèle illustratif, pas une prédiction.</p>
      <h3>Projections d'âge</h3>
      <p>CAN 2027 supposée mi-2027 (dates non finalisées), CM 2030 en juin 2030. Fenêtres de pic indicatives : gardiens 26–33 ans, défenseurs 25–30, milieux et attaquants 24–29.</p>
      <h3>Périodes de jeu & physionomie</h3>
      <p>Chronologie reconstruite match par match à partir des incidents (arrêts de jeu inclus ; prolongations détectées, y compris via la présence d'une séance de tirs au but). Les buts sont classés en 6 périodes de 15 minutes — ceux du temps additionnel restent dans 31–45+ / 76–90+, leur part est affichée séparément ; la prolongation est comptée à part. Une période n'est déclarée atypique que si le χ² sur les 6 périodes réglementaires est significatif (p &lt; 0,05). Les minutes en tête / à égalité / menés découlent de la même chronologie.</p>
      <h3>Importance des joueurs</h3>
      <p>Pas d'indice composite. Chaque composante est affichée séparément, avec son seuil : part des minutes (fenêtre = depuis la première convocation du joueur) ; on/off ±/90 (≥ 900 min sur le terrain ET ≥ 450 min hors terrain en étant dans le groupe) ; points par match titulaire vs remplaçant (≥ 10 titularisations ET ≥ 8 matchs dans le groupe sans titularisation) ; buts+passes /90 (≥ 450 min) ; note pondérée par les minutes (≥ 5 matchs notés ET ≥ 300 min). Rôles : Pilier ≥ 60 % des minutes ET ≥ 66 % de titularisations ; Rotation ≥ 25 % ; sinon Marge. Percentiles calculés parmi les seuls joueurs qualifiés pour chaque composante. Lecture descriptive, jamais causale.</p>
      <h3>Impact du banc</h3>
      <p>Buts + passes en sortie de banc en valeurs brutes ; /90 uniquement à partir de 5 entrées et 150 minutes ; différence de buts après entrée (≥ 8 entrées) à comparer à la référence de l'équipe après la 60e minute, affichée à côté.</p>
      <h3>Limites connues</h3>
      <p>Sélections/buts « carrière » figés à la dernière mise à jour Wikipedia ; pas de listes complètes pour les fenêtres de qualifications (contributions bienvenues) ; ~24 % des apparitions (amicaux mineurs) sans statistiques détaillées.</p>`,
    footer: "Étalons Analytics — projet open source (MIT). Données : Wikipedia (CC BY-SA), martj42/international_results (CC0), Sofascore (non affilié). Généré le {date}.",
  },
  en: {
    tagline: "Data analysis of Burkina Faso's senior national football team — squad, individual performances since AFCON 2021, history and projections.",
    nav_squad: "Squad", nav_pool: "Players", nav_breakdowns: "Breakdowns",
    nav_history: "History", nav_elo: "Elo", nav_proj: "Projections", nav_method: "Methodology",
    tile_caf: "CAF Elo rank", tile_caf_sub: "{world} in the world · {n} CAF teams",
    tile_elo: "Elo points", tile_elo_sub: "peak {peak} ({year})",
    tile_age: "Average age (squad)", tile_age_sub: "median {median} yrs",
    tile_europe: "Based in Europe", tile_europe_sub: "{top5} players in Europe's top 5",
    tile_record: "Matches since 1960", tile_record_sub: "{w}% won",
    tile_pool: "Players used (4 yrs)", tile_pool_sub: "{events} matches analysed",
    s_squad: "Current squad", s_squad_lead: "Latest known list ({asof_short}) — ages, clubs and squad profile.",
    s_pool: "The players — last 4 years", s_pool_lead: "Everyone called up since AFCON 2021 (Jan 2022): playing time and individual performance for the national team, match by match.",
    s_break: "Breakdowns", s_break_lead: "Where the Étalons play and how the squad is built.",
    s_history: "History (1960–{last_year})", s_history_lead: "{pld} official matches since {first_year}: trends, AFCON runs and legends.",
    s_elo: "Elo rating", s_elo_lead: "Elo computed over every international match since 1960 (eloratings.net formula).",
    s_proj: "Projections: AFCON 2027 & WC 2030", s_proj_lead: "Squad age at the next big tournaments and the Elo trajectory — simple, transparent models.",
    s_method: "Methodology & sources",
    c_pos: "Squad by position", c_pos_sub: "Current squad",
    c_age: "Age distribution", c_age_sub: "Current squad, by bracket",
    c_minutes: "National-team minutes", c_minutes_sub: "Top 15 minutes played since Jan 2022",
    c_goals: "Scorers & creators", c_goals_sub: "Goals + assists since Jan 2022",
    c_clubs: "Club countries", c_clubs_sub: "Current squad",
    c_leagues: "League type", c_leagues_sub: "Current squad",
    nav_tempo: "Timing", nav_imp: "Importance",
    s_tempo: "Strong and weak periods", s_tempo_lead: "When the Étalons score and concede since Jan 2022, and what a match becomes depending on who scores first. Raw counts — {n} matches.",
    c_bins: "Goals by period of play", c_bins_sub: "Lighter caps = share scored in stoppage time (45+ / 90+) · ET counted apart",
    c_gamestate: "Game states", c_gamestate_sub: "Minutes spent leading, level, trailing — and what the first goal does",
    bin_1_15: "1–15", bin_16_30: "16–30", bin_31_45: "31–45+", bin_46_60: "46–60",
    bin_61_75: "61–75", bin_76_90: "76–90+", bin_et: "ET",
    legend_gf: "Goals scored", legend_ga: "Goals conceded",
    legend_gf_stop: "Scored (stoppage)", legend_ga_stop: "Conceded (stoppage)",
    chi_none: "No statistically unusual period (χ², p ≥ 0.05).",
    chi_low: "Statistically unusual period ({side}): {bin} — unusually few (χ² = {stat}, p < 0.05).",
    chi_high: "Statistically unusual period ({side}): {bin} — unusually many (χ² = {stat}, p < 0.05).",
    side_gf: "goals scored", side_ga: "goals conceded",
    t_scored_first: "Scores first", t_conceded_first: "Concedes first",
    t_comebacks: "Trailed, then…", t_blown: "Led, then…",
    st_leading: "Leading", st_level: "Level", st_trailing: "Trailing",
    pts_per_match: "pts/m",
    s_imp: "Player importance & bench", s_imp_lead: "Who actually moves results since Jan 2022 — no composite index: every component is shown with its sample and hidden below its threshold (\"–\"). Window = since the player's first call-up.",
    c_imp_table: "Importance components", c_imp_table_sub: "Players with ≥ 8 team matches in their window, ranked by minutes share · \"–\" = insufficient sample",
    c_imp_prof: "Percentile profile", c_imp_prof_sub: "Player's position among qualified peers for each component (grey dots = peers)",
    c_bench: "Bench impact", c_bench_sub: "Goals + assists off the bench (raw) · /90 only with ≥ 5 sub apps and ≥ 150 min",
    h_tier: "Role", h_share: "Min. share", h_onoff: "On/Off ±/90", h_ppgdiff: "PPG started−sub",
    h_ga90: "G+A /90", h_subs: "Sub apps", h_entry: "Avg entry",
    tier_pilier: "Pillar", tier_rotation: "Rotation", tier_marge: "Fringe",
    comp_share: "Minutes share", comp_onoff: "On/Off (±/90)", comp_ppg: "PPG started vs sub",
    comp_ga90: "Goals+assists /90", comp_rating: "Average rating",
    imp_picker: "Player:",
    bench_baseline: "Team baseline after 60': {gd90} goal difference /90 ({gf} scored, {ga} conceded in {min} min).",
    bench_bar_label: "{ga} G+A · {min} min",
    c_strip: "Last appearance per player", c_strip_sub: "Each dot is a player at their last call-up or matchday sheet, colored by status",
    no_pilier_note: "No player clears the \"Pillar\" bar (≥ 60% of minutes AND ≥ 66% of squad matches started) — the squad rotates heavily.",
    s_forms: "Playing systems", s_forms_lead: "Record by starting formation since Jan 2022. Systems used fewer than 8 times are pooled — samples stay too small for causal claims.",
    c_forms: "Results by formation", c_forms_sub: "W / D / L by starting system · details (goals, average opponent Elo) in the tooltip and data view",
    forms_other: "Other ({n} systems)",
    legend_w: "Wins", legend_d: "Draws", legend_l: "Losses",
    forms_tip: "{n} matches · {ppg} pts/m<br/>GF {gf} ({gfpm}/m) · GA {ga} ({gapm}/m)<br/>Avg opponent Elo {elo} (over {nelo} matches)",
    c_decades: "Win rate by decade", c_decades_sub: "Official matches (2020s ongoing)",
    c_form: "Rolling 5-year form", c_form_sub: "Win %, weighted moving average",
    c_afcon: "AFCON campaigns", c_afcon_sub: "Stage reached by edition — 2013 finalists, 3rd in 2017",
    c_elo_tl: "Elo since 1960", c_elo_tl_sub: "With 2027–2030 projection (≈80% band)",
    c_winexp: "Expected result vs CAF rivals", c_winexp_sub: "Elo expected score (win + ½ draw), neutral ground",
    c_proj_age: "Ages at AFCON 2027", c_proj_age_sub: "Current squad projected — band = peak window by position",
    t_squad: "Squad list (latest camp)", t_callups: "Other recent call-ups (12 months)",
    t_capped: "Most capped", t_scorers: "Top scorers",
    t_last10: "Last 10 matches",
    h_player: "Player", h_pos: "P.", h_age: "Age", h_caps: "Caps", h_goals: "Goals",
    h_club: "Club", h_country: "Country", h_age27: "Age AFCON 27", h_career: "Career",
    h_rank: "#", h_windows: "Windows", h_sheets: "Sheets", h_apps: "Apps", h_starts: "Starts",
    h_min: "Min", h_assists: "Assists", h_passes: "Passes", h_passpct: "Pass %",
    h_dribbles: "Dribbles", h_tackles: "Tackles", h_inter: "Int.", h_saves: "Saves",
    h_rating: "Rating", h_date: "Date", h_opp: "Opponent", h_score: "Score", h_comp: "Competition",
    pos_GK: "Goalkeepers", pos_DF: "Defenders", pos_MF: "Midfielders", pos_FW: "Forwards",
    lg_top5: "European top 5", lg_europe_other: "Rest of Europe", lg_africa: "Africa",
    lg_home: "Burkina Faso", lg_world_other: "Other", lg_unknown: "Unknown",
    round_1: "Groups", round_2: "R16", round_3: "QF", round_4: "SF / 4th",
    round_5: "3rd place", round_6: "Final", round_7: "Champions",
    phase_before: "pre-peak", phase_peak: "in peak", phase_after: "post-peak",
    st_active: "Active", st_fringe: "Fringe", st_out: "Out of group",
    st_retired_int: "Int. retired", st_retired_career: "Retired (car.)",
    h_status: "Status", h_league: "League", h_mv: "MV",
    club_verified_tip: "Verified club (Sofascore)", club_wiki_tip: "Last known club (Wikipedia, may be stale)",
    peak_band: "Peak window",
    elo_hist: "History", elo_proj: "Projection", elo_peak: "Peak",
    goals_g: "Goals", goals_a: "Assists",
    gf_per_match: "Goals scored / match", ga_per_match: "Goals conceded / match",
    winexp_note: "0.5 = evenly matched opponent. Based on current Elo ratings.",
    pool_search: "Filter by name…", pool_min_note: "Coverage: {pct}% of appearances have detailed stats ({events_stats}/{events} matches). Minor friendlies sometimes carry minutes only.",
    show_data: "View data", core_title: "Core generation",
    core_text: "{n} players with 15+ caps: average age {age_now} today, {age_27} at AFCON 2027 — {in_peak} will be in their peak window.",
    win_result: "W", draw_result: "D", loss_result: "L",
    method_html: `
      <h3>Open pipeline (ETL)</h3>
      <p>Extract: immutable raw snapshots of each source (Wikipedia, martj42, Sofascore) → <code>data/raw/</code>.
      Transform: player registry (homonyms resolved by date of birth), call-ups, match-by-match appearances → <code>data/staging/</code>.
      Load: analysis marts → <code>data/marts/</code> + the JSONs behind this dashboard. Quality checks run on every build (uniqueness, referential integrity, bounds, player-vs-team goals consistency).</p>
      <h3>Player scope</h3>
      <p>Every player called up since AFCON 2021 (Jan 2022): AFCON 2021/2023/2025 squad lists, the current squad and recent call-ups (Wikipedia), plus anyone who appeared on a matchday sheet (Sofascore). Individual stats (minutes, passes, dribbles, saves…) come from Sofascore matchday data — unaffiliated project, non-commercial use with attribution.</p>
      <h3>Elo</h3>
      <p>Recomputed over ~49,000 internationals since 1872 (martj42 data, CC0): K = 60 (WC), 50 (AFCON), 40 (qualifiers), 30 (other), 20 (friendlies); goal-difference multiplier; +100 home advantage. The projection is a linear trend on year-end Elo since 2010 with an ≈80% band from year-on-year volatility — an illustrative model, not a prediction.</p>
      <h3>Age projections</h3>
      <p>AFCON 2027 assumed mid-2027 (dates not final), WC 2030 in June 2030. Indicative peak windows: goalkeepers 26–33, defenders 25–30, midfielders and forwards 24–29.</p>
      <h3>Periods of play & game states</h3>
      <p>A per-match timeline is rebuilt from incident data (stoppage time included; extra time detected, including via the presence of a shootout). Goals fall into six 15-minute periods — stoppage-time goals stay in 31–45+ / 76–90+ with their share shown separately; extra time is counted apart. A period is flagged as unusual only when the χ² across the six regulation periods is significant (p &lt; 0.05). Minutes leading / level / trailing come from the same timeline.</p>
      <h3>Player importance</h3>
      <p>No composite index. Each component is shown separately with its own gate: minutes share (window = since the player's first call-up); on/off goal difference per 90 (≥ 900 min on pitch AND ≥ 450 min off pitch while in the squad); points per game started vs not started (≥ 10 starts AND ≥ 8 squad matches without starting); goals+assists per 90 (≥ 450 min); minutes-weighted rating (≥ 5 rated matches AND ≥ 300 min). Roles: Pillar ≥ 60% of minutes AND ≥ 66% of squad matches started; Rotation ≥ 25%; otherwise Fringe. Percentiles are computed only among players qualified for each component. Descriptive reading only, never causal.</p>
      <h3>Bench impact</h3>
      <p>Goals + assists off the bench are raw counts; per-90 only with ≥ 5 sub appearances and ≥ 150 minutes; goal difference after entry (≥ 8 sub apps) should be read against the team's own post-60' baseline, shown alongside.</p>
      <h3>Known limitations</h3>
      <p>Career caps/goals frozen at the latest Wikipedia update; no complete squad lists for qualifier windows yet (contributions welcome); ~24% of appearances (minor friendlies) lack detailed stats.</p>`,
    footer: "Étalons Analytics — open-source project (MIT). Data: Wikipedia (CC BY-SA), martj42/international_results (CC0), Sofascore (unaffiliated). Generated {date}.",
  },
};

let LANG = localStorage.getItem("ea_lang") || "fr";

function t(key, vars) {
  let s = (I18N[LANG] && I18N[LANG][key]) || I18N.fr[key] || key;
  if (vars) {
    for (const [k, v] of Object.entries(vars)) {
      s = s.replaceAll(`{${k}}`, v);
    }
  }
  return s;
}

function setLang(lang) {
  LANG = lang;
  localStorage.setItem("ea_lang", lang);
  document.documentElement.lang = lang;
  document.querySelectorAll(".lang button").forEach(b => {
    b.classList.toggle("on", b.dataset.lang === lang);
  });
  if (window.renderAll) {
    window.renderAll();
  }
}

function fmt(n, dec = 0) {
  if (n === null || n === undefined || n === "") {
    return "–";
  }
  return Number(n).toLocaleString(LANG === "fr" ? "fr-FR" : "en-GB",
    { minimumFractionDigits: dec, maximumFractionDigits: dec });
}
