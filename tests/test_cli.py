import os
from datetime import datetime, timedelta

from click.testing import CliRunner
from PIL import Image

from photobook_as_code.cli import main


def _make_photos_dir(tmp_path):
    """
    Create a photos directory with 3 photos whose deterministic mtimes are
    NOT in filename-alphabetical order, so a test can distinguish
    chronological stub ordering from alphabetical layout order.
    """
    photos_dir = tmp_path / "photos"
    photos_dir.mkdir()

    base = datetime(2026, 7, 1, 10, 0, 0)
    # filename -> hours offset from base; alphabetical filename order
    # (photo_a, photo_m, photo_z) differs from chronological order
    # (photo_z, photo_m, photo_a).
    offsets = {"photo_a.jpg": 2, "photo_m.jpg": 1, "photo_z.jpg": 0}
    for filename, hours in offsets.items():
        path = photos_dir / filename
        Image.new("RGB", (800, 600), color="blue").save(path)
        mtime = (base + timedelta(hours=hours)).timestamp()
        os.utime(path, (mtime, mtime))

    return photos_dir, base


def test_extract_labels_prints_stubs_and_writes_no_output(tmp_path):
    photos_dir, base = _make_photos_dir(tmp_path)
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    config_content = f"""photo_folders:
  - {photos_dir}
output:
  size: A4
  format: pdf
  directory: {output_dir}
layout:
  photos_per_page: 4
theme: clean
text_labels:
  - timestamp: "2020-01-01T00:00:00"
    text: "Pre-existing entry, must be ignored"
"""
    config_path = tmp_path / "test-config.yaml"
    config_path.write_text(config_content)

    runner = CliRunner()
    result = runner.invoke(main, ["--config", str(config_path), "--extract-labels"])

    assert result.exit_code == 0, result.output

    expected = (
        "text_labels:\n"
        f'  - timestamp: "{base.isoformat()}"  # photo_z.jpg\n'
        '    text: ""\n'
        f'  - timestamp: "{(base + timedelta(hours=1)).isoformat()}"  # photo_m.jpg\n'
        '    text: ""\n'
        f'  - timestamp: "{(base + timedelta(hours=2)).isoformat()}"  # photo_a.jpg\n'
        '    text: ""\n'
    )
    assert result.output == expected

    # Chronological order beats the config's (default) alphabetical layout order
    assert result.output.index("photo_z.jpg") < result.output.index("photo_m.jpg") < result.output.index("photo_a.jpg")

    # No photobook output was generated
    assert list(output_dir.iterdir()) == []


def test_extract_labels_collapses_shared_timestamp(tmp_path):
    photos_dir = tmp_path / "photos"
    photos_dir.mkdir()

    shared = datetime(2026, 7, 1, 10, 0, 0)
    for filename in ("photo_b.jpg", "photo_c.jpg"):
        path = photos_dir / filename
        Image.new("RGB", (800, 600), color="blue").save(path)
        mtime = shared.timestamp()
        os.utime(path, (mtime, mtime))

    config_content = f"""photo_folders:
  - {photos_dir}
output:
  size: A4
  format: pdf
layout:
  photos_per_page: 4
theme: clean
"""
    config_path = tmp_path / "test-config.yaml"
    config_path.write_text(config_content)

    runner = CliRunner()
    result = runner.invoke(main, ["--config", str(config_path), "--extract-labels"])

    assert result.exit_code == 0, result.output
    assert result.output == (
        "text_labels:\n"
        f'  - timestamp: "{shared.isoformat()}"  # photo_b.jpg, photo_c.jpg\n'
        '    text: ""\n'
    )


