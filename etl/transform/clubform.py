from ..config import RAW, STAGING
from ..util import read_json, write_csv

CLUB_FORM_FIELDS = ["player_id", "sofa_id", "tournament", "season_year",
                    "apps", "starts", "minutes", "rating", "as_of"]


def run(registry):
    sofa2pid = {str(p["sofa_id"]): pid for pid, p in registry.items() if p["sofa_id"]}
    folder = RAW / "sofascore" / "club_form"
    rows = []
    if folder.exists():
        for f in sorted(folder.glob("*.json")):
            data = read_json(f)
            pick = data.get("pick")
            st = data.get("statistics") or {}
            pid = sofa2pid.get(f.stem, "")
            if not pick or not pid:
                continue
            rows.append({
                "player_id": pid, "sofa_id": f.stem,
                "tournament": pick["tournament"], "season_year": pick["year"],
                "apps": st.get("appearances", 0),
                "starts": st.get("matchesStarted", 0),
                "minutes": st.get("minutesPlayed", 0),
                "rating": round(st["rating"], 2) if st.get("rating") else "",
                "as_of": data.get("fetched_at", "")[:10],
            })
    rows.sort(key=lambda r: r["player_id"])
    write_csv(STAGING / "club_form.csv", rows, CLUB_FORM_FIELDS)
