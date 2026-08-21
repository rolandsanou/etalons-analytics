from datetime import datetime

from ..config import RAW, SEED, WIKI_TEAM_URL
from ..http import get_bytes
from ..util import read_csv, write_json

OUT = RAW / "wikipedia"


def squad_windows():
    return read_csv(SEED / "wiki_squads.csv")


def raw_path(window):
    if window["url"] == "TEAM_PAGE":
        return OUT / "team_page.html"
    return OUT / f"{window['window_id']}.html"


def run(force=False):
    OUT.mkdir(parents=True, exist_ok=True)
    fetched = {}
    manifest = []
    for w in squad_windows():
        url = WIKI_TEAM_URL if w["url"] == "TEAM_PAGE" else w["url"]
        dest = raw_path(w)
        if dest.exists() and not force:
            continue
        if url not in fetched:
            fetched[url] = get_bytes(url)
        dest.write_bytes(fetched[url])
        manifest.append({"file": dest.name, "url": url,
                         "fetched_at": datetime.now().isoformat(timespec="seconds")})
        print(f"fetched {dest}")
    if manifest:
        write_json(OUT / "manifest.json", manifest)
