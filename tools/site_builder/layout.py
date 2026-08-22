"""HTML shell shared by every generated page.

Plain Python string building — no template engine, no JS toolchain. Each page
declares which data documents it needs and which section scripts to load; the
boot script only runs renderers whose anchor element is present on the page.

The site is generated once per language (see routes.py). Because each page is a
real file in its own language, the copy is in the HTML rather than swapped in by
JavaScript — so it is readable without JS and indexable, and the FR/EN control is
a pair of links to the counterpart page rather than a client-side toggle.
"""

import html
import json

from . import seo
from .routes import NAV, depth_of, path_for

SITE_NAME = "Étalons Analytics"

SITE_URL = seo.SITE_URL

# Short content hash appended to every stylesheet and script URL so a deploy is
# visible immediately instead of waiting for the CDN cache to expire. Set by
# build_site.main() from the actual asset contents.
ASSET_VERSION = ""

# Attribution, licence, update date and contact — the same on every page, so it
# is baked in at build time rather than fetched. It used to be written by the
# boot script from meta.json, which meant the 374 pages that do not load that
# document showed an empty footer. Set by build_site.main().
FOOTER = {}

FOOTER_TEMPLATE = {
    "fr": ("Étalons Analytics — projet open source (MIT). Données : Wikipedia "
           "(CC BY-SA), martj42/international_results (CC0), Sofascore (non "
           "affilié), portraits Wikimedia Commons. Mis à jour le {date}. "
           'Contact : <a href="mailto:{mail}">{mail}</a> · '
           '<a href="{repo}">code source</a>.'),
    "en": ("Étalons Analytics — open-source project (MIT). Data: Wikipedia "
           "(CC BY-SA), martj42/international_results (CC0), Sofascore "
           "(unaffiliated), portraits from Wikimedia Commons. Updated {date}. "
           'Contact: <a href="mailto:{mail}">{mail}</a> · '
           '<a href="{repo}">source code</a>.'),
}


def build_footers(updated_on, contact):
    """Render the footer once per language, for build_site to install."""
    return {lang: tpl.format(date=updated_on, mail=contact, repo=seo.REPO_URL)
            for lang, tpl in FOOTER_TEMPLATE.items()}

LANG_LABEL = {"fr": "FR", "en": "EN"}


def esc(text):
    return html.escape(str(text if text is not None else ""), quote=True)


def initials(name):
    parts = [p for p in str(name).split() if p]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


# CSS box for each portrait class, all square with object-fit: cover. Declaring
# the intrinsic size lets the browser reserve the space before the image arrives,
# so the text beside it does not jump once it does.
PORTRAIT_BOX = {"photo": 96, "pic": 42}


def avatar(photo, name, cls, size=None, eager=False):
    """<img> when a freely-licensed portrait exists, initials otherwise.

    `eager` is for a portrait above the fold: lazy-loading the largest element
    on screen only delays the paint the visitor is waiting for.
    """
    style = f' style="width:{size}px;height:{size}px"' if size else ""
    if photo:
        box = size or PORTRAIT_BOX.get(cls.split()[0])
        dims = f' width="{box}" height="{box}"' if box else ""
        load = ('loading="eager" fetchpriority="high"' if eager
                else 'loading="lazy"')
        return (f'<img class="{cls}" src="{esc(photo)}" alt="{esc(name)}" '
                f'{load} decoding="async"{dims}{style}>')
    return (f'<span class="{cls} avatar" aria-hidden="true"{style}>'
            f'{esc(initials(name))}</span>')


