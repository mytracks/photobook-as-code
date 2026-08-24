"""
Photo discovery, metadata reading, and ordering.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import logging

from PIL import Image
from PIL.ExifTags import TAGS

logger = logging.getLogger(__name__)


# Supported image extensions
SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG'}

# Minimum recommended resolution for print quality (pixels)
MIN_RECOMMENDED_WIDTH = 1200
MIN_RECOMMENDED_HEIGHT = 1200


@dataclass
class PhotoMetadata:
    """Metadata for a single photo."""
    path: Path
    filename: str
    date_taken: Optional[datetime] = None
    width: int = 0
    height: int = 0
    file_modified: Optional[datetime] = None
    
    @property
    def orientation(self) -> str:
        """Get photo orientation ('landscape' or 'portrait')."""
        return 'landscape' if self.width >= self.height else 'portrait'
    
    @property
    def sort_date(self) -> datetime:
        """Get the best available date for sorting."""
        return self.date_taken or self.file_modified or datetime.min


class PhotoCollectionError(Exception):
    """Raised when photo collection fails."""
    pass


def discover_photos(directories: List[Path], recursive: bool = False) -> List[Path]:
    """
    Discover all supported image files across one or more directories.

    Each directory is validated and searched independently; an individual
    directory is allowed to contain zero supported images. The discovered
    files are merged into one pool and deduplicated by resolved path, so a
    directory listed more than once (or two paths resolving to the same
    directory) contributes its photos only once.

    Args:
        directories: Directories to search
        recursive: Whether to search subdirectories

    Returns:
        List of photo file paths, deduplicated and sorted

    Raises:
        PhotoCollectionError: If a directory is invalid, or no photos are
            found across all directories combined
    """
    photos = []

    for directory in directories:
        if not directory.exists():
            raise PhotoCollectionError(f"Directory does not exist: {directory}")

        if not directory.is_dir():
            raise PhotoCollectionError(f"Not a directory: {directory}")

        if recursive:
            # Search recursively
            for ext in SUPPORTED_EXTENSIONS:
                # Normalize extension for glob
                ext_lower = ext.lower()
                photos.extend(directory.rglob(f"*{ext_lower}"))
                # Also check uppercase
                ext_upper = ext.upper()
                if ext_upper != ext_lower:
                    photos.extend(directory.rglob(f"*{ext_upper}"))
        else:
            # Search single level only
            for item in directory.iterdir():
                if item.is_file() and item.suffix in SUPPORTED_EXTENSIONS:
                    photos.append(item)

    # Remove duplicates by resolved path (across directories too) and sort
    photos = sorted({photo.resolve() for photo in photos})

    if not photos:
        directories_desc = ", ".join(str(d) for d in directories)
        raise PhotoCollectionError(
            f"No supported image files found in {directories_desc}. "
            f"Supported formats: JPG, JPEG, PNG"
        )

    return photos


def read_exif_date(image_path: Path) -> Optional[datetime]:
    """
    Read date taken from EXIF data.
    
    Args:
        image_path: Path to image file
        
    Returns:
        Datetime if found, None otherwise
    """
    try:
        with Image.open(image_path) as img:
            exif_data = img._getexif()
            
            if not exif_data:
                return None
            
            # Prioritize DateTimeOriginal (36867) over DateTime (306)
            # DateTimeOriginal is the actual capture time, DateTime may be modification time
            for tag_id in [36867, 306]:  # DateTimeOriginal, then DateTime
                if tag_id in exif_data:
                    value = exif_data[tag_id]
                    # Parse EXIF datetime format: "YYYY:MM:DD HH:MM:SS"
                    try:
                        return datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
                    except (ValueError, TypeError):
                        continue
            
            return None
            
    except Exception as e:
        logger.debug(f"Could not read EXIF from {image_path}: {e}")
        return None


def read_photo_metadata(photo_path: Path) -> PhotoMetadata:
    """
    Read metadata for a single photo.
    
    Args:
        photo_path: Path to photo file
        
    Returns:
        PhotoMetadata instance
    """
    # Get file modification time
    file_modified = datetime.fromtimestamp(photo_path.stat().st_mtime)
    
    # Try to read EXIF date
    date_taken = read_exif_date(photo_path)
    
    # Read image dimensions
    width, height = 0, 0
    try:
        with Image.open(photo_path) as img:
            width, height = img.size
    except Exception as e:
        logger.warning(f"Could not read dimensions from {photo_path}: {e}")
    
    return PhotoMetadata(
        path=photo_path,
        filename=photo_path.name,
        date_taken=date_taken,
        width=width,
        height=height,
        file_modified=file_modified,
    )


def collect_photos(directories: List[Path], order: str = "alphabetical",
                   recursive: bool = False) -> List[PhotoMetadata]:
    """
    Collect and order photos from one or more directories.

    Args:
        directories: Directories containing photos
        order: Ordering method - 'alphabetical' or 'date'
        recursive: Whether to search subdirectories

    Returns:
        Ordered list of photo metadata, merged across all directories

    Raises:
        PhotoCollectionError: If collection fails
    """
    # Discover photo files across all directories, merged into one pool
    photo_paths = discover_photos(directories, recursive)

    logger.info(f"Found {len(photo_paths)} photos across {len(directories)} folder(s)")
    
    # Read metadata for each photo
    photos = []
    for path in photo_paths:
        try:
            metadata = read_photo_metadata(path)
            photos.append(metadata)
        except Exception as e:
            logger.warning(f"Skipping {path}: {e}")
    
    if not photos:
        raise PhotoCollectionError("No valid photos could be loaded")
    
    # Order photos
    if order == "alphabetical":
        photos.sort(key=lambda p: p.filename.lower())
    elif order == "date":
        photos.sort(key=lambda p: p.sort_date)
        
        # Warn about missing EXIF data
        missing_exif = sum(1 for p in photos if p.date_taken is None)
        if missing_exif > 0:
            logger.warning(
                f"{missing_exif}/{len(photos)} photos lack EXIF date data, "
                f"using file modification time"
            )
    else:
        raise PhotoCollectionError(f"Invalid order method: {order}")
    
    # Check for low-resolution photos
    low_res_photos = [
        p for p in photos 
        if p.width < MIN_RECOMMENDED_WIDTH or p.height < MIN_RECOMMENDED_HEIGHT
    ]
    
    if low_res_photos:
        logger.warning(
            f"{len(low_res_photos)}/{len(photos)} photos have resolution "
            f"below recommended minimum ({MIN_RECOMMENDED_WIDTH}x{MIN_RECOMMENDED_HEIGHT}). "
            f"Print quality may be affected."
        )

    return photos


def group_photos_by_timestamp(photos: List[PhotoMetadata]) -> List[tuple[datetime, List[str]]]:
    """
    Group photos by identical timestamp, in chronological order.

    Args:
        photos: Photos to group, in any order

    Returns:
        List of (timestamp, filenames) tuples, one per distinct timestamp
        among the given photos, sorted chronologically. Filenames within a
        group are in the input list's relative order.
    """
    sorted_photos = sorted(photos, key=lambda p: p.sort_date)

    groups: List[tuple[datetime, List[str]]] = []
    for photo in sorted_photos:
        if groups and groups[-1][0] == photo.sort_date:
            groups[-1][1].append(photo.filename)
        else:
            groups.append((photo.sort_date, [photo.filename]))

    return groups


def format_text_label_stubs(photos: List[PhotoMetadata]) -> str:
    """
    Format photos as an empty `text_labels` YAML stub block, one entry per
    distinct timestamp among the photos, ready to paste into a
    configuration file's `text_labels` section.

    Args:
        photos: Photos to extract timestamps from

    Returns:
        YAML text block, e.g.:
            text_labels:
              - timestamp: "2026-04-30T09:12:03"  # IMG_0001.jpg
                text: ""
    """
    lines = ["text_labels:"]
    for timestamp, filenames in group_photos_by_timestamp(photos):
        comment = ", ".join(filenames)
        lines.append(f'  - timestamp: "{timestamp.isoformat()}"  # {comment}')
        lines.append('    text: ""')

    return "\n".join(lines) + "\n"
