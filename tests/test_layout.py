"""
Tests for layout calculation module.
"""

import pytest
import math
import logging
from typing import List
from photobook_as_code.layout import (
    PhotoDistribution,
    distribute_photos,
    calculate_photos_per_page,
    match_template,
    LayoutError,
)
from photobook_as_code.themes import LayoutTemplate, LayoutPhoto, LayoutPosition
from photobook_as_code.photos import PhotoMetadata
from photobook_as_code.text_labels import TitleLabel
from pathlib import Path
from datetime import datetime, timedelta

def make_photo(orientation: str, day: int = 1, seq: int = 0) -> PhotoMetadata:
    """A dummy photo. `day` (1-indexed) controls its calendar date; `seq`
    only disambiguates photos within the same day."""
    width = 1920 if orientation == 'landscape' else 1080
    height = 1080 if orientation == 'landscape' else 1920
    return PhotoMetadata(
        path=Path(f"dummy-{day}-{seq}.jpg"),
        filename=f"dummy-{day}-{seq}.jpg",
        date_taken=datetime(2026, 1, 1) + timedelta(days=day - 1, seconds=seq),
        width=width,
        height=height
    )

def make_photos(n: int, orientation: str = 'landscape', day: int = 1) -> List[PhotoMetadata]:
    """`n` dummy photos, all on the same calendar day."""
    return [make_photo(orientation, day=day, seq=i) for i in range(n)]

def make_multi_day_photos(day_sizes: List[int], orientation: str = 'landscape') -> List[PhotoMetadata]:
    """Dummy photos spread across consecutive days, `day_sizes[i]` photos on day i+1."""
    items = []
    for day_idx, size in enumerate(day_sizes, start=1):
        items.extend(make_photo(orientation, day=day_idx, seq=i) for i in range(size))
    return items

class TestMatchTemplate:
    """Tests for match_template function."""

    def test_match_exact_order(self):
        t1 = LayoutTemplate(count=2, photos=[
            LayoutPhoto('landscape', LayoutPosition(0.5, 0.25), 0.7),
            LayoutPhoto('portrait', LayoutPosition(0.5, 0.75), 0.7)
        ])
        t2 = LayoutTemplate(count=2, photos=[
            LayoutPhoto('portrait', LayoutPosition(0.5, 0.25), 0.7),
            LayoutPhoto('landscape', LayoutPosition(0.5, 0.75), 0.7)
        ])
        photos = [make_photo('landscape'), make_photo('portrait')]
        matched = match_template([t1, t2], photos)
        assert matched is t1

    def test_match_any_order_fallback(self):
        t1 = LayoutTemplate(count=2, photos=[
            LayoutPhoto('landscape', LayoutPosition(0.5, 0.25), 0.7),
            LayoutPhoto('portrait', LayoutPosition(0.5, 0.75), 0.7)
        ])
        photos = [make_photo('portrait'), make_photo('landscape')]
        matched = match_template([t1], photos)
        assert matched is t1

    def test_error_no_matching_count(self):
        t1 = LayoutTemplate(count=1, photos=[
            LayoutPhoto('landscape', LayoutPosition(0.5, 0.5), 0.8)
        ])
        photos = [make_photo('landscape'), make_photo('portrait')]
        with pytest.raises(LayoutError, match="No layout template found for 2 photos"):
            match_template([t1], photos)

    def test_error_no_matching_orientation(self):
        t1 = LayoutTemplate(count=2, photos=[
            LayoutPhoto('landscape', LayoutPosition(0.5, 0.25), 0.7),
            LayoutPhoto('landscape', LayoutPosition(0.5, 0.75), 0.7)
        ])
        photos = [make_photo('landscape'), make_photo('portrait')]
        with pytest.raises(LayoutError, match="with orientations"):
            match_template([t1], photos)

    def test_title_matches_as_landscape_orientation(self):
        """A title slot reports 'landscape' and matches a template built for a landscape photo."""
        t1 = LayoutTemplate(count=2, photos=[
            LayoutPhoto('portrait', LayoutPosition(0.5, 0.25), 0.7),
            LayoutPhoto('landscape', LayoutPosition(0.5, 0.75), 0.7)
        ])
        title = TitleLabel(timestamp=datetime.now(), title='A title')
        items = [make_photo('portrait'), title]
        matched = match_template([t1], items)
        assert matched is t1

    def test_mixed_photo_and_title_page_matches_by_combined_count(self):
        """Matching uses the total item count, including title slots."""
        t2 = LayoutTemplate(count=2, photos=[
            LayoutPhoto('portrait', LayoutPosition(0.5, 0.25), 0.7),
            LayoutPhoto('landscape', LayoutPosition(0.5, 0.75), 0.7)
        ])
        title = TitleLabel(timestamp=datetime.now(), title='A title')
        items = [make_photo('portrait'), title]
        with pytest.raises(LayoutError, match="No layout template found for 2 photos"):
            # A count:1 template shouldn't match a page with 1 photo + 1 title (count 2)
            match_template([LayoutTemplate(count=1, photos=[
                LayoutPhoto('landscape', LayoutPosition(0.5, 0.5), 0.8)
            ])], items)
        matched = match_template([t2], items)
        assert matched is t2

