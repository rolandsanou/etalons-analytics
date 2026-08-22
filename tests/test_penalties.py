from etl.transform.penalties import parse_penalty_incidents

RAW = {"incidents": [
    {"incidentType": "goal", "incidentClass": "penalty", "time": 30, "isHome": True,
     "player": {"id": 1, "name": "A"}},
    {"incidentType": "goal", "incidentClass": "regular", "time": 40, "isHome": True,
     "player": {"id": 2, "name": "B"}},
    {"incidentType": "inGamePenalty", "incidentClass": "missed", "time": 55,
     "isHome": False, "player": {"id": 3, "name": "C"}},
    {"incidentType": "penaltyShootout", "incidentClass": "scored", "time": 121,
     "isHome": True, "player": {"id": 4, "name": "D"}},
    {"incidentType": "penaltyShootout", "incidentClass": "missed", "time": 121,
     "isHome": False, "player": {"id": 5, "name": "E"}},
]}


def test_parse_penalties_bf_home():
    rows = parse_penalty_incidents(RAW, bf_home=True)
    kinds = [(r["kind"], r["outcome"], r["is_bf"]) for r in rows]
    assert kinds == [
        ("ingame", "scored", True),
        ("ingame", "missed", False),
        ("shootout", "scored", True),
        ("shootout", "missed", False),
    ]
    assert rows[0]["player"]["name"] == "A"


def test_parse_penalties_bf_away_flips():
    rows = parse_penalty_incidents(RAW, bf_home=False)
    assert [(r["kind"], r["is_bf"]) for r in rows] == [
        ("ingame", False), ("ingame", True), ("shootout", False), ("shootout", True)]
