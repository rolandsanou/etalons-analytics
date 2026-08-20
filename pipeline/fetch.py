import requests

from .config import DATA_RAW, USER_AGENT


def fetch(url, filename, force=False):
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    dest = DATA_RAW / filename
    if dest.exists() and not force:
        return dest
    r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=60)
    r.raise_for_status()
    dest.write_bytes(r.content)
    return dest
