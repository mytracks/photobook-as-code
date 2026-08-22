"""
Tests for the web editor's read-side data loading (config + photo order +
text associations).
"""

import os
import time
from datetime import datetime
from pathlib import Path

from PIL import Image

from photobook_as_code.webapp.data import load_editor_data


def _make_photo_file(path: Path, mtime_offset_seconds: float) -> None:
    Image.new("RGB", (20, 20), color="white").save(path)
    now = time.time()
    os.utime(path, (now + mtime_offset_seconds, now + mtime_offset_seconds))


def _make_photo_file_with_exif(path: Path, date_taken: datetime) -> None:
    img = Image.new("RGB", (20, 20), color="white")
    exif = Image.Exif()
    exif[36867] = date_taken.strftime("%Y:%m:%d %H:%M:%S")  # DateTimeOriginal
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
        f"photos: {photos_dir}\n"
        "output:\n"
        "  size: A4\n"
        "layout:\n"
        "  photos_per_page: 2\n"
        f"  order: {order}\n"
        "theme: clean\n"
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
