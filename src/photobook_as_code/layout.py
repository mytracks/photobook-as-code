"""
Layout calculation for photo grid arrangements.
"""

from dataclasses import dataclass
from typing import List, Tuple, Optional
import math
from photobook_as_code.themes import LayoutTemplate
from photobook_as_code.photos import PhotoMetadata


@dataclass
class PhotoDistribution:
    """Distribution of photos across pages."""
    total_photos: int
    total_pages: int
    photos_per_page: int
    photos_on_last_page: int
    exact_page_count: bool = False  # Whether page count is enforced exactly
    sparse_distribution: bool = False  # Whether using interval-based sparse distribution
    photo_to_page_map: dict = None  # Mapping of photo index to page number for sparse distribution
    
    def __post_init__(self):
        """Initialize mutable defaults."""
        if self.photo_to_page_map is None:
            self.photo_to_page_map = {}
    
    def _calculate_sparse_page_assignments(self) -> dict:
        """
        Calculate which page each photo should appear on for sparse distribution.
        Uses interval-based spacing to distribute photos evenly across all pages.
        
        Returns:
            Dictionary mapping photo index to page number
        """
        if self.total_photos == 0:
            return {}
        
        # Calculate spacing interval (floating point for even distribution)
        interval = self.total_pages / self.total_photos
        
        assignments = {}
        for photo_idx in range(self.total_photos):
            # Calculate target page position and round to nearest integer
            page_num = round(photo_idx * interval)
            
            # Ensure first photo is on page 0
            if photo_idx == 0:
                page_num = 0
            
            # Ensure last photo is within valid page range
            if page_num >= self.total_pages:
                page_num = self.total_pages - 1
            
            assignments[photo_idx] = page_num
        
        return assignments
    
    def get_photos_for_page(self, page_num: int) -> int:
        """Get number of photos for a specific page (0-indexed)."""
        if self.sparse_distribution:
            # In sparse distribution mode, count photos assigned to this page
            photos_on_page = sum(1 for page in self.photo_to_page_map.values() 
                                if page == page_num)
            return photos_on_page
        elif self.exact_page_count:
            # In exact page count mode, use even distribution algorithm
            # This ensures ALL pages are used, not just consecutive filling
            base = self.total_photos // self.total_pages
            remainder = self.total_photos % self.total_pages
            
            # First 'remainder' pages get base + 1 photos
            # Remaining pages get base photos
            if page_num < remainder:
                return base + 1
            else:
                return base
        else:
            # Original behavior: all pages have photos_per_page except last
            if page_num < self.total_pages - 1:
                return self.photos_per_page
            else:
                return self.photos_on_last_page
    
    def get_photo_indices_for_page(self, page_num: int) -> list:
        """
        Get the photo indices (into all_photos list) for a specific page.
        
        Args:
            page_num: Page number (0-indexed)
            
        Returns:
            List of photo indices that should appear on this page
        """
        if self.sparse_distribution:
            # In sparse distribution, look up which photos are assigned to this page
            return [photo_idx for photo_idx, page in self.photo_to_page_map.items() 
                   if page == page_num]
        else:
            # For normal distribution, calculate photo range
            photos_before = sum(self.get_photos_for_page(i) for i in range(page_num))
            photos_on_page = self.get_photos_for_page(page_num)
            return list(range(photos_before, photos_before + photos_on_page))


class LayoutError(Exception):
    """Raised when layout calculation fails."""
    pass


def match_template(templates: List[LayoutTemplate], photos: List[PhotoMetadata]) -> LayoutTemplate:
    """
    Match photos to a layout template based on count and orientation.
    Prefers exact orientation order match.
    
    Args:
        templates: Available layout templates from theme
        photos: Photos for a specific page
        
    Returns:
        Matched LayoutTemplate
        
    Raises:
        LayoutError: If no matching template is found
    """
    photo_count = len(photos)
    orientations = [p.orientation for p in photos]
    
    # Filter by count
    matching_count = [t for t in templates if t.count == photo_count]
    
    if not matching_count:
        raise LayoutError(f"No layout template found for {photo_count} photos.")
        
    # Filter by orientations (independent of order first)
    valid_templates = []
    for t in matching_count:
        if sorted(t.orientations) == sorted(orientations):
            valid_templates.append(t)
            
    if not valid_templates:
        raise LayoutError(
            f"No layout template found for {photo_count} photos with orientations: {orientations}."
        )
        
    # Prefer exact order match
    for t in valid_templates:
        if t.orientations == orientations:
            return t
            
    # Fallback to any template with correct orientations
    return valid_templates[0]


