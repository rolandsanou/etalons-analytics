"""Verify every internal link in the generated site resolves to a real file."""

import re
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent / "site"
HREF = re.compile(r'(?:href|src)="([^"#:]+?)"')


def main():
    pages = sorted(SITE.rglob("*.html"))
    missing = []
    for page in pages:
        text = page.read_text(encoding="utf-8")
        for href in HREF.findall(text):
            if href.startswith(("http", "//", "data:", "mailto:")):
                continue
            target = (page.parent / href).resolve()
            if not target.exists():
                missing.append(f"{page.relative_to(SITE)} -> {href}")
    print(f"checked {len(pages)} pages, {len(missing)} broken internal links")
    for m in missing[:15]:
        print("  ", m)
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
