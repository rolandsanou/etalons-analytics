import json

from tools.site_builder import seo


def test_canonical_url_drops_index_html():
    base = seo.SITE_URL
    assert seo.canonical_url("index.html") == f"{base}/"
    assert seo.canonical_url("en/index.html") == f"{base}/en/"
    assert seo.canonical_url("joueurs.html") == f"{base}/joueurs.html"
    assert seo.canonical_url("en/players/x.html") == f"{base}/en/players/x.html"


def test_canonical_url_keeps_a_filename_merely_ending_in_index():
    # "reindex.html" is not "index.html" — a naive suffix strip would maul it
    assert seo.canonical_url("reindex.html").endswith("/reindex.html")


def test_absolute_is_idempotent():
    already = f"{seo.SITE_URL}/assets/x.png"
    assert seo.absolute(already) == already
    assert seo.absolute("assets/x.png") == already
    assert seo.absolute("/assets/x.png") == already


def test_long_date_per_language():
    assert seo.long_date("2026-01-06", "fr") == "6 janvier 2026"
    assert seo.long_date("2026-01-06", "en") == "6 January 2026"
    assert seo.long_date("2025-08-06", "en") == "6 August 2025"
    # unparseable input is passed through rather than crashing the build
    assert seo.long_date("", "fr") == ""
    assert seo.long_date("soon", "en") == "soon"


def test_jsonld_skips_empty_blocks_and_emits_valid_json():
    out = seo.jsonld({"@type": "Thing"}, None, {})
    assert out.count("<script") == 1
    payload = out.split(">", 1)[1].rsplit("<", 1)[0]
    assert json.loads(payload) == {"@type": "Thing"}
    assert seo.jsonld() == ""


def test_titles_cover_every_hub_in_both_languages():
    from tools.site_builder.routes import LANGS, NAV
    for route, _ in NAV:
        assert route in seo.TITLES, route
        for lang in LANGS:
            title = seo.TITLES[route][lang]
            # a title Google will truncate defeats the point of writing one
            assert 20 < len(title) <= 65, (route, lang, len(title))


def test_person_omits_fields_the_data_does_not_have():
    bare = seo.person("en", {"name": "A B"}, "u")
    assert "image" not in bare and "birthDate" not in bare
    assert "height" not in bare and "affiliation" not in bare
    assert bare["nationality"]["name"] == "Burkina Faso"


def test_person_height_survives_a_float_string_and_ignores_junk():
    assert seo.person("en", {"name": "A", "height": "177.0"}, "u")["height"] == {
        "@type": "QuantitativeValue", "value": 177, "unitCode": "CMT"}
    assert "height" not in seo.person("en", {"name": "A", "height": "n/a"}, "u")


def test_sports_event_makes_no_home_away_claim():
    """The source venue column is only H/A and is unreliable at tournaments, so
    the markup must not assert a home side. Guards a deliberate omission."""
    event = {"date": "2026-01-06", "opponent": "Côte d'Ivoire", "venue": "A",
             "tournament": "Africa Cup of Nations"}
    block = seo.sports_event("en", event, "u", "BF 0–3 CIV", "Burkina Faso")
    assert "homeTeam" not in block and "awayTeam" not in block
    assert [c["name"] for c in block["competitor"]] == \
        ["Burkina Faso", "Côte d'Ivoire"]
    assert block["startDate"] == "2026-01-06"


def test_dataset_declares_a_licence_and_a_download():
    block = seo.dataset("fr", "u")
    assert block["license"].startswith("http")
    assert block["distribution"][0]["encodingFormat"] == "text/csv"
