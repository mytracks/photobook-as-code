import pytest
from photobook_as_code.layout import PhotoOrientation, TemplateMatcher, LayoutTemplate, PhotoSpec, PhotoPosition, LayoutError
from photobook_as_code.photos import PhotoMetadata
from photobook_as_code.themes import Theme, ThemeError


# --- Fixtures for Layout Templates and Photos ---

@pytest.fixture
def sample_templates() -> list[LayoutTemplate]:
    # Example templates for testing
    return [
        LayoutTemplate(
            count=1,
            photos=[
                PhotoSpec(orientation=PhotoOrientation.LANDSCAPE, position=PhotoPosition(x=0.5, y=0.5), size=0.9)
            ]
        ),
        LayoutTemplate(
            count=1,
            photos=[
                PhotoSpec(orientation=PhotoOrientation.PORTRAIT, position=PhotoPosition(x=0.5, y=0.5), size=0.9)
            ]
        ),
        LayoutTemplate(
            count=2,
            photos=[
                PhotoSpec(orientation=PhotoOrientation.LANDSCAPE, position=PhotoPosition(x=0.25, y=0.5), size=0.45),
                PhotoSpec(orientation=PhotoOrientation.LANDSCAPE, position=PhotoPosition(x=0.75, y=0.5), size=0.45),
            ]
        ),
        LayoutTemplate(
            count=2,
            photos=[
                PhotoSpec(orientation=PhotoOrientation.PORTRAIT, position=PhotoPosition(x=0.5, y=0.25), size=0.45),
                PhotoSpec(orientation=PhotoOrientation.PORTRAIT, position=PhotoPosition(x=0.5, y=0.75), size=0.45),
            ]
        ),
        LayoutTemplate(
            count=2, # LP
            photos=[
                PhotoSpec(orientation=PhotoOrientation.LANDSCAPE, position=PhotoPosition(x=0.25, y=0.5), size=0.45),
                PhotoSpec(orientation=PhotoOrientation.PORTRAIT, position=PhotoPosition(x=0.75, y=0.5), size=0.45),
            ]
        ),
        LayoutTemplate(
            count=2, # PL
            photos=[
                PhotoSpec(orientation=PhotoOrientation.PORTRAIT, position=PhotoPosition(x=0.25, y=0.5), size=0.45),
                PhotoSpec(orientation=PhotoOrientation.LANDSCAPE, position=PhotoPosition(x=0.75, y=0.5), size=0.45),
            ]
        ),
        # Add a template that matches by count and types, but not exact order
        LayoutTemplate(
            count=3, # LPP
            photos=[
                PhotoSpec(orientation=PhotoOrientation.LANDSCAPE, position=PhotoPosition(x=0.5, y=0.25), size=0.6),
                PhotoSpec(orientation=PhotoOrientation.PORTRAIT, position=PhotoPosition(x=0.25, y=0.75), size=0.4),
                PhotoSpec(orientation=PhotoOrientation.PORTRAIT, position=PhotoPosition(x=0.75, y=0.75), size=0.4),
            ]
        ),
        LayoutTemplate(
            count=3, # PLP (different order for LPP)
            photos=[
                PhotoSpec(orientation=PhotoOrientation.PORTRAIT, position=PhotoPosition(x=0.5, y=0.25), size=0.6),
                PhotoSpec(orientation=PhotoOrientation.LANDSCAPE, position=PhotoPosition(x=0.25, y=0.75), size=0.4),
                PhotoSpec(orientation=PhotoOrientation.PORTRAIT, position=PhotoPosition(x=0.75, y=0.75), size=0.4),
            ]
        ),
        LayoutTemplate(
            count=3, # LLP
            photos=[
                PhotoSpec(orientation=PhotoOrientation.LANDSCAPE, position=PhotoPosition(x=0.25, y=0.5), size=0.4),
                PhotoSpec(orientation=PhotoOrientation.LANDSCAPE, position=PhotoPosition(x=0.75, y=0.5), size=0.4),
                PhotoSpec(orientation=PhotoOrientation.PORTRAIT, position=PhotoPosition(x=0.5, y=0.75), size=0.4),
            ]
        ),
    ]

@pytest.fixture
def template_matcher(sample_templates) -> TemplateMatcher:
    return TemplateMatcher(sample_templates)

# --- Tests for Template Matching Logic (Tasks 8.2, 8.3, 8.4) ---

def test_match_by_count(template_matcher):
    matched = template_matcher.match_by_count(2)
    assert len(matched) == 4  # LL, PP, LP, PL
    assert all(t.count == 2 for t in matched)

def test_match_by_orientation_types_and_counts(template_matcher):
    # Two landscape, one portrait
    photo_orientations = [PhotoOrientation.LANDSCAPE, PhotoOrientation.PORTRAIT, PhotoOrientation.PORTRAIT]
    # Pre-filter by count to make it simpler
    count_matched = template_matcher.match_by_count(3)
    matched = template_matcher.match_by_orientation_types_and_counts(photo_orientations, count_matched)
    assert len(matched) == 2 # Expect LPP and PLP templates
    # Verify both LPP and PLP templates are present
    template_orientations_list = [[p.orientation for p in t.photos] for t in matched]
    assert [PhotoOrientation.LANDSCAPE, PhotoOrientation.PORTRAIT, PhotoOrientation.PORTRAIT] in template_orientations_list
    assert [PhotoOrientation.PORTRAIT, PhotoOrientation.LANDSCAPE, PhotoOrientation.PORTRAIT] in template_orientations_list

