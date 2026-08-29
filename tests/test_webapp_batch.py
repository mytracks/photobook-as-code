"""
Tests for the batch operation engine: new-day eligibility (reusing
EditorData.is_new_day/is_title), the four date-destination x
existing-content combinations, reverse-geocoding under both strictness
settings, combining date+geocode on one photo, cancellation/incremental
save, and the single-active-job guard.
"""

import threading
import time
from datetime import datetime

import pytest
from PIL import ExifTags, Image

from photobook_as_code.config import load_config
from photobook_as_code.webapp import batch
from photobook_as_code.webapp.batch import (
    DATE_DESTINATION_TEXT_LABEL,
    DATE_DESTINATION_TITLE,
    SKIP_MODE_APPEND,
    SKIP_MODE_SKIP,
    BatchAlreadyRunningError,
    BatchSettings,
    JobState,
    start_batch_job,
)
from photobook_as_code.webapp.data import PhotoDirectoryCache, load_editor_data


@pytest.fixture(autouse=True)
def _reset_job_store():
    batch._jobs.clear()
    batch._active_job_id = None
    yield
    batch._jobs.clear()
    batch._active_job_id = None


def _make_photo_file_with_exif(path, date_taken: datetime, with_gps: bool = False) -> None:
    img = Image.new("RGB", (20, 20), color="white")
    exif = Image.Exif()
    exif[36867] = date_taken.strftime("%Y:%m:%d %H:%M:%S")  # DateTimeOriginal
    if with_gps:
        exif[ExifTags.IFD.GPSInfo] = {1: "N", 2: (53.0, 33.0, 12.6), 3: "E", 4: (10.0, 0.0, 0.0)}
    img.save(path, exif=exif.tobytes())


def _write_config(tmp_path, photos_dir, order="date", text_labels_yaml=""):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        f"photo_folders:\n  - {photos_dir}\n"
        "output:\n  size: A4\n"
        "layout:\n  photos_per_page: 2\n"
        f"  order: {order}\n"
        "theme: clean\n"
        f"{text_labels_yaml}"
    )
    return config_path


def _default_settings(**overrides) -> BatchSettings:
    base = dict(
        date_enabled=False,
        date_destination=DATE_DESTINATION_TEXT_LABEL,
        geocode_enabled=False,
        geocode_strict=False,
        skip_mode=SKIP_MODE_SKIP,
    )
    base.update(overrides)
    return BatchSettings(**base)


def _run(config_path, settings, accept_language="de-DE") -> JobState:
    """Run the batch synchronously against a fresh snapshot - bypasses the
    background thread for deterministic, easy-to-assert-on tests."""
    snapshot = load_editor_data(config_path)
    job = JobState(job_id="test-job", total=snapshot.count, accept_language=accept_language)
    batch._run_job(job, config_path, snapshot, settings)
    return job


def _text_labels(config_path) -> list:
    return load_config(config_path).text_labels


