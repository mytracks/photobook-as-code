"""
Integration tests for text labels feature.
Tests the complete pipeline from configuration to rendered output.
"""

import pytest
from pathlib import Path
import tempfile
import shutil
import os
from datetime import datetime, timedelta
from PIL import Image, ImageDraw
import yaml

from src.photobook_as_code.config import load_config
from src.photobook_as_code.photos import collect_photos
from src.photobook_as_code.themes import load_theme
from src.photobook_as_code.layout import distribute_photos
from src.photobook_as_code.renderer import render_all_pages, render_title_slot
from src.photobook_as_code.text_labels import (
    associate_text_labels_with_photos,
    parse_title_labels,
    merge_titles_with_photos,
    parse_markdown_text,
    TitleLabel,
)


class TestTextLabelsIntegration:
    """Integration tests for full text labels pipeline."""
    
    @pytest.fixture
    def test_config_file(self, tmp_path):
        """Create a test configuration file with text labels."""
        config_content = """photo_folders:
  - tests/fixtures/sample-photos
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
        photos = collect_photos([Path('tests/fixtures/sample-photos')])
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
            items=photos,
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
            f.write("""photo_folders:
  - tests/fixtures/sample-photos
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
            
            photos = collect_photos([Path('tests/fixtures/sample-photos')])
            theme = load_theme('clean')
            
            page_width, page_height = config.get_paper_size_pixels()
            distribution = distribute_photos(
                items=photos,
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
        config_content = """photo_folders:
  - tests/fixtures/sample-photos
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
        photos = collect_photos([Path('tests/fixtures/sample-photos')])
        
        # Labels will still be associated with closest photos
        text_associations = associate_text_labels_with_photos(config.text_labels, photos)
        
        # All labels get associated with some photo
        associated_count = sum(1 for _, label in text_associations if label is not None)
        assert associated_count == 2
    
    def test_markdown_formatting_in_pipeline(self, tmp_path):
        """Test that markdown formatting is preserved through pipeline."""
        config_content = """photo_folders:
  - tests/fixtures/sample-photos
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
        
        photos = collect_photos([Path('tests/fixtures/sample-photos')])
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
        photos = collect_photos([Path('tests/fixtures/sample-photos')])[:2]
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
        
        photos = collect_photos([Path('tests/fixtures/sample-photos')])[:2]
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
            render_text_label(draw, label, text_pos, 800, 600,
                               photo_pos_x=100, photo_pos_y=50, photo_width=600, photo_height=400,
                               theme=theme)


class TestOutputFormats:
    """Tests for different output formats with text labels."""
    
    def test_pdf_output_with_text(self, tmp_path):
        """Test PDF generation with text labels."""
        from src.photobook_as_code.output import generate_output
        
        photos = collect_photos([Path('tests/fixtures/sample-photos')])[:4]
        theme = load_theme('clean')
        
        config_content = """photo_folders:
  - tests/fixtures/sample-photos
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
            items=photos,
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

        import pikepdf
        with pikepdf.open(output_files[0]) as pdf:
            assert len(pdf.pages) == distribution.total_pages

    def test_png_output_with_text(self, tmp_path):
        """Test PNG generation with text labels."""
        from src.photobook_as_code.output import generate_output
        
        photos = collect_photos([Path('tests/fixtures/sample-photos')])[:2]
        theme = load_theme('clean')
        
        config_content = """photo_folders:
  - tests/fixtures/sample-photos
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
            items=photos,
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


class TestMixedTextAndTitleLabelsIntegration:
    """Integration tests for a photobook mixing 'text' captions and 'title' slots."""

    @pytest.fixture
    def photos_dir_with_titles_config(self, tmp_path):
        """
        Create a photos directory (4 photos, deterministic mtimes an hour apart)
        and a config file with 2 'title' entries and 1 'text' entry, chosen so
        the titles land before-all, and between two photos.
        """
        photos_dir = tmp_path / "photos"
        photos_dir.mkdir()

        base = datetime(2026, 7, 1, 10, 0, 0)
        filenames = ["photo_a.jpg", "photo_b.jpg", "photo_c.jpg", "photo_d.jpg"]
        for i, filename in enumerate(filenames):
            path = photos_dir / filename
            Image.new("RGB", (800, 600), color="blue").save(path)
            mtime = (base + timedelta(hours=i)).timestamp()
            os.utime(path, (mtime, mtime))

        title_before_all = base - timedelta(hours=1)  # before photo_a
        title_between_b_and_c = base + timedelta(hours=1, minutes=30)  # between photo_b (+1h) and photo_c (+2h)
        caption_near_a = base + timedelta(minutes=5)  # closest to photo_a

        config_content = f"""photo_folders:
  - {photos_dir}
output:
  size: A4
  format: pdf
layout:
  photos_per_page: 2
  order: date
theme: clean
text_labels:
  - timestamp: "{title_before_all.isoformat()}"
    title: "# Chapter One"
  - timestamp: "{title_between_b_and_c.isoformat()}"
    title: "## Chapter Two"
  - timestamp: "{caption_near_a.isoformat()}"
    text: "A caption"
"""
        config_path = tmp_path / "test-config.yaml"
        config_path.write_text(config_content)
        return config_path, photos_dir

    def test_mixed_config_merges_titles_and_increases_page_count(self, photos_dir_with_titles_config):
        config_path, photos_dir = photos_dir_with_titles_config

        config = load_config(config_path)
        assert len(config.text_labels) == 3

        photos = collect_photos([photos_dir], order=config.layout.order)
        assert len(photos) == 4

        theme = load_theme(config.theme)

        # Caption association is unaffected by the presence of title entries
        text_associations = associate_text_labels_with_photos(config.text_labels, photos)
        assert sum(1 for _, label in text_associations if label is not None) == 1

        # Titles merge chronologically: before all photos, and between photo_b/photo_c
        titles = parse_title_labels(config.text_labels)
        assert len(titles) == 2
        merged = merge_titles_with_photos(titles, photos)

        assert len(merged) == len(photos) + len(titles)
        assert isinstance(merged[0], TitleLabel) and merged[0].title == "# Chapter One"
        assert merged[1] == photos[0]  # photo_a
        assert merged[2] == photos[1]  # photo_b
        assert isinstance(merged[3], TitleLabel) and merged[3].title == "## Chapter Two"
        assert merged[4] == photos[2]  # photo_c
        assert merged[5] == photos[3]  # photo_d

        # Distribution must account for titles increasing the total slot count
        distribution_with_titles = distribute_photos(
            items=merged,
            photos_per_page=config.layout.photos_per_page,
        )
        distribution_without_titles = distribute_photos(
            items=photos,
            photos_per_page=config.layout.photos_per_page,
        )
        assert distribution_with_titles.total_pages == 3  # 6 items / 2 per page
        assert distribution_without_titles.total_pages == 2  # 4 photos / 2 per page
        assert distribution_with_titles.total_pages > distribution_without_titles.total_pages

        # Full rendering pipeline runs over the merged sequence without error
        page_width, page_height = config.get_paper_size_pixels()
        pages = list(render_all_pages(
            page_width, page_height, merged, distribution_with_titles, theme, text_associations
        ))

        assert len(pages) == distribution_with_titles.total_pages
        for page in pages:
            assert page.width == page_width
            assert page.height == page_height


class TestExampleConfigBlankLineTitle:
    """Regression test for the motivating case: example-config.yaml's title
    entry (`# **Hamburg**` / blank line / `30. April 2026`) uses an interior
    blank line to separate heading from date, written as a YAML `|` block
    scalar - which also appends a trailing newline nobody typed."""

    def _load_example_title_text(self):
        config_path = Path(__file__).resolve().parent.parent / "example-config.yaml"
        data = yaml.safe_load(config_path.read_text())
        return data["text_labels"][0]["title"]

    def test_example_title_trims_trailing_blank_but_keeps_interior_one(self):
        title_text = self._load_example_title_text()
        lines = parse_markdown_text(title_text)

        # Heading + interior blank + date line - the YAML clip-chomping
        # trailing blank must not survive as a fourth entry.
        assert len(lines) == 3
        assert lines[0][1] == 1  # "# **Hamburg**" is a level-1 heading
        assert lines[1][0][0].text == ""  # interior blank line preserved
        assert "30. April 2026" in lines[2][0][0].text

    def test_example_title_renders_with_visible_gap_between_heading_and_date(self):
        title_text = self._load_example_title_text()
        theme = load_theme("clean2")

        box_width, box_height = 1600, 900
        img = Image.new("RGB", (box_width, box_height), color=(0, 0, 0))
        draw = ImageDraw.Draw(img)
        title_label = TitleLabel(datetime.now(), title_text)
        render_title_slot(draw, title_label, box_x=0, box_y=0,
                           box_width=box_width, box_height=box_height, theme=theme)

        def row_has_ink(y):
            return any(img.getpixel((x, y)) != (0, 0, 0) for x in range(box_width))

        ink_rows = [y for y in range(box_height) if row_has_ink(y)]
        assert ink_rows

        # Group ink_rows into contiguous runs (bands of glyph ink).
        runs = [[ink_rows[0]]]
        for y in ink_rows[1:]:
            if y == runs[-1][-1] + 1:
                runs[-1].append(y)
            else:
                runs.append([y])

        # Exactly two lines rendered ink: the heading, then the date -
        # nothing left over from a phantom trailing blank line.
        assert len(runs) == 2
        gap = runs[1][0] - runs[0][-1] - 1
        assert gap > 20  # a real line-height gap, not the old ~4px sliver
