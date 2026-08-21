import time

import requests

from .config import SOFA_SLEEP, USER_AGENT

try:
    from curl_cffi import requests as curl_requests
except ImportError:
    curl_requests = None


def get_bytes(url, timeout=60):
    r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout)
    r.raise_for_status()
    return r.content


def get_sofa_json(url, retries=2):
    if curl_requests is None:
        raise RuntimeError("curl_cffi is required for the Sofascore extractor "
                           "(pip install curl_cffi)")
    last = None
    for attempt in range(retries + 1):
        try:
            r = curl_requests.get(url, impersonate="chrome", timeout=40)
            if r.status_code == 200:
                time.sleep(SOFA_SLEEP)
                return r.json()
            last = RuntimeError(f"HTTP {r.status_code} for {url}")
        except Exception as e:
            last = e
        time.sleep(SOFA_SLEEP * (attempt + 2))
    raise last
