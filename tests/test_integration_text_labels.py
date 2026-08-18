"""
Integration tests for text labels feature.
Tests the complete pipeline from configuration to rendered output.
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from src.photobook_as_code.config import load_config
from src.photobook_as_code.photos import collect_photos
from src.photobook_as_code.themes import load_theme
from src.photobook_as_code.layout import distribute_photos
from src.photobook_as_code.renderer import render_all_pages
from src.photobook_as_code.text_labels import associate_text_labels_with_photos


class TestTextLabelsIntegration:
    """Integration tests for full text labels pipeline."""
    
    @pytest.fixture
    def test_config_file(self, tmp_path):
        """Create a test configuration file with text labels."""
        config_content = """photos: tests/fixtures/sample-photos
output:
  size: A4
  format: pdf
  filename: test-output.pdf
layout:
  photos_per_page: 2
theme: clean
text_labels:
  - timestamp: "2026-07-03T17:32:24"
    text: "# Test Heading\\nSome description"
  - timestamp: "2026-07-03T17:32:25"
    text: "Second photo with *italic* text"
"""
        config_path = tmp_path / "test-config.yaml"
        config_path.write_text(config_content)
        return config_path
    
    def test_full_pipeline_with_text_labels(self, test_config_file):
        """Test complete pipeline with text labels."""
        # Load configuration
        config = load_config(test_config_file)
        assert config.text_labels is not None
        assert len(config.text_labels) == 2
        
        # Collect photos
        photos = collect_photos(Path('tests/fixtures/sample-photos'))
        assert len(photos) > 0
        
        # Load theme
        theme = load_theme('clean')
        assert theme is not None
        
        # Associate text labels
        text_associations = associate_text_labels_with_photos(config.text_labels, photos)
        assert len(text_associations) == len(photos)
        
        # Check that at least some labels were associated
        associated_count = sum(1 for _, label in text_associations if label is not None)
        assert associated_count == 2  # We have 2 text labels
        
        # Calculate layout
        page_width, page_height = config.get_paper_size_pixels()
        distribution = distribute_photos(
            total_photos=len(photos),
            photos_per_page=config.layout.photos_per_page,
            total_pages=config.layout.pages
        )
        
        # Render pages
        pages = list(render_all_pages(
            page_width, page_height, photos, distribution, theme, text_associations
        ))
        
        assert len(pages) == distribution.total_pages
        for page in pages:
            assert page.width == page_width
            assert page.height == page_height
    
    def test_pipeline_without_text_labels(self):
        """Test pipeline works without text labels (backward compatibility)."""
        # Create minimal config without text labels
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""photos: tests/fixtures/sample-photos
output:
  size: A4
  format: pdf
layout:
  photos_per_page: 2
theme: clean
""")
            config_path = Path(f.name)
        
        try:
            config = load_config(config_path)
            assert config.text_labels == []
            
            photos = collect_photos(Path('tests/fixtures/sample-photos'))
            theme = load_theme('clean')
            
            page_width, page_height = config.get_paper_size_pixels()
            distribution = distribute_photos(
                total_photos=len(photos),
                photos_per_page=config.layout.photos_per_page,
                total_pages=config.layout.pages
            )
            
            # Render without text associations
            pages = list(render_all_pages(
                page_width, page_height, photos, distribution, theme
            ))
            
            assert len(pages) == distribution.total_pages
        finally:
            config_path.unlink()
    
    def test_pipeline_with_unmatched_text_labels(self, tmp_path):
        """Test pipeline with text labels that don't match any photos."""
        config_content = """photos: tests/fixtures/sample-photos
output:
  size: A4
  format: pdf
layout:
  photos_per_page: 2
theme: clean
text_labels:
  - timestamp: "2020-01-01T00:00:00"
    text: "Very old timestamp"
  - timestamp: "2030-12-31T23:59:59"
    text: "Future timestamp"
"""
        config_path = tmp_path / "test-config.yaml"
        config_path.write_text(config_content)
        
        config = load_config(config_path)
        photos = collect_photos(Path('tests/fixtures/sample-photos'))
        
        # Labels will still be associated with closest photos
        text_associations = associate_text_labels_with_photos(config.text_labels, photos)
        
        # All labels get associated with some photo
        associated_count = sum(1 for _, label in text_associations if label is not None)
        assert associated_count == 2
    
    def test_markdown_formatting_in_pipeline(self, tmp_path):
        """Test that markdown formatting is preserved through pipeline."""
        config_content = """photos: tests/fixtures/sample-photos
output:
  size: A4
  format: pdf
layout:
  photos_per_page: 2
theme: clean
text_labels:
  - timestamp: "2026-07-03T17:32:24"
    text: "# Heading\\n**Bold** and *italic* and ***both***"
"""
        config_path = tmp_path / "test-config.yaml"
        config_path.write_text(config_content)
        
        config = load_config(config_path)
        assert "# Heading" in config.text_labels[0]['text']
        assert "**Bold**" in config.text_labels[0]['text']
        assert "*italic*" in config.text_labels[0]['text']
        
        photos = collect_photos(Path('tests/fixtures/sample-photos'))
        text_associations = associate_text_labels_with_photos(config.text_labels, photos)
        
        # Find the associated label
        label = next((lbl for _, lbl in text_associations if lbl is not None), None)
        assert label is not None
        assert "Heading" in label.text
        assert "Bold" in label.text
        assert "italic" in label.text