class TestNewDayEligibility:
    def test_photo_boundary_with_no_title_gets_a_new_title(self, tmp_path):
        photos_dir = tmp_path / "photos"
        photos_dir.mkdir()
        _make_photo_file_with_exif(photos_dir / "a.jpg", datetime(2026, 4, 30, 10, 0))
        _make_photo_file_with_exif(photos_dir / "b.jpg", datetime(2026, 5, 1, 10, 0))
        config_path = _write_config(tmp_path, photos_dir, order="date")
        settings = _default_settings(date_enabled=True, date_destination=DATE_DESTINATION_TITLE)

        job = _run(config_path, settings)

        labels = _text_labels(config_path)
        titles = [e["title"] for e in labels if "title" in e]
        assert titles == ["30. April 2026", "1. Mai 2026"]
        assert job.updated == 2
        assert job.status == batch.STATUS_DONE

    def test_title_boundary_suppresses_text_label_on_the_following_photo(self, tmp_path):
        photos_dir = tmp_path / "photos"
        photos_dir.mkdir()
        _make_photo_file_with_exif(photos_dir / "a.jpg", datetime(2026, 4, 30, 10, 0))
        _make_photo_file_with_exif(photos_dir / "b.jpg", datetime(2026, 5, 1, 10, 0))
        text_labels_yaml = (
            "text_labels:\n"
            '  - timestamp: "2026-05-01T00:00:00"\n'
            "    title: Existing Day Two Title\n"
        )
        config_path = _write_config(tmp_path, photos_dir, order="date", text_labels_yaml=text_labels_yaml)
        settings = _default_settings(date_enabled=True, date_destination=DATE_DESTINATION_TEXT_LABEL)

        job = _run(config_path, settings)

        data = load_editor_data(config_path)
        # merged order: a.jpg (day 1 boundary), title (day 2 boundary), b.jpg (suppressed)
        assert data.text_for(0) == "30. April 2026"
        assert data.title_text_for(1) == "Existing Day Two Title"  # untouched
        assert data.text_for(2) == ""  # b.jpg got nothing - the title already marked the day
        assert job.updated == 1

    def test_alphabetical_order_boundaries_are_respected(self, tmp_path):
        photos_dir = tmp_path / "photos"
        photos_dir.mkdir()
        # Alphabetical order differs from date order, and every alphabetically
        # consecutive pair lands on a different calendar day.
        _make_photo_file_with_exif(photos_dir / "a_third.jpg", datetime(2026, 6, 1))
        _make_photo_file_with_exif(photos_dir / "b_first.jpg", datetime(2026, 4, 30))
        _make_photo_file_with_exif(photos_dir / "c_second.jpg", datetime(2026, 5, 15))
        config_path = _write_config(tmp_path, photos_dir, order="alphabetical")
        settings = _default_settings(date_enabled=True, date_destination=DATE_DESTINATION_TITLE)

        job = _run(config_path, settings)

        # All three are new-day boundaries in *display* order, regardless of
        # chronological adjacency.
        assert job.updated == 3


class TestDateDestinationCombinations:
    def test_text_label_empty_caption_becomes_entire_content(self, tmp_path):
        photos_dir = tmp_path / "photos"
        photos_dir.mkdir()
        _make_photo_file_with_exif(photos_dir / "a.jpg", datetime(2026, 4, 30, 10, 0))
        config_path = _write_config(tmp_path, photos_dir, order="date")
        settings = _default_settings(date_enabled=True, date_destination=DATE_DESTINATION_TEXT_LABEL)

        job = _run(config_path, settings)

        assert load_editor_data(config_path).text_for(0) == "30. April 2026"
        assert job.updated == 1

    def test_text_label_skip_leaves_existing_caption_unchanged(self, tmp_path):
        photos_dir = tmp_path / "photos"
        photos_dir.mkdir()
        _make_photo_file_with_exif(photos_dir / "a.jpg", datetime(2026, 4, 30, 10, 0))
        text_labels_yaml = (
            "text_labels:\n"
            '  - timestamp: "2026-04-30T10:00:00"\n'
            "    text: Hand-written caption\n"
        )
        config_path = _write_config(tmp_path, photos_dir, order="date", text_labels_yaml=text_labels_yaml)
        settings = _default_settings(
            date_enabled=True, date_destination=DATE_DESTINATION_TEXT_LABEL, skip_mode=SKIP_MODE_SKIP
        )

        job = _run(config_path, settings)

        assert load_editor_data(config_path).text_for(0) == "Hand-written caption"
        assert job.skipped_existing == 1
        assert job.updated == 0

    def test_text_label_append_adds_after_existing_caption(self, tmp_path):
        photos_dir = tmp_path / "photos"
        photos_dir.mkdir()
        _make_photo_file_with_exif(photos_dir / "a.jpg", datetime(2026, 4, 30, 10, 0))
        text_labels_yaml = (
            "text_labels:\n"
            '  - timestamp: "2026-04-30T10:00:00"\n'
            "    text: Hand-written caption\n"
        )
        config_path = _write_config(tmp_path, photos_dir, order="date", text_labels_yaml=text_labels_yaml)
        settings = _default_settings(
            date_enabled=True, date_destination=DATE_DESTINATION_TEXT_LABEL, skip_mode=SKIP_MODE_APPEND
        )

        job = _run(config_path, settings)

        assert load_editor_data(config_path).text_for(0) == "Hand-written caption\n30. April 2026"
        assert job.updated == 1

    def test_title_mode_skip_leaves_existing_title_unchanged(self, tmp_path):
        photos_dir = tmp_path / "photos"
        photos_dir.mkdir()
        _make_photo_file_with_exif(photos_dir / "a.jpg", datetime(2026, 4, 30, 10, 0))
        text_labels_yaml = (
            "text_labels:\n"
            '  - timestamp: "2026-04-30T09:00:00"\n'
            "    title: Hand-written title\n"
        )
        config_path = _write_config(tmp_path, photos_dir, order="date", text_labels_yaml=text_labels_yaml)
        settings = _default_settings(
            date_enabled=True, date_destination=DATE_DESTINATION_TITLE, skip_mode=SKIP_MODE_SKIP
        )

        job = _run(config_path, settings)

        assert load_editor_data(config_path).title_text_for(0) == "Hand-written title"
        assert job.skipped_existing == 1
        assert job.updated == 0

    def test_title_mode_append_prepends_date_as_first_line(self, tmp_path):
        photos_dir = tmp_path / "photos"
        photos_dir.mkdir()
        _make_photo_file_with_exif(photos_dir / "a.jpg", datetime(2026, 4, 30, 10, 0))
        text_labels_yaml = (
            "text_labels:\n"
            '  - timestamp: "2026-04-30T09:00:00"\n'
            "    title: Hand-written title\n"
        )
        config_path = _write_config(tmp_path, photos_dir, order="date", text_labels_yaml=text_labels_yaml)
        settings = _default_settings(
            date_enabled=True, date_destination=DATE_DESTINATION_TITLE, skip_mode=SKIP_MODE_APPEND
        )

        job = _run(config_path, settings)

        assert load_editor_data(config_path).title_text_for(0) == "30. April 2026\n\nHand-written title"
        assert job.updated == 1


