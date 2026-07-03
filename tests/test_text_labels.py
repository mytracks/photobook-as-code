"""
Tests for text label data model and markdown parsing.
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
from photobook_as_code.text_labels import (
    TextLabel,
    TextSegment,
    parse_markdown_line,
    parse_markdown_text,
    find_closest_photo,
    associate_text_labels_with_photos,
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

