import re
from urllib.parse import unquote

from bs4 import BeautifulSoup

DOB_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
FLAG_RE = re.compile(r"Flag_of_(?:the_)?(.+?)\.(?:svg|png|gif)", re.I)
YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")


def _soup(html):
    return BeautifulSoup(html, "lxml")


def _heading(soup, section_id):
    return soup.find(id=section_id)


def _next_table(el, classes=None):
    if el is None:
        return None
    for table in el.find_all_next("table"):
        if classes is None or any(c in (table.get("class") or []) for c in classes):
            return table
    return None


def _flag_country(cell):
    for img in cell.find_all("img"):
        src = unquote(img.get("src", ""))
        m = FLAG_RE.search(src)
        if m:
            return m.group(1).replace("_", " ").strip()
    return None


def parse_players(html, section_id):
    table = _next_table(_heading(_soup(html), section_id))
    players = []
    if table is None:
        return players
    for tr in table.find_all("tr", class_="nat-fs-player"):
        tds = tr.find_all("td")
        th = tr.find("th")
        if th is None or len(tds) < 5:
            continue
        name_link = th.find("a")
        name = (name_link or th).get_text(strip=True)
        # locate the DOB cell: squad tables have a leading shirt-number column,
        # call-up tables do not
        dob_idx = next((i for i, td in enumerate(tds[:4])
                        if DOB_RE.search(td.get_text(" ", strip=True))), None)
        if dob_idx is None or dob_idx < 1 or len(tds) < dob_idx + 4:
            continue
        pos_cell = tds[dob_idx - 1].get_text(strip=True)
        pos = re.sub(r"^\d+", "", pos_cell) or pos_cell
        dob_m = DOB_RE.search(tds[dob_idx].get_text(" ", strip=True))
        caps = tds[dob_idx + 1].get_text(strip=True)
        goals = tds[dob_idx + 2].get_text(strip=True)
        club_cell = tds[dob_idx + 3]
        club_links = [a for a in club_cell.find_all("a") if a.get_text(strip=True)]
        club = club_links[-1].get_text(strip=True) if club_links else club_cell.get_text(strip=True)
        players.append({
            "name": name,
            "pos": pos.upper()[:2],
            "dob": dob_m.group(1) if dob_m else None,
            "caps": int(caps) if caps.isdigit() else 0,
            "goals": int(goals) if goals.isdigit() else 0,
            "club": club,
            "club_country": _flag_country(club_cell),
            "note": tds[dob_idx + 4].get_text(" ", strip=True) if len(tds) > dob_idx + 4 else None,
        })
    return players


def _leaders(table):
    rows = []
    if table is None:
        return rows
    header = [th.get_text(" ", strip=True).lower() for th in table.find("tr").find_all(["th", "td"])]

    def col(*names):
        for n in names:
            for i, h in enumerate(header):
                if n in h:
                    return i
        return None

    i_player, i_caps, i_goals, i_career = col("player", "name"), col("caps"), col("goals"), col("career")
    rank = 0
    for tr in table.find_all("tr")[1:]:
        cells = [c.get_text(" ", strip=True) for c in tr.find_all(["td", "th"])]
        if not cells or i_player is None:
            continue
        offset = 0 if len(cells) == len(header) else len(cells) - len(header)
        try:
            name = cells[i_player + offset]
            caps = cells[i_caps + offset] if i_caps is not None else ""
            goals = cells[i_goals + offset] if i_goals is not None else ""
            career = cells[i_career + offset] if i_career is not None else ""
        except IndexError:
            continue
        if not name or name.lower().startswith("total"):
            continue
        rank += 1
        rows.append({
            "rank": rank,
            "name": name,
            "caps": int(caps) if caps.isdigit() else None,
            "goals": int(goals) if goals.isdigit() else None,
            "career": career,
        })
    return rows[:12]


def parse_leaders(html):
    soup = _soup(html)
    capped = _leaders(_next_table(
        _heading(soup, "Most_capped_players") or _heading(soup, "Most_appearances"),
        classes=["wikitable"]))
    scorers = _leaders(_next_table(_heading(soup, "Top_goalscorers"), classes=["wikitable"]))
    return capped, scorers


def _expand_table(table):
    grid = []
    pending = {}
    for tr in table.find_all("tr"):
        row = []
        col = 0
        cells = tr.find_all(["td", "th"])
        i = 0
        while i < len(cells) or col in pending:
            if col in pending:
                text, rem = pending[col]
                row.append(text)
                if rem > 1:
                    pending[col] = (text, rem - 1)
                else:
                    del pending[col]
                col += 1
                continue
            c = cells[i]
            i += 1
            text = c.get_text(" ", strip=True)
            try:
                rs = int(c.get("rowspan", 1))
                cs = int(c.get("colspan", 1))
            except (TypeError, ValueError):
                rs, cs = 1, 1
            for _ in range(cs):
                row.append(text)
                if rs > 1:
                    pending[col] = (text, rs - 1)
                col += 1
        grid.append(row)
    return grid


def parse_afcon_record(html):
    soup = _soup(html)
    el = _heading(soup, "Africa_Cup_of_Nations_2") or _heading(soup, "Africa_Cup_of_Nations_record")
    table = _next_table(el, classes=["wikitable"])
    if table is None:
        return []
    editions = []
    try:
        grid = _expand_table(table)
    except Exception:
        return []
    for row in grid[1:]:
        if len(row) < 2:
            continue
        ym = YEAR_RE.search(row[0])
        if not ym:
            continue
        round_ = row[1]
        low = round_.lower()
        if any(s in low for s in ("did not", "withdrew", "banned", "to be determined",
                                  "qualified", "part of", "not affiliated", "declined")):
            continue
        editions.append({"year": int(ym.group(0)), "round": round_})
    return editions


TENURE_RE = re.compile(r"^(.*?)\s*\(\s*(\d{4})\s*(?:[–\-—]\s*(\d{4})?)?\s*\)\s*$")


def parse_coaching_history(html):
    soup = _soup(html)
    el = _heading(soup, "Coaching_history")
    ul = el.find_next("ul") if el else None
    if ul is None:
        return []
    rows = []
    for li in ul.find_all("li"):
        m = TENURE_RE.match(li.get_text(" ", strip=True))
        if not m:
            continue
        name, start, end = m.group(1).strip(), m.group(2), m.group(3)
        has_dash = "–" in li.get_text() or "-" in li.get_text().split("(")[-1]
        rows.append({
            "coach": name,
            "start_year": int(start),
            "end_year": (int(end) if end else (None if has_dash else int(start))),
        })
    return rows


def parse_as_of(html):
    soup = _soup(html)
    m = soup.find(string=re.compile(r"Caps and goals (?:are )?correct as of", re.I))
    if m:
        return re.sub(r"\s+", " ", m.find_parent().get_text(" ", strip=True))
    return None
