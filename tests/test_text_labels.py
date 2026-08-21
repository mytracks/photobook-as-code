"""
Tests for text label data model and markdown parsing.
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
from photobook_as_code.text_labels import (
    TextLabel,
    TitleLabel,
    TextSegment,
    parse_markdown_line,
    parse_markdown_text,
    find_closest_photo,
    associate_text_labels_with_photos,
    parse_title_labels,
    merge_titles_with_photos,
)
from photobook_as_code.photos import PhotoMetadata


class TestTextLabel:
    """Tests for TextLabel class."""
    
    def test_from_dict_with_iso_timestamp(self):
        """Test creating TextLabel from dict with ISO timestamp."""
        data = {
            'timestamp': '2026-06-15T14:30:00',
            'text': 'Beautiful day'
        }
        label = TextLabel.from_dict(data)
        assert label.text == 'Beautiful day'
        assert isinstance(label.timestamp, datetime)
        assert label.timestamp.year == 2026
        assert label.timestamp.month == 6
        assert label.timestamp.day == 15
    
    def test_from_dict_with_unix_timestamp(self):
        """Test creating TextLabel from dict with Unix epoch timestamp."""
        data = {
            'timestamp': 1656163800,
            'text': 'Summer photo'
        }
        label = TextLabel.from_dict(data)
        assert label.text == 'Summer photo'
        assert isinstance(label.timestamp, datetime)


class TestTextSegment:
    """Tests for TextSegment class."""
    
    def test_font_size_multiplier_normal(self):
        """Test font size multiplier for normal text."""
        segment = TextSegment(text="Normal", heading_level=0)
        assert segment.font_size_multiplier == 1.0
    
    def test_font_size_multiplier_h1(self):
        """Test font size multiplier for heading 1."""
        segment = TextSegment(text="H1", heading_level=1)
        assert segment.font_size_multiplier == 1.5
    
    def test_font_size_multiplier_h2(self):
        """Test font size multiplier for heading 2."""
        segment = TextSegment(text="H2", heading_level=2)
        assert segment.font_size_multiplier == 1.3
    
    def test_font_size_multiplier_h3(self):
        """Test font size multiplier for heading 3."""
        segment = TextSegment(text="H3", heading_level=3)
        assert segment.font_size_multiplier == 1.2


class TestMarkdownParsing:
    """Tests for markdown parsing functions."""
    
    def test_parse_plain_text(self):
        """Test parsing plain text without markdown."""
        segments, heading = parse_markdown_line("Plain text")
        assert len(segments) == 1
        assert segments[0].text == "Plain text"
        assert segments[0].bold is False
        assert segments[0].italic is False
        assert heading == 0
    
    def test_parse_italic(self):
        """Test parsing italic text."""
        segments, heading = parse_markdown_line("This is *italic* text")
        assert len(segments) == 3
        assert segments[0].text == "This is "
        assert segments[0].italic is False
        assert segments[1].text == "italic"
        assert segments[1].italic is True
        assert segments[1].bold is False
        assert segments[2].text == " text"
        assert segments[2].italic is False
    
    def test_parse_underscore_italic(self):
        """Test parsing underscore-style italic text (_italic_), same result as *italic*."""
        segments, heading = parse_markdown_line("This is _italic_ text")
        assert len(segments) == 3
        assert segments[0].text == "This is "
        assert segments[0].italic is False
        assert segments[1].text == "italic"
        assert segments[1].italic is True
        assert segments[1].bold is False
        assert segments[2].text == " text"
        assert segments[2].italic is False

    def test_parse_bold(self):
        """Test parsing bold text."""
        segments, heading = parse_markdown_line("This is **bold** text")
        assert len(segments) == 3
        assert segments[0].text == "This is "
        assert segments[0].bold is False
        assert segments[1].text == "bold"
        assert segments[1].bold is True
        assert segments[1].italic is False
        assert segments[2].text == " text"
        assert segments[2].bold is False
    
    def test_parse_bold_and_italic(self):
        """Test parsing text with both bold and italic."""
        segments, heading = parse_markdown_line("Text with ***bold italic*** formatting")
        assert len(segments) == 3
        assert segments[0].text == "Text with "
        assert segments[1].text == "bold italic"
        assert segments[1].bold is True
        assert segments[1].italic is True
        assert segments[2].text == " formatting"
    
    def test_parse_bold_and_underscore_italic_combined(self):
        """Test a line combining **bold** and _italic_ (the form from the original request)."""
        segments, heading = parse_markdown_line("A **wonderful** _adventure_")
        texts_styles = [(s.text, s.bold, s.italic) for s in segments]
        assert ("wonderful", True, False) in texts_styles
        assert ("adventure", False, True) in texts_styles

    def test_parse_heading_level_1(self):
        """Test parsing heading level 1."""
        segments, heading = parse_markdown_line("# Big Title")
        assert heading == 1
        assert len(segments) == 1
        assert segments[0].text == "Big Title"
        assert segments[0].heading_level == 1
        assert segments[0].font_size_multiplier == 1.5
    
    def test_parse_heading_level_2(self):
        """Test parsing heading level 2."""
        segments, heading = parse_markdown_line("## Medium Title")
        assert heading == 2
        assert segments[0].text == "Medium Title"
        assert segments[0].heading_level == 2
        assert segments[0].font_size_multiplier == 1.3
    
    def test_parse_heading_level_3(self):
        """Test parsing heading level 3."""
        segments, heading = parse_markdown_line("### Small Title")
        assert heading == 3
        assert segments[0].text == "Small Title"
        assert segments[0].heading_level == 3
        assert segments[0].font_size_multiplier == 1.2
    
    def test_parse_heading_with_formatting(self):
        """Test parsing heading with inline formatting."""
        segments, heading = parse_markdown_line("# Title with *italic* word")
        assert heading == 1
        assert len(segments) == 3
        assert segments[0].text == "Title with "
        assert segments[0].heading_level == 1
        assert segments[1].text == "italic"
        assert segments[1].italic is True
        assert segments[1].heading_level == 1
    
    def test_parse_nested_formatting(self):
        """Test parsing nested bold and italic."""
        segments, heading = parse_markdown_line("**Bold with *nested italic* text**")
        # This should parse as bold segments with italic inside
        # Due to regex pattern, this may not work perfectly - test graceful degradation
        assert len(segments) > 0
        # Just verify it doesn't crash and produces some output
    
    def test_parse_malformed_markdown(self):
        """Test graceful degradation with malformed markdown."""
        segments, heading = parse_markdown_line("Text with *unclosed marker")
        # Should render as-is or best effort
        assert len(segments) >= 1
        # Verify it doesn't crash
    
    def test_parse_multiline_text(self):
        """Test parsing multi-line text."""
        text = "Line 1\nLine 2 with *italic*\n# Heading"
        lines = parse_markdown_text(text)
        assert len(lines) == 3
        
        # Line 1
        segments1, heading1 = lines[0]
        assert len(segments1) == 1
        assert segments1[0].text == "Line 1"
        assert heading1 == 0
        
        # Line 2
        segments2, heading2 = lines[1]
        assert any("italic" in s.text for s in segments2)
        
        # Line 3
        segments3, heading3 = lines[2]
        assert heading3 == 1
    
    def test_parse_empty_line(self):
        """Test parsing empty line."""
        segments, heading = parse_markdown_line("")
        assert len(segments) == 1
        assert segments[0].text == ""
    
    def test_multiple_formatting_on_same_line(self):
        """Test multiple formatting markers on same line."""
        segments, heading = parse_markdown_line("Start *italic* middle **bold** end")
        assert len(segments) == 5
        assert segments[0].text == "Start "
        assert segments[1].text == "italic"
        assert segments[1].italic is True
        assert segments[2].text == " middle "
        assert segments[3].text == "bold"
        assert segments[3].bold is True
        assert segments[4].text == " end"


def make_photo(filename: str, timestamp: datetime) -> PhotoMetadata:
    """Helper to create PhotoMetadata for testing."""
    return PhotoMetadata(
        path=Path(filename),
        filename=filename,
        date_taken=timestamp,
        width=1920,
        height=1080,
        file_modified=timestamp
    )


class TestPhotoTextAssociation:
    """Tests for photo-text association logic."""
    
    def test_find_closest_photo_single_match(self):
        """Test finding closest photo with single photo."""
        base_time = datetime(2026, 6, 15, 12, 0, 0)
        photos = [make_photo("photo1.jpg", base_time)]
        label = TextLabel(timestamp=base_time + timedelta(minutes=5), text="Test")
        
        closest = find_closest_photo(label, photos)
        assert closest == photos[0]
    
    def test_find_closest_photo_multiple_photos(self):
        """Test finding closest photo with multiple photos."""
        base_time = datetime(2026, 6, 15, 12, 0, 0)
        photos = [
            make_photo("photo1.jpg", base_time),
            make_photo("photo2.jpg", base_time + timedelta(hours=1)),
            make_photo("photo3.jpg", base_time + timedelta(hours=3)),
        ]
        label = TextLabel(timestamp=base_time + timedelta(minutes=55), text="Test")
        
        # Should match photo2 (1 hour mark) - closest to 55 minutes
        closest = find_closest_photo(label, photos)
        assert closest == photos[1]
    
    def test_find_closest_photo_equidistant_prefers_earlier(self):
        """Test tiebreaker prefers earlier photo when equidistant."""
        base_time = datetime(2026, 6, 15, 12, 0, 0)
        photos = [
            make_photo("photo1.jpg", base_time),
            make_photo("photo2.jpg", base_time + timedelta(hours=2)),
        ]
        # Label exactly in the middle
        label = TextLabel(timestamp=base_time + timedelta(hours=1), text="Test")
        
        closest = find_closest_photo(label, photos)
        assert closest == photos[0]  # Earlier photo
    
    def test_find_closest_photo_no_photos(self):
        """Test finding closest photo with no photos."""
        label = TextLabel(timestamp=datetime.now(), text="Test")
        closest = find_closest_photo(label, [])
        assert closest is None
    
    def test_associate_single_label_single_photo(self):
        """Test associating single label with single photo."""
        base_time = datetime(2026, 6, 15, 12, 0, 0)
        photos = [make_photo("photo1.jpg", base_time)]
        labels = [
            {'timestamp': (base_time + timedelta(minutes=5)).isoformat(), 'text': 'Label 1'}
        ]
        
        associations = associate_text_labels_with_photos(labels, photos)
        assert len(associations) == 1
        photo, label = associations[0]
        assert photo == photos[0]
        assert label.text == 'Label 1'
    
    def test_associate_multiple_labels_multiple_photos(self):
        """Test associating multiple labels with multiple photos."""
        base_time = datetime(2026, 6, 15, 12, 0, 0)
        photos = [
            make_photo("photo1.jpg", base_time),
            make_photo("photo2.jpg", base_time + timedelta(hours=2)),
            make_photo("photo3.jpg", base_time + timedelta(hours=4)),
        ]
        labels = [
            {'timestamp': (base_time + timedelta(minutes=5)).isoformat(), 'text': 'Label 1'},
            {'timestamp': (base_time + timedelta(hours=2, minutes=10)).isoformat(), 'text': 'Label 2'},
        ]
        
        associations = associate_text_labels_with_photos(labels, photos)
        assert len(associations) == 3
        
        # Check photo1 has Label 1
        photo1, label1 = associations[0]
        assert photo1 == photos[0]
        assert label1.text == 'Label 1'
        
        # Check photo2 has Label 2
        photo2, label2 = associations[1]
        assert photo2 == photos[1]
        assert label2.text == 'Label 2'
        
        # Check photo3 has no label
        photo3, label3 = associations[2]
        assert photo3 == photos[2]
        assert label3 is None
    
    def test_associate_photo_without_label(self):
        """Test that photos without matching labels get None."""
        base_time = datetime(2026, 6, 15, 12, 0, 0)
        photos = [
            make_photo("photo1.jpg", base_time),
            make_photo("photo2.jpg", base_time + timedelta(hours=2)),
        ]
        labels = [
            {'timestamp': (base_time + timedelta(minutes=5)).isoformat(), 'text': 'Label 1'},
        ]
        
        associations = associate_text_labels_with_photos(labels, photos)
        photo1, label1 = associations[0]
        assert label1.text == 'Label 1'
        
        photo2, label2 = associations[1]
        assert label2 is None
    
    def test_associate_no_labels(self):
        """Test associating with no text labels."""
        base_time = datetime(2026, 6, 15, 12, 0, 0)
        photos = [
            make_photo("photo1.jpg", base_time),
            make_photo("photo2.jpg", base_time + timedelta(hours=1)),
        ]
        labels = []
        
        associations = associate_text_labels_with_photos(labels, photos)
        assert len(associations) == 2
        assert all(label is None for _, label in associations)
    
    def test_associate_labels_without_photos(self):
        """Test graceful handling when labels exist but no photos."""
        labels = [
            {'timestamp': '2026-06-15T12:00:00', 'text': 'Label 1'},
        ]
        
        associations = associate_text_labels_with_photos(labels, [])
        assert len(associations) == 0


class TestTitleLabel:
    """Tests for TitleLabel class."""

    def test_from_dict_with_iso_timestamp(self):
        """Test creating TitleLabel from dict with ISO timestamp."""
        data = {'timestamp': '2026-06-15T14:30:00', 'title': '# Chapter One'}
        label = TitleLabel.from_dict(data)
        assert label.title == '# Chapter One'
        assert isinstance(label.timestamp, datetime)
        assert label.timestamp.year == 2026

    def test_from_dict_with_unix_timestamp(self):
        """Test creating TitleLabel from dict with Unix epoch timestamp."""
        data = {'timestamp': 1656163800, 'title': 'A title'}
        label = TitleLabel.from_dict(data)
        assert label.title == 'A title'

    def test_orientation_is_always_portrait(self):
        """Titles always report portrait orientation for layout matching."""
        label = TitleLabel(timestamp=datetime.now(), title='Anything')
        assert label.orientation == 'portrait'


class TestParseTitleLabels:
    """Tests for parse_title_labels function."""

    def test_parses_only_title_entries(self):
        """Entries with 'text' are skipped; only 'title' entries are parsed."""
        entries = [
            {'timestamp': '2026-06-15T10:00:00', 'text': 'A caption'},
            {'timestamp': '2026-06-15T11:00:00', 'title': 'A title'},
        ]
        titles = parse_title_labels(entries)
        assert len(titles) == 1
        assert titles[0].title == 'A title'

    def test_no_title_entries(self):
        """No title entries yields an empty list."""
        entries = [{'timestamp': '2026-06-15T10:00:00', 'text': 'A caption'}]
        assert parse_title_labels(entries) == []

    def test_invalid_title_entry_skipped(self):
        """An entry with an unparseable timestamp is skipped, not raised."""
        entries = [{'timestamp': 'not-a-date', 'title': 'Broken'}]
        assert parse_title_labels(entries) == []


class TestMergeTitlesWithPhotos:
    """Tests for merge_titles_with_photos function."""

    def test_title_between_two_photos(self):
        base = datetime(2026, 6, 15, 12, 0, 0)
        photos = [
            make_photo('p1.jpg', base),
            make_photo('p2.jpg', base + timedelta(hours=2)),
        ]
        title = TitleLabel(timestamp=base + timedelta(hours=1), title='Mid title')
        merged = merge_titles_with_photos([title], photos)
        assert merged == [photos[0], title, photos[1]]

    def test_title_before_all_photos(self):
        base = datetime(2026, 6, 15, 12, 0, 0)
        photos = [make_photo('p1.jpg', base), make_photo('p2.jpg', base + timedelta(hours=1))]
        title = TitleLabel(timestamp=base - timedelta(hours=1), title='Intro')
        merged = merge_titles_with_photos([title], photos)
        assert merged == [title, photos[0], photos[1]]

    def test_title_after_all_photos(self):
        base = datetime(2026, 6, 15, 12, 0, 0)
        photos = [make_photo('p1.jpg', base), make_photo('p2.jpg', base + timedelta(hours=1))]
        title = TitleLabel(timestamp=base + timedelta(hours=5), title='Outro')
        merged = merge_titles_with_photos([title], photos)
        assert merged == [photos[0], photos[1], title]

    def test_title_wins_exact_timestamp_tie(self):
        """A title with a timestamp exactly equal to a photo's comes first."""
        base = datetime(2026, 6, 15, 12, 0, 0)
        photos = [make_photo('p1.jpg', base)]
        title = TitleLabel(timestamp=base, title='Tied title')
        merged = merge_titles_with_photos([title], photos)
        assert merged == [title, photos[0]]

    def test_multiple_titles_at_same_insertion_point_ordered_by_own_timestamp(self):
        base = datetime(2026, 6, 15, 12, 0, 0)
        photos = [make_photo('p1.jpg', base + timedelta(hours=5))]
        title_a = TitleLabel(timestamp=base + timedelta(hours=1), title='First')
        title_b = TitleLabel(timestamp=base + timedelta(hours=2), title='Second')
        # Pass in reverse order; merge should still sort them by their own timestamp
        merged = merge_titles_with_photos([title_b, title_a], photos)
        assert merged == [title_a, title_b, photos[0]]

    def test_no_titles_returns_photos_unchanged(self):
        base = datetime(2026, 6, 15, 12, 0, 0)
        photos = [make_photo('p1.jpg', base)]
        merged = merge_titles_with_photos([], photos)
        assert merged == photos

    def test_no_photos_appends_all_titles(self):
        base = datetime(2026, 6, 15, 12, 0, 0)
        title = TitleLabel(timestamp=base, title='Only title')
        merged = merge_titles_with_photos([title], [])
        assert merged == [title]

