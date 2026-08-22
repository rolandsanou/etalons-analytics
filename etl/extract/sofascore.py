import re
from datetime import date, datetime, timezone
from urllib.parse import quote

from ..config import (FIXTURES_MAX_AGE_DAYS, PROFILE_MAX_AGE_DAYS, RAW, SEED,
                      SOFA_BASE, SOFA_TEAM_ID, STAGING, STATS_SINCE)
from ..http import get_sofa_json
from ..util import norm_name, read_csv, read_json, write_json

OUT = RAW / "sofascore"
LINEUPS = OUT / "lineups"
INCIDENTS = OUT / "incidents"
STATISTICS = OUT / "statistics"
PLAYERS_DIR = OUT / "players"
SEARCH_DIR = OUT / "search"
CLUB_FORM_DIR = OUT / "club_form"

NT_COMP_RE = re.compile(r"africa cup|world cup|friendl|wafu|cosafa|african nations"
                        r"|olympic|nations league|world championship"
                        r"|\bu-?1[5-9]\b|\bu-?2[0-3]\b", re.I)
CUP_RE = re.compile(r"cup|kupa|coupe|pokal|beker|ta[cç]a|copa|champions league"
                    r"|europa|conference", re.I)


def season_start_year(year):
    """Sortable start year for a season label: '25/26' -> 2025, '2026' -> 2026.

    Returns -1 for anything unparseable so it sorts behind every real season
    rather than ahead of them.
    """
    y = str(year or "").strip()
    if "/" in y:
        head = y.split("/")[0]
        return 2000 + int(head) if head.isdigit() and len(head) <= 2 else -1
    return int(y) if y.isdigit() else -1


def pick_baseline_season(seasons_data, before_year, exclude=()):
    """The player's most recent *completed* club season, wherever it was played.

    A figure from a league that restarted a fortnight ago means nothing on its
    own, so a settled season travels beside it. Searching every club competition
    rather than only the current one matters for a transfer: a player in their
    first season at a new club has nothing behind them there, while their last
    real campaign sits in their old league. Only seasons starting strictly before
    the reported one qualify, which is what makes them complete; within a year a
    league ranks ahead of a cup, because a four-match cup run is not a baseline.
    """
    cands = []
    for ut in seasons_data.get("uniqueTournamentSeasons", []):
        name = (ut.get("uniqueTournament") or {}).get("name", "")
        if NT_COMP_RE.search(name):
            continue
        ut_id = (ut.get("uniqueTournament") or {}).get("id")
        for season in ut.get("seasons") or []:
            start = season_start_year(season.get("year"))
            if start < 0 or start >= before_year:
                continue
            if (ut_id, season["id"]) in exclude:
                continue
            cands.append({"tournament": name, "ut_id": ut_id,
                          "season_id": season["id"], "year": season.get("year", ""),
                          "_start": start, "_cup": bool(CUP_RE.search(name))})
    if not cands:
        return None
    cands.sort(key=lambda c: (-c["_start"], c["_cup"]))
    return {k: v for k, v in cands[0].items() if not k.startswith("_")}


def pick_club_seasons(seasons_data, limit=3):
    """Latest season of club tournaments, leagues before cups, listed order kept."""
    cands = []
    for ut in seasons_data.get("uniqueTournamentSeasons", []):
        name = (ut.get("uniqueTournament") or {}).get("name", "")
        if NT_COMP_RE.search(name):
            continue
        seasons = ut.get("seasons") or []
        if not seasons:
            continue
        cands.append({
            "tournament": name,
            "ut_id": ut["uniqueTournament"]["id"],
            "season_id": seasons[0]["id"],
            "year": seasons[0].get("year", ""),
        })
    cands.sort(key=lambda c: bool(CUP_RE.search(c["tournament"])))
    return cands[:limit]


def _real_score(score):
    # "current" includes penalty-shootout goals; the match score excludes them
    cur = score.get("current")
    if cur is None:
        return None, 0
    pens = score.get("penalties") or 0
    return cur - pens, pens


def _event_row(e):
    ts = e["startTimestamp"]
    home, home_pens = _real_score(e.get("homeScore", {}))
    away, away_pens = _real_score(e.get("awayScore", {}))
    return {
        "event_id": e["id"],
        "date": datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d"),
        "ts": ts,
        "tournament": e["tournament"]["name"],
        "home_id": e["homeTeam"]["id"],
        "home": e["homeTeam"]["name"],
        "away_id": e["awayTeam"]["id"],
        "away": e["awayTeam"]["name"],
        "home_score": home,
        "away_score": away,
        "home_pens": home_pens,
        "away_pens": away_pens,
        "status": e.get("status", {}).get("type"),
    }


