"""
Layout calculation for photo grid arrangements.
"""

from dataclasses import dataclass
from typing import List, Tuple, Dict, Any, Optional
import math
from enum import Enum


class PhotoOrientation(str, Enum):
    LANDSCAPE = "landscape"
    PORTRAIT = "portrait"


@dataclass
class PhotoPosition:
    x: float
    y: float


@dataclass
class PhotoSpec:
    orientation: PhotoOrientation
    position: PhotoPosition
    size: float


@dataclass
class LayoutTemplate:
    count: int
    photos: List[PhotoSpec]


@dataclass
class PhotoDistribution:
    """Distribution of photos across pages."""
    total_photos: int
    total_pages: int
    photos_per_page: int
    photos_on_last_page: int
    
    def get_photos_for_page(self, page_num: int) -> int:
        """Get number of photos for a specific page (0-indexed)."""
        if page_num < self.total_pages - 1:
            return self.photos_per_page
        else:
            return self.photos_on_last_page

class TemplateMatcher:
    """Matches photos to best available layout template."""
    def __init__(self, templates: List[LayoutTemplate]):
        self.templates = templates

    def match_by_count(self, photo_count: int) -> List[LayoutTemplate]:
        """
        Finds layout templates that match the given photo count.
        """
        return [template for template in self.templates if template.count == photo_count]

    def _get_orientation_counts(self, orientations: List[PhotoOrientation]) -> Dict[PhotoOrientation, int]:
        counts = {PhotoOrientation.LANDSCAPE: 0, PhotoOrientation.PORTRAIT: 0}
        for orientation in orientations:
            counts[orientation] += 1
        return counts

    def match_by_orientation_types_and_counts(self, photo_orientations: List[PhotoOrientation], 
                                              templates: List[LayoutTemplate]) -> List[LayoutTemplate]:
        """
        Finds layout templates that match the photo orientation types and counts, ignoring order.
        """
        target_counts = self._get_orientation_counts(photo_orientations)
        matching_templates = []
        for template in templates:
            template_orientations = [photo_spec.orientation for photo_spec in template.photos]
            template_counts = self._get_orientation_counts(template_orientations)
            if template_counts == target_counts:
                matching_templates.append(template)
        return matching_templates

    def select_best_template_by_order_preference(self, photo_orientations: List[PhotoOrientation], 
                                                 candidate_templates: List[LayoutTemplate]) -> LayoutTemplate | None:
        """
        Selects the best template from candidates, prioritizing exact orientation sequence match.
        This algorithm matches templates by count and orientation sequence, preferring exact
        order matches when multiple templates qualify. For example, a [landscape, portrait, portrait]
        sequence has different visual weight than [portrait, landscape, portrait].
        """
        for template in candidate_templates:
            template_orientations = [photo_spec.orientation for photo_spec in template.photos]
            if template_orientations == photo_orientations:
                return template
        return None

    def find_best_template(self, photo_orientations: List[PhotoOrientation]) -> LayoutTemplate | None:
        """
        Finds the best layout template for a given list of photo orientations.
        """
        photo_count = len(photo_orientations)

        # 1. Match by photo count
        count_matched_templates = self.match_by_count(photo_count)
        if not count_matched_templates:
            raise LayoutError(f"No layout templates found for {photo_count} photos.")

        # 2. Match by orientation types and counts (ignoring order initially)
        orientation_matched_templates = self.match_by_orientation_types_and_counts(
            photo_orientations, count_matched_templates
        )
        if not orientation_matched_templates:
            raise LayoutError(f"No layout templates found matching orientation types/counts for {photo_orientations}.")

        # 3. Select best template by exact order preference
        best_template = self.select_best_template_by_order_preference(
            photo_orientations, orientation_matched_templates
        )
        if not best_template:
            raise LayoutError(f"No exact order-matching template found for orientations: {photo_orientations}.")
        
        return best_template




@dataclass
class PageLayout:
    """Layout specification for a page."""
    page_width: int
    page_height: int
    photos_per_page: int
    cell_width: float
    cell_height: float
    cols: int
    rows: int


def distribute_photos(total_photos: int, photos_per_page: Optional[int] = None,
                      total_pages: Optional[int] = None) -> PhotoDistribution:
    """
    Distribute photos across pages.

    Args:
        total_photos: Total number of photos
        photos_per_page: Photos per page (or None if total_pages is specified)
        total_pages: Total number of pages (or None if photos_per_page is specified)

    Returns:
        PhotoDistribution instance

    Raises:
        LayoutError: If distribution calculation fails
    """
    if photos_per_page is not None and total_pages is not None:
        raise LayoutError("Cannot specify both photos_per_page and total_pages")

    if photos_per_page is not None:
        if photos_per_page <= 0:
            raise LayoutError("photos_per_page must be positive")
        calc_total_pages = math.ceil(total_photos / photos_per_page)
        photos_on_last_page = total_photos % photos_per_page
        if photos_on_last_page == 0:
            photos_on_last_page = photos_per_page
        calc_photos_per_page = photos_per_page
    elif total_pages is not None:
        if total_pages <= 0:
            raise LayoutError("total_pages must be positive")
        calc_total_pages = total_pages
        calc_photos_per_page = math.ceil(total_photos / total_pages)
        photos_on_last_page = total_photos - (total_pages - 1) * calc_photos_per_page
        if photos_on_last_page <= 0:
            photos_on_last_page = calc_photos_per_page
    else:
        raise LayoutError("Must specify either photos_per_page or total_pages")

    return PhotoDistribution(
        total_photos=total_photos,
        total_pages=calc_total_pages,
        photos_per_page=calc_photos_per_page,
        photos_on_last_page=photos_on_last_page,
    )


def calculate_page_layout(page_width: int, page_height: int, photos_per_page: int,
                          page_margin: int, grid_gap: int) -> PageLayout:
    """
    Calculate grid layout for a page.

    Args:
        page_width: Page width in pixels
        page_height: Page height in pixels
        photos_per_page: Number of photos per page
        page_margin: Margin around the page in pixels
        grid_gap: Gap between grid cells in pixels

    Returns:
        PageLayout instance
    """
    cols = math.ceil(math.sqrt(photos_per_page))
    rows = math.ceil(photos_per_page / cols)

    available_width = page_width - 2 * page_margin
    available_height = page_height - 2 * page_margin

    cell_width = (available_width - (cols - 1) * grid_gap) / cols
    cell_height = (available_height - (rows - 1) * grid_gap) / rows

    return PageLayout(
        page_width=page_width,
        page_height=page_height,
        photos_per_page=photos_per_page,
        cell_width=cell_width,
        cell_height=cell_height,
        cols=cols,
        rows=rows,
    )


class LayoutError(Exception):
    """Raised when layout calculation fails."""
    pass



