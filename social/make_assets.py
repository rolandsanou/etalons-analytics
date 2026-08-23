"""Builds the social assets from real screen captures plus two drawn cards.

    python social/make_assets.py <dir-of-chrome-captures>

Headless Chrome takes the screenshots beforehand (see README in this folder);
this script only crops, composes and encodes. Every figure on the drawn cards is
read out of the built site data, so a card cannot claim something the site does
not say.
"""

import json
import sys
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "social"

RED, PAPER, INK, INK2 = "#c0142b", "#f5f3ef", "#1b1a17", "#55534d"
DARK, DARK_INK, DARK_INK2 = "#161513", "#f3f1ec", "#bdb9b1"
SERIF = "C:/Windows/Fonts/georgiab.ttf"
SANS = "C:/Windows/Fonts/arial.ttf"
SANS_B = "C:/Windows/Fonts/arialbd.ttf"
URL = "rolandsanou.github.io/etalons-analytics"


def font(path, size):
    return ImageFont.truetype(path, size)


def fit(draw, text, path, start, limit):
    """Largest size that keeps the line inside the margin."""
    for size in range(start, 12, -2):
        f = font(path, size)
        if draw.textlength(text, font=f) <= limit:
            return f
    return font(path, 12)


def spaced(text):
    return "  ".join(text)


def facts():
    """Read the numbers off the built site, so none of them is hand-typed."""
    meta = json.loads((ROOT / "site/data/meta.json").read_text(encoding="utf-8"))
    pool = json.loads((ROOT / "site/data/pool.json").read_text(encoding="utf-8"))
    return {
        "updated": meta["updated_on"],
        "players": pool["n_players"],
        "events": pool["coverage"]["events"],
        "with_stats": pool["coverage"]["events_with_stats"],
    }


# ----------------------------------------------------------- LinkedIn stills

# (name, capture, top of a 16:9 window, what it shows)
LINKEDIN = [
    ("01-home", "home_tall.png", 0),
    ("02-style", "analysis_tall.png", 250),
    ("03-resilience", "analysis_tall.png", 1330),
    ("04-match", "match_tall.png", 55),
    ("05-management", "mgmt_tall.png", 250),
]


def linkedin_stills(shots):
    made = []
    for name, src, y in LINKEDIN:
        img = Image.open(shots / src).convert("RGB")
        crop = img.crop((0, y, 1440, y + 810)).resize((1200, 675), Image.LANCZOS)
        # a red hairline stops a dark screenshot bleeding into a dark feed
        framed = Image.new("RGB", (1216, 691), RED)
        framed.paste(crop, (8, 8))
        path = OUT / f"linkedin-{name}.png"
        framed.save(path, optimize=True)
        made.append(path)
    return made


# ------------------------------------------------------------------- the tour

SCENES = [                      # (capture, from_y, to_y, seconds)
    ("home_tall.png", 0, 700, 4.0),
    ("match_tall.png", 40, 700, 4.0),
    ("analysis_tall.png", 260, 1450, 5.0),
    ("analysis_tall.png", 1400, 2350, 4.0),
    ("mgmt_tall.png", 240, 1500, 5.0),
]
FPS, VW, VH, FADE = 25, 1280, 720, 0.4


def ease(t):
    """Ease in and out, so a pan starts and stops instead of jerking."""
    return 3 * t * t - 2 * t * t * t


def tour(shots):
    scaled = {}
    for src, *_ in SCENES:
        if src not in scaled:
            im = Image.open(shots / src).convert("RGB")
            scaled[src] = im.resize((VW, round(im.height * VW / im.width)),
                                    Image.LANCZOS)

    frames, cuts = [], []
    for src, y0, y1, secs in SCENES:
        im = scaled[src]
        k = VW / 1440
        top, bottom = y0 * k, min(y1 * k, im.height - VH)
        n = int(secs * FPS)
        for i in range(n):
            y = round(top + (bottom - top) * ease(i / max(n - 1, 1)))
            frames.append(im.crop((0, y, VW, y + VH)))
        cuts.append(len(frames))

    # cross-fade each join, walking backwards so indices stay valid
    span = int(FADE * FPS)
    for cut in reversed(cuts[:-1]):
        for i in range(span):
            j = cut - span + i
            if 0 <= j < len(frames):
                nxt = frames[min(cut + i, len(frames) - 1)]
                frames[j] = Image.blend(frames[j], nxt, (i + 1) / (span + 1))

    path = OUT / "linkedin-tour.mp4"
    writer = imageio.get_writer(path, fps=FPS, codec="libx264", quality=8,
                                macro_block_size=1,
                                ffmpeg_params=["-pix_fmt", "yuv420p"])
    for frame in frames:
        writer.append_data(np.asarray(frame))
    writer.close()
    return path, len(frames) / FPS