def test_jpg_output_writes_pages_directly_into_output_directory(tmp_path):
    photos_dir, _ = _make_photos_dir(tmp_path)
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    config_content = f"""photo_folders:
  - {photos_dir}
output:
  size: A4
  format: jpg
  filename: mondsee
  directory: {output_dir}
layout:
  photos_per_page: 4
theme: clean
"""
    config_path = tmp_path / "test-config.yaml"
    config_path.write_text(config_content)

    runner = CliRunner()
    result = runner.invoke(main, ["--config", str(config_path)])

    assert result.exit_code == 0, result.output

    # Page files land directly in the configured output directory.
    assert sorted(p.name for p in output_dir.iterdir()) == ["mondsee_page_001.jpg"]
    # No subfolder shaped like a file (e.g. "mondsee.jpg") was created.
    assert not (output_dir / "mondsee.jpg").exists()


def test_transparent_png_output_produces_rgba_with_transparent_margin(tmp_path):
    photos_dir, _ = _make_photos_dir(tmp_path)
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    config_content = f"""photo_folders:
  - {photos_dir}
output:
  size: A4
  format: png
  transparent: true
  filename: mondsee
  directory: {output_dir}
layout:
  photos_per_page: 4
theme: clean
"""
    config_path = tmp_path / "test-config.yaml"
    config_path.write_text(config_content)

    runner = CliRunner()
    result = runner.invoke(main, ["--config", str(config_path)])

    assert result.exit_code == 0, result.output

    output_files = sorted(output_dir.iterdir())
    assert [p.name for p in output_files] == ["mondsee_page_001.png"]

    page = Image.open(output_files[0])
    assert page.mode == 'RGBA'
    # Corner pixel is page margin, never covered by a photo - must be fully transparent
    assert page.getpixel((0, 0))[3] == 0


def test_transparent_true_with_pdf_format_reports_configuration_error(tmp_path):
    photos_dir, _ = _make_photos_dir(tmp_path)
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    config_content = f"""photo_folders:
  - {photos_dir}
output:
  size: A4
  format: pdf
  transparent: true
  directory: {output_dir}
layout:
  photos_per_page: 4
theme: clean
"""
    config_path = tmp_path / "test-config.yaml"
    config_path.write_text(config_content)

    runner = CliRunner()
    result = runner.invoke(main, ["--config", str(config_path)])

    assert result.exit_code == 1
    assert "output.transparent" in result.output


_PAGE_MARGIN_TEST_THEME = """
name: page-margin-test
description: minimal single-photo theme for page_margin override tests
background: {color: '#000000'}
borders: {enabled: false, width: 0, color: '#000000', shadow: false}
spacing: {page_margin: 90, photo_margin: 0}
layouts:
- count: 1
  photos:
  - orientation: landscape
    position: {x: 0.5, y: 0.5}
    size: {width: 1.0, height: 1.0}
"""


def _run_page_margin_config(tmp_path, page_margin_line):
    """Render one page from a single 800x600 blue photo against a minimal
    custom theme (page_margin: 90, photo_margin: 0) whose only layout fits
    the photo full-bleed within the margin. Since photo_margin is 0 and the
    photo is width-constrained (4:3 photo into a much taller A4 usable box),
    the photo's left edge lands at exactly x=page_margin - letting a single
    pixel column tell the two cases apart precisely.
    """
    photos_dir, _ = _make_photos_dir(tmp_path)
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    theme_path = tmp_path / "theme.yaml"
    theme_path.write_text(_PAGE_MARGIN_TEST_THEME)

    config_content = f"""photo_folders:
  - {photos_dir}
output:
  size: A4
  format: png
  directory: {output_dir}
{page_margin_line}
layout:
  photos_per_page: 1
theme: {theme_path}
"""
    config_path = tmp_path / "test-config.yaml"
    config_path.write_text(config_content)

    runner = CliRunner()
    result = runner.invoke(main, ["--config", str(config_path)])
    assert result.exit_code == 0, result.output

    page = Image.open(sorted(output_dir.iterdir())[0])
    mid_y = page.height // 2
    return page, mid_y


