from datetime import datetime
from pathlib import Path

from photobook_as_code.photos import (
    PhotoMetadata,
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
