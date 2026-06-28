"""
Tests for layout calculation module.
"""

import pytest
import math
from photobook_as_code.layout import (
    PhotoDistribution,
    distribute_photos,
    calculate_photos_per_page,
    calculate_grid_dimensions,
    LayoutError,
)


class TestPhotoDistribution:
    """Tests for PhotoDistribution dataclass."""
    
    def test_get_photos_for_page_normal_mode(self):
        """Test photo distribution in normal mode (photos_per_page specified)."""
        dist = PhotoDistribution(
            total_photos=10,
            total_pages=3,
            photos_per_page=4,
            photos_on_last_page=2,
            exact_page_count=False,
        )
        
        assert dist.get_photos_for_page(0) == 4
        assert dist.get_photos_for_page(1) == 4
        assert dist.get_photos_for_page(2) == 2
    
    def test_get_photos_for_page_exact_mode_with_photos(self):
        """Test photo distribution in exact page count mode with sufficient photos."""
        dist = PhotoDistribution(
            total_photos=20,
            total_pages=5,
            photos_per_page=4,
            photos_on_last_page=4,
            exact_page_count=True,
        )
        
        assert dist.get_photos_for_page(0) == 4
        assert dist.get_photos_for_page(1) == 4
        assert dist.get_photos_for_page(2) == 4
        assert dist.get_photos_for_page(3) == 4
        assert dist.get_photos_for_page(4) == 4
    
    def test_get_photos_for_page_exact_mode_with_excess_pages(self):
        """Test photo distribution when page count exceeds photos needed."""
        # 10 photos, 5 pages requested -> 2 photos per page, then 5th page is empty
        dist = PhotoDistribution(
            total_photos=10,
            total_pages=5,
            photos_per_page=2,
            photos_on_last_page=2,
            exact_page_count=True,
        )
        
        assert dist.get_photos_for_page(0) == 2
        assert dist.get_photos_for_page(1) == 2
        assert dist.get_photos_for_page(2) == 2
        assert dist.get_photos_for_page(3) == 2
        assert dist.get_photos_for_page(4) == 2
    
    def test_get_photos_for_page_exact_mode_empty_trailing_pages(self):
        """Test empty trailing pages when photos run out."""
        # 7 photos, 10 pages requested -> 1 per page, then empty
        dist = PhotoDistribution(
            total_photos=7,
            total_pages=10,
            photos_per_page=1,
            photos_on_last_page=1,
            exact_page_count=True,
        )
        
        assert dist.get_photos_for_page(0) == 1
        assert dist.get_photos_for_page(6) == 1
        assert dist.get_photos_for_page(7) == 0  # Empty
        assert dist.get_photos_for_page(8) == 0  # Empty
        assert dist.get_photos_for_page(9) == 0  # Empty


