# Social assets

The images and the video are **generated**, not hand-made, so they can be redrawn
whenever the site changes. Only the scripts and the post copy are committed; the
media is gitignored, since it is derived and heavy.

## What is here

| File | Use |
|---|---|
| `linkedin-post.md` | two versions of the post text, plus carousel captions |
| `linkedin-tour.mp4` | 22 s, 1280×720, H.264 — a pan through five real pages |
| `linkedin-01..05-*.png` | 1216×691 stills, framed in the accent red |
| `whatsapp-1-intro.png` | 1080×1920 status card — what the project is |
| `whatsapp-2-finding.png` | 1080×1920 status card — the deficit ladder |

## Regenerating

Two steps: capture, then compose. Capture uses headless Chrome against the live
site, so what you get is genuinely what a visitor sees.

```bash
# 1. capture — adjust the heights if a page has grown
SHOTS=/tmp/shots && mkdir -p "$SHOTS"
CHROME="/c/Program Files/Google/Chrome/Application/chrome.exe"
B=https://rolandsanou.github.io/etalons-analytics

shot () {
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars \
            --virtual-time-budget=12000 --window-size="$2" \
            --screenshot="$(cygpath -w "$SHOTS/$1.png")" "$3"
}
shot home_tall     "1440,3400" "$B/en/"
shot players_tall  "1440,3000" "$B/en/players.html"
shot match_tall    "1440,2600" "$B/en/matches/2026-01-06-cote-d-ivoire.html"
shot analysis_tall "1440,3600" "$B/en/analysis.html"
shot mgmt_tall     "1440,3200" "$B/en/management.html"
```

```bash
# 2. compose
pip install pillow imageio imageio-ffmpeg
python social/make_assets.py "$SHOTS"
```

`--virtual-time-budget` is what lets the charts finish drawing before the shutter
closes; drop it and the hub pages come out blank. The window height has to exceed
the page height, because a headless screenshot captures the viewport — measure
with the content-end scan in the script if a page has grown.

The captures come out in dark mode, following the machine's own system setting.
That is a deliberate choice for social — dark reads better in a feed — but the
site itself follows each visitor's preference.

## The rule these follow

The figures on the drawn cards are read out of `site/data/*.json` at build time,
never typed into the script. A card cannot claim something the site does not say,
and when the data moves the cards move with it.