def fetch_events_index(force=False):
    index_path = OUT / "events_index.json"
    if index_path.exists() and not force:
        return read_json(index_path)
    since_ts = int(datetime(STATS_SINCE.year, STATS_SINCE.month, STATS_SINCE.day,
                            tzinfo=timezone.utc).timestamp())
    rows = []
    page = 0
    while True:
        data = get_sofa_json(f"{SOFA_BASE}/team/{SOFA_TEAM_ID}/events/last/{page}")
        events = data.get("events", [])
        if not events:
            break
        rows.extend(_event_row(e) for e in events)
        oldest = min(e["startTimestamp"] for e in events)
        if oldest < since_ts or not data.get("hasNextPage"):
            break
        page += 1
    rows = [r for r in rows
            if r["ts"] >= since_ts and r["status"] == "finished"
            and r["home_score"] is not None]
    rows.sort(key=lambda r: r["ts"])
    write_json(index_path, rows)
    return rows


def fetch_fixtures(force=False):
    """Scheduled matches, when the source has published any.

    This endpoint answers 404 when a team has nothing upcoming, which is
    information rather than a failure — it is recorded as an empty list so the
    site can say "no fixtures published" from a real answer instead of from a
    request that fell over. Anything else is kept as an error so a genuine
    outage does not masquerade as an empty calendar.
    """
    dest = OUT / "fixtures.json"
    if dest.exists() and not force:
        stamp = read_json(dest).get("fetched_at", "")[:10]
        try:
            if (date.today() - date.fromisoformat(stamp)).days <= FIXTURES_MAX_AGE_DAYS:
                return 0
        except ValueError:
            pass
    payload = {"fetched_at": datetime.now().isoformat(timespec="seconds"),
               "events": []}
    try:
        data = get_sofa_json(f"{SOFA_BASE}/team/{SOFA_TEAM_ID}/events/next/0")
        payload["events"] = [_event_row(e) for e in data.get("events", [])]
    except Exception as e:
        if "HTTP 404" not in str(e):
            payload["error"] = str(e)
    write_json(dest, payload)
    return 1


def search_match(search_data, name):
    """Auto-accept only an exact normalized-name match on a Burkinabè player."""
    for r in search_data.get("results", []):
        if r.get("type") != "player":
            continue
        ent = r.get("entity", {})
        country = (ent.get("country") or {}).get("alpha2")
        if norm_name(ent.get("name", "")) == norm_name(name) and country == "BF":
            return ent.get("id")
    return None


def _profile_targets():
    ids, unlinked = set(), []
    players_path = STAGING / "players.csv"
    if players_path.exists():
        for r in read_csv(players_path):
            if r.get("sofa_id"):
                ids.add(str(r["sofa_id"]))
            else:
                unlinked.append((r["player_id"], r["name"]))
    seed_path = SEED / "sofa_ids.csv"
    if seed_path.exists():
        for r in read_csv(seed_path):
            if r.get("sofa_id"):
                ids.add(str(r["sofa_id"]))
    return ids, unlinked


def resolve_sofa_ids(unlinked, force=False):
    SEARCH_DIR.mkdir(parents=True, exist_ok=True)
    accepted = set()
    for pid, name in unlinked:
        dest = SEARCH_DIR / f"{pid}.json"
        if not dest.exists() or force:
            try:
                data = get_sofa_json(f"{SOFA_BASE}/search/all?q={quote(name)}")
            except Exception as e:
                data = {"error": str(e)}
            write_json(dest, {"fetched_at": datetime.now().isoformat(timespec="seconds"),
                              "data": data})
        cached = read_json(dest)
        sid = search_match(cached.get("data", {}), name)
        if sid:
            accepted.add(str(sid))
    return accepted


def fetch_player_profiles(ids, force=False):
    PLAYERS_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today()
    fetched = 0
    for sid in sorted(ids):
        dest = PLAYERS_DIR / f"{sid}.json"
        if dest.exists() and not force:
            stamp = read_json(dest).get("fetched_at", "")[:10]
            try:
                if (today - date.fromisoformat(stamp)).days <= PROFILE_MAX_AGE_DAYS:
                    continue
            except ValueError:
                pass
        try:
            data = get_sofa_json(f"{SOFA_BASE}/player/{sid}")
        except Exception as e:
            data = {"error": str(e)}
        write_json(dest, {"fetched_at": datetime.now().isoformat(timespec="seconds"),
                          "data": data})
        fetched += 1
    return fetched


def fetch_incidents(index):
    INCIDENTS.mkdir(parents=True, exist_ok=True)
    fetched = 0
    for ev in index:
        dest = INCIDENTS / f"{ev['event_id']}.json"
        if dest.exists():
            continue
        try:
            data = get_sofa_json(f"{SOFA_BASE}/event/{ev['event_id']}/incidents")
        except Exception as e:
            data = {"error": str(e)}
        write_json(dest, data)
        fetched += 1
    return fetched


def fetch_statistics(index):
    """Team match statistics per event (immutable once played)."""
    STATISTICS.mkdir(parents=True, exist_ok=True)
    fetched = 0
    for ev in index:
        dest = STATISTICS / f"{ev['event_id']}.json"
        if dest.exists():
            continue
        try:
            data = get_sofa_json(f"{SOFA_BASE}/event/{ev['event_id']}/statistics")
        except Exception as e:
            data = {"error": str(e)}
        write_json(dest, data)
        fetched += 1
    return fetched


