import csv
import json
import re
import unicodedata

from .config import SEED


def norm_name(name):
    s = unicodedata.normalize("NFD", str(name))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-zA-Z ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip().lower()


def slugify(name):
    return norm_name(name).replace(" ", "-")


def load_overrides():
    path = SEED / "name_overrides.csv"
    if not path.exists():
        return {}
    with path.open(encoding="utf-8-sig", newline="") as f:
        return {norm_name(r["variant"]): r["canonical"].strip()
                for r in csv.DictReader(f) if r.get("variant") and r.get("canonical")}


def canonical_name(name, overrides):
    return overrides.get(norm_name(name), name)


def write_csv(path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"wrote {path} ({len(rows)} rows)")


def read_csv(path):
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {path} ({path.stat().st_size // 1024} KB)")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))