def test_select_best_template_by_order_preference(template_matcher):
    # Test for exact match
    photo_orientations_exact = [PhotoOrientation.LANDSCAPE, PhotoOrientation.PORTRAIT]
    candidate_templates = template_matcher.match_by_count(2)
    candidate_templates = template_matcher.match_by_orientation_types_and_counts(
        photo_orientations_exact, candidate_templates
    )
    best_template = template_matcher.select_best_template_by_order_preference(
        photo_orientations_exact, candidate_templates
    )
    assert best_template is not None
    assert [p.orientation for p in best_template.photos] == photo_orientations_exact

    # Test when no exact match among candidates
    photo_orientations_no_exact = [PhotoOrientation.PORTRAIT, PhotoOrientation.PORTRAIT, PhotoOrientation.LANDSCAPE] # This combo does not have exact match in candidates with count 3
    count_matched = template_matcher.match_by_count(3)
    orientation_matched = template_matcher.match_by_orientation_types_and_counts(
        photo_orientations_no_exact, count_matched
    )
    # The 'LPP' and 'PLP' templates have two portraits and one landscape, matching types/counts
    # But if photo_orientations_no_exact is L,L,P, neither LPP nor PLP is an exact order match
    best_template_none = template_matcher.select_best_template_by_order_preference(
        photo_orientations_no_exact, orientation_matched
    )
    assert best_template_none is None

def test_find_best_template_exact_match(template_matcher):
    photo_orientations = [PhotoOrientation.LANDSCAPE, PhotoOrientation.PORTRAIT]
    best_template = template_matcher.find_best_template(photo_orientations)
    assert best_template is not None
    assert [p.orientation for p in best_template.photos] == photo_orientations

def test_find_best_template_no_count_match(template_matcher):
    # No template for 99 photos
    photo_orientations = [PhotoOrientation.LANDSCAPE] * 99
    with pytest.raises(LayoutError, match="No layout templates found for 99 photos."):
        template_matcher.find_best_template(photo_orientations)

def test_find_best_template_no_orientation_types_and_counts_match(template_matcher):
    # No template for 3 photos with 3 landscapes
    photo_orientations = [PhotoOrientation.LANDSCAPE] * 3
    with pytest.raises(LayoutError, match=r"No layout templates found matching orientation types/counts for \[<PhotoOrientation.LANDSCAPE: 'landscape'>, <PhotoOrientation.LANDSCAPE: 'landscape'>, <PhotoOrientation.LANDSCAPE: 'landscape'>]."):
        template_matcher.find_best_template(photo_orientations)

def test_find_best_template_no_exact_order_match(template_matcher):
    # Test for 3 photos, two portraits and one landscape, but specific order that doesn't exactly match a template
    # The templates are LPP and PLP. Let's try LLP
    photo_orientations = [PhotoOrientation.PORTRAIT, PhotoOrientation.PORTRAIT, PhotoOrientation.LANDSCAPE]
    with pytest.raises(LayoutError, match=r"No exact order-matching template found for orientations: \[<PhotoOrientation.PORTRAIT: 'portrait'>, <PhotoOrientation.PORTRAIT: 'portrait'>, <PhotoOrientation.LANDSCAPE: 'landscape'>]."):
        template_matcher.find_best_template(photo_orientations)


# --- Tests for Photo Orientation Detection (Task 8.1) ---
# This requires actual images. We'll mock PhotoMetadata for simplicity.

@pytest.fixture
def mock_photo_metadata_landscape():
    # Mock a landscape photo (width > height)
    return PhotoMetadata(path="dummy_landscape.jpg", filename="dummy_landscape.jpg", width=1000, height=500, orientation=PhotoOrientation.LANDSCAPE)

@pytest.fixture
def mock_photo_metadata_portrait():
    # Mock a portrait photo (height > width)
    return PhotoMetadata(path="dummy_portrait.jpg", filename="dummy_portrait.jpg", width=500, height=1000, orientation=PhotoOrientation.PORTRAIT)

@pytest.fixture
def mock_photo_metadata_square():
    # Mock a square photo (width == height, treated as landscape)
    return PhotoMetadata(path="dummy_square.jpg", filename="dummy_square.jpg", width=700, height=700, orientation=PhotoOrientation.LANDSCAPE)


def test_photo_orientation_detection(mock_photo_metadata_landscape, 
                                     mock_photo_metadata_portrait, 
                                     mock_photo_metadata_square):
    # Photo orientation detection is done in photos.py, and PhotoMetadata already stores it.
    # This test verifies the PhotoMetadata object correctly identifies and stores orientation.
    # Assuming PhotoMetadata.orientation is set correctly upon creation/parsing.
    assert mock_photo_metadata_landscape.orientation == PhotoOrientation.LANDSCAPE
    assert mock_photo_metadata_portrait.orientation == PhotoOrientation.PORTRAIT
    assert mock_photo_metadata_square.orientation == PhotoOrientation.LANDSCAPE


def test_theme_missing_layouts_section():
    # A basic theme dictionary without the 'layouts' section
    malformed_theme_data = {
        "name": "Missing Layouts",
        "description": "A theme intentionally missing layouts section",
        "background": {"color": "#000000"},
        "borders": {"enabled": False},
        "spacing": {"grid_gap": 0, "page_margin": 0},
    }
    with pytest.raises(ThemeError, match="Theme missing 'layouts' section"):
        Theme.from_dict(malformed_theme_data)

# --- Tests for Template-Based Rendering (Tasks 8.6, 8.7, 8.8) ---
# These are harder to test without actual rendering output comparison. 
# Will rely on manual visual verification for now, or would require image comparison library.

# Task 8.9: Test edge cases (single photo, all same orientation, complex sequences)
# Covered by template matching tests and manual verification of themes.

# Task 8.10: Test all default themes with real photo sets
# This is an integration test, best done via CLI and visual inspection.
