"""Where every page lives, per language.

French is the primary tree at the root; English mirrors it under /en/ with
English filenames. Every link is computed as a relative path from the page doing
the linking, so the site works from any base path — a user's localhost root or
the /etalons-analytics/ subpath on GitHub Pages.
"""

import posixpath

from .seo import canonical_url

LANGS = ("fr", "en")

ROUTES = {
    "home":        {"fr": "index.html",         "en": "en/index.html"},
    "squad":       {"fr": "effectif.html",      "en": "en/squad.html"},
    "players":     {"fr": "joueurs.html",       "en": "en/players.html"},
    "matches":     {"fr": "matchs.html",        "en": "en/matches.html"},
    "analysis":    {"fr": "analyse.html",       "en": "en/analysis.html"},
    "mgmt":        {"fr": "gestion.html",       "en": "en/management.html"},
    "history":     {"fr": "histoire.html",      "en": "en/history.html"},
    "projections": {"fr": "projections.html",   "en": "en/projections.html"},
    "method":      {"fr": "methodologie.html",  "en": "en/methodology.html"},
    "player":      {"fr": "joueurs/{slug}.html", "en": "en/players/{slug}.html"},
    "match":       {"fr": "matchs/{slug}.html",  "en": "en/matches/{slug}.html"},
}

# the header, in order: (route, French label used as the translation key)
NAV = [
    ("home", "Accueil"),
    ("squad", "Effectif"),
    ("players", "Joueurs"),
    ("matches", "Matchs"),
    ("analysis", "Analyse"),
    ("mgmt", "Gestion"),
    ("history", "Histoire"),
    ("projections", "Projections"),
    ("method", "Méthodologie"),
]


def path_for(lang, route, slug=None):
    template = ROUTES[route][lang]
    return template.format(slug=slug) if slug else template


def rel(from_path, to_path):
    """Relative link from one output file to another."""
    base = posixpath.dirname(from_path)
    return posixpath.relpath(to_path, base or ".")


def depth_of(path):
    return path.count("/")


class Ctx:
    """Everything a page builder needs to know about where and in what language
    it is being rendered."""

    def __init__(self, lang, route, slug=None):
        from .strings import RESULT_LETTER, translator
        self.lang = lang
        self.route = route
        self.slug = slug
        self.self_path = path_for(lang, route, slug)
        self.canonical = canonical_url(self.self_path)
        self.t = translator(lang)
        self.result_letter = RESULT_LETTER[lang]

    def url(self, route, slug=None):
        return rel(self.self_path, path_for(self.lang, route, slug))

    def abs_url(self, route, slug=None):
        """Absolute URL — for structured data, which cannot use relative paths."""
        return canonical_url(path_for(self.lang, route, slug))

    def asset(self, path):
        return rel(self.self_path, path)

    def alternates(self):
        """[(lang, relative url)] for hreflang and the language switcher."""
        return [(lang, rel(self.self_path, path_for(lang, self.route, self.slug)))
                for lang in LANGS]
