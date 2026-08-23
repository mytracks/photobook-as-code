"""
Tests for configuration parsing and validation.
"""

import pytest
import tempfile
from pathlib import Path
from photobook_as_code.config import (
    load_config,
    validate_text_labels,
    ConfigurationError,
)


class TestTextLabelValidation:
    """Tests for text label validation."""
    
    def test_valid_text_labels_with_iso_timestamp(self):
        """Test valid text labels with ISO 8601 timestamps."""
        text_labels = [
            {'timestamp': '2026-06-15T14:30:00', 'text': 'A beautiful day'},
            {'timestamp': '2026-06-16T10:00:00Z', 'text': 'Morning walk'},
        ]
        # Should not raise
        validate_text_labels(text_labels)
    
    def test_valid_text_labels_with_unix_timestamp(self):
        """Test valid text labels with Unix epoch timestamps."""
        text_labels = [
            {'timestamp': 1656163800, 'text': 'Summer photo'},
            {'timestamp': 1656250200.5, 'text': 'Another moment'},
        ]
        # Should not raise
        validate_text_labels(text_labels)
    
    def test_valid_multiline_text(self):
        """Test text labels with multi-line text content."""
        text_labels = [
            {'timestamp': '2026-06-15T14:30:00', 'text': 'Line 1\nLine 2\nLine 3'},
        ]
        # Should not raise
        validate_text_labels(text_labels)
    
    def test_empty_text_labels_list(self):
        """Test empty text labels list is valid."""
        # Should not raise
        validate_text_labels([])
    
    def test_invalid_not_a_list(self):
        """Test that non-list text_labels raises error."""
        with pytest.raises(ConfigurationError, match="text_labels must be a list"):
            validate_text_labels("not a list")
    
    def test_invalid_entry_not_object(self):
        """Test that non-object entry raises error."""
        with pytest.raises(ConfigurationError, match="entry 0 must be an object"):
            validate_text_labels(["string entry"])
    
    def test_missing_timestamp_field(self):
        """Test that missing timestamp raises error."""
        text_labels = [
            {'text': 'Missing timestamp'},
        ]
        with pytest.raises(ConfigurationError, match="missing required field 'timestamp'"):
            validate_text_labels(text_labels)
    
    def test_missing_text_and_title_field(self):
        """Test that missing both text and title raises error."""
        text_labels = [
            {'timestamp': '2026-06-15T14:30:00'},
        ]
        with pytest.raises(ConfigurationError, match="one of 'text' or 'title'"):
            validate_text_labels(text_labels)

    def test_both_text_and_title_fields(self):
        """Test that having both text and title raises error."""
        text_labels = [
            {'timestamp': '2026-06-15T14:30:00', 'text': 'A caption', 'title': 'A title'},
        ]
        with pytest.raises(ConfigurationError, match="mutually exclusive"):
            validate_text_labels(text_labels)

    def test_valid_title_field(self):
        """Test that a title entry (no text field) is valid."""
        text_labels = [
            {'timestamp': '2026-06-15T14:30:00', 'title': '# A Title'},
        ]
        validate_text_labels(text_labels)  # Should not raise
    
    def test_invalid_iso_timestamp_format(self):
        """Test that invalid ISO timestamp raises error."""
        text_labels = [
            {'timestamp': 'not-a-date', 'text': 'Invalid timestamp'},
        ]
        with pytest.raises(ConfigurationError, match="invalid timestamp format"):
            validate_text_labels(text_labels)
    
    def test_invalid_unix_timestamp(self):
        """Test that invalid Unix timestamp raises error."""
        text_labels = [
            {'timestamp': -100000000000, 'text': 'Way too old'},
        ]
        with pytest.raises(ConfigurationError, match="invalid Unix epoch timestamp"):
            validate_text_labels(text_labels)
    
    def test_invalid_timestamp_type(self):
        """Test that boolean timestamp raises error."""
        text_labels = [
            {'timestamp': True, 'text': 'Boolean timestamp'},
        ]
        with pytest.raises(ConfigurationError, match="invalid timestamp type"):
            validate_text_labels(text_labels)
    
    def test_invalid_text_type(self):
        """Test that non-string text raises error."""
        text_labels = [
            {'timestamp': '2026-06-15T14:30:00', 'text': 12345},
        ]
        with pytest.raises(ConfigurationError, match="invalid text type"):
            validate_text_labels(text_labels)