def _is_photo_blue(pixel):
    # LANCZOS resampling can shift a solid color by a shade even where the
    # photo is unscaled along that axis, so allow a little slack.
    r, g, b = pixel
    return r < 5 and g < 5 and b > 250


def test_page_margin_override_zero_moves_photo_flush_to_page_edge(tmp_path):
    page, mid_y = _run_page_margin_config(tmp_path, "  page_margin: 0")

    # Theme's own margin is 90; overriding to 0 must move the photo's left
    # edge all the way to the page border.
    assert _is_photo_blue(page.getpixel((0, mid_y)))


def test_page_margin_unset_keeps_theme_default_margin(tmp_path):
    page, mid_y = _run_page_margin_config(tmp_path, "")

    # No override: theme's own page_margin (90) still applies exactly as
    # before this change - column 0 is still background, column 90 is the
    # photo's left edge.
    assert page.getpixel((0, mid_y)) == (0, 0, 0)
    assert _is_photo_blue(page.getpixel((90, mid_y)))


def test_output_override_directory_for_jpg_uses_config_base_filename(tmp_path):
    photos_dir, _ = _make_photos_dir(tmp_path)
    override_dir = tmp_path / "override"
    override_dir.mkdir()

    config_content = f"""photo_folders:
  - {photos_dir}
output:
  size: A4
  format: jpg
  filename: mondsee
layout:
  photos_per_page: 4
theme: clean
"""
    config_path = tmp_path / "test-config.yaml"
    config_path.write_text(config_content)

    runner = CliRunner()
    result = runner.invoke(
        main, ["--config", str(config_path), "--output", str(override_dir)]
    )

    assert result.exit_code == 0, result.output

    # --output for jpg/png is always treated as the target directory, and the
    # base filename still comes from config, not the directory's own name.
    assert sorted(p.name for p in override_dir.iterdir()) == ["mondsee_page_001.jpg"]


