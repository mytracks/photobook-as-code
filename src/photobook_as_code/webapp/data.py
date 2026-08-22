"""
Read-side data access for the web editor: loading the configuration,
collecting photos in the configured order, and looking up each photo's
current text_labels content - all reused, unchanged, from the existing
config/photos/text_labels modules.
"""

from pathlib import Path
from typing import List, Optional, Tuple

from ..config import PhotobookConfig, load_config, validate_photos_path
from ..photos import PhotoMetadata, collect_photos
from ..text_labels import TextLabel, associate_text_labels_with_photos


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


def load_editor_data(config_path: Path) -> EditorData:
    """
    Load the configuration and photo list fresh from disk, in the same
    order and with the same photo/text associations the CLI render
    pipeline would use for this configuration.
    """
    config = load_config(config_path)
    validate_photos_path(config)
    photos_dir = config.resolve_photos_path()
    photos = collect_photos(photos_dir, order=config.layout.order, recursive=False)
    associations = associate_text_labels_with_photos(config.text_labels, photos)
    return EditorData(config=config, photos=photos, associations=associations)