class TestLayoutWithTextPositions:
    """Tests for layout engine with text positions."""
    
    def test_theme_with_text_positions(self):
        """Test loading theme with text positions."""
        theme = load_theme('clean')
        
        # Find a layout with text positions
        has_text_position = False
        for layout in theme.layouts:
            for photo_spec in layout.photos:
                if photo_spec.text is not None:
                    has_text_position = True
                    assert 0 <= photo_spec.text.x <= 100
                    assert 0 <= photo_spec.text.y <= 100
                    assert 0 <= photo_spec.text.width <= 100
                    # Height is optional - if specified, must be in range
                    if photo_spec.text.height is not None:
                        assert 0 <= photo_spec.text.height <= 100
                    assert photo_spec.text.align in ['left', 'center', 'right']
        
        # Clean theme should have at least one layout with text positioning
        assert has_text_position
    
    def test_theme_without_text_positions(self):
        """Test that layouts without text positions work correctly."""
        theme = load_theme('clean')
        
        # Count layouts without text positions
        layouts_without_text = 0
        for layout in theme.layouts:
            has_text = any(photo.text is not None for photo in layout.photos)
            if not has_text:
                layouts_without_text += 1
        
        # Should have some layouts without text (backward compatibility)
        assert layouts_without_text > 0


class TestTextRendering:
    """Tests for text rendering in output."""
    
    def test_render_page_with_text(self):
        """Test rendering a page with text labels."""
        from src.photobook_as_code.renderer import render_page
        from src.photobook_as_code.text_labels import TextLabel
        from datetime import datetime
        
        # Create test data
        photos = collect_photos(Path('tests/fixtures/sample-photos'))[:2]
        theme = load_theme('clean')
        
        # Create text labels
        text_labels = [
            TextLabel(datetime.now(), "# Test Heading\nSome text"),
            TextLabel(datetime.now(), "**Bold text**")
        ]
        
        # Render page
        page = render_page(
            page_width=2480,
            page_height=3508,
            photos=photos,
            theme=theme,
            page_number=0,
            text_labels=text_labels
        )
        
        assert page is not None
        assert page.width == 2480
        assert page.height == 3508
    
    def test_render_page_without_text(self):
        """Test rendering a page without text labels."""
        from src.photobook_as_code.renderer import render_page
        
        photos = collect_photos(Path('tests/fixtures/sample-photos'))[:2]
        theme = load_theme('clean')
        
        # Render without text labels
        page = render_page(
            page_width=2480,
            page_height=3508,
            photos=photos,
            theme=theme,
            page_number=0
        )
        
        assert page is not None
    
    def test_render_with_various_alignments(self):
        """Test rendering text with different alignments."""
        from src.photobook_as_code.themes import TextPosition
        from PIL import Image, ImageDraw
        from src.photobook_as_code.renderer import render_text_label
        from src.photobook_as_code.text_labels import TextLabel
        from datetime import datetime
        
        theme = load_theme('clean')
        img = Image.new('RGB', (800, 600), color='white')
        draw = ImageDraw.Draw(img)
        
        label = TextLabel(datetime.now(), "Test text")
        
        # Test different alignments
        for align in ['left', 'center', 'right']:
            text_pos = TextPosition(
                x=10, y=10, width=80,
                align=align
            )
            
            # Should not raise an error
            render_text_label(draw, label, text_pos, 800, 600, photo_pos_y=50, photo_height=400, theme=theme)


