"""Generates every page of the site from the committed data tables.

    python tools/build_site.py

Writes hub pages into site/, plus one page per match (site/matchs/) and per
player (site/joueurs/). Charts stay client-side; detail pages are static HTML so
they work without JavaScript and can be indexed.
"""

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.site_builder import hubs, layout  # noqa: E402
from tools.site_builder.data import Data  # noqa: E402
from tools.site_builder.detail import match_page, match_slug, player_page  # noqa: E402

SITE = ROOT / "site"


def write(path, html):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")


def asset_version():
    """Short hash of every stylesheet and script, so a deploy busts the cache."""
    digest = hashlib.md5()
    assets = sorted((SITE / "assets").rglob("*.css")) + \
        sorted((SITE / "assets").rglob("*.js"))
    for path in assets:
        digest.update(path.read_bytes())
    return digest.hexdigest()[:8]


def main():
    d = Data()
    layout.ASSET_VERSION = asset_version()
    pages = 0

    for name, builder in [
        ("index.html", hubs.home_page),
        ("effectif.html", hubs.squad_page),
        ("joueurs.html", hubs.players_index),
        ("matchs.html", hubs.matches_index),
        ("analyse.html", hubs.analysis_page),
        ("gestion.html", hubs.management_page),
        ("histoire.html", hubs.history_page),
        ("projections.html", hubs.projections_page),
        ("methodologie.html", hubs.methodology_page),
    ]:
        write(SITE / name, builder(d))
        pages += 1

    # every player in the registry gets a page, so no index link can 404
    with_pages = {p["player_id"] for p in d.profiles}
    for profile in d.profiles:
        write(SITE / "joueurs" / f"{profile['player_id']}.html",
              player_page(d, profile, with_pages))
        pages += 1

    events = sorted(d.events, key=lambda e: e["date"])
    for i, event in enumerate(events):
        prev_e = events[i - 1] if i else None
        next_e = events[i + 1] if i + 1 < len(events) else None
        write(SITE / "matchs" / f"{match_slug(event)}.html",
              match_page(d, event, prev_e, next_e, with_pages))
        pages += 1

    sitemap(d, events, with_pages)
    print(f"built {pages} pages "
          f"({len(with_pages)} players, {len(events)} matches)")


def sitemap(d, events, with_pages):
    urls = ["index.html", "effectif.html", "joueurs.html", "matchs.html",
            "analyse.html", "gestion.html", "histoire.html", "projections.html",
            "methodologie.html"]
    urls += [f"joueurs/{pid}.html" for pid in sorted(with_pages)]
    urls += [f"matchs/{match_slug(e)}.html" for e in events]
    lastmod = d.meta["generated_at"][:10]
    body = "\n".join(
        f"  <url><loc>https://rolandsanou.github.io/etalons-analytics/{u}</loc>"
        f"<lastmod>{lastmod}</lastmod></url>" for u in urls)
    (SITE / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{body}\n</urlset>\n", encoding="utf-8")
    (SITE / "robots.txt").write_text(
        "User-agent: *\nAllow: /\nSitemap: "
        "https://rolandsanou.github.io/etalons-analytics/sitemap.xml\n", encoding="utf-8")


if __name__ == "__main__":
    main()
