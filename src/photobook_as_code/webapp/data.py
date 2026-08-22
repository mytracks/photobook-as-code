"""
Read-side data access for the web editor: loading the configuration,
collecting photos in the configured order, and looking up each photo's
current text_labels content - all reused, unchanged, from the existing
config/photos/text_labels modules.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..config import PhotobookConfig, load_config, validate_photos_path
from ..photos import PhotoMetadata, collect_photos
from ..text_labels import TextLabel, associate_text_labels_with_photos


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
    """A fresh, request-scoped view of a config file's photos and their text."""

    def __init__(
        self,
        config: PhotobookConfig,
        photos: List[PhotoMetadata],
        associations: List[Tuple[PhotoMetadata, Optional[TextLabel]]],
    ):
        self.config = config
        self.photos = photos
        self.associations = associations

    @property
    def count(self) -> int:
        return len(self.photos)

    def photo_at(self, index: int) -> PhotoMetadata:
        return self.photos[index]

    def text_for(self, index: int) -> str:
        """Current text for the photo at `index`, or '' if it has none yet."""
        label = self.label_for(index)
        return label.text if label is not None else ""

    def label_for(self, index: int) -> Optional[TextLabel]:
        _, label = self.associations[index]
        return label

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
        photo's date. Uses each photo's best-available date (falling back
        to file_modified) so this stays computable even when display_date
        falls back to showing a filename.
        """
        if index == 0:
            return True
        current = self.photo_at(index).sort_date.date()
        previous = self.photo_at(index - 1).sort_date.date()
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
    return EditorData(config=config, photos=photos, associations=associations)
