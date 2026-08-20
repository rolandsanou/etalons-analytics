import argparse
import json
from datetime import date, datetime

from . import analytics, elo, parse_squad, results
from .config import (FORMER_NAMES_URL, RESULTS_URL, SITE_DATA, TEAM, WIKI_URL)
from .fetch import fetch


def write(name, obj):
    SITE_DATA.mkdir(parents=True, exist_ok=True)
    path = SITE_DATA / name
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {path} ({path.stat().st_size // 1024} KB)")


def main(force=False):
    today = date.today()
    wiki_path = fetch(WIKI_URL, "wikipedia_bfa.html", force)
    results_path = fetch(RESULTS_URL, "results.csv", force)
    former_path = fetch(FORMER_NAMES_URL, "former_names.csv", force)

    page = parse_squad.parse_page(wiki_path.read_text(encoding="utf-8"))
    squad = analytics.enrich_players(page["squad"], today)
    callups = analytics.enrich_players(page["callups"], today)
    print(f"squad: {len(squad)} players, call-ups: {len(callups)}, "
          f"capped: {len(page['most_capped'])}, scorers: {len(page['top_scorers'])}")

    df = results.load_results(results_path, former_path)
    bf = results.team_matches(df, TEAM)
    print(f"matches: {len(bf)} ({bf.date.min().date()} -> {bf.date.max().date()})")

    elo_data = elo.run_elo(df, TEAM)

    write("squad.json", {
        "as_of": page["as_of"],
        "players": squad,
        "callups": callups,
        "stats": analytics.squad_stats(squad),
        "core_generation": analytics.core_generation(squad + [p for p in callups if p["name"] not in {q["name"] for q in squad}]),
    })
    write("history.json", {
        **results.history_stats(bf),
        "most_capped": page["most_capped"],
        "top_scorers": page["top_scorers"],
        "afcon_record": page["afcon_record"],
    })
    write("elo.json", analytics.elo_summary(elo_data))
    write("meta.json", {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "team": TEAM,
        "sources": {
            "squad": WIKI_URL,
            "results": "https://github.com/martj42/international_results",
        },
    })


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="re-download sources")
    args = ap.parse_args()
    main(force=args.force)