# Shape of a cached club-form file. Bump it when fields are added, so files
# written by an older build are re-read once instead of sitting there incomplete
# until the 30-day clock happens to expire.
CLUB_FORM_SCHEMA = 3


def fetch_club_form(force=False):
    CLUB_FORM_DIR.mkdir(parents=True, exist_ok=True)
    players_path = STAGING / "players.csv"
    if not players_path.exists():
        return 0
    targets = [p for p in read_csv(players_path)
               if p.get("sofa_id") and p.get("status") in ("active", "fringe")]
    today = date.today()
    fetched = 0
    for p in targets:
        sid = str(p["sofa_id"])
        dest = CLUB_FORM_DIR / f"{sid}.json"
        if dest.exists() and not force:
            cached = read_json(dest)
            stamp = cached.get("fetched_at", "")[:10]
            fresh = False
            try:
                fresh = (today - date.fromisoformat(stamp)).days <= PROFILE_MAX_AGE_DAYS
            except ValueError:
                pass
            # a file written before the previous-season fields existed has to be
            # re-read once, however fresh it is, or it would never gain them
            current_shape = cached.get("schema") == CLUB_FORM_SCHEMA
            # a cached zero-minute pick may just be the wrong competition — retry
            if fresh and current_shape and (cached.get("statistics") or {}).get("minutesPlayed"):
                continue
            if fresh and current_shape and cached.get("pick") is None \
                    and "error" not in cached:
                continue
        payload = {"fetched_at": datetime.now().isoformat(timespec="seconds"),
                   "schema": CLUB_FORM_SCHEMA}
        seasons_payload = None
        try:
            seasons_payload = get_sofa_json(
                f"{SOFA_BASE}/player/{sid}/statistics/seasons")
            best = None
            for pick in pick_club_seasons(seasons_payload):
                st = get_sofa_json(
                    f"{SOFA_BASE}/player/{sid}/unique-tournament/{pick['ut_id']}"
                    f"/season/{pick['season_id']}/statistics/overall").get("statistics", {})
                if best is None:
                    best = (pick, st)
                if st.get("minutesPlayed"):
                    best = (pick, st)
                    break
            payload["pick"] = best[0] if best else None
            if best:
                payload["statistics"] = best[1]
        except Exception as e:
            payload["error"] = str(e)
        # One extra request, in its own guard: the baseline is worth having but
        # never worth losing the current season's figures over.
        pick = payload.get("pick") or {}
        if pick and seasons_payload is not None:
            try:
                base = pick_baseline_season(
                    seasons_payload, season_start_year(pick.get("year")),
                    exclude={(pick.get("ut_id"), pick.get("season_id"))})
                if base:
                    payload["pick_prev"] = base
                    payload["statistics_prev"] = get_sofa_json(
                        f"{SOFA_BASE}/player/{sid}/unique-tournament/{base['ut_id']}"
                        f"/season/{base['season_id']}/statistics/overall"
                    ).get("statistics", {})
            except Exception as e:
                payload["prev_error"] = str(e)
        write_json(dest, payload)
        fetched += 1
    return fetched


def run(force=False, force_profiles=False):
    OUT.mkdir(parents=True, exist_ok=True)
    LINEUPS.mkdir(parents=True, exist_ok=True)
    index = fetch_events_index(force=force)
    n_fix = fetch_fixtures(force=force)
    fetched = 0
    for ev in index:
        dest = LINEUPS / f"{ev['event_id']}.json"
        if dest.exists():
            continue
        try:
            data = get_sofa_json(f"{SOFA_BASE}/event/{ev['event_id']}/lineups")
        except Exception as e:
            data = {"error": str(e)}
        write_json(dest, data)
        fetched += 1
    n_inc = fetch_incidents(index)
    n_stats = fetch_statistics(index)
    print(f"sofascore: {n_inc} incident files, {n_stats} statistics files fetched")
    ids, unlinked = _profile_targets()
    ids |= resolve_sofa_ids(unlinked, force=force)

    # A played match never changes, so lineups, incidents and statistics stay
    # cached whatever is asked of them. Profiles and club form DO change — a
    # transfer moves a player mid-window, and club, market value and contract
    # come from the profile — so they are the only caches a force flag reaches.
    # Both calls used to pass force=False outright, which is why --force could
    # never refresh a club.
    refresh = force or force_profiles
    n_profiles = fetch_player_profiles(ids, force=refresh)
    n_club = fetch_club_form(force=refresh)
    forced = " (forced)" if refresh else f" (cache kept under {PROFILE_MAX_AGE_DAYS}d)"
    print(f"sofascore: {len(index)} events in window, {fetched} lineups fetched, "
          f"{n_profiles} player profiles fetched/refreshed{forced}, "
          f"{len(unlinked)} players searched, {n_club} club-form files "
          f"fetched/refreshed, fixtures checked: {bool(n_fix)}")
