from etl.transform.incidents import parse_event_incidents

RAW = {"incidents": [
    {"incidentType": "period", "text": "FT", "time": 90, "addedTime": 999,
     "homeScore": 2, "awayScore": 1},
    {"incidentType": "injuryTime", "time": 90, "length": 4},
    {"incidentType": "goal", "time": 88, "incidentClass": "regular", "isHome": True,
     "homeScore": 2, "awayScore": 1, "player": {"id": 1, "name": "A"},
     "assist1": {"id": 2, "name": "B"},
     "footballPassingNetworkAction": [{"huge": "blob"}]},
    {"incidentType": "goal", "time": 60, "incidentClass": "ownGoal", "isHome": True,
     "homeScore": 1, "awayScore": 1, "player": {"id": 9, "name": "OppDef"}},
    {"incidentType": "goal", "time": 30, "addedTime": 2, "incidentClass": "penalty",
     "isHome": False, "homeScore": 0, "awayScore": 1,
     "player": {"id": 5, "name": "OppFw"}},
    {"incidentType": "substitution", "time": 46, "isHome": True, "injury": True,
     "playerIn": {"id": 3, "name": "C"}, "playerOut": {"id": 4, "name": "D"}},
    {"incidentType": "card", "time": 12, "isHome": False, "incidentClass": "yellow",
     "player": {"id": 6, "name": "E"}, "reason": "Foul", "rescinded": False},
    {"incidentType": "injuryTime", "time": 45, "length": 3},
]}


def test_parse_bf_home():
    goals, subs, cards, injuries = parse_event_incidents(RAW, bf_home=True)
    assert len(goals) == 3 and len(subs) == 1 and len(cards) == 1 and len(injuries) == 2
    late, own, pen = goals
    assert late["is_bf"] is True
    assert late["bf_score_after"] == 2 and late["opp_score_after"] == 1
    assert own["class"] == "ownGoal" and own["is_bf"] is True
    assert pen["is_bf"] is False
    assert pen["added_time"] == 2
    assert pen["bf_score_after"] == 0 and pen["opp_score_after"] == 1
    assert subs[0]["is_bf"] is True and subs[0]["injury"] is True
    assert cards[0]["is_bf"] is False
    assert sorted(i["period_end"] for i in injuries) == [45, 90]


def test_parse_bf_away_flips_sides():
    goals, subs, cards, _ = parse_event_incidents(RAW, bf_home=False)
    late, own, pen = goals
    assert late["is_bf"] is False
    assert late["bf_score_after"] == 1 and late["opp_score_after"] == 2
    assert own["is_bf"] is False
    assert pen["is_bf"] is True
    assert subs[0]["is_bf"] is False
    assert cards[0]["is_bf"] is True
