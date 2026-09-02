"""
Tests for HTML slideshow generation.
"""

import os
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from PIL import Image

from photobook_as_code.html_output import (
    HtmlOutputError,
    _relative_href,
    _render_markdown_html,
    generate_html_slideshow,
)
from photobook_as_code.photos import collect_photos
from photobook_as_code.text_labels import (
    associate_text_labels_with_photos,
    merge_titles_with_photos,
    parse_title_labels,
)
from photobook_as_code.themes import load_theme


def _make_photos_dir(tmp_path, filenames, base=None, subdir="photos"):
    base = base or datetime(2026, 7, 1, 10, 0, 0)
    photos_dir = tmp_path / subdir
    photos_dir.mkdir()
    for i, filename in enumerate(filenames):
        path = photos_dir / filename
        Image.new("RGB", (800, 600), color="blue").save(path)
        mtime = (base + timedelta(hours=i)).timestamp()
        os.utime(path, (mtime, mtime))
    return photos_dir, base


class TestGenerateHtmlSlideshow:
    def test_creates_single_html_file(self, tmp_path):
        photos_dir, _ = _make_photos_dir(tmp_path, ["a.jpg", "b.jpg", "c.jpg"])
        photos = collect_photos([photos_dir], order="date")
        theme = load_theme("clean")

        output_path = photos_dir / "slideshow.html"
        result = generate_html_slideshow(photos, None, theme, output_path)

        assert result == output_path
        assert output_path.exists()
        # single file: nothing else written into the directory besides the photos
        assert sorted(p.name for p in photos_dir.iterdir()) == ["a.jpg", "b.jpg", "c.jpg", "slideshow.html"]

    def test_one_slide_per_page_item_in_order(self, tmp_path):
        photos_dir, base = _make_photos_dir(tmp_path, ["a.jpg", "b.jpg"])
        photos = collect_photos([photos_dir], order="date")
        titles = parse_title_labels([
            {"timestamp": (base - timedelta(hours=1)).isoformat(), "title": "Intro"},
        ])
        page_items = merge_titles_with_photos(titles, photos)
        theme = load_theme("clean")

        output_path = photos_dir / "slideshow.html"
        generate_html_slideshow(page_items, None, theme, output_path)
        html = output_path.read_text()

        assert html.count('class="ps-slide') == 3
        assert html.index("Intro") < html.index('data-src="a.jpg"') < html.index('data-src="b.jpg"')

    def test_no_page_items_raises(self, tmp_path):
        theme = load_theme("clean")
        with pytest.raises(HtmlOutputError, match="No pages"):
            generate_html_slideshow([], None, theme, tmp_path / "out.html")

    def test_write_failure_raises_clear_html_output_error(self, tmp_path, monkeypatch):
        """No fallback location is attempted if the output path can't be
        written to (e.g. a read-only first photo folder) - a clear
        HtmlOutputError is raised instead."""
        photos_dir, _ = _make_photos_dir(tmp_path, ["a.jpg"])
        photos = collect_photos([photos_dir])
        theme = load_theme("clean")
        output_path = photos_dir / "slideshow.html"

        def raising_write_text(self, *args, **kwargs):
            raise PermissionError("Permission denied")

        monkeypatch.setattr(Path, "write_text", raising_write_text)

        with pytest.raises(HtmlOutputError, match=str(output_path)):
            generate_html_slideshow(photos, None, theme, output_path)

    def test_photo_without_caption_has_no_caption_markup(self, tmp_path):
        photos_dir, _ = _make_photos_dir(tmp_path, ["a.jpg"])
        photos = collect_photos([photos_dir])
        theme = load_theme("clean")

        output_path = photos_dir / "slideshow.html"
        generate_html_slideshow(photos, None, theme, output_path)
        html = output_path.read_text()

        assert '<div class="ps-caption"' not in html

    def test_photo_with_caption_has_caption_markup(self, tmp_path):
        photos_dir, base = _make_photos_dir(tmp_path, ["a.jpg"])
        photos = collect_photos([photos_dir])
        text_assoc = associate_text_labels_with_photos(
            [{"timestamp": base.isoformat(), "text": "Hello **world**"}], photos
        )
        theme = load_theme("clean")

        output_path = photos_dir / "slideshow.html"
        generate_html_slideshow(photos, text_assoc, theme, output_path)
        html = output_path.read_text()

        assert 'class="ps-caption"' in html
        assert "Hello <strong>world</strong>" in html

    def test_title_slide_has_no_image(self, tmp_path):
        photos_dir, base = _make_photos_dir(tmp_path, ["a.jpg"])
        photos = collect_photos([photos_dir])
        titles = parse_title_labels([{"timestamp": base.isoformat(), "title": "# Chapter"}])
        page_items = merge_titles_with_photos(titles, photos)
        theme = load_theme("clean")

        output_path = photos_dir / "slideshow.html"
        generate_html_slideshow(page_items, None, theme, output_path)
        html = output_path.read_text()

        start = html.index('class="ps-slide ps-title"')
        title_block = html[start:html.index('</section>', start)]
        assert "<img" not in title_block
        assert "Chapter" in title_block

    def test_jit_loading_markup_no_eager_src(self, tmp_path):
        photos_dir, _ = _make_photos_dir(tmp_path, ["a.jpg", "b.jpg", "c.jpg"])
        photos = collect_photos([photos_dir], order="date")
        theme = load_theme("clean")

        output_path = photos_dir / "slideshow.html"
        generate_html_slideshow(photos, None, theme, output_path)
        html = output_path.read_text()

        # No <img> tag ships with a real src attribute - only data-src - so
        # nothing loads until the inline script assigns it.
        assert html.count("data-src=") == 3
        assert 'src="' not in html.replace('data-src="', '')

    def test_alt_text_is_photo_filename(self, tmp_path):
        photos_dir, _ = _make_photos_dir(tmp_path, ["holiday.jpg"])
        photos = collect_photos([photos_dir])
        theme = load_theme("clean")

        output_path = photos_dir / "slideshow.html"
        generate_html_slideshow(photos, None, theme, output_path)
        html = output_path.read_text()

        assert 'alt="holiday.jpg"' in html

    def test_relative_path_within_same_folder(self, tmp_path):
        photos_dir, _ = _make_photos_dir(tmp_path, ["a.jpg"])
        photos = collect_photos([photos_dir])
        theme = load_theme("clean")

        output_path = photos_dir / "slideshow.html"
        generate_html_slideshow(photos, None, theme, output_path)
        html = output_path.read_text()

        assert 'data-src="a.jpg"' in html

    def test_relative_path_across_multiple_folders(self, tmp_path):
        base = datetime(2026, 7, 1, 10, 0, 0)
        folder1 = tmp_path / "first"
        folder2 = tmp_path / "second"
        folder1.mkdir()
        folder2.mkdir()
        photo_a, photo_b = folder1 / "a.jpg", folder2 / "b.jpg"
        Image.new("RGB", (800, 600)).save(photo_a)
        Image.new("RGB", (800, 600)).save(photo_b)
        for i, p in enumerate([photo_a, photo_b]):
            mtime = (base + timedelta(hours=i)).timestamp()
            os.utime(p, (mtime, mtime))

        photos = collect_photos([folder1, folder2], order="date")
        theme = load_theme("clean")

        output_path = folder1 / "slideshow.html"  # written into the "first" folder
        generate_html_slideshow(photos, None, theme, output_path)
        html = output_path.read_text()

        assert 'data-src="a.jpg"' in html
        assert 'data-src="../second/b.jpg"' in html

    def test_relative_path_encodes_spaces_and_non_ascii(self, tmp_path):
        folder1 = tmp_path / "für Heinz"
        folder1.mkdir()
        Image.new("RGB", (800, 600)).save(folder1 / "München Foto.jpg")

        photos = collect_photos([folder1])
        theme = load_theme("clean")

        output_path = folder1 / "slideshow.html"
        generate_html_slideshow(photos, None, theme, output_path)
        html = output_path.read_text()

        assert 'data-src="M%C3%BCnchen%20Foto.jpg"' in html

    def test_embeds_font_once_when_text_and_title_share_a_family(self, tmp_path):
        photos_dir, _ = _make_photos_dir(tmp_path, ["a.jpg"])
        photos = collect_photos([photos_dir])
        theme = load_theme("clean2")  # text and title both use DejaVuSans

        output_path = photos_dir / "slideshow.html"
        generate_html_slideshow(photos, None, theme, output_path)
        html = output_path.read_text()

        assert "data:font/ttf;base64," in html
        # 4 variants (regular/bold/italic/bold-italic) embedded once, not twice
        assert html.count("@font-face") == 4

    def test_missing_font_falls_back_without_failing(self, tmp_path, monkeypatch):
        from photobook_as_code import html_output

        photos_dir, _ = _make_photos_dir(tmp_path, ["a.jpg"])
        photos = collect_photos([photos_dir])
        theme = load_theme("clean")

        monkeypatch.setattr(
            html_output, "font_variant_paths",
            lambda family: tuple(Path("/nonexistent") / f"{family}{i}.ttf" for i in range(4))
        )

        output_path = photos_dir / "slideshow.html"
        generate_html_slideshow(photos, None, theme, output_path)  # must not raise
        html = output_path.read_text()

        assert "@font-face" not in html
        assert "sans-serif" in html

    def test_interval_seconds_reflected_in_script(self, tmp_path):
        photos_dir, _ = _make_photos_dir(tmp_path, ["a.jpg"])
        photos = collect_photos([photos_dir])
        theme = load_theme("clean")

        output_path = photos_dir / "slideshow.html"
        generate_html_slideshow(photos, None, theme, output_path, interval_seconds=2.5)
        html = output_path.read_text()

        assert "INTERVAL_MS = 2500" in html

    def test_script_has_loop_pause_and_manual_navigation_hooks(self, tmp_path):
        photos_dir, _ = _make_photos_dir(tmp_path, ["a.jpg", "b.jpg"])
        photos = collect_photos([photos_dir], order="date")
        theme = load_theme("clean")

        output_path = photos_dir / "slideshow.html"
        generate_html_slideshow(photos, None, theme, output_path)
        html = output_path.read_text()

        assert "setTimeout" in html  # autoplay scheduling
        assert "% slides.length" in html  # wraps/loops rather than stopping at the end
        assert "togglePlay" in html
        assert "keydown" in html and "ArrowRight" in html and "ArrowLeft" in html


