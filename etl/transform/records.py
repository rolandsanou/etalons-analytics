"""Reference tables parsed out of the team page into staging.

Keeps the load layer free of any dependency on `data/raw/` (which is gitignored),
so marts and dashboard data rebuild from committed staging alone.
"""

from ..config import RAW, STAGING
from ..parsers.wikipedia import (parse_afcon_record, parse_as_of, parse_coaching_history,
                                 parse_leaders)
from ..util import write_json


def run():
    html = (RAW / "wikipedia" / "team_page.html").read_text(encoding="utf-8")
    capped, scorers = parse_leaders(html)
    write_json(STAGING / "reference.json", {
        "as_of": parse_as_of(html),
        "most_capped": capped,
        "top_scorers": scorers,
        "afcon_record": parse_afcon_record(html),
        "coaching_history": parse_coaching_history(html),
    })
