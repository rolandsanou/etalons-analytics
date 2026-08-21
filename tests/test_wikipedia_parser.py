from etl.parsers.wikipedia import parse_players

WITH_NUMBER = """
<h3 id="Current_squad">Current squad</h3>
<table><tr><th>No.</th><th>Pos.</th><th>Player</th><th>DOB</th><th>Caps</th><th>Goals</th><th>Club</th></tr>
<tr class="nat-fs-player"><td>1</td><td>1GK</td><th><a>Hervé Koffi</a></th>
<td>(1996-10-16)16 October 1996</td><td>70</td><td>0</td>
<td><img src="/x/Flag_of_France.svg"/><a>Angers</a></td></tr></table>
"""

WITHOUT_NUMBER = """
<h3 id="Recent_call-ups">Recent call-ups</h3>
<table><tr><th>Pos.</th><th>Player</th><th>DOB</th><th>Caps</th><th>Goals</th><th>Club</th><th>Latest call-up</th></tr>
<tr class="nat-fs-player"><td>2DF</td><th><a>Issa Kaboré</a></th>
<td>(2001-05-12)12 May 2001</td><td>50</td><td>2</td>
<td><img src="/x/Flag_of_England.svg"/><a>Manchester City</a></td>
<td>v. Belarus, 9 June 2026</td></tr></table>
"""


def test_squad_table_with_shirt_numbers():
    rows = parse_players(WITH_NUMBER, "Current_squad")
    assert len(rows) == 1
    p = rows[0]
    assert p["name"] == "Hervé Koffi"
    assert p["pos"] == "GK"
    assert p["dob"] == "1996-10-16"
    assert p["caps"] == 70
    assert p["goals"] == 0
    assert p["club"] == "Angers"
    assert p["club_country"] == "France"


def test_callup_table_without_shirt_numbers():
    rows = parse_players(WITHOUT_NUMBER, "Recent_call-ups")
    assert len(rows) == 1
    p = rows[0]
    assert p["name"] == "Issa Kaboré"
    assert p["pos"] == "DF"
    assert p["dob"] == "2001-05-12"
    assert p["caps"] == 50
    assert p["goals"] == 2
    assert p["club"] == "Manchester City"
    assert p["club_country"] == "England"
    assert "Belarus" in p["note"]
