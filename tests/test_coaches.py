from etl.parsers.wikipedia import parse_coaching_history
from etl.transform.matches import assign_coach

HTML = """
<h3 id="Coaching_history">Coaching history</h3>
<ul>
<li>Otto Pfister (1976–1978)</li>
<li>Calixte Zagre (1996)</li>
<li>Jacques Yaméogo &amp; Pihouri Weboanga (2002)</li>
<li>Amir Abdou (2026–)</li>
</ul>
"""


def test_parse_coaching_history():
    rows = parse_coaching_history(HTML)
    assert rows[0] == {"coach": "Otto Pfister", "start_year": 1976, "end_year": 1978}
    assert rows[1] == {"coach": "Calixte Zagre", "start_year": 1996, "end_year": 1996}
    assert rows[2]["coach"] == "Jacques Yaméogo & Pihouri Weboanga"
    assert rows[3] == {"coach": "Amir Abdou", "start_year": 2026, "end_year": None}


TENURES = [
    {"coach": "A", "start": "1992-01-01", "end": "1996-12-31", "idx": 0},
    {"coach": "B", "start": "1996-01-01", "end": "1996-12-31", "idx": 1},
    {"coach": "C", "start": "1996-01-01", "end": "1997-12-31", "idx": 2},
    {"coach": "D", "start": "2026-01-01", "end": "9999-12-31", "idx": 3},
]


def test_assign_coach_precedence_and_open_end():
    assert assign_coach("1995-06-01", TENURES) == ("A", "1992-01-01")
    # boundary year: latest-start then latest-listed wins
    assert assign_coach("1996-06-01", TENURES) == ("C", "1996-01-01")
    assert assign_coach("1997-06-01", TENURES) == ("C", "1996-01-01")
    assert assign_coach("2026-08-01", TENURES) == ("D", "2026-01-01")
    assert assign_coach("1980-01-01", TENURES) == ("", "")