class TestSequentialWritesDoNotCorruptEachOther:
    """
    Regression test: each write must locate its target entry against a
    *fresh* view of the file, not the job-start snapshot - an earlier
    write in the same run (e.g. inserting a new entry before an existing
    one) shifts later entries' positions in the file, and a stale index
    would land the next write on the wrong entry.
    """

    def test_three_boundaries_interleaving_inserts_and_updates(self, tmp_path):
        photos_dir = tmp_path / "photos"
        photos_dir.mkdir()
        _make_photo_file_with_exif(photos_dir / "a.jpg", datetime(2026, 4, 30, 9, 0))  # new entry
        _make_photo_file_with_exif(photos_dir / "b.jpg", datetime(2026, 5, 1, 9, 0))  # existing entry, append
        _make_photo_file_with_exif(photos_dir / "c.jpg", datetime(2026, 5, 2, 9, 0))  # new entry
        text_labels_yaml = (
            "text_labels:\n"
            '  - timestamp: "2026-05-01T09:00:00"\n'
            "    text: Existing caption for b\n"
        )
        config_path = _write_config(tmp_path, photos_dir, order="date", text_labels_yaml=text_labels_yaml)
        settings = _default_settings(
            date_enabled=True, date_destination=DATE_DESTINATION_TEXT_LABEL, skip_mode=SKIP_MODE_APPEND
        )

        job = _run(config_path, settings)

        data = load_editor_data(config_path)
        assert data.text_for(0) == "30. April 2026"
        assert data.text_for(1) == "Existing caption for b\n1. Mai 2026"
        assert data.text_for(2) == "2. Mai 2026"
        assert job.updated == 3


