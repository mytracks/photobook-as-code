"""
Tests for the web editor's read-side data loading (config + photo order +
text associations).
"""

import os
import time
from datetime import datetime
from pathlib import Path

from PIL import ExifTags, Image

import photobook_as_code.webapp.data as data_module
from photobook_as_code.photos import PhotoMetadata
from photobook_as_code.webapp.data import PhotoDirectoryCache, ThumbnailCache, load_editor_data


def _counting_collect_photos(monkeypatch):
    """Wraps data_module.collect_photos to count real (non-cached) scans."""
    original = data_module.collect_photos
    calls = {"count": 0}

    def wrapper(*args, **kwargs):
        calls["count"] += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(data_module, "collect_photos", wrapper)
    return calls


def _make_photo_file(path: Path, mtime_offset_seconds: float) -> None:
    Image.new("RGB", (20, 20), color="white").save(path)
    now = time.time()
    os.utime(path, (now + mtime_offset_seconds, now + mtime_offset_seconds))


def _make_photo_file_with_exif(path: Path, date_taken: datetime) -> None:
    img = Image.new("RGB", (20, 20), color="white")
    exif = Image.Exif()
    exif[36867] = date_taken.strftime("%Y:%m:%d %H:%M:%S")  # DateTimeOriginal
    img.save(path, exif=exif.tobytes())


def _make_photo_file_with_gps(path: Path) -> None:
    img = Image.new("RGB", (20, 20), color="white")
    exif = Image.Exif()
    exif[ExifTags.IFD.GPSInfo] = {
        1: "N",
        2: (53.0, 33.0, 12.6),
        3: "E",
        4: (10.0, 0.0, 0.0),
    }
    img.save(path, exif=exif.tobytes())


def _make_photos_dir(tmp_path: Path) -> Path:
    # Filenames sort alphabetically opposite to their mtime (date) order,
    # so alphabetical vs date ordering can be distinguished in a test.
    photos_dir = tmp_path / "photos"
    photos_dir.mkdir()
    _make_photo_file(photos_dir / "a_taken_last.jpg", mtime_offset_seconds=20)
    _make_photo_file(photos_dir / "b_taken_middle.jpg", mtime_offset_seconds=10)
    _make_photo_file(photos_dir / "c_taken_first.jpg", mtime_offset_seconds=0)
    return photos_dir


def _write_config(tmp_path: Path, photos_dir: Path, order: str) -> Path:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        f"photo_folders:\n  - {photos_dir}\n"
        "output:\n"
        "  size: A4\n"
        "layout:\n"
        "  photos_per_page: 2\n"
        f"  order: {order}\n"
        "theme: clean\n"
    )
    return config_path


def _write_config_with_labels(
    tmp_path: Path, photos_dir: Path, order: str, text_labels_yaml: str
) -> Path:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        f"photo_folders:\n  - {photos_dir}\n"
        "output:\n"
        "  size: A4\n"
        "layout:\n"
        "  photos_per_page: 2\n"
        f"  order: {order}\n"
        "theme: clean\n"
        f"{text_labels_yaml}"
    )
    return config_path


class TestEditorDataOrdering:
    def test_alphabetical_order(self, tmp_path):
        photos_dir = _make_photos_dir(tmp_path)
        config_path = _write_config(tmp_path, photos_dir, order="alphabetical")

        data = load_editor_data(config_path)

        assert [p.filename for p in data.photos] == [
            "a_taken_last.jpg",
            "b_taken_middle.jpg",
            "c_taken_first.jpg",
        ]

    def test_date_order(self, tmp_path):
        photos_dir = _make_photos_dir(tmp_path)
        config_path = _write_config(tmp_path, photos_dir, order="date")

        data = load_editor_data(config_path)

        assert [p.filename for p in data.photos] == [
            "c_taken_first.jpg",
            "b_taken_middle.jpg",
            "a_taken_last.jpg",
        ]

    def test_count_and_text_for_photo_without_association(self, tmp_path):
        photos_dir = _make_photos_dir(tmp_path)
        config_path = _write_config(tmp_path, photos_dir, order="alphabetical")

        data = load_editor_data(config_path)

        assert data.count == 3
        assert data.text_for(0) == ""
        assert data.label_for(0) is None


