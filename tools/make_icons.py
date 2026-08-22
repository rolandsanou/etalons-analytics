"""Draws the site icon into site/assets/, in every form a browser asks for.

Run by hand, not from the build — the output is committed, so the normal build
and CI stay free of an image dependency:

    pip install pillow && python tools/make_icons.py

The mark is the same ascending-bars motif as the social cards, in the Burkina
Faso red, and it is drawn from geometry rather than set as a character. A glyph
would depend on the reader having a font that carries it — the reason the site
used to show a tofu box where the theme toggle's icon should have been, and the
reason the old favicon (an emoji inside an SVG <text>) rendered differently on
every platform.
"""

import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "site" / "assets"

RED = "#c0142b"        # --s1, the Burkina Faso accent
PAPER = "#f5f3ef"      # --paper

BOX = 32               # design grid; every figure below is in these units
RADIUS = 7
BAR_W = 5
BAR_GAP = 2
BAR_HEIGHTS = (8, 13, 19)
BAR_BASE = 25.5        # y of the bars' shared baseline
BAR_R = 1

# centred as a group, so the mark stays balanced at 16px
_SPAN = len(BAR_HEIGHTS) * BAR_W + (len(BAR_HEIGHTS) - 1) * BAR_GAP
BAR_X0 = (BOX - _SPAN) / 2


def bars():
    """(x0, y0, x1, y1) per bar, in design units."""
    for i, h in enumerate(BAR_HEIGHTS):
        x = BAR_X0 + i * (BAR_W + BAR_GAP)
        yield x, BAR_BASE - h, x + BAR_W, BAR_BASE


def svg():
    rects = "".join(
        f'<rect x="{x:g}" y="{y:g}" width="{x1 - x:g}" height="{y1 - y:g}" '
        f'rx="{BAR_R}" fill="{PAPER}"/>'
        for x, y, x1, y1 in bars())
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {BOX} {BOX}">'
            f'<title>Étalons Analytics</title>'
            f'<rect width="{BOX}" height="{BOX}" rx="{RADIUS}" fill="{RED}"/>'
            f"{rects}</svg>\n")


def raster(size, rounded=True):
    """The same mark as pixels. Drawn 4x and reduced, so the curves stay clean."""
    scale = 4
    px = size * scale
    img = Image.new("RGBA", (px, px), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    k = px / BOX
    if rounded:
        draw.rounded_rectangle([0, 0, px - 1, px - 1], radius=RADIUS * k, fill=RED)
    else:
        draw.rectangle([0, 0, px, px], fill=RED)
    for x, y, x1, y1 in bars():
        draw.rounded_rectangle([x * k, y * k, x1 * k, y1 * k],
                               radius=max(1, BAR_R * k), fill=PAPER)
    return img.resize((size, size), Image.LANCZOS)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "favicon.svg").write_text(svg(), encoding="utf-8")

    # .ico carries several sizes: browsers pick, and the small one is what a
    # crowded tab bar actually shows
    raster(48).save(OUT / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    # iOS masks the corners itself, so this one is square and fully opaque
    apple = Image.new("RGB", (180, 180), RED)
    apple.paste(raster(180, rounded=False), (0, 0), raster(180, rounded=False))
    apple.save(OUT / "apple-touch-icon.png", optimize=True)

    for name in ("favicon.svg", "favicon.ico", "apple-touch-icon.png"):
        p = OUT / name
        print(f"  {p.relative_to(ROOT)}  {p.stat().st_size} bytes")


if __name__ == "__main__":
    sys.exit(main())