class TestGeocoding:
    def _config_with_gps_photo(self, tmp_path):
        photos_dir = tmp_path / "photos"
        photos_dir.mkdir()
        _make_photo_file_with_exif(photos_dir / "a.jpg", datetime(2026, 4, 30, 10, 0), with_gps=True)
        return _write_config(tmp_path, photos_dir, order="date")

    def test_fallback_strictness_uses_named_place(self, tmp_path, monkeypatch):
        config_path = self._config_with_gps_photo(tmp_path)
        monkeypatch.setattr(
            batch.geocoding, "reverse_geocode", lambda *a, **k: {"name": "St. Michaelis Church"}
        )
        settings = _default_settings(geocode_enabled=True, geocode_strict=False)

        job = _run(config_path, settings)

        assert load_editor_data(config_path).text_for(0) == "St. Michaelis Church"
        assert job.updated == 1

    def test_fallback_strictness_falls_back_to_city(self, tmp_path, monkeypatch):
        config_path = self._config_with_gps_photo(tmp_path)
        monkeypatch.setattr(
            batch.geocoding,
            "reverse_geocode",
            lambda *a, **k: {"address": {"city": "Hamburg", "country": "Germany"}},
        )
        settings = _default_settings(geocode_enabled=True, geocode_strict=False)

        job = _run(config_path, settings)

        assert load_editor_data(config_path).text_for(0) == "Hamburg, Germany"
        assert job.updated == 1

    def test_strict_strictness_skips_when_only_a_city_is_found(self, tmp_path, monkeypatch):
        config_path = self._config_with_gps_photo(tmp_path)
        monkeypatch.setattr(
            batch.geocoding,
            "reverse_geocode",
            lambda *a, **k: {"address": {"city": "Hamburg", "country": "Germany"}},
        )
        settings = _default_settings(geocode_enabled=True, geocode_strict=True)

        job = _run(config_path, settings)

        assert load_editor_data(config_path).text_for(0) == ""
        assert job.skipped_no_poi == 1
        assert job.updated == 0

    def test_strict_strictness_accepts_a_named_place(self, tmp_path, monkeypatch):
        config_path = self._config_with_gps_photo(tmp_path)
        monkeypatch.setattr(
            batch.geocoding, "reverse_geocode", lambda *a, **k: {"name": "St. Michaelis Church"}
        )
        settings = _default_settings(geocode_enabled=True, geocode_strict=True)

        job = _run(config_path, settings)

        assert load_editor_data(config_path).text_for(0) == "St. Michaelis Church"
        assert job.updated == 1

    def test_photo_without_gps_is_not_attempted(self, tmp_path, monkeypatch):
        photos_dir = tmp_path / "photos"
        photos_dir.mkdir()
        _make_photo_file_with_exif(photos_dir / "a.jpg", datetime(2026, 4, 30, 10, 0), with_gps=False)
        config_path = _write_config(tmp_path, photos_dir, order="date")

        def unexpected(*a, **k):
            raise AssertionError("reverse_geocode should not be called for a photo without GPS")

        monkeypatch.setattr(batch.geocoding, "reverse_geocode", unexpected)
        settings = _default_settings(geocode_enabled=True, geocode_strict=False)

        job = _run(config_path, settings)

        assert job.updated == 0
        assert job.skipped_existing == 0
        assert job.skipped_no_poi == 0
        assert job.failed == 0

    def test_geocoding_error_is_tallied_as_failed_and_caption_is_untouched(self, tmp_path, monkeypatch):
        config_path = self._config_with_gps_photo(tmp_path)

        def failing(*a, **k):
            raise batch.geocoding.GeocodingError("boom")

        monkeypatch.setattr(batch.geocoding, "reverse_geocode", failing)
        settings = _default_settings(geocode_enabled=True, geocode_strict=False)

        job = _run(config_path, settings)

        assert load_editor_data(config_path).text_for(0) == ""
        assert job.failed == 1
        assert job.updated == 0

    def test_skip_mode_with_existing_caption_never_calls_the_service(self, tmp_path, monkeypatch):
        photos_dir = tmp_path / "photos"
        photos_dir.mkdir()
        _make_photo_file_with_exif(photos_dir / "a.jpg", datetime(2026, 4, 30, 10, 0), with_gps=True)
        text_labels_yaml = (
            "text_labels:\n"
            '  - timestamp: "2026-04-30T10:00:00"\n'
            "    text: Hand-written caption\n"
        )
        config_path = _write_config(tmp_path, photos_dir, order="date", text_labels_yaml=text_labels_yaml)

        def unexpected(*a, **k):
            raise AssertionError("reverse_geocode should not be called when skipping")

        monkeypatch.setattr(batch.geocoding, "reverse_geocode", unexpected)
        settings = _default_settings(geocode_enabled=True, geocode_strict=False, skip_mode=SKIP_MODE_SKIP)

        job = _run(config_path, settings)

        assert load_editor_data(config_path).text_for(0) == "Hand-written caption"
        assert job.skipped_existing == 1