class TestOutputFormats:
    """Tests for different output formats with text labels."""
    
    def test_pdf_output_with_text(self, tmp_path):
        """Test PDF generation with text labels."""
        from src.photobook_as_code.output import generate_output
        
        photos = collect_photos(Path('tests/fixtures/sample-photos'))[:4]
        theme = load_theme('clean')
        
        config_content = """photos: tests/fixtures/sample-photos
output:
  size: A4
  format: pdf
layout:
  photos_per_page: 2
theme: clean
text_labels:
  - timestamp: "2026-07-03T17:32:24"
    text: "Test label"
"""
        config_path = tmp_path / "test-config.yaml"
        config_path.write_text(config_content)
        
        config = load_config(config_path)
        text_associations = associate_text_labels_with_photos(config.text_labels, photos)
        
        page_width, page_height = config.get_paper_size_pixels()
        distribution = distribute_photos(
            total_photos=len(photos),
            photos_per_page=config.layout.photos_per_page,
            total_pages=config.layout.pages
        )
        
        pages_gen = render_all_pages(
            page_width, page_height, photos, distribution, theme, text_associations
        )
        
        output_path = tmp_path / "test-output.pdf"
        output_files = generate_output(
            pages=pages_gen,
            output_format='pdf',
            output_path=output_path,
            page_width=page_width,
            page_height=page_height,
            total_pages=distribution.total_pages,
            quality=85,
            dpi=300
        )
        
        assert len(output_files) == 1
        assert Path(output_files[0]).exists()
        assert Path(output_files[0]).stat().st_size > 0
    
    def test_png_output_with_text(self, tmp_path):
        """Test PNG generation with text labels."""
        from src.photobook_as_code.output import generate_output
        
        photos = collect_photos(Path('tests/fixtures/sample-photos'))[:2]
        theme = load_theme('clean')
        
        config_content = """photos: tests/fixtures/sample-photos
output:
  size: A4
  format: png
layout:
  photos_per_page: 2
theme: clean
text_labels:
  - timestamp: "2026-07-03T17:32:24"
    text: "Test label"
"""
        config_path = tmp_path / "test-config.yaml"
        config_path.write_text(config_content)
        
        config = load_config(config_path)
        text_associations = associate_text_labels_with_photos(config.text_labels, photos)
        
        page_width, page_height = config.get_paper_size_pixels()
        distribution = distribute_photos(
            total_photos=len(photos),
            photos_per_page=config.layout.photos_per_page,
            total_pages=config.layout.pages
        )
        
        pages_gen = render_all_pages(
            page_width, page_height, photos, distribution, theme, text_associations
        )
        
        output_path = tmp_path / "test-output.png"
        output_files = generate_output(
            pages=pages_gen,
            output_format='png',
            output_path=output_path,
            page_width=page_width,
            page_height=page_height,
            total_pages=distribution.total_pages,
            quality=85,
            dpi=300
        )
        
        # PNG format creates one file per page
        assert len(output_files) >= 1
        for output_file in output_files:
            assert Path(output_file).exists()
            assert Path(output_file).stat().st_size > 0