class TestMarkdownToHtml:
    def test_bold_and_italic(self):
        result = _render_markdown_html("**bold** and *italic*")
        assert "<strong>bold</strong>" in result
        assert "<em>italic</em>" in result

    def test_heading_levels_get_progressively_larger_font_size(self):
        assert "font-size:1.5em" in _render_markdown_html("# Heading 1")
        assert "font-size:1.3em" in _render_markdown_html("## Heading 2")
        assert "font-size:1.2em" in _render_markdown_html("### Heading 3")
        assert "font-size:" not in _render_markdown_html("Not a heading")

    def test_blank_interior_line_preserved(self):
        result = _render_markdown_html("Line one\n\nLine two")
        assert result.count('class="ps-line"') == 3

    def test_html_is_escaped(self):
        result = _render_markdown_html("<script>alert(1)</script>")
        assert "<script>" not in result
        assert "&lt;script&gt;" in result


class TestRelativeHref:
    def test_same_directory(self, tmp_path):
        photo = tmp_path / "a.jpg"
        photo.touch()
        assert _relative_href(photo, tmp_path) == "a.jpg"

    def test_sibling_directory_uses_parent_traversal(self, tmp_path):
        other = tmp_path / "other"
        other.mkdir()
        photo = other / "a.jpg"
        photo.touch()
        assert _relative_href(photo, tmp_path) == "other/a.jpg"