def calculate_photos_per_page(total_photos: int, total_pages: int) -> int:
    """
    Calculate photos per page for even distribution.
    
    Args:
        total_photos: Total number of photos
        total_pages: Desired number of pages
        
    Returns:
        Photos per page (ceiling division)
        
    Raises:
        LayoutError: If values are invalid
    """
    if total_photos < 1:
        raise LayoutError("total_photos must be at least 1")
    
    if total_pages < 1:
        raise LayoutError("total_pages must be at least 1")
    
    # Use ceiling division to ensure all photos fit
    return math.ceil(total_photos / total_pages)


def distribute_photos(total_photos: int, photos_per_page: int = None, 
                      total_pages: int = None) -> PhotoDistribution:
    """
    Calculate photo distribution across pages.
    
    Args:
        total_photos: Total number of photos
        photos_per_page: Photos per page (mutually exclusive with total_pages)
        total_pages: Total pages desired (takes precedence if both specified)
        
    Returns:
        PhotoDistribution instance
        
    Raises:
        LayoutError: If parameters are invalid or inconsistent
    """
    # If both specified, total_pages takes precedence
    if photos_per_page is not None and total_pages is not None:
        photos_per_page = None  # Ignore photos_per_page
    
    if photos_per_page is None and total_pages is None:
        raise LayoutError("Must specify either photos_per_page or total_pages")
    
    if total_photos < 0:
        raise LayoutError("total_photos cannot be negative")
    
    # Handle edge case: zero photos
    if total_photos == 0:
        if total_pages is not None:
            # Generate empty pages if page count is specified
            return PhotoDistribution(
                total_photos=0,
                total_pages=total_pages,
                photos_per_page=0,
                photos_on_last_page=0,
                exact_page_count=True,
            )
        else:
            # No pages needed if no photos and no page count specified
            return PhotoDistribution(
                total_photos=0,
                total_pages=0,
                photos_per_page=photos_per_page or 0,
                photos_on_last_page=0,
                exact_page_count=False,
            )
    
    if photos_per_page is not None:
        # Photos-per-page mode: calculate minimum pages needed
        if photos_per_page < 1:
            raise LayoutError("photos_per_page must be at least 1")
        
        pages = math.ceil(total_photos / photos_per_page)
        photos_on_last = total_photos % photos_per_page
        if photos_on_last == 0:
            photos_on_last = photos_per_page
            
        return PhotoDistribution(
            total_photos=total_photos,
            total_pages=pages,
            photos_per_page=photos_per_page,
            photos_on_last_page=photos_on_last,
            exact_page_count=False,
        )
    
    else:  # total_pages specified - exact page count mode
        if total_pages < 1:
            raise LayoutError("total_pages must be at least 1")
        
        # Check if we need sparse distribution (more pages than photos)
        if total_pages > total_photos and total_photos > 0:
            # Sparse distribution: spread photos evenly across pages
            distribution = PhotoDistribution(
                total_photos=total_photos,
                total_pages=total_pages,
                photos_per_page=1,  # Each page with photo has exactly 1 photo
                photos_on_last_page=1,
                exact_page_count=True,
                sparse_distribution=True,
            )
            # Calculate page assignments using interval-based spacing
            distribution.photo_to_page_map = distribution._calculate_sparse_page_assignments()
            return distribution
        
        # Dense distribution: calculate photos per page for even distribution
        photos_pp = calculate_photos_per_page(total_photos, total_pages)
        
        # In exact page count mode, generate exactly the requested number of pages
        # Photos are distributed evenly, with remainder pages being empty
        photos_on_last = total_photos % photos_pp
        if photos_on_last == 0 and total_photos > 0:
            photos_on_last = photos_pp
        
        return PhotoDistribution(
            total_photos=total_photos,
            total_pages=total_pages,  # Use exact requested count
            photos_per_page=photos_pp,
            photos_on_last_page=photos_on_last,
            exact_page_count=True,  # Enable exact page count mode
        )


def fit_photo_in_cell(photo_width: int, photo_height: int,
                      cell_width: int, cell_height: int) -> Tuple[int, int, int, int]:
    """
    Calculate dimensions and position to fit photo in cell preserving aspect ratio.
    
    Args:
        photo_width: Original photo width
        photo_height: Original photo height
        cell_width: Cell width
        cell_height: Cell height
        
    Returns:
        Tuple of (fitted_width, fitted_height, x_offset, y_offset)
        Photo is centered in cell with letterboxing/pillarboxing as needed
    """
    # Calculate aspect ratios
    photo_aspect = photo_width / photo_height
    cell_aspect = cell_width / cell_height
    
    if photo_aspect > cell_aspect:
        # Photo is wider - fit to width
        fitted_width = cell_width
        fitted_height = int(cell_width / photo_aspect)
    else:
        # Photo is taller - fit to height
        fitted_height = cell_height
        fitted_width = int(cell_height * photo_aspect)
    
    # Center in cell
    x_offset = (cell_width - fitted_width) // 2
    y_offset = (cell_height - fitted_height) // 2
    
    return (fitted_width, fitted_height, x_offset, y_offset)