class TestEditorDataDisplayDate:
    def test_uses_exif_date_with_weekday(self, tmp_path):
        photos_dir = tmp_path / "photos"
        photos_dir.mkdir()
        _make_photo_file_with_exif(photos_dir / "a.jpg", datetime(2025, 6, 14))
        config_path = _write_config(tmp_path, photos_dir, order="date")

        data = load_editor_data(config_path)

        assert data.display_date(0) == "Saturday, June 14, 2025 · 00:00"

    def test_falls_back_to_filename_without_exif_date(self, tmp_path):
        photos_dir = tmp_path / "photos"
        photos_dir.mkdir()
        _make_photo_file(photos_dir / "no_exif.jpg", mtime_offset_seconds=0)
        config_path = _write_config(tmp_path, photos_dir, order="date")

        data = load_editor_data(config_path)

        assert data.display_date(0) == "no_exif.jpg"


class TestEditorDataIsNewDay:
    def test_first_photo_is_new_day(self, tmp_path):
        photos_dir = tmp_path / "photos"
        photos_dir.mkdir()
        _make_photo_file_with_exif(photos_dir / "a.jpg", datetime(2025, 6, 14))
        config_path = _write_config(tmp_path, photos_dir, order="date")

        data = load_editor_data(config_path)

        assert data.is_new_day(0) is True

    def test_same_calendar_day_is_not_new_day(self, tmp_path):
        photos_dir = tmp_path / "photos"
        photos_dir.mkdir()
        _make_photo_file_with_exif(photos_dir / "a.jpg", datetime(2025, 6, 14, 9, 0))
        _make_photo_file_with_exif(photos_dir / "b.jpg", datetime(2025, 6, 14, 15, 0))
        config_path = _write_config(tmp_path, photos_dir, order="date")

        data = load_editor_data(config_path)

        assert data.is_new_day(1) is False

    def test_date_change_is_new_day(self, tmp_path):
        photos_dir = tmp_path / "photos"
        photos_dir.mkdir()
        _make_photo_file_with_exif(photos_dir / "a.jpg", datetime(2025, 6, 14))
        _make_photo_file_with_exif(photos_dir / "b.jpg", datetime(2025, 6, 15))
        config_path = _write_config(tmp_path, photos_dir, order="date")

        data = load_editor_data(config_path)

        assert data.is_new_day(1) is True

    def test_uses_best_available_date_when_exif_is_missing(self, tmp_path):
        photos_dir = tmp_path / "photos"
        photos_dir.mkdir()
        _make_photo_file_with_exif(photos_dir / "a.jpg", datetime(2025, 6, 14))
        # No EXIF - falls back to file_modified, which lands on today's
        # real date (via mtime_offset), guaranteed to differ from a's
        # fixed 2025-06-14 EXIF date.
        _make_photo_file(photos_dir / "z_no_exif.jpg", mtime_offset_seconds=0)
        config_path = _write_config(tmp_path, photos_dir, order="date")

        data = load_editor_data(config_path)

        # display falls back to filename, but the new-day flag is still
        # computed from the best-available (file_modified) date
        assert data.display_date(1) == "z_no_exif.jpg"
        assert data.is_new_day(1) is True


