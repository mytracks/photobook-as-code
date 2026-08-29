"""
Server-side reverse geocoding of a photo's GPS location via the public
Nominatim (OpenStreetMap) API - no API key required.
"""

import json
import logging
import threading
import time
import urllib.parse
import urllib.request
from typing import Optional

logger = logging.getLogger(__name__)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"
USER_AGENT = "mytracks-photobook-as-code"
REQUEST_TIMEOUT_SECONDS = 10

# Nominatim's usage policy caps requests at 1/second. Enforced process-wide
# (not per-caller) so the single-photo editor button and the batch feature
# share one throttle and neither can violate the limit.
MIN_REQUEST_INTERVAL_SECONDS = 1.0

_rate_limit_lock = threading.Lock()
_last_request_at: Optional[float] = None


class GeocodingError(Exception):
    """Raised when a reverse-geocode request fails (network, HTTP, timeout, or unparsable response)."""
    pass


def _throttle() -> None:
    """
    Block the calling thread, if needed, so that no two reverse-geocoding
    requests across the whole process start less than
    MIN_REQUEST_INTERVAL_SECONDS apart. Holding the lock for the sleep's
    duration (rather than releasing and re-checking) is what makes this
    correct under concurrent callers: two threads can't both observe "no
    wait needed" for the same slot.
    """
    global _last_request_at
    with _rate_limit_lock:
        now = time.monotonic()
        if _last_request_at is not None:
            wait = MIN_REQUEST_INTERVAL_SECONDS - (now - _last_request_at)
            if wait > 0:
                time.sleep(wait)
                now = time.monotonic()
        _last_request_at = now


def reverse_geocode(lat: float, lon: float, accept_language: str = "") -> dict:
    """
    Query Nominatim's reverse-geocoding endpoint for the given coordinates.

    Waits as needed beforehand to respect Nominatim's 1 request/second usage
    policy, across all callers in the process.

    Args:
        lat: Latitude in decimal degrees
        lon: Longitude in decimal degrees
        accept_language: Value to forward as Nominatim's `accept-language`
            query parameter (typically the requesting browser's own
            Accept-Language header), so the result matches its locale.

    Returns:
        The parsed JSON response.

    Raises:
        GeocodingError: on a network error, non-2xx response, timeout, or
            a response body that isn't valid JSON.
    """
    _throttle()

    params = {
        "format": "jsonv2",
        "lat": str(lat),
        "lon": str(lon),
        "zoom": "18",
        "addressdetails": "1",
    }
    if accept_language:
        params["accept-language"] = accept_language

    url = f"{NOMINATIM_URL}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            body = response.read()
    except OSError as e:
        # Covers urllib.error.URLError/HTTPError (both OSError subclasses,
        # so this includes non-2xx responses) as well as socket timeouts.
        logger.debug(f"Reverse geocoding request failed: {e}")
        raise GeocodingError("Reverse geocoding request failed") from e

    try:
        return json.loads(body)
    except (ValueError, TypeError) as e:
        logger.debug(f"Could not parse reverse geocoding response: {e}")
        raise GeocodingError("Reverse geocoding response was not valid JSON") from e


def resolve_place_name(response: dict, strict: bool = False) -> Optional[str]:
    """
    Resolve a human-readable place name from a parsed Nominatim response.

    Prefers a specific named place (the response's top-level `name`, e.g. a
    landmark or building). Falls back to the address's city (or town/village
    when Nominatim used one of those instead) combined with its country, or
    just the country when no locality is available. Returns None when
    nothing usable is present.

    Args:
        strict: When True, only a named place is accepted - the city/country
            fallback is skipped entirely, so this returns None whenever no
            specific named place is nearby.
    """
    name = response.get("name")
    if name:
        return name

    if strict:
        return None

    address = response.get("address") or {}
    locality = address.get("city") or address.get("town") or address.get("village")
    country = address.get("country")

    if locality and country:
        return f"{locality}, {country}"
    if locality:
        return locality
    if country:
        return country

    return None
