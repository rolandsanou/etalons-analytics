import re

RATIO_RE = re.compile(r"^(\d+)\s*/\s*(\d+)")
PCT_RE = re.compile(r"^(\d+(?:\.\d+)?)\s*%$")
NUM_RE = re.compile(r"^(\d+(?:\.\d+)?)$")

# sofascore key -> (column, kind); "ratio" keys also emit <column>_att
STAT_KEYS = {
    "ballPossession": ("possession_pct", "pct"),
    "bigChanceCreated": ("big_chances", "count"),
    "bigChanceScored": ("big_chances_scored", "count"),
    "bigChanceMissed": ("big_chances_missed", "count"),
    "totalShotsOnGoal": ("shots", "count"),
    "shotsOnGoal": ("shots_on_target", "count"),
    "shotsOffGoal": ("shots_off_target", "count"),
    "blockedScoringAttempt": ("shots_blocked", "count"),
    "totalShotsInsideBox": ("shots_inside_box", "count"),
    "totalShotsOutsideBox": ("shots_outside_box", "count"),
    "touchesInOppBox": ("touches_opp_box", "count"),
    "fouledFinalThird": ("fouled_final_third", "count"),
    "passes": ("passes", "count"),
    "accuratePasses": ("passes_accurate", "count"),
    "finalThirdEntries": ("final_third_entries", "count"),
    "finalThirdPhaseStatistic": ("final_third_phase", "ratio"),
    "accurateLongBalls": ("long_balls", "ratio"),
    "accurateCross": ("crosses", "ratio"),
    "groundDuelsPercentage": ("ground_duels", "ratio"),
    "aerialDuelsPercentage": ("aerial_duels", "ratio"),
    "dribblesPercentage": ("dribbles", "ratio"),
    "duelWonPercent": ("duels_won_pct", "pct"),
    "totalTackle": ("tackles", "count"),
    "wonTacklePercent": ("tackles_won_pct", "pct"),
    "interceptionWon": ("interceptions", "count"),
    "ballRecovery": ("recoveries", "count"),
    "totalClearance": ("clearances", "count"),
    "errorsLeadToShot": ("errors_lead_to_shot", "count"),
    "goalkeeperSaves": ("saves", "count"),
    "cornerKicks": ("corners", "count"),
    "fouls": ("fouls", "count"),
    "yellowCards": ("yellow_cards", "count"),
    "throwIns": ("throw_ins", "count"),
    "dispossessed": ("dispossessed", "count"),
    "goalKicks": ("goal_kicks", "count"),
}

COUNT_COLS = sorted({c for c, k in STAT_KEYS.values() if k == "count"})
PCT_COLS = sorted({c for c, k in STAT_KEYS.values() if k == "pct"})
RATIO_COLS = sorted({c for c, k in STAT_KEYS.values() if k == "ratio"})
VALUE_COLS = COUNT_COLS + PCT_COLS + RATIO_COLS + [c + "_att" for c in RATIO_COLS]


def parse_stat_value(raw, kind):
    """Return (value, attempted). Ratio strings like "22/39 (56%)" -> (22, 39)."""
    if raw is None:
        return None, None
    s = str(raw).strip()
    if not s or s == "-":
        return None, None
    m = RATIO_RE.match(s)
    if m:
        made, att = int(m.group(1)), int(m.group(2))
        if kind == "ratio":
            return made, att
        return made, None
    m = PCT_RE.match(s)
    if m:
        return float(m.group(1)), None
    m = NUM_RE.match(s)
    if m:
        v = float(m.group(1))
        return (int(v) if kind == "count" and v.is_integer() else v), None
    return None, None


def parse_event_statistics(data, bf_home):
    """-> {period: {"bf": {col: val}, "opp": {col: val}}} for ALL/1ST/2ND."""
    out = {}
    for block in data.get("statistics", []):
        period = block.get("period")
        if not period:
            continue
        sides = {"bf": {}, "opp": {}}
        for group in block.get("groups", []):
            for item in group.get("statisticsItems", []):
                mapping = STAT_KEYS.get(item.get("key"))
                if not mapping:
                    continue
                col, kind = mapping
                home_v, home_att = parse_stat_value(item.get("home"), kind)
                away_v, away_att = parse_stat_value(item.get("away"), kind)
                bf_v, bf_att = (home_v, home_att) if bf_home else (away_v, away_att)
                op_v, op_att = (away_v, away_att) if bf_home else (home_v, home_att)
                if bf_v is not None:
                    sides["bf"][col] = bf_v
                if op_v is not None:
                    sides["opp"][col] = op_v
                if kind == "ratio":
                    if bf_att is not None:
                        sides["bf"][col + "_att"] = bf_att
                    if op_att is not None:
                        sides["opp"][col + "_att"] = op_att
        out[period] = sides
    return out