class TestDistributePhotos:
    """Tests for distribute_photos function."""
    
    def test_photos_per_page_mode(self):
        """Test distribution when photos_per_page is specified."""
        dist = distribute_photos(total_photos=10, photos_per_page=4)
        
        assert dist.total_photos == 10
        assert dist.total_pages == 3
        assert dist.photos_per_page == 4
        assert dist.photos_on_last_page == 2
        assert dist.exact_page_count is False
    
    def test_total_pages_mode(self):
        """Test distribution when total_pages is specified (exact mode)."""
        dist = distribute_photos(total_photos=20, total_pages=5)
        
        assert dist.total_photos == 20
        assert dist.total_pages == 5  # Exact count
        assert dist.photos_per_page == 4
        assert dist.exact_page_count is True
    
    def test_page_count_takes_precedence(self):
        """Test that page count takes precedence over photos_per_page when both specified."""
        dist = distribute_photos(total_photos=20, photos_per_page=10, total_pages=5)
        
        # Should use total_pages=5, not photos_per_page=10
        assert dist.total_pages == 5
        assert dist.photos_per_page == 4  # Calculated from pages
        assert dist.exact_page_count is True
    
    def test_exact_page_count_with_sufficient_photos(self):
        """Test exact page count when photos divide evenly."""
        dist = distribute_photos(total_photos=100, total_pages=10)
        
        assert dist.total_pages == 10
        assert dist.photos_per_page == 10
        assert dist.exact_page_count is True
        
        # Verify all pages get photos
        for i in range(10):
            assert dist.get_photos_for_page(i) == 10
    
    def test_exact_page_count_with_excess_pages(self):
        """Test exact page count when pages exceed photos needed."""
        dist = distribute_photos(total_photos=10, total_pages=20)
        
        assert dist.total_pages == 20  # Exactly 20 pages
        assert dist.photos_per_page == 1  # 1 photo per page
        assert dist.exact_page_count is True
        
        # First 10 pages have photos
        for i in range(10):
            assert dist.get_photos_for_page(i) == 1
        
        # Last 10 pages are empty
        for i in range(10, 20):
            assert dist.get_photos_for_page(i) == 0
    
    def test_exact_page_count_uneven_distribution(self):
        """Test exact page count with uneven photo distribution."""
        dist = distribute_photos(total_photos=23, total_pages=5)
        
        assert dist.total_pages == 5
        assert dist.photos_per_page == 5  # ceil(23/5)
        
        # Pages should have: 5, 5, 5, 5, 3
        assert dist.get_photos_for_page(0) == 5
        assert dist.get_photos_for_page(1) == 5
        assert dist.get_photos_for_page(2) == 5
        assert dist.get_photos_for_page(3) == 5
        assert dist.get_photos_for_page(4) == 3
    
    def test_zero_photos_with_page_count(self):
        """Test edge case: zero photos but page count specified."""
        dist = distribute_photos(total_photos=0, total_pages=5)
        
        assert dist.total_pages == 5
        assert dist.total_photos == 0
        assert dist.exact_page_count is True
        
        # All pages should be empty
        for i in range(5):
            assert dist.get_photos_for_page(i) == 0
    
    def test_zero_photos_with_photos_per_page(self):
        """Test edge case: zero photos with photos_per_page."""
        dist = distribute_photos(total_photos=0, photos_per_page=4)
        
        assert dist.total_pages == 0
        assert dist.total_photos == 0
        assert dist.exact_page_count is False
    
    def test_single_page_requested(self):
        """Test edge case: single page with multiple photos."""
        dist = distribute_photos(total_photos=10, total_pages=1)
        
        assert dist.total_pages == 1
        assert dist.photos_per_page == 10
        assert dist.get_photos_for_page(0) == 10
    
    def test_very_high_page_count(self):
        """Test edge case: very high page count (should still work)."""
        dist = distribute_photos(total_photos=5, total_pages=100)
        
        assert dist.total_pages == 100
        assert dist.photos_per_page == 1
        
        # First 5 pages have 1 photo each
        for i in range(5):
            assert dist.get_photos_for_page(i) == 1
        
        # Remaining 95 pages are empty
        for i in range(5, 100):
            assert dist.get_photos_for_page(i) == 0
    
    def test_error_no_parameters(self):
        """Test error when neither parameter is specified."""
        with pytest.raises(LayoutError, match="Must specify either"):
            distribute_photos(total_photos=10)
    
    def test_error_negative_photos(self):
        """Test error with negative photo count."""
        with pytest.raises(LayoutError, match="cannot be negative"):
            distribute_photos(total_photos=-5, total_pages=10)
    
    def test_error_invalid_photos_per_page(self):
        """Test error with invalid photos_per_page."""
        with pytest.raises(LayoutError, match="must be at least 1"):
            distribute_photos(total_photos=10, photos_per_page=0)
    
    def test_error_invalid_total_pages(self):
        """Test error with invalid total_pages."""
        with pytest.raises(LayoutError, match="must be at least 1"):
            distribute_photos(total_photos=10, total_pages=0)
    
    def test_backward_compatibility(self):
        """Test that existing behavior is preserved for photos_per_page mode."""
        # Old behavior: photos_per_page specified
        dist = distribute_photos(total_photos=25, photos_per_page=4)
        
        assert dist.total_pages == 7  # ceil(25/4)
        assert dist.photos_per_page == 4
        assert dist.exact_page_count is False
        
        # First 6 pages have 4 photos
        for i in range(6):
            assert dist.get_photos_for_page(i) == 4
        
        # Last page has 1 photo
        assert dist.get_photos_for_page(6) == 1


class TestCalculatePhotosPerPage:
    """Tests for calculate_photos_per_page function."""
    
    def test_even_distribution(self):
        """Test even distribution of photos."""
        assert calculate_photos_per_page(20, 5) == 4
        assert calculate_photos_per_page(100, 10) == 10
    
    def test_uneven_distribution_ceiling(self):
        """Test that ceiling division is used."""
        assert calculate_photos_per_page(23, 5) == 5  # ceil(23/5)
        assert calculate_photos_per_page(11, 3) == 4  # ceil(11/3)
    
    def test_more_pages_than_photos(self):
        """Test when pages exceed photos."""
        assert calculate_photos_per_page(5, 10) == 1  # ceil(5/10)
    
    def test_single_photo(self):
        """Test single photo across multiple pages."""
        assert calculate_photos_per_page(1, 5) == 1
    
    def test_error_invalid_photos(self):
        """Test error with invalid photo count."""
        with pytest.raises(LayoutError):
            calculate_photos_per_page(0, 5)
    
    def test_error_invalid_pages(self):
        """Test error with invalid page count."""
        with pytest.raises(LayoutError):
            calculate_photos_per_page(10, 0)


class TestCalculateGridDimensions:
    """Tests for calculate_grid_dimensions function."""
    
    def test_single_photo(self):
        """Test grid for single photo."""
        grid = calculate_grid_dimensions(1)
        assert grid.rows == 1
        assert grid.cols == 1
    
    def test_perfect_square(self):
        """Test grid for perfect square."""
        grid = calculate_grid_dimensions(4)
        assert grid.rows == 2
        assert grid.cols == 2
        
        grid = calculate_grid_dimensions(9)
        assert grid.rows == 3
        assert grid.cols == 3
    
    def test_rectangular_grid(self):
        """Test grid for non-square layouts."""
        grid = calculate_grid_dimensions(6)
        assert grid.rows * grid.cols == 6
        assert grid.rows >= grid.cols  # Portrait orientation preferred
    
    def test_error_invalid_count(self):
        """Test error with invalid photo count."""
        with pytest.raises(LayoutError):
            calculate_grid_dimensions(0)
        
        with pytest.raises(LayoutError):
            calculate_grid_dimensions(-1)
