"""
Read-side data access for the web editor: loading the configuration,
collecting photos in the configured order, merging in titles the same way
the renderer does, and looking up each item's current text_labels content -
built from the existing config/photos/text_labels modules.
"""

from datetime import date as CalendarDate
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from ..config import PhotobookConfig, load_config, validate_photo_folders
from ..photos import PhotoMetadata, collect_photos
from ..text_labels import (
    TextLabel,
    TitleLabel,
    associate_text_labels_with_photos,
    merge_titles_with_photos,
    parse_title_labels,
)

Item = Union[PhotoMetadata, TitleLabel]


class PhotoDirectoryCache:
    """
    Caches the expensive photo-folder scan (collect_photos, which opens
    every photo file to read EXIF/dimensions) across requests for one
    running editor session, keyed by (photo_folders, order) so a changed
    layout.order or folder set naturally misses the cache instead of needing
    explicit invalidation. The folder set is sorted before keying so listing
    order in `photo_folders` doesn't affect cache hits.
    """

    def __init__(self):
        self._cache: Dict[Tuple[Tuple[str, ...], str], List[PhotoMetadata]] = {}

    def get(self, photo_folders: List[Path], order: str) -> List[PhotoMetadata]:
        key = (tuple(sorted(str(folder) for folder in photo_folders)), order)
        if key not in self._cache:
            self._cache[key] = collect_photos(photo_folders, order=order, recursive=False)
        return self._cache[key]


class EditorData:
    """
    A fresh, request-scoped view of a config file's items - photos and
    titles, merged into the same order the photobook renderer would produce
    - and the photos' associated caption text.
    """

    def __init__(
        self,
        config: PhotobookConfig,
        photos: List[PhotoMetadata],
        associations: List[Tuple[PhotoMetadata, Optional[TextLabel]]],
        items: List[Item],
    ):
        self.config = config
        self.photos = photos
        self.associations = associations
        self.items = items

        # Maps each merged-sequence index to its position in `photos`
        # (None for a title item), so caption/date logic - which is
        # inherently photo-scoped - can keep working in terms of `photos`.
        self._item_to_photo_index: List[Optional[int]] = []
        photo_index = 0
        for item in items:
            if isinstance(item, TitleLabel):
                self._item_to_photo_index.append(None)
            else:
                self._item_to_photo_index.append(photo_index)
                photo_index += 1

    @property
    def count(self) -> int:
        return len(self.items)

    def item_at(self, index: int) -> Item:
        return self.items[index]

    def is_title(self, index: int) -> bool:
        return isinstance(self.items[index], TitleLabel)

    def title_at(self, index: int) -> TitleLabel:
        return self.items[index]

    def _photo_index(self, index: int) -> int:
        """The position within `photos` of the (photo) item at `index`."""
        return self._item_to_photo_index[index]

    def photo_at(self, index: int) -> PhotoMetadata:
        return self.photos[self._photo_index(index)]

    def text_for(self, index: int) -> str:
        """Current caption text for the photo at `index`, or '' if it has none yet."""
        label = self.label_for(index)
        return label.text if label is not None else ""

    def label_for(self, index: int) -> Optional[TextLabel]:
        _, label = self.associations[self._photo_index(index)]
        return label

    def title_text_for(self, index: int) -> str:
        """Current content of the title at `index`."""
        return self.title_at(index).title

    def has_gps(self, index: int) -> bool:
        """Whether the item at `index` is a photo with a known GPS location."""
        if self.is_title(index):
            return False
        return self.photo_at(index).gps is not None

    def date_taken_iso(self, index: int) -> Optional[str]:
        """
        ISO 8601 timestamp of the item's date - a title's own timestamp
        (always present), or a photo's capture date, or None when no EXIF
        capture date is known (in which case `display_date` falls back to
        the filename and there is nothing to format on the client).
        """
        if self.is_title(index):
            return self.title_at(index).timestamp.isoformat()
        photo = self.photo_at(index)
        return photo.date_taken.isoformat() if photo.date_taken is not None else None

    def display_date(self, index: int) -> str:
        """
        The item's date and time, formatted with weekday (e.g.
        "Saturday, June 14, 2025 · 09:00"). A title always uses its own
        timestamp. A photo uses its EXIF capture date when known, or its
        filename when not - showing a real but unverified filesystem date
        as if it were the capture date would be misleading.
        """
        if self.is_title(index):
            return self._format_date(self.title_at(index).timestamp)
        photo = self.photo_at(index)
        if photo.date_taken is None:
            return photo.filename
        return self._format_date(photo.date_taken)

    @staticmethod
    def _format_date(dt: datetime) -> str:
        return f"{dt.strftime('%A, %B')} {dt.day}, {dt.year} · {dt.strftime('%H:%M')}"

    def _item_date(self, index: int) -> CalendarDate:
        """The best-available calendar date for the item at `index`, used for new-day grouping."""
        if self.is_title(index):
            return self.title_at(index).timestamp.date()
        return self.photo_at(index).sort_date.date()

    def is_new_day(self, index: int) -> bool:
        """
        Whether this item's date differs from the previously displayed
        item's date, comparing across the full merged sequence of photos
        and titles together (not photos alone, skipping over titles), using
        each item's best-available date (falling back to file_modified for
        a photo) so this stays computable even when display_date falls back
        to showing a filename.
        """
        if index == 0:
            return True
        return self._item_date(index) != self._item_date(index - 1)


def load_editor_data(
    config_path: Path, photo_cache: Optional[PhotoDirectoryCache] = None
) -> EditorData:
    """
    Load the configuration fresh from disk (so hand-edited text_labels are
    always reflected), in the same order and with the same photo/text
    associations the CLI render pipeline would use for this configuration.

    The photo directory listing itself - expensive to compute, since it
    opens every photo file - is re-scanned fresh unless a `photo_cache` is
    given, in which case it's scanned once and reused.
    """
    config = load_config(config_path)
    validate_photo_folders(config)
    photo_folders = config.resolve_photo_folders()
    if photo_cache is not None:
        photos = photo_cache.get(photo_folders, config.layout.order)
    else:
        photos = collect_photos(photo_folders, order=config.layout.order, recursive=False)
    associations = associate_text_labels_with_photos(config.text_labels, photos)
    titles = parse_title_labels(config.text_labels)
    items = merge_titles_with_photos(titles, photos)
    return EditorData(config=config, photos=photos, associations=associations, items=items)
