from ..config import FORMER_NAMES_URL, RAW, RESULTS_URL, SHOOTOUTS_URL
from ..http import get_bytes

OUT = RAW / "martj42"


def run(force=False):
    OUT.mkdir(parents=True, exist_ok=True)
    for url, name in ((RESULTS_URL, "results.csv"), (FORMER_NAMES_URL, "former_names.csv"),
                      (SHOOTOUTS_URL, "shootouts.csv")):
        dest = OUT / name
        if dest.exists() and not force:
            continue
        dest.write_bytes(get_bytes(url))
        print(f"fetched {dest}")
