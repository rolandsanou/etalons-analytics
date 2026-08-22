"""HTML shell shared by every generated page.

Plain Python string building — no template engine, no JS toolchain. Each page
declares which data documents it needs and which section scripts to load; the
boot script only runs renderers whose anchor element is present on the page.
"""

import html
import json

SITE_NAME = "Étalons Analytics"

# (href, i18n label key, nav id)
NAV = [
    ("index.html", "nav_home", "home"),
    ("effectif.html", "nav_squad", "squad"),
    ("joueurs.html", "nav_pool", "players"),
    ("matchs.html", "nav_matches", "matches"),
    ("analyse.html", "nav_analysis", "analysis"),
    ("gestion.html", "nav_mgmt", "mgmt"),
    ("histoire.html", "nav_history", "history"),
    ("projections.html", "nav_proj", "projections"),
    ("methodologie.html", "nav_method", "method"),
]

SECTION_SCRIPTS = ["overview", "players", "breakdowns", "style", "tempo",
                   "importance", "history", "elo", "outlook", "match", "player"]


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


def page(*, title, description, body, depth=0, active="", needs=(), scripts=(),
         inline_data=None, page_class=""):
    """Render a complete page. `depth` is how many folders deep the file sits."""
    up = "../" * depth
    nav_items = "".join(
        '<a href="{u}{h}" data-i18n="{k}"{c}></a>'.format(
            u=up, h=href, k=key, c=' class="on"' if nav_id == active else "")
        for href, key, nav_id in NAV)
    script_tags = "\n".join(
        f'<script src="{up}assets/sections/{name}.js"></script>'
        for name in scripts)
    data_attr = f' data-needs="{",".join(needs)}"' if needs else ""
    inline = ""
    if inline_data is not None:
        payload = json.dumps(inline_data, ensure_ascii=False, separators=(",", ":"))
        inline = f'<script id="page-data" type="application/json">{payload}</script>'
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} — {SITE_NAME}</title>
<meta name="description" content="{esc(description)}">
<meta property="og:title" content="{esc(title)} — {SITE_NAME}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:type" content="website">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>⭐</text></svg>">
<link rel="stylesheet" href="{up}assets/style.css">
<link rel="stylesheet" href="{up}assets/pages.css">
</head>
<body class="{esc(page_class)}"{data_attr} data-base="{up}">

<header class="top">
  <div class="top-inner">
    <a class="brand" href="{up}index.html">{SITE_NAME}</a>
    <nav>{nav_items}</nav>
    <div class="lang">
      <button data-lang="fr">FR</button>
      <button data-lang="en">EN</button>
    </div>
  </div>
</header>

{body}

<footer>
  <p id="footer_text"></p>
</footer>

{inline}
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<script src="{up}assets/i18n.js"></script>
<script src="{up}assets/core.js"></script>
{script_tags}
<script src="{up}assets/boot.js"></script>
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
