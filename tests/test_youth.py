from etl.transform.youth import link_youth


def _senior(pid, name, dob):
    return {"player_id": pid, "name": name, "dob": dob}


INDEX = {
    "issa kabore": [_senior("issa-kabore", "Issa Kaboré", "2001-05-12")],
    "mohamed ouedraogo": [
        _senior("mohamed-ouedraogo-1998", "Mohamed Ouédraogo", "1998-01-01"),
        _senior("mohamed-ouedraogo-2004", "Mohamed Ouédraogo", "2004-05-05"),
    ],
    "no dob": [_senior("no-dob", "No Dob", "")],
}


def test_link_exact_name_and_dob():
    assert link_youth("Issa Kabore", "2001-05-12", INDEX) == ("issa-kabore", "exact")


def test_link_dob_mismatch_refused():
    assert link_youth("Issa Kaboré", "2003-01-01", INDEX) == ("", "")


def test_link_homonym_resolved_by_dob():
    pid, q = link_youth("Mohamed Ouédraogo", "2004-05-05", INDEX)
    assert pid == "mohamed-ouedraogo-2004" and q == "exact"


def test_link_name_only_when_senior_missing_dob():
    assert link_youth("No Dob", "2007-01-01", INDEX) == ("no-dob", "name_only")


def test_link_unknown():
    assert link_youth("Somebody Else", "2005-01-01", INDEX) == ("", "")
