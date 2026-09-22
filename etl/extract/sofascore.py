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


# Words that appear in a club's formal name but not in how anyone refers to it.
# "FC Rapid Bucuresti" and "Rapid Bucuresti" are the same club.
CLUB_NOISE = {"fc", "sc", "ac", "cf", "sk", "fk", "ss", "as", "us", "if", "bk",
              "club", "de", "del", "the", "football", "futbol", "calcio"}
# How many parts of a name must agree exactly before two spellings are taken to
# be the same person. One is a surname, which half of Burkina shares.
MIN_SHARED_PARTS = 2


def _club_key(club):
    return {w for w in norm_name(club).split() if w and w not in CLUB_NOISE}


def _same_club(a, b):
    """One club name contains the other, once formal noise is dropped."""
    ka, kb = _club_key(a), _club_key(b)
    return bool(ka and kb and (ka <= kb or kb <= ka))


def _name_compatible(candidate, known):
    """Two names share at least two parts exactly, ignoring order and accents.

    Federations publish full civil names; Sofascore carries shorter, reordered
    and sometimes misspelt ones — "Taonsa Axel" for "Axel Sountonoma Taonsa",
    "Chec Bebel Doumbia" for "Cheick Bebel Doumbia". Requiring every part to
    line up rejects both; requiring one part accepts anyone who shares a
    surname. Two exact parts is the rule that takes the real people and still
    refuses "Moise Kabore" when the search was for Elohim Kabore.
    """
    cand = set(norm_name(candidate).split())
    mine = set(norm_name(known).split())
    return len(cand & mine) >= MIN_SHARED_PARTS


def club_backed_match(search_data, name, club):
    """Accept a near-name match only when the club independently agrees.

    Two weak signals that cannot both be coincidence: the search was for a
    Burkinabe international, and the player it returned is at the exact club the
    federation listed beside that name. Neither is trusted on its own.
    """
    if not club:
        return None
    for r in search_data.get("results", []):
        if r.get("type") != "player":
            continue
        ent = r.get("entity", {})
        if (ent.get("country") or {}).get("alpha2") != "BF":
            continue
        if not _same_club((ent.get("team") or {}).get("name", ""), club):
            continue
        if _name_compatible(ent.get("name", ""), name):
            return ent.get("id")
    return None


def name_variants(name):
    """Shorter forms to try when the full civil name returns nothing."""
    parts = norm_name(name).split()
    if len(parts) < 3:
        return []
    seen, out = set(), []
    for v in (f"{parts[0]} {parts[-1]}", " ".join(parts[-2:]), parts[-1]):
        if v not in seen and v != norm_name(name):
            seen.add(v)
            out.append(v)
    return out


def _profile_targets():
    ids, unlinked = set(), []
    players_path = STAGING / "players.csv"
    if players_path.exists():
        for r in read_csv(players_path):
            if r.get("sofa_id"):
                ids.add(str(r["sofa_id"]))
            else:
                # the club travels with the name: it is the second, independent
                # signal that lets a shortened name be accepted safely below
                unlinked.append((r["player_id"], r["name"], r.get("club", "")))
    seed_path = SEED / "sofa_ids.csv"
    if seed_path.exists():
        for r in read_csv(seed_path):
            if r.get("sofa_id"):
                ids.add(str(r["sofa_id"]))
    return ids, unlinked


def _cached_search(dest, query, force=False):
    if not dest.exists() or force:
        try:
            data = get_sofa_json(f"{SOFA_BASE}/search/all?q={quote(query)}")
        except Exception as e:
            data = {"error": str(e)}
        write_json(dest, {"fetched_at": datetime.now().isoformat(timespec="seconds"),
                          "data": data})
    return read_json(dest).get("data", {})


def _variant_path(pid, variant):
    return SEARCH_DIR / f"{pid}--{variant.replace(' ', '-')}.json"


def resolve_from_cache(pid, name, club):
    """The Sofascore id for a player, from searches already on disk.

    Extract and transform have to reach the same verdict — one to know which
    profile to download, the other to know whose profile it is. When that rule
    existed in both places they disagreed, and a player the extractor had
    correctly identified was still written out with no club, no league and no
    form. So the rule lives here, once, and both call it.

    The full civil name is accepted on its own, because an exact match needs no
    corroboration. A shortened form is accepted only with the club agreeing as
    well.
    """
    dest = SEARCH_DIR / f"{pid}.json"
    if dest.exists():
        sid = search_match(read_json(dest).get("data", {}), name)
        if sid:
            return sid
    for variant in name_variants(name):
        cached = _variant_path(pid, variant)
        if cached.exists():
            sid = club_backed_match(read_json(cached).get("data", {}), name, club)
            if sid:
                return sid
    return None


def resolve_sofa_ids(unlinked, force=False):
    """Search for every unlinked player, then resolve from what came back.

    Anything still unmatched is left unmatched: data/seed/sofa_ids.csv is where
    a human settles the cases a rule should not guess at.
    """
    SEARCH_DIR.mkdir(parents=True, exist_ok=True)
    accepted = set()
    for pid, name, club in unlinked:
        _cached_search(SEARCH_DIR / f"{pid}.json", name, force)
        if not search_match(read_json(SEARCH_DIR / f"{pid}.json").get("data", {}), name):
            for variant in name_variants(name):
                _cached_search(_variant_path(pid, variant), variant, force)
                if club_backed_match(read_json(_variant_path(pid, variant))
                                     .get("data", {}), name, club):
                    break
        sid = resolve_from_cache(pid, name, club)
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


def fetch_club_form(force=False, also=()):
    """Club form for every active linked player, and for `also`.

    players.csv is written by the transform, so a player linked during THIS run
    is not in it yet and would wait a whole further pass for his club form —
    which is exactly the data a newly called-up player is on the page for. The
    ids just resolved are therefore passed in directly.
    """
    CLUB_FORM_DIR.mkdir(parents=True, exist_ok=True)
    players_path = STAGING / "players.csv"
    known = ({p["sofa_id"]: p for p in read_csv(players_path) if p.get("sofa_id")}
             if players_path.exists() else {})
    targets = [p for p in known.values() if p.get("status") in ("active", "fringe")]
    targets += [{"sofa_id": sid} for sid in sorted(set(map(str, also)))
                if sid not in known]
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
    linked_now = resolve_sofa_ids(unlinked, force=force)
    ids |= linked_now

    # A played match never changes, so lineups, incidents and statistics stay
    # cached whatever is asked of them. Profiles and club form DO change — a
    # transfer moves a player mid-window, and club, market value and contract
    # come from the profile — so they are the only caches a force flag reaches.
    # Both calls used to pass force=False outright, which is why --force could
    # never refresh a club.
    refresh = force or force_profiles
    n_profiles = fetch_player_profiles(ids, force=refresh)
    n_club = fetch_club_form(force=refresh, also=linked_now)
    forced = " (forced)" if refresh else f" (cache kept under {PROFILE_MAX_AGE_DAYS}d)"
    print(f"sofascore: {len(index)} events in window, {fetched} lineups fetched, "
          f"{n_profiles} player profiles fetched/refreshed{forced}, "
          f"{len(unlinked)} players searched, {n_club} club-form files "
          f"fetched/refreshed, fixtures checked: {bool(n_fix)}")
