"""Loads the committed staging/marts tables the page builders need."""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
STAGING = ROOT / "data" / "staging"
MARTS = ROOT / "data" / "marts"
SITE_DATA = ROOT / "site" / "data"


def rows(path):
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def doc(name):
    return json.loads((SITE_DATA / f"{name}.json").read_text(encoding="utf-8"))


class Data:
    """Everything the generator reads, loaded once."""

    def __init__(self):
        self.players = rows(STAGING / "players.csv")
        self.appearances = rows(STAGING / "appearances.csv")
        self.events = rows(STAGING / "events.csv")
        self.matches = rows(STAGING / "matches.csv")
        self.goals = rows(STAGING / "goal_events.csv")
        self.subs = rows(STAGING / "substitutions.csv")
        self.cards = rows(STAGING / "cards.csv")
        self.states = rows(STAGING / "match_states.csv")
        self.team_stats = rows(STAGING / "team_match_stats.csv")
        self.photos = rows(STAGING / "photos.csv")
        # may legitimately be empty, and is absent on a tree built before the
        # fixtures step existed
        fx = STAGING / "fixtures.csv"
        self.fixtures = rows(fx) if fx.exists() else []
        self.profiles = rows(MARTS / "player_profile.csv")
        self.importance = rows(MARTS / "player_importance.csv")
        self.bench = rows(MARTS / "bench_impact.csv")
        self.coach_eras = rows(MARTS / "coach_eras.csv")
        self.meta = doc("meta")
        self.team = doc("team")
        self.history = doc("history")
        self.elo = doc("elo")
        self.squad = doc("squad")
        self.pool = doc("pool")

        self.photo_by = {(p["kind"], p["slug"]): p for p in self.photos}
        self.profile_by = {p["player_id"]: p for p in self.profiles}
        self.importance_by = {r["player_id"]: r for r in self.importance}
        self.bench_by = {r["player_id"]: r for r in self.bench}
        self.event_by = {e["event_id"]: e for e in self.events}
        self.state_by = {s["event_id"]: s for s in self.states}

    def photo(self, kind, slug):
        p = self.photo_by.get((kind, slug))
        return p["local_path"] if p else None

    def photo_credit(self, kind, slug):
        return self.photo_by.get((kind, slug))

    def apps_for_player(self, player_id):
        return [a for a in self.appearances if a["player_id"] == player_id]

    def apps_for_event(self, event_id):
        return [a for a in self.appearances if a["event_id"] == event_id]

    def goals_for_event(self, event_id):
        return [g for g in self.goals if g["event_id"] == event_id]

    def subs_for_event(self, event_id):
        return [s for s in self.subs if s["event_id"] == event_id]

    def cards_for_event(self, event_id):
        return [c for c in self.cards if c["event_id"] == event_id]

    def stats_for_event(self, event_id, period="ALL"):
        out = {}
        for r in self.team_stats:
            if r["event_id"] == event_id and r["period"] == period:
                out[r["side"]] = r
        return out
