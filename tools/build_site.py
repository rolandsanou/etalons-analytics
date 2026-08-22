"""Generates every page of the site, in every language, from the committed data.

    python tools/build_site.py        (or: python -m etl pages)

French is the primary tree at the root; English mirrors it under /en/. Hub pages
keep their charts client-side; match and player pages are static HTML so they
work without JavaScript and can be indexed. Untranslated copy is reported at the
end of the build instead of silently shipping in French.
"""

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.site_builder import hubs, layout  # noqa: E402
from tools.site_builder.data import Data  # noqa: E402
from tools.site_builder.detail import (match_page, match_slug,  # noqa: E402
                                       player_page, set_locale)
from tools.site_builder.routes import LANGS, Ctx, path_for  # noqa: E402
from tools.site_builder.strings import MISSES  # noqa: E402

SITE = ROOT / "site"

HUBS = [
    ("home", hubs.home_page),
    ("squad", hubs.squad_page),
    ("players", hubs.players_index),
    ("matches", hubs.matches_index),
    ("analysis", hubs.analysis_page),
    ("mgmt", hubs.management_page),
    ("history", hubs.history_page),
    ("projections", hubs.projections_page),
    ("method", hubs.methodology_page),
]


def write(rel_path, html):
    path = SITE / rel_path
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
    players = [p["player_id"] for p in d.profiles]
    events = sorted(d.events, key=lambda e: e["date"])
    with_pages = set(players)
    counts = {}

    for lang in LANGS:
        set_locale(lang)   # number formatting for this tree
        pages = 0
        for route, builder in HUBS:
            ctx = Ctx(lang, route)
            write(ctx.self_path, builder(d, ctx))
            pages += 1
        for profile in d.profiles:
            ctx = Ctx(lang, "player", profile["player_id"])
            write(ctx.self_path, player_page(d, ctx, profile, with_pages))
            pages += 1
        for i, event in enumerate(events):
            ctx = Ctx(lang, "match", match_slug(event))
            write(ctx.self_path, match_page(
                d, ctx, event,
                events[i - 1] if i else None,
                events[i + 1] if i + 1 < len(events) else None,
                with_pages))
            pages += 1
        counts[lang] = pages

    sitemap(d, events, players)
    total = sum(counts.values())
    print(f"built {total} pages ("
          + ", ".join(f"{lang}: {n}" for lang, n in counts.items())
          + f" — {len(players)} players, {len(events)} matches per language)")
    if MISSES:
        print(f"WARNING: {len(MISSES)} strings have no English translation:")
        for source in sorted(MISSES)[:12]:
            print(f"  - {source[:96]}")
    else:
        print("every generated string is translated")


def sitemap(d, events, players):
    base = layout.SITE_URL
    lastmod = d.meta["generated_at"][:10]
    urls = []
    for lang in LANGS:
        for route, _ in HUBS:
            urls.append(path_for(lang, route))
        urls += [path_for(lang, "player", pid) for pid in sorted(players)]
        urls += [path_for(lang, "match", match_slug(e)) for e in events]
    body = "\n".join(f"  <url><loc>{base}/{u}</loc>"
                     f"<lastmod>{lastmod}</lastmod></url>" for u in urls)
    (SITE / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{body}\n</urlset>\n", encoding="utf-8")
    (SITE / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml\n", encoding="utf-8")


if __name__ == "__main__":
    main()
