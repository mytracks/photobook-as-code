from datetime import datetime
from pathlib import Path

import pytest
from PIL import Image

from photobook_as_code.photos import (
    PhotoCollectionError,
    PhotoMetadata,
    collect_photos,
    discover_photos,
    group_photos_by_timestamp,
    format_text_label_stubs,
)


def make_photo(filename: str, timestamp: datetime) -> PhotoMetadata:
    return PhotoMetadata(
        path=Path(filename),
        filename=filename,
        date_taken=timestamp,
        width=1920,
        height=1080,
    )


def _make_image(path: Path, date_taken: datetime = None) -> None:
    img = Image.new("RGB", (20, 20), color="white")
    if date_taken is not None:
        exif = Image.Exif()
        exif[36867] = date_taken.strftime("%Y:%m:%d %H:%M:%S")  # DateTimeOriginal
        img.save(path, exif=exif.tobytes())
    else:
        img.save(path)


def test_group_photos_by_timestamp_distinct_timestamps():
    photos = [
        make_photo("b.jpg", datetime(2026, 4, 30, 9, 14, 51)),
        make_photo("a.jpg", datetime(2026, 4, 30, 9, 12, 3)),
    ]

    groups = group_photos_by_timestamp(photos)

    assert groups == [
        (datetime(2026, 4, 30, 9, 12, 3), ["a.jpg"]),
        (datetime(2026, 4, 30, 9, 14, 51), ["b.jpg"]),
    ]


def test_group_photos_by_timestamp_collapses_duplicates():
    shared = datetime(2026, 4, 30, 9, 14, 51)
    photos = [
        make_photo("IMG_0002.jpg", shared),
        make_photo("IMG_0003.jpg", shared),
        make_photo("IMG_0001.jpg", datetime(2026, 4, 30, 9, 12, 3)),
    ]

    groups = group_photos_by_timestamp(photos)

    assert groups == [
        (datetime(2026, 4, 30, 9, 12, 3), ["IMG_0001.jpg"]),
        (shared, ["IMG_0002.jpg", "IMG_0003.jpg"]),
    ]


def test_group_photos_by_timestamp_chronological_regardless_of_input_order():
    # Photos passed in alphabetical (filename) order must still group/sort
    # by timestamp, not by input order.
    photos = [
        make_photo("a_later.jpg", datetime(2026, 4, 30, 12, 0, 0)),
        make_photo("b_earlier.jpg", datetime(2026, 4, 30, 8, 0, 0)),
    ]

    groups = group_photos_by_timestamp(photos)

    assert [ts for ts, _ in groups] == [
        datetime(2026, 4, 30, 8, 0, 0),
        datetime(2026, 4, 30, 12, 0, 0),
    ]


def test_format_text_label_stubs_distinct_timestamps():
    photos = [
        make_photo("IMG_0001.jpg", datetime(2026, 4, 30, 9, 12, 3)),
        make_photo("IMG_0002.jpg", datetime(2026, 4, 30, 9, 14, 51)),
    ]

    output = format_text_label_stubs(photos)

    assert output == (
        "text_labels:\n"
        '  - timestamp: "2026-04-30T09:12:03"  # IMG_0001.jpg\n'
        '    text: ""\n'
        '  - timestamp: "2026-04-30T09:14:51"  # IMG_0002.jpg\n'
        '    text: ""\n'
    )


def test_format_text_label_stubs_joins_filenames_for_shared_timestamp():
    shared = datetime(2026, 4, 30, 9, 14, 51)
    photos = [
        make_photo("IMG_0002.jpg", shared),
        make_photo("IMG_0003.jpg", shared),
    ]

    output = format_text_label_stubs(photos)

    assert output == (
        "text_labels:\n"
        '  - timestamp: "2026-04-30T09:14:51"  # IMG_0002.jpg, IMG_0003.jpg\n'
        '    text: ""\n'
    )