class TestCombineDateAndGeocodeOnOnePhoto:
    def test_date_first_then_geocoded_location_in_one_write(self, tmp_path, monkeypatch):
        photos_dir = tmp_path / "photos"
        photos_dir.mkdir()
        _make_photo_file_with_exif(photos_dir / "a.jpg", datetime(2026, 4, 30, 10, 0), with_gps=True)
        config_path = _write_config(tmp_path, photos_dir, order="date")
        monkeypatch.setattr(
            batch.geocoding, "reverse_geocode", lambda *a, **k: {"name": "Brandenburger Tor"}
        )
        settings = _default_settings(
            date_enabled=True,
            date_destination=DATE_DESTINATION_TEXT_LABEL,
            geocode_enabled=True,
            geocode_strict=False,
        )

        job = _run(config_path, settings)

        assert load_editor_data(config_path).text_for(0) == "30. April 2026\nBrandenburger Tor"
        # One combined write, not two.
        assert job.updated == 1

    def test_skip_setting_blocks_both_together_when_caption_pre_existed(self, tmp_path, monkeypatch):
        photos_dir = tmp_path / "photos"
        photos_dir.mkdir()
        _make_photo_file_with_exif(photos_dir / "a.jpg", datetime(2026, 4, 30, 10, 0), with_gps=True)
        text_labels_yaml = (
            "text_labels:\n"
            '  - timestamp: "2026-04-30T10:00:00"\n'
            "    text: Hand-written caption\n"
        )
        config_path = _write_config(tmp_path, photos_dir, order="date", text_labels_yaml=text_labels_yaml)

        def unexpected(*a, **k):
            raise AssertionError("reverse_geocode should not be called when skipping")

        monkeypatch.setattr(batch.geocoding, "reverse_geocode", unexpected)
        settings = _default_settings(
            date_enabled=True,
            date_destination=DATE_DESTINATION_TEXT_LABEL,
            geocode_enabled=True,
            geocode_strict=False,
            skip_mode=SKIP_MODE_SKIP,
        )

        job = _run(config_path, settings)

        assert load_editor_data(config_path).text_for(0) == "Hand-written caption"
        assert job.skipped_existing == 1
        assert job.updated == 0

    def test_append_setting_combines_existing_date_and_geocode_in_order(self, tmp_path, monkeypatch):
        photos_dir = tmp_path / "photos"
        photos_dir.mkdir()
        _make_photo_file_with_exif(photos_dir / "a.jpg", datetime(2026, 4, 30, 10, 0), with_gps=True)
        text_labels_yaml = (
            "text_labels:\n"
            '  - timestamp: "2026-04-30T10:00:00"\n'
            "    text: Hand-written caption\n"
        )
        config_path = _write_config(tmp_path, photos_dir, order="date", text_labels_yaml=text_labels_yaml)
        monkeypatch.setattr(
            batch.geocoding, "reverse_geocode", lambda *a, **k: {"name": "Brandenburger Tor"}
        )
        settings = _default_settings(
            date_enabled=True,
            date_destination=DATE_DESTINATION_TEXT_LABEL,
            geocode_enabled=True,
            geocode_strict=False,
            skip_mode=SKIP_MODE_APPEND,
        )

        job = _run(config_path, settings)

        assert (
            load_editor_data(config_path).text_for(0)
            == "Hand-written caption\n30. April 2026\nBrandenburger Tor"
        )
        assert job.updated == 1


