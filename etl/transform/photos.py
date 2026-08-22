"""Stage the portrait catalogue (licence + author) for attribution."""

from ..config import RAW, STAGING
from ..util import read_json, write_csv

PHOTO_FIELDS = ["kind", "slug", "name", "file", "licence", "author", "credit_url",
                "local_path"]


def run():
    folder = RAW / "commons"
    rows = []
    if folder.exists():
        for f in sorted(folder.glob("*.json")):
            data = read_json(f)
            image = data.get("image") or {}
            if not image:
                continue
            rows.append({
                "kind": data["kind"], "slug": data["slug"], "name": data["title"],
                "file": image["file"], "licence": image["licence"],
                "author": image["author"], "credit_url": image["credit_url"],
                "local_path": f"assets/photos/{data['kind']}-{data['slug']}.jpg",
            })
    rows.sort(key=lambda r: (r["kind"], r["slug"]))
    write_csv(STAGING / "photos.csv", rows, PHOTO_FIELDS)
