import time

import requests

from .config import SOFA_SLEEP, USER_AGENT

try:
    from curl_cffi import requests as curl_requests
except ImportError:
    curl_requests = None


# Sofascore accepts some TLS fingerprints and refuses others, and which is
# which changes without notice: every Chrome profile began answering 403 in
# late September 2026 while Safari kept working unchanged. One hard-coded
# profile means the pipeline stops the day that profile is added to the list —
# and stops *quietly*, because the refresh still runs, still passes its gates
# and still publishes, having simply learned nothing. So several profiles are
# tried in order and the first that answers is reused for the rest of the run.
SOFA_PROFILES = ("chrome", "safari170", "safari155", "chrome146", "chrome131")

_working = None


def get_bytes(url, timeout=60):
    r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout)
    r.raise_for_status()
    return r.content


def _profiles():
    """The profile that last worked first, then the rest as fallbacks."""
    if _working is None:
        return SOFA_PROFILES
    return (_working,) + tuple(p for p in SOFA_PROFILES if p != _working)


def get_sofa_json(url, retries=2):
    global _working
    if curl_requests is None:
        raise RuntimeError("curl_cffi is required for the Sofascore extractor "
                           "(pip install curl_cffi)")
    last = None
    for attempt in range(retries + 1):
        for profile in _profiles():
            try:
                r = curl_requests.get(url, impersonate=profile, timeout=40)
            except Exception as e:
                last = e
                continue
            if r.status_code == 200:
                if _working != profile:
                    print(f"sofascore: using the {profile} client profile")
                    _working = profile
                time.sleep(SOFA_SLEEP)
                return r.json()
            last = RuntimeError(f"HTTP {r.status_code} for {url}")
            # 404 is an answer, not a refusal — another profile will not change
            # it, and trying them all would turn every absent record into five
            # pointless requests.
            if r.status_code == 404:
                raise last
        time.sleep(SOFA_SLEEP * (attempt + 2))
    raise last
