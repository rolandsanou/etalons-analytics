from etl.transform.players import _split_homonyms
from etl.util import norm_name, slugify


def test_norm_name_accents_and_case():
    assert norm_name("Hervé Koffi") == "herve koffi"
    assert norm_name("Ouédraogo,  Farid") == "ouedraogo farid"
    assert norm_name("Saïdou N'Simporé") == "saidou n simpore"


def test_slugify():
    assert slugify("Bertrand Traoré") == "bertrand-traore"


def _c(name, dob, window):
    return {"name": name, "dob": dob, "window_id": window, "window_date": "2024-01-01"}


def test_split_homonyms_same_dob_merges():
    rows = [_c("Mohamed Ouédraogo", "1998-01-01", "a"),
            _c("Mohamed Ouédraogo", "1998-01-01", "b")]
    groups = _split_homonyms(rows)
    assert len(groups) == 1
    assert len(groups[0]) == 2


def test_split_homonyms_distinct_dob_splits():
    rows = [_c("Mohamed Ouédraogo", "1998-01-01", "a"),
            _c("Mohamed Ouédraogo", "2003-05-05", "b")]
    groups = _split_homonyms(rows)
    assert len(groups) == 2


def test_split_homonyms_missing_dob_joins_largest():
    rows = [_c("X", "1998-01-01", "a"), _c("X", "1998-01-01", "b"),
            _c("X", "2003-05-05", "c"), _c("X", "", "d")]
    groups = _split_homonyms(rows)
    sizes = sorted(len(g) for g in groups)
    assert sizes == [1, 3]
