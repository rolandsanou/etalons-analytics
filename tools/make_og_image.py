"""Draws the social-share cards (one per language) into site/assets/.

Run by hand, not from the build — the output is committed, so the normal build
and CI stay free of an image dependency:

    pip install pillow && python tools/make_og_image.py

Colours are the site's own tokens from assets/style.css; keep them in step if the
palette changes.
"""

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "site" / "assets"

W, H = 1200, 630
PAPER = "#f5f3ef"
INK = "#1b1a17"
INK2 = "#55534d"
RULE = "#cfcac0"
RED = "#c0142b"

SERIF = "C:/Windows/Fonts/georgiab.ttf"
SANS = "C:/Windows/Fonts/arial.ttf"

COPY = {
    "fr": ("Les Étalons, en chiffres",
           "Analyse de données ouverte sur l’équipe nationale",
           "du Burkina Faso — sélections, minutes, buts, Elo."),
    "en": ("The Étalons, by the numbers",
           "Open data analysis of the Burkina Faso national",
           "football team — caps, minutes, goals, Elo."),
}

# heights of the decorative bar motif, as fractions of its box
BARS = [0.35, 0.55, 0.42, 0.78, 0.62, 1.0, 0.71]


def font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        sys.exit(f"font not found: {path} — edit SERIF/SANS for this machine")


def spaced(text):
    """Letterspacing for small caps — Pillow has no tracking control."""
    return " ".join(text)


def fitted(draw, text, path, start, limit):
    """Largest size at or below `start` keeping `text` inside `limit` px, so a
    longer translation shrinks instead of running off the edge of the card."""
    for size in range(start, 24, -2):
        f = font(path, size)
        if draw.textlength(text, font=f) <= limit:
            return f
    return font(path, 24)


def card(lang):
    title, line1, line2 = COPY[lang]
    img = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(img)

    # masthead rule and wordmark
    draw.rectangle([0, 0, W, 10], fill=RED)
    draw.text((72, 74), spaced("ÉTALONS ANALYTICS"),
              font=font(SANS, 22), fill=INK2)

    draw.text((72, 176), title,
              font=fitted(draw, title, SERIF, 76, W - 2 * 72), fill=INK)
    draw.line([(72, 300), (312, 300)], fill=RED, width=4)

    sans28 = font(SANS, 29)
    draw.text((72, 340), line1, font=sans28, fill=INK2)
    draw.text((72, 384), line2, font=sans28, fill=INK2)

    # bar motif: signals "this is a data site" without asserting any figure
    bx, by, bw, bh, gap = 72, 560, 26, 88, 14
    for i, share in enumerate(BARS):
        x = bx + i * (bw + gap)
        draw.rectangle([x, by - bh, x + bw, by], fill=RULE)
        draw.rectangle([x, by - bh * share, x + bw, by], fill=RED if i == 5 else INK2)

    draw.text((W - 72, 566), "rolandsanou.github.io/etalons-analytics",
              font=font(SANS, 22), fill=INK2, anchor="rs")

    path = OUT / f"og-{lang}.png"
    img.save(path, optimize=True)
    print(f"{path.relative_to(ROOT)}  {path.stat().st_size // 1024} kB")


if __name__ == "__main__":
    for lang in COPY:
        card(lang)