class TestDuplicateLocationSuppression:
    def _two_gps_photos_config(self, tmp_path, same_day: bool):
        photos_dir = tmp_path / "photos"
        photos_dir.mkdir()
        _make_photo_file_with_exif(photos_dir / "a.jpg", datetime(2026, 4, 30, 9, 0), with_gps=True)
        second_date = datetime(2026, 4, 30, 15, 0) if same_day else datetime(2026, 5, 1, 9, 0)
        _make_photo_file_with_exif(photos_dir / "b.jpg", second_date, with_gps=True)
        return _write_config(tmp_path, photos_dir, order="date")

    def test_second_photo_with_same_resolved_text_gets_nothing(self, tmp_path, monkeypatch):
        config_path = self._two_gps_photos_config(tmp_path, same_day=True)
        monkeypatch.setattr(batch.geocoding, "reverse_geocode", lambda *a, **k: {"name": "Fernsehturm"})
        settings = _default_settings(geocode_enabled=True, geocode_strict=False)

        job = _run(config_path, settings)

        data = load_editor_data(config_path)
        assert data.text_for(0) == "Fernsehturm"
        assert data.text_for(1) == ""
        assert job.updated == 1
        assert job.skipped_duplicate_location == 1

    def test_different_resolved_texts_are_both_inserted(self, tmp_path, monkeypatch):
        config_path = self._two_gps_photos_config(tmp_path, same_day=True)
        names = iter(["Fernsehturm", "Reichstag"])
        monkeypatch.setattr(batch.geocoding, "reverse_geocode", lambda *a, **k: {"name": next(names)})
        settings = _default_settings(geocode_enabled=True, geocode_strict=False)

        job = _run(config_path, settings)

        data = load_editor_data(config_path)
        assert data.text_for(0) == "Fernsehturm"
        assert data.text_for(1) == "Reichstag"
        assert job.updated == 2
        assert job.skipped_duplicate_location == 0

    def test_duplicate_suppression_does_not_block_that_photos_own_date_marker(self, tmp_path, monkeypatch):
        # b.jpg is a new-day boundary (text-label mode) *and* resolves to the
        # same location as a.jpg - it should still get its date marker, just
        # not the duplicate location text.
        config_path = self._two_gps_photos_config(tmp_path, same_day=False)
        monkeypatch.setattr(batch.geocoding, "reverse_geocode", lambda *a, **k: {"name": "Fernsehturm"})
        settings = _default_settings(
            date_enabled=True,
            date_destination=DATE_DESTINATION_TEXT_LABEL,
            geocode_enabled=True,
            geocode_strict=False,
        )

        job = _run(config_path, settings)

        data = load_editor_data(config_path)
        assert data.text_for(0) == "30. April 2026\nFernsehturm"
        assert data.text_for(1) == "1. Mai 2026"  # date only - location was a duplicate
        assert job.skipped_duplicate_location == 1
        assert job.updated == 2

    def test_dedup_does_not_carry_over_to_a_fresh_run(self, tmp_path, monkeypatch):
        monkeypatch.setattr(batch.geocoding, "reverse_geocode", lambda *a, **k: {"name": "Fernsehturm"})
        settings = _default_settings(geocode_enabled=True, geocode_strict=False)

        photos_dir_1 = tmp_path / "photos1"
        photos_dir_1.mkdir()
        _make_photo_file_with_exif(photos_dir_1 / "a.jpg", datetime(2026, 4, 30, 9, 0), with_gps=True)
        config_path_1 = _write_config(tmp_path, photos_dir_1, order="date")

        photos_dir_2 = tmp_path / "photos2"
        photos_dir_2.mkdir()
        _make_photo_file_with_exif(photos_dir_2 / "b.jpg", datetime(2026, 5, 1, 9, 0), with_gps=True)
        config_path_2 = tmp_path / "config2.yaml"
        config_path_2.write_text(
            f"photo_folders:\n  - {photos_dir_2}\n"
            "output:\n  size: A4\n"
            "layout:\n  photos_per_page: 2\n  order: date\n"
            "theme: clean\n"
        )

        job1 = _run(config_path_1, settings)
        job2 = _run(config_path_2, settings)

        assert load_editor_data(config_path_1).text_for(0) == "Fernsehturm"
        assert load_editor_data(config_path_2).text_for(0) == "Fernsehturm"
        assert job1.skipped_duplicate_location == 0
        assert job2.skipped_duplicate_location == 0


