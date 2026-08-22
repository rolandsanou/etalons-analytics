"""Search-engine and social metadata: canonicals, dates and JSON-LD.

Structured data is emitted as schema.org JSON-LD so a match page can be
understood as a SportsEvent, a player page as a Person, and the methodology page
as an openly-licensed Dataset. Everything asserted here must be true of the page
it sits on — structured data that overstates the content is worse than none.
"""

import json

SITE_URL = "https://rolandsanou.github.io/etalons-analytics"

# social card size, matching tools/make_og_image.py
CARD_W, CARD_H = 1200, 630
TEAM_NAME = "Burkina Faso national football team"
TEAM_NAME_FR = "Équipe du Burkina Faso de football"
REPO_URL = "https://github.com/rolandsanou/etalons-analytics"

MONTHS = {
    "fr": ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
           "août", "septembre", "octobre", "novembre", "décembre"],
    "en": ["January", "February", "March", "April", "May", "June", "July",
           "August", "September", "October", "November", "December"],
}


# <title> per hub route. The nav label ("Accueil") is a wasted first keyword in a
# search result, so each hub states what it actually holds. Kept near 60
# characters — beyond that Google truncates.
TITLES = {
    "home": {
        "fr": "Étalons Analytics — statistiques du Burkina Faso",
        "en": "Étalons Analytics — Burkina Faso national team stats"},
    "squad": {
        "fr": "Effectif actuel des Étalons — Burkina Faso",
        "en": "Current Burkina Faso squad — Étalons Analytics"},
    "players": {
        "fr": "Tous les joueurs appelés depuis 2022 — Burkina Faso",
        "en": "Every player called up since 2022 — Burkina Faso"},
    "matches": {
        "fr": "Tous les matchs depuis 2022 — résultats et compositions",
        "en": "Every match since 2022 — results and lineups"},
    "analysis": {
        "fr": "Style de jeu et résilience des Étalons — analyse",
        "en": "Burkina Faso style of play and resilience — analysis"},
    "mgmt": {
        "fr": "Rotation, importance des joueurs et entrées en jeu",
        "en": "Squad rotation, player importance and substitutions"},
    "history": {
        "fr": "Histoire des Étalons : records, sélectionneurs, CAN",
        "en": "Burkina Faso football history: records, coaches, AFCON"},
    "projections": {
        "fr": "Projections Elo et CAN 2027 — Burkina Faso",
        "en": "Elo projections and AFCON 2027 — Burkina Faso"},
    "method": {
        "fr": "Méthodologie, sources et données ouvertes",
        "en": "Methodology, sources and open data"},
}


def absolute(path):
    if str(path).startswith("http"):
        return path
    return f"{SITE_URL}/{path.lstrip('/')}"


def canonical_url(path):
    """Absolute URL for a generated file, in one canonical form.

    A trailing `index.html` is dropped because the host serves the same page at
    the directory URL too; declaring one form keeps the pair from competing as
    duplicates.
    """
    path = path.lstrip("/")
    if path == "index.html" or path.endswith("/index.html"):
        path = path[: -len("index.html")]
    return f"{SITE_URL}/{path}"


def long_date(iso, lang):
    """2026-01-06 -> "6 janvier 2026" / "6 January 2026"."""
    try:
        year, month, day = (int(part) for part in iso.split("-")[:3])
    except (ValueError, AttributeError):
        return iso
    return f"{day} {MONTHS[lang][month - 1]} {year}"


def jsonld(*blocks):
    """Render one <script> per structured-data block, skipping empties."""
    out = []
    for block in blocks:
        if not block:
            continue
        payload = json.dumps(block, ensure_ascii=False, separators=(",", ":"))
        out.append('<script type="application/ld+json">' + payload + "</script>")
    return "\n".join(out)


def team_ref(lang):
    return {
        "@type": "SportsTeam",
        "name": TEAM_NAME_FR if lang == "fr" else TEAM_NAME,
        "sport": "Football",
        "url": canonical_url("index.html" if lang == "fr" else "en/index.html"),
    }


def website(lang, description):
    """Site-level identity, emitted on the home page only."""
    return {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": "Étalons Analytics",
        "url": canonical_url("index.html" if lang == "fr" else "en/index.html"),
        "inLanguage": lang,
        "description": description,
        "about": team_ref(lang),
        "isAccessibleForFree": True,
        "license": "https://opensource.org/licenses/MIT",
        "codeRepository": REPO_URL,
    }


def breadcrumbs(items):
    """items: [(name, absolute url or None for the current page)]"""
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": name,
             **({"item": url} if url else {})}
            for i, (name, url) in enumerate(items)
        ],
    }


def person(lang, profile, url, image=None):
    """A player. Only fields the data actually supports are asserted."""
    block = {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": profile["name"],
        "url": url,
        "nationality": {"@type": "Country", "name": "Burkina Faso"},
        "memberOf": team_ref(lang),
    }
    if image:
        block["image"] = image
    if profile.get("dob"):
        block["birthDate"] = profile["dob"]
    if profile.get("height"):
        try:
            block["height"] = {"@type": "QuantitativeValue",
                               "value": int(float(profile["height"])),
                               "unitCode": "CMT"}
        except (TypeError, ValueError):
            pass
    club = profile.get("club_v") or profile.get("club")
    if club:
        block["affiliation"] = {"@type": "SportsTeam", "name": club}
    return block


def sports_event(lang, event, url, name, home_name):
    """A played match.

    Deliberately no homeTeam/awayTeam: the source `venue` column only holds H/A,
    and at a tournament it marks the nominal designation rather than a real home
    ground — AFCON 2022 group games in Cameroon are labelled both ways. So the
    two sides are stated as `competitor`, which claims no such thing. There is
    likewise no clean result field in the vocabulary, so the score stays in the
    name rather than being asserted through an invented property.
    """
    return {
        "@context": "https://schema.org",
        "@type": "SportsEvent",
        "name": name,
        "startDate": event["date"],
        "eventStatus": "https://schema.org/EventScheduled",
        "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
        "sport": "Football",
        "url": url,
        "competitor": [
            {"@type": "SportsTeam", "name": home_name},
            {"@type": "SportsTeam", "name": event["opponent"]},
        ],
        "superEvent": {"@type": "SportsOrganization", "name": event["tournament"]},
    }


def dataset(lang, url):
    """The open data behind the site — eligible for dataset search engines."""
    return {
        "@context": "https://schema.org",
        "@type": "Dataset",
        "name": ("Étalons Analytics — données ouvertes sur l'équipe du Burkina Faso"
                 if lang == "fr" else
                 "Étalons Analytics — open data on the Burkina Faso national team"),
        "description": (
            "Tables intermédiaires et agrégats : convocations, apparitions match "
            "par match, statistiques d'équipe, classement Elo, sélectionneurs."
            if lang == "fr" else
            "Staging tables and analysis marts: call-ups, match-by-match "
            "appearances, team statistics, Elo ratings and head-coach records."),
        "url": url,
        "license": "https://opensource.org/licenses/MIT",
        "creator": {"@type": "Person", "name": "Roland Sanou"},
        "isAccessibleForFree": True,
        "keywords": ["Burkina Faso", "football", "Étalons", "AFCON", "Elo",
                     "football analytics", "open data"],
        "distribution": [{
            "@type": "DataDownload",
            "encodingFormat": "text/csv",
            "contentUrl": f"{REPO_URL}/tree/main/data/marts",
        }],
    }
