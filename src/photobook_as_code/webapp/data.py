"""
Read-side data access for the web editor: loading the configuration,
collecting photos in the configured order, merging in titles the same way
the renderer does, and looking up each item's current text_labels content -
built from the existing config/photos/text_labels modules.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from ..config import PhotobookConfig, load_config, validate_photos_path
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
    Caches the expensive photo-directory scan (collect_photos, which opens
    every photo file to read EXIF/dimensions) across requests for one
    running editor session, keyed by (photos_dir, order) so a changed
    layout.order naturally misses the cache instead of needing explicit
    invalidation.
    """

    def __init__(self):
        self._cache: Dict[Tuple[str, str], List[PhotoMetadata]] = {}

    def get(self, photos_dir: Path, order: str) -> List[PhotoMetadata]:
        key = (str(photos_dir), order)
        if key not in self._cache:
            self._cache[key] = collect_photos(photos_dir, order=order, recursive=False)
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

    def date_taken_iso(self, index: int) -> Optional[str]:
        """
        ISO 8601 timestamp of the photo's capture date, or None when no EXIF
        capture date is known (in which case `display_date` falls back to
        the filename and there is nothing to format on the client).
        """
        photo = self.photo_at(index)
        return photo.date_taken.isoformat() if photo.date_taken is not None else None

    def display_date(self, index: int) -> str:
        """
        The photo's capture date and time, formatted with weekday (e.g.
        "Saturday, June 14, 2025 · 09:00"), or its filename when no EXIF
        capture date is known - showing a real but unverified
        filesystem date as if it were the capture date would be
        misleading.
        """
        photo = self.photo_at(index)
        if photo.date_taken is None:
            return photo.filename
        date = photo.date_taken
        return f"{date.strftime('%A, %B')} {date.day}, {date.year} · {date.strftime('%H:%M')}"

    def is_new_day(self, index: int) -> bool:
        """
        Whether this photo's date differs from the previously displayed
        photo's date. Compares consecutive photos only (skipping over any
        title in between), using each photo's best-available date (falling
        back to file_modified) so this stays computable even when
        display_date falls back to showing a filename.
        """
        photo_index = self._photo_index(index)
        if photo_index == 0:
            return True
        current = self.photos[photo_index].sort_date.date()
        previous = self.photos[photo_index - 1].sort_date.date()
        return current != previous


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
    validate_photos_path(config)
    photos_dir = config.resolve_photos_path()
    if photo_cache is not None:
        photos = photo_cache.get(photos_dir, config.layout.order)
    else:
        photos = collect_photos(photos_dir, order=config.layout.order, recursive=False)
    associations = associate_text_labels_with_photos(config.text_labels, photos)
    titles = parse_title_labels(config.text_labels)
    items = merge_titles_with_photos(titles, photos)
    return EditorData(config=config, photos=photos, associations=associations, items=items)
