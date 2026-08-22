"""Freely-licensed portraits from Wikimedia Commons.

Only Commons-hosted images are used: they carry an explicit free licence (CC0,
CC BY, CC BY-SA or public domain) and a named author, both recorded for
attribution. Press photos from the stats providers are deliberately NOT used —
they are copyrighted and could not be republished here.

Images are downloaded and self-hosted (Wikimedia discourages hotlinking) into
site/assets/photos/, and the licence metadata is staged for the credits page.
"""

import re
import time
from datetime import datetime

import requests

from ..config import RAW, ROOT, SEED
from ..util import read_csv, read_json, write_json

OUT = RAW / "commons"
PHOTO_DIR = ROOT / "site" / "assets" / "photos"
API_EN = "https://en.wikipedia.org/w/api.php"
API_COMMONS = "https://commons.wikimedia.org/w/api.php"
THUMB_WIDTH = 420
SLEEP = 0.4

# Wikimedia asks for a descriptive User-Agent identifying the project
UA = {"User-Agent": "etalons-analytics/1.0 (open-source football analytics; "
                    "https://github.com/rolandsanou/etalons-analytics)"}

FREE_LICENCES = ("cc0", "cc by", "cc-by", "public domain", "pd-", "cc sa")


def _strip_html(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s or "")).strip()


def is_free(licence):
    """Only republish licences that explicitly allow it."""
    low = (licence or "").lower()
    return any(tag in low for tag in FREE_LICENCES)


def _api(url, params, retries=2):
    for attempt in range(retries + 1):
        try:
            r = requests.get(url, params=params, headers=UA, timeout=30)
            if r.status_code == 200 and r.text.lstrip().startswith(("{", "[")):
                time.sleep(SLEEP)
                return r.json()
        except Exception:
            pass
        time.sleep(SLEEP * (attempt + 2))
    return {}


def lookup(title):
    """-> {file, thumb_url, licence, author, credit_url} or {} when unusable."""
    page_q = _api(API_EN, {"action": "query", "titles": title, "prop": "pageimages",
                           "piprop": "thumbnail|name", "pithumbsize": THUMB_WIDTH,
                           "format": "json", "redirects": 1})
    page = next(iter(page_q.get("query", {}).get("pages", {}).values()), {})
    fname = page.get("pageimage")
    thumb = (page.get("thumbnail") or {}).get("source")
    if not fname or not thumb:
        return {}
    info = _api(API_COMMONS, {"action": "query", "titles": f"File:{fname}",
                              "prop": "imageinfo", "iiprop": "extmetadata|url",
                              "iiurlwidth": THUMB_WIDTH, "format": "json"})
    p2 = next(iter(info.get("query", {}).get("pages", {}).values()), {})
    if not p2 or p2.get("missing") is not None:
        return {}  # not on Commons -> may be non-free local upload, skip
    ii = (p2.get("imageinfo") or [{}])[0]
    meta = ii.get("extmetadata", {})
    licence = meta.get("LicenseShortName", {}).get("value", "")
    if not is_free(licence):
        return {}
    return {
        "file": fname,
        "thumb_url": ii.get("thumburl") or thumb,
        "licence": licence,
        "author": _strip_html(meta.get("Artist", {}).get("value")) or "unknown",
        "credit_url": ii.get("descriptionurl")
                      or f"https://commons.wikimedia.org/wiki/File:{fname}",
    }


def _targets():
    """(kind, slug, wikipedia title) for players in the registry and coaches."""
    from ..config import STAGING
    out = []
    players = STAGING / "players.csv"
    if players.exists():
        for p in read_csv(players):
            if p.get("status") in ("active", "fringe") or p.get("n_windows") not in ("0", ""):
                out.append(("player", p["player_id"], p["name"]))
    coaches = SEED / "coach_tenures.csv"
    if coaches.exists():
        seen = set()
        for c in read_csv(coaches):
            name = c["coach"].split(" & ")[0].strip()
            slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
            if slug not in seen:
                seen.add(slug)
                out.append(("coach", slug, name))
    return out


def run(force=False):
    OUT.mkdir(parents=True, exist_ok=True)
    PHOTO_DIR.mkdir(parents=True, exist_ok=True)
    found = downloaded = 0
    for kind, slug, title in _targets():
        cache = OUT / f"{kind}-{slug}.json"
        if cache.exists() and not force:
            data = read_json(cache)
        else:
            data = {"fetched_at": datetime.now().isoformat(timespec="seconds"),
                    "kind": kind, "slug": slug, "title": title, "image": lookup(title)}
            write_json(cache, data)
        image = data.get("image") or {}
        if not image:
            continue
        found += 1
        dest = PHOTO_DIR / f"{kind}-{slug}.jpg"
        if dest.exists() and not force:
            continue
        try:
            r = requests.get(image["thumb_url"], headers=UA, timeout=40)
            if r.status_code == 200 and r.content:
                dest.write_bytes(r.content)
                downloaded += 1
                time.sleep(SLEEP)
        except Exception:
            pass
    print(f"commons: {found} freely-licensed portraits, {downloaded} downloaded")