class TestEditorDataItems:
    def test_titles_are_merged_among_photos(self, tmp_path):
        photos_dir = tmp_path / "photos"
        photos_dir.mkdir()
        _make_photo_file_with_exif(photos_dir / "a.jpg", datetime(2025, 6, 14, 9, 0))
        _make_photo_file_with_exif(photos_dir / "b.jpg", datetime(2025, 6, 15, 9, 0))
        text_labels_yaml = (
            "text_labels:\n"
            '  - timestamp: "2025-06-14T09:00:00"\n'
            "    title: Day One\n"
            '  - timestamp: "2025-06-16T00:00:00"\n'
            "    title: Trailing\n"
        )
        config_path = _write_config_with_labels(tmp_path, photos_dir, "date", text_labels_yaml)

        data = load_editor_data(config_path)

        assert data.count == 4
        assert data.is_title(0) is True
        assert data.title_text_for(0) == "Day One"
        assert data.is_title(1) is False  # a.jpg - tied timestamp loses to the title
        assert data.is_title(2) is False  # b.jpg
        assert data.is_title(3) is True  # Trailing, appended after every photo
        assert data.title_text_for(3) == "Trailing"

    def test_photo_lookups_still_work_around_titles(self, tmp_path):
        photos_dir = tmp_path / "photos"
        photos_dir.mkdir()
        _make_photo_file_with_exif(photos_dir / "a.jpg", datetime(2025, 6, 14, 9, 0))
        _make_photo_file_with_exif(photos_dir / "b.jpg", datetime(2025, 6, 15, 9, 0))
        text_labels_yaml = (
            "text_labels:\n"
            '  - timestamp: "2025-06-14T09:00:00"\n'
            "    title: Day One\n"
            '  - timestamp: "2025-06-15T09:00:00"\n'
            "    text: caption for b\n"
        )
        config_path = _write_config_with_labels(tmp_path, photos_dir, "date", text_labels_yaml)

        data = load_editor_data(config_path)

        # merged order: [title "Day One", a.jpg, b.jpg]
        assert data.is_title(0) is True
        assert data.photo_at(1).filename == "a.jpg"
        assert data.text_for(1) == ""
        assert data.photo_at(2).filename == "b.jpg"
        assert data.text_for(2) == "caption for b"
        assert data.display_date(1) == "Saturday, June 14, 2025 · 09:00"
        # a.jpg and b.jpg differ in calendar day, despite the title in between
        assert data.is_new_day(2) is True

    def test_title_date_display_and_iso(self, tmp_path):
        photos_dir = tmp_path / "photos"
        photos_dir.mkdir()
        _make_photo_file_with_exif(photos_dir / "a.jpg", datetime(2025, 6, 14, 9, 0))
        text_labels_yaml = (
            "text_labels:\n"
            '  - timestamp: "2025-06-14T08:00:00"\n'
            "    title: Day One\n"
        )
        config_path = _write_config_with_labels(tmp_path, photos_dir, "date", text_labels_yaml)

        data = load_editor_data(config_path)

        assert data.is_title(0) is True
        assert data.display_date(0) == "Saturday, June 14, 2025 · 08:00"
        assert data.date_taken_iso(0) == datetime(2025, 6, 14, 8, 0).isoformat()

    def test_title_as_first_item_of_new_day_carries_the_indicator(self, tmp_path):
        photos_dir = tmp_path / "photos"
        photos_dir.mkdir()
        _make_photo_file_with_exif(photos_dir / "a.jpg", datetime(2025, 6, 14, 9, 0))
        _make_photo_file_with_exif(photos_dir / "b.jpg", datetime(2025, 6, 15, 9, 0))
        text_labels_yaml = (
            "text_labels:\n"
            '  - timestamp: "2025-06-15T00:00:00"\n'
            "    title: Day Two\n"
        )
        config_path = _write_config_with_labels(tmp_path, photos_dir, "date", text_labels_yaml)

        data = load_editor_data(config_path)

        # merged order: [a.jpg (6/14), title "Day Two" (6/15), b.jpg (6/15)]
        assert data.is_title(1) is True
        assert data.is_new_day(0) is True  # a.jpg: first item overall
        assert data.is_new_day(1) is True  # title: first item of 6/15
        assert data.is_new_day(2) is False  # b.jpg: same day as the title before it

    def test_no_titles_behaves_like_photo_only_sequence(self, tmp_path):
        photos_dir = _make_photos_dir(tmp_path)
        config_path = _write_config(tmp_path, photos_dir, order="alphabetical")

        data = load_editor_data(config_path)

        assert data.count == len(data.photos) == 3
        assert all(data.is_title(i) is False for i in range(data.count))


