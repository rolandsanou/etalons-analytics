from etl.load.leadership import build_captains, build_goalkeepers


def _gk(event, minutes, entry, exit_, ga_on, saves, started="1", rating="7.0"):
    return {"event_id": event, "date": "2024-01-01", "player_id": "gk1", "name": "GK One",
            "pos": "GK", "played": "1", "started": started, "captain": "0",
            "minutes": str(minutes), "rating": rating,
            "entry_min": str(entry), "exit_min": str(exit_),
            "ga_on": str(ga_on), "saves": str(saves),
            "high_claims": "1", "punches": "0", "pens_faced": "0",
            "shootout_saves": "0", "gf": "1", "ga": str(ga_on)}


def test_goalkeeper_aggregates_and_clean_sheets():
    eff = {"e1": 95.0, "e2": 96.0, "e3": 94.0, "e4": 95.0}
    apps = [
        _gk("e1", 90, 0, 95, 0, 3),    # clean sheet
        _gk("e2", 90, 0, 96, 2, 4),    # conceded twice
        _gk("e3", 90, 0, 94, 0, 1),    # clean sheet
        _gk("e4", 90, 0, 60, 0, 1),    # subbed off -> not a clean sheet
    ]
    rows = build_goalkeepers(apps, eff)
    assert len(rows) == 1
    r = rows[0]
    assert r["apps"] == 4
    assert r["clean_sheets"] == 2
    assert r["ga_on"] == 2
    assert r["saves"] == 9
    assert r["gated"] == 1
    assert r["save_pct"] == round(100 * 9 / 11, 1)


def test_goalkeeper_below_gate_hides_rates():
    eff = {"e1": 95.0}
    rows = build_goalkeepers([_gk("e1", 90, 0, 95, 1, 2)], eff)
    assert rows[0]["gated"] == 0
    assert rows[0]["save_pct"] == ""
    assert rows[0]["ga90"] == ""


def _cap(event, gf, ga):
    return {"event_id": event, "date": "2024-01-0" + event[-1], "player_id": "c1",
            "name": "Cap", "pos": "MF", "played": "1", "started": "1", "captain": "1",
            "minutes": "90", "entry_min": "0", "exit_min": "95",
            "gf": str(gf), "ga": str(ga)}


def test_captains_record():
    rows = build_captains([_cap("e1", 2, 0), _cap("e2", 1, 1), _cap("e3", 0, 1)])
    r = rows[0]
    assert (r["matches"], r["w"], r["d"], r["l"]) == (3, 1, 1, 1)
    assert r["ppg"] == round(4 / 3, 2)
