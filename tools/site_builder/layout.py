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

from .routes import NAV, depth_of, path_for

SITE_NAME = "Étalons Analytics"

SITE_URL = "https://rolandsanou.github.io/etalons-analytics"

# Short content hash appended to every stylesheet and script URL so a deploy is
# visible immediately instead of waiting for the CDN cache to expire. Set by
# build_site.main() from the actual asset contents.
ASSET_VERSION = ""

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


def avatar(photo, name, cls, size=None):
    """<img> when a freely-licensed portrait exists, initials otherwise."""
    style = f' style="width:{size}px;height:{size}px"' if size else ""
    if photo:
        return (f'<img class="{cls}" src="{esc(photo)}" alt="{esc(name)}" '
                f'loading="lazy" decoding="async"{style}>')
    return (f'<span class="{cls} avatar" aria-hidden="true"{style}>'
            f'{esc(initials(name))}</span>')


def page(ctx, *, title, description, body, needs=(), scripts=(), page_class=""):
    """Render a complete page for ctx (language + location)."""
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
    hreflang = "\n".join(
        f'<link rel="alternate" hreflang="{lang}" '
        f'href="{SITE_URL}/{path_for(lang, ctx.route, ctx.slug)}">'
        for lang, _ in alternates)

    script_tags = "\n".join(
        f'<script src="{asset(f"assets/sections/{name}.js")}"></script>'
        for name in scripts)
    data_attr = f' data-needs="{",".join(needs)}"' if needs else ""

    return f"""<!DOCTYPE html>
<html lang="{ctx.lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} — {SITE_NAME}</title>
<meta name="description" content="{esc(description)}">
<meta property="og:title" content="{esc(title)} — {SITE_NAME}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:type" content="website">
<meta property="og:locale" content="{'fr_FR' if ctx.lang == 'fr' else 'en_GB'}">
{hreflang}
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
  <p id="footer_text"></p>
</footer>

<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
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