class TestHtmlSlideshowFormat:
    """CLI-level tests for output.format: html - directory-forcing, filename
    override, and multi-folder relative paths."""

    def test_ignores_output_directory_writes_into_first_photo_folder(self, tmp_path):
        photos_dir, _ = _make_photos_dir(tmp_path)
        elsewhere = tmp_path / "elsewhere"
        elsewhere.mkdir()

        config_content = f"""photo_folders:
  - {photos_dir}
output:
  size: A4
  format: html
  directory: {elsewhere}
layout:
  photos_per_page: 4
theme: clean
"""
        config_path = tmp_path / "test-config.yaml"
        config_path.write_text(config_content)

        runner = CliRunner()
        result = runner.invoke(main, ["--config", str(config_path)])

        assert result.exit_code == 0, result.output
        assert (photos_dir / "test-config.html").exists()
        assert list(elsewhere.iterdir()) == []
        assert "ignored for html" in result.output

    def test_output_flag_directory_ignored_but_filename_honored(self, tmp_path):
        photos_dir, _ = _make_photos_dir(tmp_path)
        elsewhere = tmp_path / "elsewhere"
        elsewhere.mkdir()

        config_content = f"""photo_folders:
  - {photos_dir}
output:
  size: A4
  format: html
layout:
  photos_per_page: 4
theme: clean
"""
        config_path = tmp_path / "test-config.yaml"
        config_path.write_text(config_content)

        runner = CliRunner()
        result = runner.invoke(
            main, ["--config", str(config_path), "--output", str(elsewhere / "custom.html")]
        )

        assert result.exit_code == 0, result.output
        # Filename honored, but written into the first photo folder, not "elsewhere"
        assert (photos_dir / "custom.html").exists()
        assert list(elsewhere.iterdir()) == []
        assert "ignored for html" in result.output

    def test_output_filename_config_field_honored_directory_ignored(self, tmp_path):
        photos_dir, _ = _make_photos_dir(tmp_path)
        elsewhere = tmp_path / "elsewhere"
        elsewhere.mkdir()

        config_content = f"""photo_folders:
  - {photos_dir}
output:
  size: A4
  format: html
  filename: {elsewhere / "custom.html"}
layout:
  photos_per_page: 4
theme: clean
"""
        config_path = tmp_path / "test-config.yaml"
        config_path.write_text(config_content)

        runner = CliRunner()
        result = runner.invoke(main, ["--config", str(config_path)])

        assert result.exit_code == 0, result.output
        assert (photos_dir / "custom.html").exists()
        assert list(elsewhere.iterdir()) == []

    def test_no_override_uses_config_stem_and_no_notice_printed(self, tmp_path):
        photos_dir, _ = _make_photos_dir(tmp_path)

        config_content = f"""photo_folders:
  - {photos_dir}
output:
  size: A4
  format: html
layout:
  photos_per_page: 4
theme: clean
"""
        config_path = tmp_path / "test-config.yaml"
        config_path.write_text(config_content)

        runner = CliRunner()
        result = runner.invoke(main, ["--config", str(config_path)])

        assert result.exit_code == 0, result.output
        assert (photos_dir / "test-config.html").exists()
        assert "ignored for html" not in result.output

    def test_multi_folder_relative_paths_from_first_folder(self, tmp_path):
        photos_dir_1, base = _make_photos_dir(tmp_path)
        photos_dir_2 = tmp_path / "photos2"
        photos_dir_2.mkdir()
        second_photo = photos_dir_2 / "photo_extra.jpg"
        Image.new("RGB", (800, 600), color="green").save(second_photo)
        mtime = (base + timedelta(hours=10)).timestamp()
        os.utime(second_photo, (mtime, mtime))

        config_content = f"""photo_folders:
  - {photos_dir_1}
  - {photos_dir_2}
output:
  size: A4
  format: html
layout:
  photos_per_page: 4
theme: clean
"""
        config_path = tmp_path / "test-config.yaml"
        config_path.write_text(config_content)

        runner = CliRunner()
        result = runner.invoke(main, ["--config", str(config_path)])

        assert result.exit_code == 0, result.output
        html_path = photos_dir_1 / "test-config.html"
        assert html_path.exists()
        html = html_path.read_text()
        assert 'data-src="../photos2/photo_extra.jpg"' in html

    def test_transparent_true_no_longer_errors_with_html_format(self, tmp_path):
        """A config still carrying transparent: true from a previous png export
        (the motivating YAML-reuse case) must not block switching to html."""
        photos_dir, _ = _make_photos_dir(tmp_path)

        config_content = f"""photo_folders:
  - {photos_dir}
output:
  size: A4
  format: html
  transparent: true
layout:
  photos_per_page: 4
theme: clean
"""
        config_path = tmp_path / "test-config.yaml"
        config_path.write_text(config_content)

        runner = CliRunner()
        result = runner.invoke(main, ["--config", str(config_path)])

        assert result.exit_code == 0, result.output
        assert (photos_dir / "test-config.html").exists()

    def test_html_generation_error_reported_clearly(self, tmp_path, monkeypatch):
        photos_dir, _ = _make_photos_dir(tmp_path)

        config_content = f"""photo_folders:
  - {photos_dir}
output:
  size: A4
  format: html
layout:
  photos_per_page: 4
theme: clean
"""
        config_path = tmp_path / "test-config.yaml"
        config_path.write_text(config_content)

        from photobook_as_code import cli as cli_module
        from photobook_as_code.html_output import HtmlOutputError

        def failing_generate(*args, **kwargs):
            raise HtmlOutputError(f"Could not write to {photos_dir}: permission denied")

        monkeypatch.setattr(cli_module, "generate_html_slideshow", failing_generate)

        runner = CliRunner()
        result = runner.invoke(main, ["--config", str(config_path)])

        assert result.exit_code == 1
        assert "HTML slideshow error" in result.output
        assert "permission denied" in result.output
