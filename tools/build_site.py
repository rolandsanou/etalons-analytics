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

from tools.site_builder import hubs, layout, seo  # noqa: E402
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
    # The report below quotes site copy, which is full of accents, em dashes
    # and arrows. On a cp1252 console that raises UnicodeEncodeError and takes
    # the whole build down over a print statement, so widen stdout first.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass
    d = Data()
    layout.ASSET_VERSION = asset_version()
    layout.FOOTER = layout.build_footers(
        d.meta.get("updated_on") or d.meta["generated_at"][:10],
        d.meta["contact"])
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

    write("404.html", not_found())
    listed = sitemap(d, events, players)
    total = sum(counts.values())
    print(f"built {total} pages ("
          + ", ".join(f"{lang}: {n}" for lang, n in counts.items())
          + f" — {len(players)} players, {len(events)} matches per language)")
    print(f"sitemap lists {listed} URLs with language alternates; 404.html written")
    if MISSES:
        print(f"WARNING: {len(MISSES)} strings have no English translation:")
        for source in sorted(MISSES)[:12]:
            print(f"  - {source[:96]}")
    else:
        print("every generated string is translated")


def not_found():
    """site/404.html — served by GitHub Pages for any unknown path.

    Deliberately self-contained: the host serves this one file for URLs at every
    depth, so relative asset paths would resolve differently each time. Inline
    styles and absolute links are the only things that behave the same
    everywhere. It serves both language trees, so it says everything twice.
    """
    home_fr = seo.canonical_url("index.html")
    home_en = seo.canonical_url("en/index.html")
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Page introuvable — {layout.SITE_NAME}</title>
<meta name="robots" content="noindex, follow">
<style>
:root {{ color-scheme: light dark; --paper:#f5f3ef; --ink:#1b1a17;
         --ink2:#55534d; --red:#c0142b; }}
@media (prefers-color-scheme: dark) {{
  :root {{ --paper:#161513; --ink:#f3f1ec; --ink2:#bdb9b1; --red:#f2617a; }}
}}
* {{ box-sizing: border-box }}
body {{ margin:0; min-height:100vh; display:grid; place-items:center;
        background:var(--paper); color:var(--ink); padding:2rem;
        font:400 1rem/1.6 Georgia, "Times New Roman", serif; }}
main {{ max-width:34rem }}
.rule {{ width:4rem; height:4px; background:var(--red); margin:0 0 2rem }}
h1 {{ font-size:clamp(1.8rem,5vw,2.6rem); line-height:1.15; margin:0 0 .5rem;
      letter-spacing:-.01em }}
p {{ color:var(--ink2); margin:.4rem 0 0 }}
.sep {{ border:0; border-top:1px solid var(--ink2); opacity:.25; margin:2rem 0 }}
a {{ color:var(--ink); text-decoration-color:var(--red);
     text-underline-offset:3px }}
a:hover {{ color:var(--red) }}
</style>
</head>
<body>
<main>
  <div class="rule"></div>
  <h1>Cette page n’existe pas</h1>
  <p>Le lien est peut-être ancien, ou l’adresse mal recopiée.</p>
  <p><a href="{home_fr}">Retour à l’accueil d’{layout.SITE_NAME}</a></p>
  <hr class="sep">
  <h1 lang="en">This page doesn’t exist</h1>
  <p lang="en">The link may be out of date, or the address mistyped.</p>
  <p lang="en"><a href="{home_en}" hreflang="en">Back to the
     {layout.SITE_NAME} home page</a></p>
</main>
</body>
</html>
"""


def sitemap(d, events, players):
    """One <url> per page per language, each declaring the whole set of language
    alternates. Search engines use that to serve the right tree rather than
    treating the two as competing duplicates."""
    base = layout.SITE_URL
    lastmod = d.meta["generated_at"][:10]

    pages = [(route, None) for route, _ in HUBS]
    pages += [("player", pid) for pid in sorted(players)]
    pages += [("match", match_slug(e)) for e in events]

    entries = []
    for route, slug in pages:
        alts = "".join(
            f'\n    <xhtml:link rel="alternate" hreflang="{hl}" '
            f'href="{seo.canonical_url(path_for(lang, route, slug))}"/>'
            for hl, lang in list(zip(LANGS, LANGS)) + [("x-default", "fr")])
        for lang in LANGS:
            entries.append(
                f"  <url>\n    <loc>"
                f"{seo.canonical_url(path_for(lang, route, slug))}</loc>{alts}\n"
                f"    <lastmod>{lastmod}</lastmod>\n  </url>")

    (SITE / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
        '        xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
        + "\n".join(entries) + "\n</urlset>\n", encoding="utf-8")
    (SITE / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {base}/sitemap.xml\n", encoding="utf-8")
    return len(entries)


if __name__ == "__main__":
    main()