class TestEditorDataHasGps:
    def test_photo_with_gps_is_true(self, tmp_path):
        photos_dir = tmp_path / "photos"
        photos_dir.mkdir()
        _make_photo_file_with_gps(photos_dir / "a.jpg")
        config_path = _write_config(tmp_path, photos_dir, order="alphabetical")

        data = load_editor_data(config_path)

        assert data.has_gps(0) is True

    def test_photo_without_gps_is_false(self, tmp_path):
        photos_dir = tmp_path / "photos"
        photos_dir.mkdir()
        _make_photo_file(photos_dir / "a.jpg", mtime_offset_seconds=0)
        config_path = _write_config(tmp_path, photos_dir, order="alphabetical")

        data = load_editor_data(config_path)

        assert data.has_gps(0) is False

    def test_title_item_is_false(self, tmp_path):
        photos_dir = tmp_path / "photos"
        photos_dir.mkdir()
        _make_photo_file_with_exif(photos_dir / "a.jpg", datetime(2025, 6, 14, 9, 0))
        text_labels_yaml = (
            "text_labels:\n"
            '  - timestamp: "2025-06-14T08:00:00"\n'
            "    title: Day One\n"
        )
        config_path = _write_config_with_labels(tmp_path, photos_dir, "date", text_labels_yaml)

        data = load_editor_data(config_path)

        assert data.is_title(0) is True
        assert data.has_gps(0) is False


class TestPhotoDirectoryCache:
    def test_without_cache_each_call_rescans(self, tmp_path, monkeypatch):
        photos_dir = _make_photos_dir(tmp_path)
        config_path = _write_config(tmp_path, photos_dir, order="alphabetical")
        calls = _counting_collect_photos(monkeypatch)

        load_editor_data(config_path)
        load_editor_data(config_path)

        assert calls["count"] == 2

    def test_with_shared_cache_scans_once(self, tmp_path, monkeypatch):
        photos_dir = _make_photos_dir(tmp_path)
        config_path = _write_config(tmp_path, photos_dir, order="alphabetical")
        calls = _counting_collect_photos(monkeypatch)
        cache = PhotoDirectoryCache()

        first = load_editor_data(config_path, photo_cache=cache)
        second = load_editor_data(config_path, photo_cache=cache)

        assert calls["count"] == 1
        assert [p.filename for p in first.photos] == [p.filename for p in second.photos]

    def test_cache_scans_once_per_distinct_order(self, tmp_path, monkeypatch):
        photos_dir = _make_photos_dir(tmp_path)
        date_config_path = _write_config(tmp_path, photos_dir, order="date")
        alpha_config_path = tmp_path / "alpha-config.yaml"
        alpha_config_path.write_text(
            f"photo_folders:\n  - {photos_dir}\n"
            "output:\n"
            "  size: A4\n"
            "layout:\n"
            "  photos_per_page: 2\n"
            "  order: alphabetical\n"
            "theme: clean\n"
        )
        calls = _counting_collect_photos(monkeypatch)
        cache = PhotoDirectoryCache()

        load_editor_data(date_config_path, photo_cache=cache)
        load_editor_data(date_config_path, photo_cache=cache)
        load_editor_data(alpha_config_path, photo_cache=cache)
        load_editor_data(alpha_config_path, photo_cache=cache)

        assert calls["count"] == 2

    def test_cache_key_ignores_folder_listing_order(self, tmp_path, monkeypatch):
        photos_dir = _make_photos_dir(tmp_path)
        other_dir = tmp_path / "other"
        other_dir.mkdir()
        _make_photo_file(other_dir / "z_other.jpg", mtime_offset_seconds=30)
        calls = _counting_collect_photos(monkeypatch)
        cache = PhotoDirectoryCache()

        first = cache.get([photos_dir, other_dir], "alphabetical")
        second = cache.get([other_dir, photos_dir], "alphabetical")

        assert calls["count"] == 1
        assert first is second


