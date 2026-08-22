"""Audit the search metadata of every generated page.

    python tools/check_seo.py

Checks the things that break quietly: a canonical pointing at the wrong file, a
title that will be truncated in results, a social image that 404s, hreflang that
forgets to name itself, structured data that stopped parsing. Exits non-zero on a
FAIL so it can gate a deploy; WARN is advisory.
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.site_builder.seo import canonical_url  # noqa: E402

SITE = ROOT / "site"

# Google truncates a title near 60 characters and a description near 160.
TITLE_MAX = 65
DESC_MIN, DESC_MAX = 50, 170

TITLE = re.compile(r"<title>(.*?)</title>", re.S)
CANON = re.compile(r'<link rel="canonical" href="([^"]+)"')
DESC = re.compile(r'<meta name="description" content="([^"]*)"')
OG_IMAGE = re.compile(r'<meta property="og:image" content="([^"]+)"')
HREFLANG = re.compile(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"')
LD = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)
H1 = re.compile(r"<h1[\s>]")
ID_ATTR = re.compile(r'\sid="([^"]+)"')
SITE_BASE = canonical_url("")


def audit(page):
    """[(level, message)] for one built page."""
    rel = page.relative_to(SITE).as_posix()
    text = page.read_text(encoding="utf-8")
    out = []
    noindex = 'name="robots" content="noindex' in text

    titles = TITLE.findall(text)
    if len(titles) != 1:
        out.append(("FAIL", f"{len(titles)} <title> tags"))
    elif len(titles[0]) > TITLE_MAX:
        out.append(("WARN", f"title is {len(titles[0])} chars, "
                            f"over {TITLE_MAX}: {titles[0][:70]}…"))

    if H1.search(text) is None:
        out.append(("FAIL", "no <h1>"))

    # a duplicated id silently breaks the client-side renderers, which look
    # elements up by id
    dupes = [i for i, n in Counter(ID_ATTR.findall(text)).items() if n > 1]
    if dupes:
        out.append(("FAIL", f"duplicate id(s): {', '.join(sorted(dupes)[:4])}"))

    # Everything below is about how the page appears in results, so it does not
    # apply to a page that asks not to be indexed — the bilingual 404 carries two
    # h1s and no description on purpose.
    if noindex:
        return out

    if len(H1.findall(text)) > 1:
        out.append(("WARN", f"{len(H1.findall(text))} <h1> tags"))

    descs = DESC.findall(text)
    if len(descs) != 1:
        out.append(("FAIL", f"{len(descs)} meta descriptions"))
    elif not DESC_MIN <= len(descs[0]) <= DESC_MAX:
        out.append(("WARN", f"description is {len(descs[0])} chars "
                            f"(want {DESC_MIN}–{DESC_MAX})"))

    canon = CANON.findall(text)
    if len(canon) != 1:
        out.append(("FAIL", f"{len(canon)} canonical links"))
    elif canon[0] != canonical_url(rel):
        out.append(("FAIL", f"canonical points elsewhere: {canon[0]}"))

    langs = dict(HREFLANG.findall(text))
    for want in ("fr", "en", "x-default"):
        if want not in langs:
            out.append(("FAIL", f"no hreflang={want}"))
    self_lang = "en" if rel.startswith("en/") else "fr"
    if langs.get(self_lang) and canon and langs[self_lang] != canon[0]:
        out.append(("FAIL", "hreflang does not name this page's own canonical"))

    images = OG_IMAGE.findall(text)
    if len(images) != 1:
        out.append(("FAIL", f"{len(images)} og:image tags"))
    else:
        local = SITE / images[0][len(SITE_BASE):]
        if not images[0].startswith(SITE_BASE):
            out.append(("FAIL", f"og:image is not on this site: {images[0]}"))
        elif not local.exists():
            out.append(("FAIL", f"og:image file missing: {local.name}"))

    for block in LD.findall(text):
        try:
            obj = json.loads(block)
        except json.JSONDecodeError as exc:
            out.append(("FAIL", f"structured data does not parse: {exc}"))
            continue
        if "@type" not in obj or "@context" not in obj:
            out.append(("FAIL", "structured data missing @type/@context"))
    return out


def asset_faults():
    """Control characters and replacement chars in the stylesheets and scripts.

    Twice now a non-ASCII escape has been mangled on its way into an asset: a
    combining-mark range became a raw U+0300 and silently killed all of core.js,
    and a `\\25D1` escape became byte 0x15 followed by the literal text "D1",
    which is what the theme toggle rendered. Neither shows up as a broken link or
    a failed request, so nothing else would catch it.
    """
    faults = []
    for path in sorted((SITE / "assets").rglob("*.css")) + \
            sorted((SITE / "assets").rglob("*.js")):
        text = path.read_text(encoding="utf-8", errors="replace")
        for n, line in enumerate(text.splitlines(), 1):
            bad = {c for c in line if (ord(c) < 32 and c != "\t") or ord(c) == 127
                   or c == "�"}
            if bad:
                names = ", ".join(f"U+{ord(c):04X}" for c in sorted(bad))
                faults.append(f"{path.relative_to(SITE).as_posix()}:{n}: "
                              f"stray control/replacement char ({names})")
    return faults


def main():
    pages = sorted(SITE.rglob("*.html"))
    if not pages:
        sys.exit("no pages built — run tools/build_site.py first")

    fails, warns = [], []
    for page in pages:
        for level, message in audit(page):
            line = f"{page.relative_to(SITE).as_posix()}: {message}"
            (fails if level == "FAIL" else warns).append(line)

    fails += asset_faults()

    sitemap = SITE / "sitemap.xml"
    if not sitemap.exists():
        fails.append("sitemap.xml is missing")
    if not (SITE / "robots.txt").exists():
        fails.append("robots.txt is missing")
    if not (SITE / "404.html").exists():
        fails.append("404.html is missing")

    if sitemap.exists():
        listed = set(re.findall(r"<loc>([^<]+)</loc>", sitemap.read_text("utf-8")))
        expected = {canonical_url(p.relative_to(SITE).as_posix()) for p in pages
                    if "noindex" not in p.read_text(encoding="utf-8")}
        for url in sorted(expected - listed)[:5]:
            fails.append(f"indexable page not in sitemap: {url}")
        for url in sorted(listed - expected)[:5]:
            fails.append(f"sitemap lists a page that was not built: {url}")

    print(f"audited {len(pages)} pages: {len(fails)} failures, {len(warns)} warnings")
    for line in fails[:20]:
        print("  FAIL", line)
    for line in warns[:20]:
        print("  WARN", line)
    if len(warns) > 20:
        print(f"  … and {len(warns) - 20} more warnings")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