class TestWorkerLoopCancellationAndPersistence:
    def test_completes_all_items_when_not_cancelled(self, tmp_path):
        photos_dir = tmp_path / "photos"
        photos_dir.mkdir()
        _make_photo_file_with_exif(photos_dir / "a.jpg", datetime(2026, 4, 30, 10, 0))
        _make_photo_file_with_exif(photos_dir / "b.jpg", datetime(2026, 5, 1, 10, 0))
        config_path = _write_config(tmp_path, photos_dir, order="date")
        settings = _default_settings(date_enabled=True, date_destination=DATE_DESTINATION_TITLE)

        job = _run(config_path, settings)

        assert job.status == batch.STATUS_DONE
        assert job.processed == job.total == 2

    def test_cancellation_keeps_already_saved_items_and_stops_before_the_next(self, tmp_path, monkeypatch):
        photos_dir = tmp_path / "photos"
        photos_dir.mkdir()
        _make_photo_file_with_exif(photos_dir / "a.jpg", datetime(2026, 4, 30, 10, 0))
        _make_photo_file_with_exif(photos_dir / "b.jpg", datetime(2026, 5, 1, 10, 0))
        config_path = _write_config(tmp_path, photos_dir, order="date")
        settings = _default_settings(date_enabled=True, date_destination=DATE_DESTINATION_TITLE)

        snapshot = load_editor_data(config_path)
        job = JobState(job_id="cancel-test", total=snapshot.count, accept_language="de-DE")

        real_format = batch.format_batch_date
        call_count = {"n": 0}

        def cancel_after_first_call(dt, accept_language):
            call_count["n"] += 1
            if call_count["n"] == 1:
                job.cancel_event.set()
            return real_format(dt, accept_language)

        monkeypatch.setattr(batch, "format_batch_date", cancel_after_first_call)

        batch._run_job(job, config_path, snapshot, settings)

        assert job.status == batch.STATUS_CANCELLED
        assert job.processed == 1
        assert job.updated == 1

        titles = [e["title"] for e in _text_labels(config_path) if "title" in e]
        assert titles == ["30. April 2026"]  # only a.jpg's title was created


class TestSingleActiveJob:
    def test_second_start_is_rejected_while_one_is_running(self, tmp_path, monkeypatch):
        photos_dir = tmp_path / "photos"
        photos_dir.mkdir()
        _make_photo_file_with_exif(photos_dir / "a.jpg", datetime(2026, 4, 30, 10, 0))
        config_path = _write_config(tmp_path, photos_dir, order="date")
        settings = _default_settings(date_enabled=True, date_destination=DATE_DESTINATION_TITLE)
        cache = PhotoDirectoryCache()

        release = threading.Event()
        real_process = batch._process_new_title_for_photo

        def blocking_process(*args, **kwargs):
            release.wait(timeout=5)
            return real_process(*args, **kwargs)

        monkeypatch.setattr(batch, "_process_new_title_for_photo", blocking_process)

        job_id = start_batch_job(config_path, cache, settings, "de-DE")
        try:
            running_job_before = batch.get_job(job_id)
            with pytest.raises(BatchAlreadyRunningError):
                start_batch_job(config_path, cache, settings, "de-DE")
            # The rejected attempt didn't disturb the running job's state.
            assert batch.get_job(job_id) is running_job_before
            assert batch.get_job(job_id).status == batch.STATUS_RUNNING
        finally:
            release.set()
            for _ in range(50):
                if batch.get_job(job_id).status != batch.STATUS_RUNNING:
                    break
                time.sleep(0.05)

        assert batch.get_job(job_id).status == batch.STATUS_DONE
        assert batch.get_job(job_id).updated == 1
