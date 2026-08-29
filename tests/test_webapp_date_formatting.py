"""Tests for locale-aware batch date formatting."""

from datetime import datetime

from photobook_as_code.webapp.date_formatting import format_batch_date

DT = datetime(2026, 4, 30, 10, 24, 45)


def test_german_tag_formats_german_long_date():
    assert format_batch_date(DT, "de-DE,de;q=0.9,en;q=0.8") == "30. April 2026"


def test_unrecognized_tag_falls_back_to_default_locale():
    assert format_batch_date(DT, "xx-XX") == format_batch_date(DT, "")


def test_multi_tag_header_uses_first_tag_only():
    # First tag is German; a later, unrelated tag must not win.
    assert format_batch_date(DT, "de,fr;q=0.5") == "30. April 2026"


def test_empty_accept_language_uses_default_locale():
    result = format_batch_date(DT, "")
    assert "30" in result and "2026" in result


def test_result_has_no_weekday_or_time():
    result = format_batch_date(DT, "en-US")
    assert "10" not in result  # the hour
    assert ":" not in result
