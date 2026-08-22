from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"

RAW = ROOT / "data" / "raw"
STAGING = ROOT / "data" / "staging"
MARTS = ROOT / "data" / "marts"
SEED = ROOT / "data" / "seed"
SITE_DATA = ROOT / "site" / "data"

TEAM = "Burkina Faso"

WIKI_TEAM_URL = "https://en.wikipedia.org/wiki/Burkina_Faso_national_football_team"
RESULTS_URL = "https://raw.githubusercontent.com/martj42/international_results/master/results.csv"
FORMER_NAMES_URL = "https://raw.githubusercontent.com/martj42/international_results/master/former_names.csv"
SHOOTOUTS_URL = "https://raw.githubusercontent.com/martj42/international_results/master/shootouts.csv"

SOFA_BASE = "https://www.sofascore.com/api/v1"
SOFA_TEAM_ID = 4749
SOFA_SLEEP = 1.3
PROFILE_MAX_AGE_DAYS = 30
# A calendar changes far more often than a played match, and it is one request.
FIXTURES_MAX_AGE_DAYS = 1

# study window: every call-up since AFCON 2021 (played January 2022)
STATS_SINCE = date(2022, 1, 1)

# tournament reference dates (AFCON 2027 dates not final yet: mid-2027 assumption)
AFCON_2027 = date(2027, 7, 1)
WC_2030 = date(2030, 6, 15)

USER_AGENT = "etalons-analytics/0.2 (open-source data pipeline)"

# published on the site so readers can report an error or offer data
CONTACT_EMAIL = "rolandS01@outlook.fr"

TOP5_LEAGUES = {"England", "Spain", "Italy", "Germany", "France"}

# rough peak-age windows by position, inclusive
PEAK_WINDOW = {"GK": (26, 33), "DF": (25, 30), "MF": (24, 29), "FW": (24, 29)}
