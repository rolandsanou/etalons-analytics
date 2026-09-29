from datetime import date, datetime

from ..config import (FORMER_NAMES_URL, RAW, RESULTS_MAX_AGE_DAYS, RESULTS_URL,
                      SHOOTOUTS_URL)
from ..http import get_bytes

OUT = RAW / "martj42"


def _stale(dest):
    """A local copy older than the feed's own update rhythm.

    These files gain a row within days of every international match, and the
    Elo model, the all-time record and every historical page are built from
    them. Keeping the first copy forever — which is what `if dest.exists()`
    did — froze the team's history at whatever day the download first landed,
    silently: the pipeline still ran, still passed, still published, and the
    record simply stopped moving.
    """
    if not dest.exists():
        return True
    age = (date.today() - datetime.fromtimestamp(dest.stat().st_mtime).date()).days
    return age >= RESULTS_MAX_AGE_DAYS


def run(force=False):
    OUT.mkdir(parents=True, exist_ok=True)
    for url, name in ((RESULTS_URL, "results.csv"), (FORMER_NAMES_URL, "former_names.csv"),
                      (SHOOTOUTS_URL, "shootouts.csv")):
        dest = OUT / name
        if not (force or _stale(dest)):
            continue
        try:
            payload = get_bytes(url)
        except Exception as e:
            # a kept copy beats no copy; the freshness gate reports the drift
            if dest.exists():
                print(f"martj42: keeping the cached {name} ({e})")
                continue
            raise
        dest.write_bytes(payload)
        print(f"fetched {dest}")