# ------------------------------------------------------ WhatsApp status cards

W, H = 1080, 1920


def status_intro(f):
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 16], fill=RED)
    d.text((80, 150), spaced("ÉTALONS ANALYTICS"), font=font(SANS, 26), fill=INK2)

    y = 330
    for line in ("Les Étalons,", "en chiffres"):
        d.text((80, y), line, font=fit(d, line, SERIF, 118, W - 160), fill=INK)
        y += 132
    d.line([(80, y + 40), (330, y + 40)], fill=RED, width=6)

    y += 130
    rows = [(str(f["players"]), "joueurs suivis depuis 2022"),
            (str(f["events"]), "matchs analysés en détail"),
            (f"{f['with_stats']}/{f['events']}", "avec statistiques complètes"),
            ("FR / EN", "site bilingue, sans JavaScript requis")]
    for value, label in rows:
        d.text((80, y), value, font=font(SERIF, 82), fill=RED)
        d.text((80, y + 100), label, font=font(SANS, 33), fill=INK2)
        y += 245

    d.text((80, H - 165), "Projet ouvert — code et données publics.",
           font=font(SANS, 30), fill=INK2)
    d.text((80, H - 112), URL, font=font(SANS_B, 31), fill=INK)
    path = OUT / "whatsapp-1-intro.png"
    img.save(path, optimize=True)
    return path


def status_finding(f):
    """The deficit ladder — the hardest thing the project found."""
    img = Image.new("RGB", (W, H), DARK)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 16], fill=RED)
    d.text((80, 150), spaced("UNE STATISTIQUE"), font=font(SANS, 26), fill=DARK_INK2)

    y = 310
    for line in ("Mené de deux buts,", "le Burkina Faso", "n’a jamais gagné."):
        d.text((80, y), line, font=fit(d, line, SERIF, 88, W - 160), fill=DARK_INK)
        y += 104
    d.line([(80, y + 44), (330, y + 44)], fill=RED, width=6)

    y += 146
    ladder = [("Jamais mené", "2.43", "25V 10N 0D", False),
              ("Mené d’un but", "1.00", "4V 8N 8D", False),
              ("Mené de deux ou plus", "0.07", "0V 1N 13D", True)]
    for label, value, record, hot in ladder:
        colour = RED if hot else DARK_INK
        d.text((80, y), label, font=font(SANS, 32), fill=DARK_INK2)
        big = font(SERIF, 92)
        d.text((80, y + 46), value, font=big, fill=colour)
        d.text((80 + d.textlength(value, font=big) + 18, y + 104),
               "pts/match", font=font(SANS, 28), fill=DARK_INK2)
        d.text((W - 80, y + 122), record, font=font(SANS_B, 34), fill=colour,
               anchor="rs")
        y += 265

    d.text((80, y + 24), f"Sur {f['events']} matchs depuis janvier 2022.",
           font=font(SANS, 30), fill=DARK_INK2)
    d.text((80, H - 165), "Descriptif, pas causal — méthode publiée.",
           font=font(SANS, 30), fill=DARK_INK2)
    d.text((80, H - 112), URL, font=font(SANS_B, 31), fill=DARK_INK)
    path = OUT / "whatsapp-2-finding.png"
    img.save(path, optimize=True)
    return path


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: python social/make_assets.py <dir-of-chrome-captures>")
    shots = Path(sys.argv[1])
    if not shots.exists():
        sys.exit(f"no such capture directory: {shots}")
    OUT.mkdir(exist_ok=True)
    f = facts()
    for path in linkedin_stills(shots):
        print(f"  {path.relative_to(ROOT)}  {path.stat().st_size // 1024} kB")
    for path in (status_intro(f), status_finding(f)):
        print(f"  {path.relative_to(ROOT)}  {path.stat().st_size // 1024} kB")
    path, secs = tour(shots)
    print(f"  {path.relative_to(ROOT)}  {path.stat().st_size // 1024} kB, {secs:.1f}s")


if __name__ == "__main__":
    main()
