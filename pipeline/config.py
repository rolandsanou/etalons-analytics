from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = ROOT / "data" / "raw"
SITE_DATA = ROOT / "site" / "data"

WIKI_URL = "https://en.wikipedia.org/wiki/Burkina_Faso_national_football_team"
RESULTS_URL = "https://raw.githubusercontent.com/martj42/international_results/master/results.csv"
FORMER_NAMES_URL = "https://raw.githubusercontent.com/martj42/international_results/master/former_names.csv"

TEAM = "Burkina Faso"

# tournament reference dates (AFCON 2027 dates not final yet: mid-2027 assumption)
AFCON_2027 = date(2027, 7, 1)
WC_2030 = date(2030, 6, 15)

USER_AGENT = "etalons-analytics/0.1 (open-source data pipeline)"

TOP5_LEAGUES = {"England", "Spain", "Italy", "Germany", "France"}

# rough peak-age windows by position, inclusive
PEAK_WINDOW = {"GK": (26, 33), "DF": (25, 30), "MF": (24, 29), "FW": (24, 29)}
