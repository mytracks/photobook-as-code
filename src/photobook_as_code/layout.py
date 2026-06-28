"""
Layout calculation for photo grid arrangements.
"""

from dataclasses import dataclass
from typing import List, Tuple
import math


@dataclass
class GridLayout:
    """Grid layout specification."""
    rows: int
    cols: int
    photos_per_page: int
    

@dataclass
class CellDimensions:
    """Dimensions for a grid cell."""
    width: int
    height: int
    x_offset: int
    y_offset: int


@dataclass
class PageLayout:
    """Complete layout specification for a page."""
    page_width: int
    page_height: int
    usable_width: int
    usable_height: int
    grid: GridLayout
    cell_width: int
    cell_height: int
    grid_gap: int
    page_margin: int
    
    def get_cell_positions(self) -> List[CellDimensions]:
        """Calculate position and size for each grid cell."""
        cells = []
        
        for row in range(self.grid.rows):
            for col in range(self.grid.cols):
                # Calculate position including grid gaps
                x = self.page_margin + col * (self.cell_width + self.grid_gap)
                y = self.page_margin + row * (self.cell_height + self.grid_gap)
                
                cells.append(CellDimensions(
                    width=self.cell_width,
                    height=self.cell_height,
                    x_offset=x,
                    y_offset=y,
                ))
        
        return cells


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


class LayoutError(Exception):
    """Raised when layout calculation fails."""
    pass


def calculate_grid_dimensions(photos_per_page: int) -> GridLayout:
    """
    Calculate optimal grid dimensions for given photos per page.
    
    Args:
        photos_per_page: Target number of photos per page
        
    Returns:
        GridLayout with rows and columns
        
    Raises:
        LayoutError: If photos_per_page is invalid
    """
    if photos_per_page < 1:
        raise LayoutError("photos_per_page must be at least 1")
    
    if photos_per_page == 1:
        return GridLayout(rows=1, cols=1, photos_per_page=1)
    
    # Find factors that create most square-like grid
    # Prefer layouts where rows >= cols (portrait orientation)
    sqrt = math.sqrt(photos_per_page)
    
    if sqrt == int(sqrt):
        # Perfect square
        dim = int(sqrt)
        return GridLayout(rows=dim, cols=dim, photos_per_page=photos_per_page)
    
    # Find best factorization
    best_rows, best_cols = 1, photos_per_page
    min_difference = photos_per_page
    
    for cols in range(1, photos_per_page + 1):
        if photos_per_page % cols == 0:
            rows = photos_per_page // cols
            
            if rows >= cols:  # Prefer portrait orientation
                difference = abs(rows - cols)
                if difference < min_difference:
                    min_difference = difference
                    best_rows, best_cols = rows, cols
    
    return GridLayout(rows=best_rows, cols=best_cols, photos_per_page=photos_per_page)


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
        total_pages: Total pages desired (mutually exclusive with photos_per_page)
        
    Returns:
        PhotoDistribution instance
        
    Raises:
        LayoutError: If parameters are invalid or inconsistent
    """
    if photos_per_page is not None and total_pages is not None:
        raise LayoutError("Cannot specify both photos_per_page and total_pages")
    
    if photos_per_page is None and total_pages is None:
        raise LayoutError("Must specify either photos_per_page or total_pages")
    
    if total_photos < 1:
        raise LayoutError("total_photos must be at least 1")
    
    if photos_per_page is not None:
        # Calculate pages needed
        pages = math.ceil(total_photos / photos_per_page)
        photos_on_last = total_photos % photos_per_page
        if photos_on_last == 0:
            photos_on_last = photos_per_page
            
        return PhotoDistribution(
            total_photos=total_photos,
            total_pages=pages,
            photos_per_page=photos_per_page,
            photos_on_last_page=photos_on_last,
        )
    
    else:  # total_pages specified
        # Calculate photos per page
        photos_pp = calculate_photos_per_page(total_photos, total_pages)
        photos_on_last = total_photos % photos_pp
        if photos_on_last == 0:
            photos_on_last = photos_pp
        
        # Recalculate actual pages needed (might be less than requested)
        actual_pages = math.ceil(total_photos / photos_pp)
        
        return PhotoDistribution(
            total_photos=total_photos,
            total_pages=actual_pages,
            photos_per_page=photos_pp,
            photos_on_last_page=photos_on_last,
        )


def calculate_cell_dimensions(usable_width: int, usable_height: int,
                              grid: GridLayout, grid_gap: int) -> Tuple[int, int]:
    """
    Calculate individual cell dimensions within grid.
    
    Args:
        usable_width: Available width after margins
        usable_height: Available height after margins
        grid: Grid layout specification
        grid_gap: Gap between grid cells in pixels
        
    Returns:
        Tuple of (cell_width, cell_height) in pixels
    """
    # Calculate total gap space
    horizontal_gaps = (grid.cols - 1) * grid_gap
    vertical_gaps = (grid.rows - 1) * grid_gap
    
    # Calculate cell dimensions
    cell_width = (usable_width - horizontal_gaps) // grid.cols
    cell_height = (usable_height - vertical_gaps) // grid.rows
    
    return (cell_width, cell_height)


def calculate_page_layout(page_width: int, page_height: int,
                          photos_per_page: int, page_margin: int,
                          grid_gap: int) -> PageLayout:
    """
    Calculate complete page layout.
    
    Args:
        page_width: Page width in pixels
        page_height: Page height in pixels
        photos_per_page: Number of photos per page
        page_margin: Margin around page edges in pixels
        grid_gap: Gap between grid cells in pixels
        
    Returns:
        PageLayout instance
        
    Raises:
        LayoutError: If layout is invalid
    """
    # Calculate usable area
    usable_width = page_width - (2 * page_margin)
    usable_height = page_height - (2 * page_margin)
    
    if usable_width <= 0 or usable_height <= 0:
        raise LayoutError("Page margins too large for page size")
    
    # Calculate grid
    grid = calculate_grid_dimensions(photos_per_page)
    
    # Calculate cell dimensions
    cell_width, cell_height = calculate_cell_dimensions(
        usable_width, usable_height, grid, grid_gap
    )
    
    if cell_width <= 0 or cell_height <= 0:
        raise LayoutError("Grid too large for available space")
    
    return PageLayout(
        page_width=page_width,
        page_height=page_height,
        usable_width=usable_width,
        usable_height=usable_height,
        grid=grid,
        cell_width=cell_width,
        cell_height=cell_height,
        grid_gap=grid_gap,
        page_margin=page_margin,
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