class TestDiscoverPhotosMultipleFolders:
    def test_merges_files_from_each_directory(self, tmp_path):
        dir_a = tmp_path / "a"
        dir_a.mkdir()
        dir_b = tmp_path / "b"
        dir_b.mkdir()
        _make_image(dir_a / "a1.jpg")
        _make_image(dir_b / "b1.jpg")
        _make_image(dir_b / "b2.jpg")

        found = discover_photos([dir_a, dir_b])

        assert {p.name for p in found} == {"a1.jpg", "b1.jpg", "b2.jpg"}

    def test_dedupes_when_same_directory_listed_twice(self, tmp_path):
        photos_dir = tmp_path / "photos"
        photos_dir.mkdir()
        _make_image(photos_dir / "only.jpg")

        found = discover_photos([photos_dir, photos_dir])

        assert [p.name for p in found] == ["only.jpg"]

    def test_dedupes_aliased_directory_paths(self, tmp_path):
        photos_dir = tmp_path / "photos"
        photos_dir.mkdir()
        _make_image(photos_dir / "only.jpg")
        aliased = photos_dir / "."

        found = discover_photos([photos_dir, aliased])

        assert [p.name for p in found] == ["only.jpg"]

    def test_individual_empty_directory_contributes_nothing(self, tmp_path):
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        photos_dir = tmp_path / "photos"
        photos_dir.mkdir()
        _make_image(photos_dir / "only.jpg")

        found = discover_photos([empty_dir, photos_dir])

        assert [p.name for p in found] == ["only.jpg"]

    def test_raises_when_all_directories_empty(self, tmp_path):
        empty_a = tmp_path / "empty_a"
        empty_a.mkdir()
        empty_b = tmp_path / "empty_b"
        empty_b.mkdir()

        with pytest.raises(PhotoCollectionError, match="No supported image files"):
            discover_photos([empty_a, empty_b])

    def test_raises_when_a_directory_does_not_exist(self, tmp_path):
        photos_dir = tmp_path / "photos"
        photos_dir.mkdir()
        _make_image(photos_dir / "only.jpg")
        missing = tmp_path / "missing"

        with pytest.raises(PhotoCollectionError, match="does not exist"):
            discover_photos([photos_dir, missing])


class TestCollectPhotosMultipleFolders:
    def test_date_order_interleaves_across_folders(self, tmp_path):
        dir_a = tmp_path / "a"
        dir_a.mkdir()
        dir_b = tmp_path / "b"
        dir_b.mkdir()
        _make_image(dir_a / "a_later.jpg", date_taken=datetime(2026, 6, 15, 12, 0, 0))
        _make_image(dir_b / "b_earlier.jpg", date_taken=datetime(2026, 6, 15, 8, 0, 0))

        photos = collect_photos([dir_a, dir_b], order="date")

        assert [p.filename for p in photos] == ["b_earlier.jpg", "a_later.jpg"]

    def test_folder_listing_order_does_not_affect_alphabetical_order(self, tmp_path):
        dir_a = tmp_path / "a"
        dir_a.mkdir()
        dir_b = tmp_path / "b"
        dir_b.mkdir()
        _make_image(dir_a / "z_from_a.jpg")
        _make_image(dir_b / "m_from_b.jpg")

        forward = collect_photos([dir_a, dir_b], order="alphabetical")
        reversed_ = collect_photos([dir_b, dir_a], order="alphabetical")

        assert [p.filename for p in forward] == [p.filename for p in reversed_] == [
            "m_from_b.jpg",
            "z_from_a.jpg",
        ]

    def test_folder_listing_order_does_not_affect_date_order(self, tmp_path):
        dir_a = tmp_path / "a"
        dir_a.mkdir()
        dir_b = tmp_path / "b"
        dir_b.mkdir()
        _make_image(dir_a / "a_later.jpg", date_taken=datetime(2026, 6, 15, 12, 0, 0))
        _make_image(dir_b / "b_earlier.jpg", date_taken=datetime(2026, 6, 15, 8, 0, 0))

        forward = collect_photos([dir_a, dir_b], order="date")
        reversed_ = collect_photos([dir_b, dir_a], order="date")

        assert [p.filename for p in forward] == [p.filename for p in reversed_] == [
            "b_earlier.jpg",
            "a_later.jpg",
        ]

    def test_no_duplicate_photos_when_folder_listed_twice(self, tmp_path):
        photos_dir = tmp_path / "photos"
        photos_dir.mkdir()
        _make_image(photos_dir / "only.jpg")

        photos = collect_photos([photos_dir, photos_dir], order="alphabetical")

        assert [p.filename for p in photos] == ["only.jpg"]

    def test_allows_one_empty_folder_among_others(self, tmp_path):
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        photos_dir = tmp_path / "photos"
        photos_dir.mkdir()
        _make_image(photos_dir / "only.jpg")

        photos = collect_photos([empty_dir, photos_dir], order="alphabetical")

        assert [p.filename for p in photos] == ["only.jpg"]

    def test_raises_when_all_folders_empty(self, tmp_path):
        empty_a = tmp_path / "empty_a"
        empty_a.mkdir()
        empty_b = tmp_path / "empty_b"
        empty_b.mkdir()

        with pytest.raises(PhotoCollectionError):
            collect_photos([empty_a, empty_b], order="alphabetical")