def page(ctx, *, title, description, body, needs=(), scripts=(), page_class="",
         full_title=None, og_image=None, og_card="summary_large_image",
         og_type="website", structured=(), noindex=False):
    """Render a complete page for ctx (language + location).

    `title` is the short label; `full_title` (or a per-route entry in
    seo.TITLES) overrides the <title> tag when a search-friendlier phrasing is
    wanted. `og_image` is a site-relative path — the branded card by default.
    """
    up = "../" * depth_of(ctx.self_path)

    def asset(path):
        suffix = f"?v={ASSET_VERSION}" if ASSET_VERSION else ""
        return f"{up}{path}{suffix}"

    nav_items = "".join(
        '<a href="{href}"{cls}>{label}</a>'.format(
            href=ctx.url(route), label=esc(ctx.t(label_fr)),
            cls=' class="on"' if route == ctx.route else "")
        for route, label_fr in NAV)

    alternates = ctx.alternates()
    lang_links = "".join(
        '<a href="{href}"{cls} hreflang="{lang}" lang="{lang}">{label}</a>'.format(
            href=href, lang=lang, label=LANG_LABEL[lang],
            cls=' class="on"' if lang == ctx.lang else "")
        for lang, href in alternates)
    # hreflang needs absolute URLs, and x-default names the version to serve when
    # no declared language matches the visitor — French, the primary tree.
    hreflang = "\n".join(
        [f'<link rel="alternate" hreflang="{lang}" '
         f'href="{seo.canonical_url(path_for(lang, ctx.route, ctx.slug))}">'
         for lang, _ in alternates]
        + [f'<link rel="alternate" hreflang="x-default" '
           f'href="{seo.canonical_url(path_for("fr", ctx.route, ctx.slug))}">'])

    canonical = seo.canonical_url(ctx.self_path)
    title_tag = full_title or seo.TITLES.get(ctx.route, {}).get(ctx.lang) \
        or f"{title} — {SITE_NAME}"
    image = seo.absolute(og_image or f"assets/og-{ctx.lang}.png")
    # the branded card is a known 1200x630; a portrait's dimensions vary, so they
    # are only declared when they are actually known
    dims = "" if og_image else f"""
<meta property="og:image:width" content="{seo.CARD_W}">
<meta property="og:image:height" content="{seo.CARD_H}">"""
    robots = ('<meta name="robots" content="noindex, follow">' if noindex
              else '<meta name="robots" content="index, follow, '
                   'max-image-preview:large">')
    social = f"""<meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{image}">{dims}
<meta property="og:image:alt" content="{esc(title_tag)}">
<meta name="twitter:card" content="{og_card}">
<meta name="twitter:title" content="{esc(title_tag)}">
<meta name="twitter:description" content="{esc(description)}">
<meta name="twitter:image" content="{image}">"""

    script_tags = "\n".join(
        f'<script src="{asset(f"assets/sections/{name}.js")}"></script>'
        for name in scripts)
    data_attr = f' data-needs="{",".join(needs)}"' if needs else ""

    # The charting library is a megabyte, and the match and player pages draw no
    # charts at all — they are static HTML by design. Asking the body whether it
    # holds a chart container keeps this honest: a renderer only ever runs
    # against an anchor that is already in the markup, so no container means no
    # chart, and the tag can go.
    echarts = ('\n<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/'
               'echarts.min.js"></script>') if 'class="chart' in body else ""

    return f"""<!DOCTYPE html>
<html lang="{ctx.lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title_tag)}</title>
<meta name="description" content="{esc(description)}">
{robots}
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{esc(title_tag)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:type" content="{og_type}">
<meta property="og:locale" content="{'fr_FR' if ctx.lang == 'fr' else 'en_GB'}">
<meta property="og:locale:alternate" content="{'en_GB' if ctx.lang == 'fr' else 'fr_FR'}">
{social}
{hreflang}
{seo.jsonld(*structured)}
<meta name="theme-color" content="#f5f3ef" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#161513" media="(prefers-color-scheme: dark)">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>⭐</text></svg>">
<script>/* set the remembered theme before first paint, so an explicit dark choice
   never flashes light. No stored choice: prefers-color-scheme decides in CSS.
   Braces are doubled because this block sits inside a Python f-string. */
try{{var _t=localStorage.getItem("ea_theme");if(_t==="dark"||_t==="light")
document.documentElement.setAttribute("data-theme",_t);}}catch(e){{}}</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@400..700&family=Newsreader:opsz,wght@6..72,500..700&display=swap">
<link rel="stylesheet" href="{asset("assets/style.css")}">
<link rel="stylesheet" href="{asset("assets/pages.css")}">
</head>
<body class="{esc(page_class)}"{data_attr} data-base="{up}">

<header class="top">
  <div class="top-inner">
    <a class="brand" href="{ctx.url('home')}">{SITE_NAME}</a>
    <nav>{nav_items}</nav>
    <div class="lang">{lang_links}</div>
    <button class="theme" id="theme_toggle" type="button"
            aria-pressed="false"><span aria-hidden="true"></span></button>
  </div>
</header>

{body}

<footer>
  <p id="footer_text">{FOOTER.get(ctx.lang, "")}</p>
</footer>

{echarts}
<script src="{asset("assets/i18n.js")}"></script>
<script src="{asset("assets/core.js")}"></script>
{script_tags}
<script src="{asset("assets/boot.js")}"></script>
</body>
</html>
"""


def hero(eyebrow, title, lead):
    return f"""<div class="hero-band"><div class="inner">
  <p class="eyebrow">{esc(eyebrow)}</p>
  <h1>{esc(title)}</h1>
  <p>{esc(lead)}</p>
</div></div>"""


def section(id_, title_key, lead_key=None, cards="", extra_head=""):
    lead = f'<p class="lead" data-i18n="{lead_key}"></p>' if lead_key else ""
    return f"""<section id="{id_}">
  <h2 data-i18n="{title_key}"></h2>
  {lead}{extra_head}
  <div class="grid">{cards}</div>
</section>"""


def card(*, chart=None, title_key=None, sub_key=None, card_id=None, width="",
         table_id=None, extra="", height="", title_html=None):
    cls = f"card {width}".strip()
    idattr = f' id="{card_id}"' if card_id else ""
    head = ""
    if title_html:
        head += title_html
    elif title_key:
        head += f'<h3 data-i18n="{title_key}"></h3>'
    if sub_key:
        head += f'<p class="sub" data-i18n="{sub_key}"></p>'
    inner = head
    if chart:
        inner += f'<div class="chart {height}" id="{chart}"></div>'
    if table_id:
        inner += f'<div class="tablewrap"><table id="{table_id}"></table></div>'
    inner += extra
    return f'<div class="{cls}"{idattr}>{inner}</div>'