class TestThumbnailCache:
    def test_second_lookup_reuses_rendered_bytes(self, tmp_path, monkeypatch):
        photo_path = tmp_path / "a.jpg"
        Image.new("RGB", (400, 300), color="white").save(photo_path)
        photo = PhotoMetadata(path=photo_path, filename="a.jpg", width=400, height=300)

        original = data_module._render_thumbnail
        calls = {"count": 0}

        def wrapper(p):
            calls["count"] += 1
            return original(p)

        monkeypatch.setattr(data_module, "_render_thumbnail", wrapper)
        cache = ThumbnailCache()

        first = cache.get(photo)
        second = cache.get(photo)

        assert calls["count"] == 1
        assert first == second

    def test_different_photos_are_cached_independently(self, tmp_path):
        path_a = tmp_path / "a.jpg"
        path_b = tmp_path / "b.jpg"
        Image.new("RGB", (400, 300), color="white").save(path_a)
        Image.new("RGB", (400, 300), color="black").save(path_b)
        photo_a = PhotoMetadata(path=path_a, filename="a.jpg", width=400, height=300)
        photo_b = PhotoMetadata(path=path_b, filename="b.jpg", width=400, height=300)
        cache = ThumbnailCache()

        assert cache.get(photo_a) != cache.get(photo_b)


class TestFilmstripItems:
    def test_one_entry_per_item_in_merged_order(self, tmp_path):
        photos_dir = _make_photos_dir(tmp_path)
        config_path = _write_config(tmp_path, photos_dir, order="alphabetical")

        data = load_editor_data(config_path)
        items = data.filmstrip_items()

        assert [item.index for item in items] == [0, 1, 2]
        assert [item.filename for item in items] == [
            "a_taken_last.jpg",
            "b_taken_middle.jpg",
            "c_taken_first.jpg",
        ]
        assert all(item.is_title is False for item in items)

    def test_title_entry_has_no_filename(self, tmp_path):
        photos_dir = tmp_path / "photos"
        photos_dir.mkdir()
        _make_photo_file_with_exif(photos_dir / "a.jpg", datetime(2025, 6, 14, 9, 0))
        text_labels_yaml = (
            "text_labels:\n"
            '  - timestamp: "2025-06-14T08:00:00"\n'
            "    title: Day One\n"
        )
        config_path = _write_config_with_labels(tmp_path, photos_dir, "date", text_labels_yaml)

        data = load_editor_data(config_path)
        items = data.filmstrip_items()

        assert items[0].is_title is True
        assert items[0].filename is None

    def test_new_day_carries_a_compact_date_label(self, tmp_path):
        photos_dir = tmp_path / "photos"
        photos_dir.mkdir()
        _make_photo_file_with_exif(photos_dir / "a.jpg", datetime(2025, 6, 14, 9, 0))
        _make_photo_file_with_exif(photos_dir / "b.jpg", datetime(2025, 6, 15, 9, 0))
        config_path = _write_config(tmp_path, photos_dir, order="date")

        data = load_editor_data(config_path)
        items = data.filmstrip_items()

        assert items[0].is_new_day is True
        assert items[0].date_label == "Jun 14"
        assert items[1].is_new_day is True
        assert items[1].date_label == "Jun 15"

    def test_same_day_has_no_date_label(self, tmp_path):
        photos_dir = tmp_path / "photos"
        photos_dir.mkdir()
        _make_photo_file_with_exif(photos_dir / "a.jpg", datetime(2025, 6, 14, 9, 0))
        _make_photo_file_with_exif(photos_dir / "b.jpg", datetime(2025, 6, 14, 15, 0))
        config_path = _write_config(tmp_path, photos_dir, order="date")

        data = load_editor_data(config_path)
        items = data.filmstrip_items()

        assert items[1].is_new_day is False
        assert items[1].date_label is None