class TestConfigWithTextLabels:
    """Tests for loading config with text labels."""
    
    def test_load_config_with_text_labels(self):
        """Test loading config with valid text labels."""
        config_content = """
photos: tests/fixtures/sample-photos
output:
  size: A4
  format: pdf
layout:
  photos_per_page: 4
theme: clean
text_labels:
  - timestamp: "2026-06-15T14:30:00"
    text: "Beautiful day at the beach"
  - timestamp: 1656163800
    text: "Mountain hike"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            f.flush()
            config_path = Path(f.name)
        
        try:
            config = load_config(config_path)
            assert len(config.text_labels) == 2
            assert config.text_labels[0]['timestamp'] == "2026-06-15T14:30:00"
            assert config.text_labels[0]['text'] == "Beautiful day at the beach"
            assert config.text_labels[1]['timestamp'] == 1656163800
            assert config.text_labels[1]['text'] == "Mountain hike"
        finally:
            config_path.unlink()
    
    def test_load_config_without_text_labels(self):
        """Test loading config without text labels (backward compatibility)."""
        config_content = """
photos: tests/fixtures/sample-photos
output:
  size: A4
  format: pdf
layout:
  photos_per_page: 4
theme: clean
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            f.flush()
            config_path = Path(f.name)
        
        try:
            config = load_config(config_path)
            assert config.text_labels == []
        finally:
            config_path.unlink()
    
    def test_load_config_with_invalid_text_labels(self):
        """Test that loading config with invalid text labels raises error."""
        config_content = """
photos: tests/fixtures/sample-photos
output:
  size: A4
  format: pdf
layout:
  photos_per_page: 4
theme: clean
text_labels:
  - text: "Missing timestamp field"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            f.flush()
            config_path = Path(f.name)
        
        try:
            with pytest.raises(ConfigurationError, match="missing required field 'timestamp'"):
                load_config(config_path)
        finally:
            config_path.unlink()


class TestNewPagePerDayConfig:
    """Tests for the layout.new_page_per_day configuration field."""

    def _write_and_load(self, config_content: str):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            f.flush()
            config_path = Path(f.name)
        try:
            return load_config(config_path)
        finally:
            config_path.unlink()

    def test_default_is_true(self):
        """Test new_page_per_day defaults to True when not specified."""
        config = self._write_and_load("""
photos: tests/fixtures/sample-photos
output:
  size: A4
layout:
  photos_per_page: 4
""")
        assert config.layout.new_page_per_day is True

    def test_explicit_true(self):
        """Test new_page_per_day can be explicitly enabled."""
        config = self._write_and_load("""
photos: tests/fixtures/sample-photos
output:
  size: A4
layout:
  photos_per_page: 4
  new_page_per_day: true
""")
        assert config.layout.new_page_per_day is True

    def test_explicit_false(self):
        """Test new_page_per_day can be explicitly disabled."""
        config = self._write_and_load("""
photos: tests/fixtures/sample-photos
output:
  size: A4
layout:
  photos_per_page: 4
  new_page_per_day: false
""")
        assert config.layout.new_page_per_day is False

    def test_invalid_type_raises(self):
        """Test a non-boolean new_page_per_day raises a clear validation error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
photos: tests/fixtures/sample-photos
output:
  size: A4
layout:
  photos_per_page: 4
  new_page_per_day: "yes please"
""")
            f.flush()
            config_path = Path(f.name)
        try:
            with pytest.raises(ConfigurationError, match="new_page_per_day"):
                load_config(config_path)
        finally:
            config_path.unlink()


class TestGetBookOrientation:
    """Tests for PhotobookConfig.get_book_orientation, used to rank orientation-matched splits."""

    def _write_and_load(self, size: str):
        config_content = f"""
photos: tests/fixtures/sample-photos
output:
  size: {size}
layout:
  photos_per_page: 4
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            f.flush()
            config_path = Path(f.name)
        try:
            return load_config(config_path)
        finally:
            config_path.unlink()

    def test_a4_is_portrait(self):
        config = self._write_and_load("A4")
        assert config.get_book_orientation() == 'portrait'

    def test_custom_landscape_size(self):
        config = self._write_and_load("3508x2480")
        assert config.get_book_orientation() == 'landscape'

    def test_custom_portrait_size(self):
        config = self._write_and_load("2480x3508")
        assert config.get_book_orientation() == 'portrait'

    def test_square_counts_as_portrait(self):
        config = self._write_and_load("2000x2000")
        assert config.get_book_orientation() == 'portrait'