class TestPhotoDistribution:
    """Tests for PhotoDistribution dataclass, driven directly by an explicit photo_to_page_map."""

    def test_get_photos_for_page_normal_mode(self):
        """Test photo distribution in normal mode (photos_per_page specified)."""
        dist = PhotoDistribution(
            total_photos=10,
            total_pages=3,
            photo_to_page_map={i: i // 4 for i in range(10)},
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
            photo_to_page_map={i: i // 4 for i in range(20)},
            photos_per_page=4,
            photos_on_last_page=4,
            exact_page_count=True,
        )

        for page in range(5):
            assert dist.get_photos_for_page(page) == 4

    def test_get_photos_for_page_exact_mode_with_excess_pages(self):
        """Test photo distribution when page count exceeds photos needed."""
        # 10 photos, 5 pages requested -> 2 photos per page
        dist = PhotoDistribution(
            total_photos=10,
            total_pages=5,
            photo_to_page_map={i: i // 2 for i in range(10)},
            photos_per_page=2,
            photos_on_last_page=2,
            exact_page_count=True,
        )

        for page in range(5):
            assert dist.get_photos_for_page(page) == 2

    def test_get_photos_for_page_exact_mode_empty_trailing_pages(self):
        """Test empty trailing pages when photos run out."""
        # 7 photos, 10 pages requested -> 1 per page, then empty
        dist = PhotoDistribution(
            total_photos=7,
            total_pages=10,
            photo_to_page_map={i: i for i in range(7)},
            photos_per_page=1,
            photos_on_last_page=1,
            exact_page_count=True,
        )

        assert dist.get_photos_for_page(0) == 1
        assert dist.get_photos_for_page(6) == 1
        assert dist.get_photos_for_page(7) == 0  # Empty
        assert dist.get_photos_for_page(8) == 0  # Empty
        assert dist.get_photos_for_page(9) == 0  # Empty

    def test_get_photo_indices_for_page_sorted(self):
        """Indices for a page are returned sorted by their original sequence order."""
        dist = PhotoDistribution(
            total_photos=4,
            total_pages=2,
            photo_to_page_map={3: 0, 1: 0, 0: 1, 2: 1},
        )
        assert dist.get_photo_indices_for_page(0) == [1, 3]
        assert dist.get_photo_indices_for_page(1) == [0, 2]


class TestDistributePhotos:
    """
    Tests for distribute_photos in its day-blind mode (new_page_per_day=False,
    the function's default) - this is the original arithmetic distribution,
    now expressed as an explicit item->page mapping.
    """

    def test_photos_per_page_mode(self):
        """Test distribution when photos_per_page is specified."""
        dist = distribute_photos(items=make_photos(10), photos_per_page=4)

        assert dist.total_photos == 10
        assert dist.total_pages == 3
        assert dist.photos_per_page == 4
        assert dist.photos_on_last_page == 2
        assert dist.exact_page_count is False

    def test_total_pages_mode(self):
        """Test distribution when total_pages is specified (exact mode)."""
        dist = distribute_photos(items=make_photos(20), total_pages=5)

        assert dist.total_photos == 20
        assert dist.total_pages == 5  # Exact count
        assert dist.photos_per_page == 4
        assert dist.exact_page_count is True

    def test_page_count_takes_precedence(self):
        """Test that page count takes precedence over photos_per_page when both specified."""
        dist = distribute_photos(items=make_photos(20), photos_per_page=10, total_pages=5)

        # Should use total_pages=5, not photos_per_page=10
        assert dist.total_pages == 5
        assert dist.photos_per_page == 4  # Calculated from pages
        assert dist.exact_page_count is True

    def test_exact_page_count_with_sufficient_photos(self):
        """Test exact page count when photos divide evenly."""
        dist = distribute_photos(items=make_photos(100), total_pages=10)

        assert dist.total_pages == 10
        assert dist.photos_per_page == 10
        assert dist.exact_page_count is True

        # Verify all pages get photos
        for i in range(10):
            assert dist.get_photos_for_page(i) == 10

    def test_exact_page_count_with_excess_pages(self):
        """Test exact page count when pages exceed photos needed (sparse distribution)."""
        dist = distribute_photos(items=make_photos(10), total_pages=20)

        assert dist.total_pages == 20  # Exactly 20 pages
        assert dist.photos_per_page == 1  # 1 photo per page
        assert dist.exact_page_count is True
        assert dist.sparse_distribution is True  # Should use sparse distribution

        # Total photos distributed should be 10
        total_photos_placed = sum(dist.get_photos_for_page(i) for i in range(20))
        assert total_photos_placed == 10

        # Photos should be spread across the range, not consecutive
        # With interval = 2.0, photos should be at: 0, 2, 4, 6, 8, 10, 12, 14, 16, 18
        pages_with_photos = [i for i in range(20) if dist.get_photos_for_page(i) == 1]
        assert len(pages_with_photos) == 10
        assert pages_with_photos[0] == 0  # First photo
        assert pages_with_photos[-1] == 18  # Last photo near end

    def test_exact_page_count_uneven_distribution(self):
        """Test exact page count with uneven photo distribution."""
        dist = distribute_photos(items=make_photos(23), total_pages=5)

        assert dist.total_pages == 5
        assert dist.photos_per_page == 5  # ceil(23/5)

        # Even distribution: 23 // 5 = 4 base, 23 % 5 = 3 remainder
        # First 3 pages get 5 photos (4+1), last 2 pages get 4 photos
        assert dist.get_photos_for_page(0) == 5
        assert dist.get_photos_for_page(1) == 5
        assert dist.get_photos_for_page(2) == 5
        assert dist.get_photos_for_page(3) == 4
        assert dist.get_photos_for_page(4) == 4

        # Verify total = 23
        total = sum(dist.get_photos_for_page(i) for i in range(5))
        assert total == 23

    def test_exact_page_count_168_photos_100_pages_legacy_arithmetic(self):
        """new_page_per_day=False reproduces the original arithmetic distribution exactly."""
        dist = distribute_photos(items=make_photos(168), total_pages=100)

        assert dist.total_pages == 100
        assert dist.exact_page_count is True
        assert dist.sparse_distribution is False  # Dense distribution, not sparse

        # Even distribution: 168 // 100 = 1 base, 168 % 100 = 68 remainder
        # First 68 pages get 2 photos, remaining 32 pages get 1 photo
        base = 168 // 100  # 1
        remainder = 168 % 100  # 68

        # Verify distribution
        for i in range(remainder):
            assert dist.get_photos_for_page(i) == base + 1  # 2 photos

        for i in range(remainder, 100):
            assert dist.get_photos_for_page(i) == base  # 1 photo

        # Verify total photos distributed = 168
        total = sum(dist.get_photos_for_page(i) for i in range(100))
        assert total == 168

        # Verify NO empty pages (bug was: pages 84-99 were empty)
        for i in range(100):
            assert dist.get_photos_for_page(i) > 0, f"Page {i} should not be empty"

    def test_zero_photos_with_page_count(self):
        """Test edge case: zero photos but page count specified."""
        dist = distribute_photos(items=[], total_pages=5)

        assert dist.total_pages == 5
        assert dist.total_photos == 0
        assert dist.exact_page_count is True

        # All pages should be empty
        for i in range(5):
            assert dist.get_photos_for_page(i) == 0

    def test_zero_photos_with_photos_per_page(self):
        """Test edge case: zero photos with photos_per_page."""
        dist = distribute_photos(items=[], photos_per_page=4)

        assert dist.total_pages == 0
        assert dist.total_photos == 0
        assert dist.exact_page_count is False

    def test_single_page_requested(self):
        """Test edge case: single page with multiple photos."""
        dist = distribute_photos(items=make_photos(10), total_pages=1)

        assert dist.total_pages == 1
        assert dist.photos_per_page == 10
        assert dist.get_photos_for_page(0) == 10

    def test_very_high_page_count(self):
        """Test edge case: very high page count (sparse distribution)."""
        dist = distribute_photos(items=make_photos(5), total_pages=100)

        assert dist.total_pages == 100
        assert dist.photos_per_page == 1
        assert dist.sparse_distribution is True

        # Total photos distributed should be 5
        total_photos_placed = sum(dist.get_photos_for_page(i) for i in range(100))
        assert total_photos_placed == 5

        # Photos should be evenly spaced, not consecutive
        # With interval = 20.0, photos should be at: 0, 20, 40, 60, 80
        pages_with_photos = [i for i in range(100) if dist.get_photos_for_page(i) == 1]
        assert len(pages_with_photos) == 5
        assert pages_with_photos[0] == 0  # First photo
        assert pages_with_photos[-1] == 80  # Last photo

    def test_error_no_parameters(self):
        """Test error when neither parameter is specified."""
        with pytest.raises(LayoutError, match="Must specify either"):
            distribute_photos(items=make_photos(10))

    def test_error_invalid_photos_per_page(self):
        """Test error with invalid photos_per_page."""
        with pytest.raises(LayoutError, match="must be at least 1"):
            distribute_photos(items=make_photos(10), photos_per_page=0)

    def test_error_invalid_total_pages(self):
        """Test error with invalid total_pages."""
        with pytest.raises(LayoutError, match="must be at least 1"):
            distribute_photos(items=make_photos(10), total_pages=0)

    def test_backward_compatibility(self):
        """Test that existing behavior is preserved for photos_per_page mode."""
        # Old behavior: photos_per_page specified
        dist = distribute_photos(items=make_photos(25), photos_per_page=4)

        assert dist.total_pages == 7  # ceil(25/4)
        assert dist.photos_per_page == 4
        assert dist.exact_page_count is False

        # First 6 pages have 4 photos
        for i in range(6):
            assert dist.get_photos_for_page(i) == 4

        # Last page has 1 photo
        assert dist.get_photos_for_page(6) == 1

    def test_sparse_distribution_8_photos_15_pages(self):
        """Test sparse distribution with 8 photos across 15 pages."""
        dist = distribute_photos(items=make_photos(8), total_pages=15)

        assert dist.total_photos == 8
        assert dist.total_pages == 15
        assert dist.sparse_distribution is True
        assert dist.photos_per_page == 1

        # Count total photos distributed
        total_photos_placed = sum(dist.get_photos_for_page(i) for i in range(15))
        assert total_photos_placed == 8

        # Verify each page has 0 or 1 photo
        for i in range(15):
            assert dist.get_photos_for_page(i) in [0, 1]

    def test_sparse_distribution_3_photos_10_pages(self):
        """Test sparse distribution with 3 photos across 10 pages."""
        dist = distribute_photos(items=make_photos(3), total_pages=10)

        assert dist.total_photos == 3
        assert dist.total_pages == 10
        assert dist.sparse_distribution is True
        assert dist.photos_per_page == 1

        # Count total photos distributed
        total_photos_placed = sum(dist.get_photos_for_page(i) for i in range(10))
        assert total_photos_placed == 3

        # Verify each page has 0 or 1 photo
        for i in range(10):
            assert dist.get_photos_for_page(i) in [0, 1]

    def test_sparse_distribution_even_spacing(self):
        """Test that photos are evenly spaced across page range."""
        dist = distribute_photos(items=make_photos(5), total_pages=25)

        assert dist.sparse_distribution is True

        # Find pages with photos
        pages_with_photos = [i for i in range(25) if dist.get_photos_for_page(i) == 1]

        assert len(pages_with_photos) == 5

        # Check spacing is even (interval = 5.0)
        # Expected positions: 0, 5, 10, 15, 20
        assert pages_with_photos == [0, 5, 10, 15, 20]

        # Calculate intervals between consecutive photos
        intervals = [pages_with_photos[i+1] - pages_with_photos[i]
                    for i in range(len(pages_with_photos)-1)]

        # All intervals should be exactly 5
        assert all(interval == 5 for interval in intervals)

    def test_sparse_distribution_single_photo_many_pages(self):
        """Test edge case: 1 photo across many pages."""
        dist = distribute_photos(items=make_photos(1), total_pages=20)

        assert dist.total_photos == 1
        assert dist.total_pages == 20
        assert dist.sparse_distribution is True

        # Exactly one page should have a photo
        pages_with_photos = sum(dist.get_photos_for_page(i) for i in range(20))
        assert pages_with_photos == 1

        # First page should have the photo (as per algorithm)
        assert dist.get_photos_for_page(0) == 1

    def test_sparse_distribution_backward_compatibility_photos_gte_pages(self):
        """Test that sparse distribution is NOT used when photos >= pages."""
        # When photos >= pages, use normal distribution, not sparse
        dist = distribute_photos(items=make_photos(10), total_pages=5)

        assert dist.sparse_distribution is False
        assert dist.exact_page_count is True

        # Should distribute normally: 2 photos per page
        assert dist.photos_per_page == 2
        for i in range(5):
            assert dist.get_photos_for_page(i) == 2


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


class TestSparseDistributionIntegration:
    """Integration tests for sparse distribution with real configurations."""

    def test_sparse_distribution_8_photos_15_pages_integration(self):
        """Test sparse distribution with 8 photos across 15 pages (real scenario)."""
        # This matches config-excess-pages.yaml
        dist = distribute_photos(items=make_photos(8), total_pages=15)

        assert dist.sparse_distribution is True
        assert dist.total_photos == 8
        assert dist.total_pages == 15

        # Verify photos are distributed at expected intervals
        # interval = 15 / 8 = 1.875
        # Expected positions: round(0*1.875)=0, round(1*1.875)=2, round(2*1.875)=4,
        #                     round(3*1.875)=6, round(4*1.875)=8, round(5*1.875)=9,
        #                     round(6*1.875)=11, round(7*1.875)=13
        expected_pages_with_photos = [0, 2, 4, 6, 8, 9, 11, 13]
        actual_pages_with_photos = [i for i in range(15) if dist.get_photos_for_page(i) == 1]

        assert actual_pages_with_photos == expected_pages_with_photos

        # Verify blank pages are truly blank (return 0 photos)
        blank_pages = [1, 3, 5, 7, 10, 12, 14]
        for page in blank_pages:
            assert dist.get_photos_for_page(page) == 0

    def test_sparse_distribution_3_photos_10_pages_integration(self):
        """Test sparse distribution with 3 photos across 10 pages."""
        dist = distribute_photos(items=make_photos(3), total_pages=10)

        assert dist.sparse_distribution is True

        # interval = 10 / 3 = 3.333...
        # Expected positions: 0, round(3.333)=3, round(6.667)=7
        expected_pages_with_photos = [0, 3, 7]
        actual_pages_with_photos = [i for i in range(10) if dist.get_photos_for_page(i) == 1]

        assert actual_pages_with_photos == expected_pages_with_photos

        # Verify all other pages are blank
        blank_pages = [1, 2, 4, 5, 6, 8, 9]
        for page in blank_pages:
            assert dist.get_photos_for_page(page) == 0

    def test_sparse_distribution_2_photos_5_pages_integration(self):
        """Test sparse distribution with 2 photos across 5 pages."""
        dist = distribute_photos(items=make_photos(2), total_pages=5)

        assert dist.sparse_distribution is True

        # interval = 5 / 2 = 2.5
        # Expected positions: 0, round(2.5)=2
        expected_pages_with_photos = [0, 2]
        actual_pages_with_photos = [i for i in range(5) if dist.get_photos_for_page(i) == 1]

        assert actual_pages_with_photos == expected_pages_with_photos

        # Verify blank pages
        blank_pages = [1, 3, 4]
        for page in blank_pages:
            assert dist.get_photos_for_page(page) == 0

    def test_sparse_distribution_1_photo_10_pages_integration(self):
        """Test sparse distribution with 1 photo across 10 pages."""
        dist = distribute_photos(items=make_photos(1), total_pages=10)

        assert dist.sparse_distribution is True

        # Single photo should be on page 0
        assert dist.get_photos_for_page(0) == 1

        # All other pages should be blank
        for page in range(1, 10):
            assert dist.get_photos_for_page(page) == 0

    def test_various_sparse_ratios(self):
        """Test various photo/page ratios for correct sparse distribution."""
        test_cases = [
            (2, 5),   # 2:5 ratio
            (1, 10),  # 1:10 ratio
            (8, 15),  # 8:15 ratio
            (5, 20),  # 1:4 ratio
            (3, 12),  # 1:4 ratio
        ]

        for photos, pages in test_cases:
            dist = distribute_photos(items=make_photos(photos), total_pages=pages)

            # Verify it's sparse distribution
            assert dist.sparse_distribution is True, f"Failed for {photos}:{pages}"

            # Verify total photos distributed
            total_distributed = sum(dist.get_photos_for_page(i) for i in range(pages))
            assert total_distributed == photos, f"Failed for {photos}:{pages}"

            # Verify each page has 0 or 1 photo
            for i in range(pages):
                assert dist.get_photos_for_page(i) in [0, 1], f"Failed for {photos}:{pages} page {i}"

    def test_memory_efficiency_with_sparse_distribution(self):
        """Test that sparse distribution doesn't store excessive data."""
        # Create distribution for a large sparse scenario
        dist = distribute_photos(items=make_photos(100), total_pages=1000)

        assert dist.sparse_distribution is True

        # photo_to_page_map should only store 100 entries (one per photo)
        assert len(dist.photo_to_page_map) == 100

        # Verify distribution still works correctly
        total_distributed = sum(dist.get_photos_for_page(i) for i in range(1000))
        assert total_distributed == 100


class TestDayAwareDistribution:
    """Tests for day-boundary page breaks (new_page_per_day=True)."""

    def test_new_day_starts_new_page(self):
        """Two days of 2 photos each get their own pages, though all 4 would fit on one."""
        items = make_multi_day_photos([2, 2])
        dist = distribute_photos(items=items, photos_per_page=4, new_page_per_day=True)
        assert dist.total_pages == 2
        assert dist.get_photo_indices_for_page(0) == [0, 1]
        assert dist.get_photo_indices_for_page(1) == [2, 3]

    def test_title_starts_new_page_on_day_change(self):
        """A title on a new calendar day starts a new page, same as a photo would."""
        photo = make_photo('landscape', day=1, seq=0)
        title = TitleLabel(timestamp=datetime(2026, 1, 2), title="Day 2")
        items = [photo, title]
        dist = distribute_photos(items=items, photos_per_page=4, new_page_per_day=True)
        assert dist.total_pages == 2
        assert dist.get_photo_indices_for_page(0) == [0]
        assert dist.get_photo_indices_for_page(1) == [1]

    def test_title_same_day_does_not_start_new_page(self):
        """A title on the same calendar day as the preceding item stays on its page."""
        photo = make_photo('landscape', day=1, seq=0)
        title = TitleLabel(timestamp=datetime(2026, 1, 1, 12), title="Later that day")
        items = [photo, title]
        dist = distribute_photos(items=items, photos_per_page=4, new_page_per_day=True)
        assert dist.total_pages == 1
        assert dist.get_photo_indices_for_page(0) == [0, 1]

    def test_reappearing_day_is_a_separate_block(self):
        """A calendar day that reoccurs later (non-adjacent) is not merged with its earlier run."""
        items = make_photo('landscape', day=1, seq=0), make_photo('landscape', day=2, seq=0), make_photo('landscape', day=1, seq=1)
        dist = distribute_photos(items=list(items), photos_per_page=4, new_page_per_day=True)
        assert dist.total_pages == 3
        assert dist.get_photo_indices_for_page(0) == [0]
        assert dist.get_photo_indices_for_page(1) == [1]
        assert dist.get_photo_indices_for_page(2) == [2]

    def test_day_rule_applies_without_fixed_page_count(self):
        """photos_per_page mode grows the book at day boundaries; no fixed budget to protect."""
        items = make_multi_day_photos([3, 3, 3])
        dist = distribute_photos(items=items, photos_per_page=4, new_page_per_day=True)
        assert dist.total_pages == 3
        for page in range(3):
            assert dist.get_photos_for_page(page) == 3

    def test_day_rule_disabled_matches_legacy_flexible_mode(self):
        """new_page_per_day=False ignores day boundaries entirely (task 6.2 regression)."""
        items = make_multi_day_photos([3, 3, 3])
        dist_multi_day = distribute_photos(items=items, photos_per_page=4, new_page_per_day=False)
        dist_single_day = distribute_photos(items=make_photos(9), photos_per_page=4, new_page_per_day=False)
        assert dist_multi_day.total_pages == dist_single_day.total_pages == 3
        assert dist_multi_day.get_photos_for_page(0) == 4
        assert dist_multi_day.get_photos_for_page(1) == 4
        assert dist_multi_day.get_photos_for_page(2) == 1

    def test_day_rule_disabled_matches_legacy_exact_mode(self):
        """new_page_per_day=False in exact-pages mode reproduces the original arithmetic (task 4.3)."""
        items = make_multi_day_photos([1] * 168)
        dist = distribute_photos(items=items, total_pages=100, new_page_per_day=False)
        legacy = distribute_photos(items=make_photos(168), total_pages=100, new_page_per_day=False)
        assert dist.photo_to_page_map == legacy.photo_to_page_map


class TestMergeFallback:
    """Tests for the last-resort day-boundary merge fallback when the page budget is tight."""

    def test_insufficient_budget_merges_days(self):
        """5 single-photo days can't each get a page within a 3-page budget; some merge."""
        items = make_multi_day_photos([1, 1, 1, 1, 1])
        dist = distribute_photos(
            items=items, total_pages=3, new_page_per_day=True, max_items_per_page=4
        )
        assert dist.total_pages == 3
        assert sum(dist.get_photos_for_page(i) for i in range(3)) == 5

    def test_deterministic_merge_prefers_earliest_boundary(self):
        """
        Hand-verified: 4 single-item days, 2 pages. The natural per-page density here
        is ceil(4/2)=2 (max_items_per_page=4 is just a validation ceiling, unused as
        the pack size) - merging proceeds pairwise, earliest tied boundary first, until
        two 2-item blocks remain, each densely packed onto its own page.
        """
        items = make_multi_day_photos([1, 1, 1, 1])
        dist = distribute_photos(
            items=items, total_pages=2, new_page_per_day=True, max_items_per_page=4
        )
        assert dist.total_pages == 2
        assert dist.get_photo_indices_for_page(0) == [0, 1]
        assert dist.get_photo_indices_for_page(1) == [2, 3]

    def test_exact_page_count_still_honored_after_merge(self):
        items = make_multi_day_photos([1] * 10)
        dist = distribute_photos(
            items=items, total_pages=4, new_page_per_day=True, max_items_per_page=4
        )
        assert dist.total_pages == 4
        assert sum(dist.get_photos_for_page(i) for i in range(4)) == 10

    def test_merge_logs_warning(self, caplog):
        items = make_multi_day_photos([1, 1, 1, 1, 1])
        with caplog.at_level(logging.WARNING):
            distribute_photos(
                items=items, total_pages=3, new_page_per_day=True, max_items_per_page=4
            )
        assert any("merged" in record.message.lower() for record in caplog.records)

    def test_determinism_with_merge_fallback(self):
        items = make_multi_day_photos([1] * 6)
        kwargs = dict(total_pages=3, new_page_per_day=True, max_items_per_page=4)
        d1 = distribute_photos(items=items, **kwargs)
        d2 = distribute_photos(items=items, **kwargs)
        assert d1.photo_to_page_map == d2.photo_to_page_map


class TestOrientationTieredSplitting:
    """Tests for orientation-matched slack-spending (final 2-item-page splits only)."""

    def test_both_match_split_first(self):
        """Book is portrait; a PP page and an LL page both exist - PP splits first."""
        items = [
            make_photo('portrait', day=1, seq=0),
            make_photo('portrait', day=1, seq=1),
            make_photo('landscape', day=1, seq=2),
            make_photo('landscape', day=1, seq=3),
        ]
        dist = distribute_photos(
            items=items, total_pages=3, new_page_per_day=True,
            max_items_per_page=2, book_orientation='portrait',
        )
        assert dist.total_pages == 3
        assert dist.get_photo_indices_for_page(0) == [0]
        assert dist.get_photo_indices_for_page(1) == [1]
        assert dist.get_photo_indices_for_page(2) == [2, 3]

    def test_partial_match_splits_before_no_match(self):
        """A page with one matching + one non-matching item splits before an all-non-matching page."""
        items = [
            make_photo('landscape', day=1, seq=0),
            make_photo('landscape', day=1, seq=1),
            make_photo('portrait', day=1, seq=2),
            make_photo('landscape', day=1, seq=3),
        ]
        dist = distribute_photos(
            items=items, total_pages=3, new_page_per_day=True,
            max_items_per_page=2, book_orientation='portrait',
        )
        assert dist.get_photo_indices_for_page(0) == [0, 1]
        assert dist.get_photo_indices_for_page(1) == [2]
        assert dist.get_photo_indices_for_page(2) == [3]

    def test_splits_spread_across_book(self):
        """When more matching pages qualify than slack requires, the chosen ones spread out."""
        items = []
        for d in range(1, 4):
            items.append(make_photo('portrait', day=d, seq=0))
            items.append(make_photo('portrait', day=d, seq=1))
        dist = distribute_photos(
            items=items, total_pages=5, new_page_per_day=True,
            max_items_per_page=2, book_orientation='portrait',
        )
        assert dist.total_pages == 5
        assert dist.get_photos_for_page(0) == 1  # split
        assert dist.get_photos_for_page(1) == 1
        assert dist.get_photos_for_page(2) == 2  # untouched, spread away from the split pages
        assert dist.get_photos_for_page(3) == 1
        assert dist.get_photos_for_page(4) == 1

    def test_block_growth_for_caps_above_two_stays_within_floor_and_ceil(self):
        """
        16 items / 5 pages -> natural density M=ceil(16/5)=4, dividing evenly into
        four 4-item pages with slack=1. Splitting a single page can't keep both
        halves within {3, 4} (only possible when the cap is 2), so the single day
        block is grown to 5 pages and re-evenly-distributed instead: every page
        stays within {3, 4}, never dropping to a stray single-item page.
        """
        items = make_photos(16, orientation='landscape', day=1)
        dist = distribute_photos(
            items=items, total_pages=5, new_page_per_day=True,
            max_items_per_page=4, book_orientation='portrait',
        )
        assert dist.total_pages == 5
        assert sum(dist.get_photos_for_page(i) for i in range(5)) == 16
        counts = sorted(dist.get_photos_for_page(i) for i in range(5))
        assert counts == [3, 3, 3, 3, 4]


class TestDayAwareDeterminism:
    """Determinism guarantees for the day-aware distribution path."""

    def test_repeated_calls_produce_identical_mapping(self):
        items = make_multi_day_photos([2, 3, 1, 4, 2])
        kwargs = dict(total_pages=6, new_page_per_day=True, max_items_per_page=3, book_orientation='landscape')
        d1 = distribute_photos(items=items, **kwargs)
        d2 = distribute_photos(items=items, **kwargs)
        assert d1.photo_to_page_map == d2.photo_to_page_map
        assert d1.total_pages == d2.total_pages


class TestDayAwareInvariants:
    """Broad invariant checks across a range of day/page/cap combinations (task 5.5)."""

    def test_item_and_page_counts_always_conserved(self):
        cases = [
            ([1, 1, 1, 1, 1, 1, 1, 1], 4, 3),
            ([2, 3, 1, 4, 2, 5], 4, 8),
            ([10, 1, 1, 1, 1, 1, 1, 1, 1, 1], 3, 15),
            ([5, 5, 5, 5], 4, 6),
            ([1] * 20, 4, 10),
            ([7], 4, 2),
        ]
        for day_sizes, cap, pages in cases:
            items = make_multi_day_photos(day_sizes)
            dist = distribute_photos(
                items=items, total_pages=pages, new_page_per_day=True,
                max_items_per_page=cap, book_orientation='portrait',
            )
            assert dist.total_pages == pages, f"Failed for {day_sizes}, cap={cap}, pages={pages}"
            total = sum(dist.get_photos_for_page(i) for i in range(pages))
            assert total == len(items), f"Failed for {day_sizes}, cap={cap}, pages={pages}"
            for i in range(pages):
                assert dist.get_photos_for_page(i) <= cap, f"Page {i} exceeds cap for {day_sizes}"

    def test_168_photos_spread_across_days_not_clustered(self):
        """Day-aware analog of the original 168-photos/100-pages regression: under-full
        pages must not all cluster at one end when day boundaries are spread throughout."""
        # 84 distinct days of 2 photos each = 168 photos, echoing the original
        # 168-photos/100-pages regression, now with real day boundaries.
        day_sizes = [2] * 84
        assert sum(day_sizes) == 168
        items = make_multi_day_photos(day_sizes)
        dist = distribute_photos(
            items=items, total_pages=100, new_page_per_day=True,
            max_items_per_page=4, book_orientation='portrait',
        )
        assert dist.total_pages == 100
        assert sum(dist.get_photos_for_page(i) for i in range(100)) == 168
        for i in range(100):
            assert dist.get_photos_for_page(i) > 0, f"Page {i} should not be empty"

        # The 16 pages of slack (100 dense pages needed vs. 84 requested) split
        # 16 two-item pages down to single-item pages; unlike the old arithmetic
        # clustering (all reduced pages at the tail), those splits must be spread
        # across the whole book, not bunched into either half.
        single_item_pages = [i for i in range(100) if dist.get_photos_for_page(i) == 1]
        assert len(single_item_pages) == 32  # 16 splits x 2 resulting single-item pages
        assert any(p < 50 for p in single_item_pages), "no split page found in the first half"
        assert any(p >= 50 for p in single_item_pages), "no split page found in the second half"

    def test_150_photos_100_pages_never_exceeds_natural_ratio_of_two(self):
        """
        Regression test for a real bug: 150 photos across 100 pages must cap every
        page at ceil(150/100)=2 photos, even though the active theme can render up
        to 4 per page. day-blocks of 5 (needing ceil(5/2)=3 pages each at the correct
        cap, vs. ceil(5/4)=2 at the theme's cap) make this discriminating - a theme-cap
        pack size would produce a different page count and pages holding 3-4 photos.
        """
        items = make_multi_day_photos([5] * 30)  # 30 distinct days, 5 photos each = 150
        dist = distribute_photos(
            items=items, total_pages=100, new_page_per_day=True,
            max_items_per_page=4, book_orientation='portrait',
        )
        assert dist.total_pages == 100
        assert sum(dist.get_photos_for_page(i) for i in range(100)) == 150
        for i in range(100):
            count = dist.get_photos_for_page(i)
            assert count <= 2, f"Page {i} has {count} photos, exceeding the natural ratio of 2"

    def test_279_photos_100_pages_matches_legacy_two_or_three_split(self):
        """
        Regression test for a real bug: when the dense-pack floor is 2 (not 1), the
        original slack-spend mechanism kept splitting pages down to a stray 1-item
        page - mathematically impossible to avoid unless the cap is 2 (splitting a
        single page in two can't keep both halves within {cap-1, cap} otherwise).
        Real day sizes proxied from an actual multi-day trip (sevilla.yaml): three of
        the ten days (37, 25, 7 photos) leave remainder 1 when chunked at cap 3,
        which is exactly what surfaced this. Every page must land in {2, 3} - the
        same split the pre-existing day-blind arithmetic (base=2, remainder=79)
        would produce, now with day boundaries additionally respected.
        """
        day_sizes = [3, 33, 37, 77, 11, 36, 38, 25, 12, 7]
        items = make_multi_day_photos(day_sizes)
        assert len(items) == 279
        dist = distribute_photos(
            items=items, total_pages=100, new_page_per_day=True,
            max_items_per_page=4, book_orientation='portrait',
        )
        assert dist.total_pages == 100
        counts = [dist.get_photos_for_page(i) for i in range(100)]
        assert sum(counts) == 279
        assert set(counts) == {2, 3}
        assert counts.count(3) == 79
        assert counts.count(2) == 21


class TestEndToEndDayTitleOrientation:
    """Combines day boundaries, title slots, and orientation-tiered splitting (task 9.3)."""

    def test_titles_days_and_orientation_together(self):
        title_day1 = TitleLabel(timestamp=datetime(2026, 1, 1), title="Day One")
        day1_photos = [make_photo('portrait', day=1, seq=i) for i in range(2)]
        title_day2 = TitleLabel(timestamp=datetime(2026, 1, 2), title="Day Two")
        day2_photos = [make_photo('landscape', day=2, seq=i) for i in range(2)]

        items = [title_day1] + day1_photos + [title_day2] + day2_photos

        dist = distribute_photos(
            items=items, total_pages=4, new_page_per_day=True,
            max_items_per_page=3, book_orientation='portrait',
        )

        assert dist.total_pages == 4
        assert sum(dist.get_photos_for_page(i) for i in range(4)) == len(items)

        # Day 1 (title + 2 portrait photos, 3 items) is isolated on its own page(s);
        # day 2 (title + 2 landscape photos, 3 items) likewise - the two days never share a page.
        day1_indices = set(range(0, 3))
        day2_indices = set(range(3, 6))
        pages_touching_day1 = {p for idx in day1_indices for p in [next(p for p in range(4) if idx in dist.get_photo_indices_for_page(p))]}
        pages_touching_day2 = {p for idx in day2_indices for p in [next(p for p in range(4) if idx in dist.get_photo_indices_for_page(p))]}
        assert pages_touching_day1.isdisjoint(pages_touching_day2)


class TestCapacityValidation:
    """Tests for the theme-capacity validation that now fires during distribution, not rendering."""

    def test_exact_mode_density_exceeds_theme_cap_legacy(self):
        with pytest.raises(LayoutError, match="exceeding the active theme's maximum"):
            distribute_photos(
                items=make_photos(50), total_pages=5, max_items_per_page=4, new_page_per_day=False
            )

    def test_flexible_mode_photos_per_page_exceeds_theme_cap(self):
        with pytest.raises(LayoutError, match="exceeds the active theme's maximum"):
            distribute_photos(items=make_photos(20), photos_per_page=6, max_items_per_page=4)

    def test_day_aware_too_few_pages_hits_capacity_error_not_merge(self):
        """
        Since the day-aware pack size is always the natural density ceil(N/P) - never
        the theme cap - and packing any single block at that density always fits within
        P pages, an over-tight page budget is caught by the capacity check before day-block
        merging ever runs (50 items / 3 pages needs 17/page, far above any real theme).
        """
        items = make_multi_day_photos([1] * 50)
        with pytest.raises(LayoutError, match="exceeding the active theme's maximum"):
            distribute_photos(
                items=items, total_pages=3, new_page_per_day=True, max_items_per_page=4
            )
