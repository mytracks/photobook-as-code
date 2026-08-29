"""
Locale-aware formatting for the date text the batch feature writes into the
photobook itself, not the editor's own UI (which stays in English regardless
of the browser's locale). See design.md's "Date formatting via Babel"
decision: unlike the editor's on-screen date display, this text becomes
permanent content of the configuration file, so it's formatted once, at
batch-start time, from the starting browser's own Accept-Language header.
"""

from datetime import datetime

from babel import UnknownLocaleError
from babel.dates import format_date

# Used when accept_language is empty or names a locale Babel doesn't
# recognize, so a batch run never fails outright over date formatting.
DEFAULT_LOCALE = "en_US"

# Day of month, full month name, year - no weekday, no time - matching the
# convention already used by hand in this project's own configurations
# (e.g. "30. April 2026"). Deliberately locale-independent in shape: only
# the month name varies by locale, not the day/month/year order.
DATE_PATTERN = "d. MMMM y"


def _first_locale_tag(accept_language: str) -> str:
    """
    Extract the first (highest-priority) language tag from an
    Accept-Language header value, normalized to Babel's underscore
    separator, e.g. "de-DE,de;q=0.9,en;q=0.8" -> "de_DE".
    """
    first_tag = accept_language.split(",")[0].split(";")[0].strip()
    return first_tag.replace("-", "_")


def format_batch_date(dt: datetime, accept_language: str = "") -> str:
    """
    Format `dt` as day-of-month, full month name, and year, in the language
    of `accept_language` (typically the browser header that started a batch
    operation). Falls back to DEFAULT_LOCALE when `accept_language` is empty
    or not a locale Babel recognizes.
    """
    locale = _first_locale_tag(accept_language) if accept_language else DEFAULT_LOCALE
    try:
        return format_date(dt, format=DATE_PATTERN, locale=locale)
    except (ValueError, UnknownLocaleError):
        return format_date(dt, format=DATE_PATTERN, locale=DEFAULT_LOCALE)
