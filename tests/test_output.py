import tempfile
from pathlib import Path

import pikepdf
import pytest
from PIL import Image

from photobook_as_code.output import OutputError, generate_pdf, generate_output


def make_solid_page(color, size=(400, 566)):
    return Image.new('RGB', size, color=color)


def test_generate_pdf_page_count_and_order(tmp_path):
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]
    pages = (make_solid_page(c) for c in colors)
    output_path = tmp_path / "out.pdf"

    generate_pdf(pages, output_path, page_width_pixels=400, page_height_pixels=566,
                 total_pages=len(colors), dpi=300, quality=95)

    assert output_path.exists()
    with pikepdf.open(output_path) as pdf:
        assert len(pdf.pages) == len(colors)
        for page, expected_color in zip(pdf.pages, colors):
            images = page.get_images()
            pdf_image = pikepdf.PdfImage(next(iter(images.values())))
            sampled = pdf_image.as_pil_image().resize((1, 1)).getpixel((0, 0))
            # JPEG compression means colors aren't pixel-exact
            assert all(abs(a - b) < 20 for a, b in zip(sampled, expected_color))


def test_generate_pdf_cleans_up_temp_dir_on_success(tmp_path, monkeypatch):
    created_dirs = []
    real_mkdtemp = tempfile.mkdtemp

    def spy_mkdtemp(*args, **kwargs):
        d = real_mkdtemp(*args, **kwargs)
        created_dirs.append(d)
        return d

    monkeypatch.setattr(tempfile, "mkdtemp", spy_mkdtemp)

    pages = (make_solid_page((10, 20, 30)) for _ in range(3))
    output_path = tmp_path / "out.pdf"

    generate_pdf(pages, output_path, page_width_pixels=400, page_height_pixels=566, total_pages=3)

    assert output_path.exists()
    assert created_dirs, "expected tempfile.mkdtemp to be called"
    assert not Path(created_dirs[0]).exists()


def test_generate_pdf_cleans_up_and_leaves_no_partial_file_on_failure(tmp_path, monkeypatch):
    created_dirs = []
    real_mkdtemp = tempfile.mkdtemp

    def spy_mkdtemp(*args, **kwargs):
        d = real_mkdtemp(*args, **kwargs)
        created_dirs.append(d)
        return d

    monkeypatch.setattr(tempfile, "mkdtemp", spy_mkdtemp)

    def failing_pages():
        yield make_solid_page((1, 2, 3))
        yield make_solid_page((4, 5, 6))
        raise RuntimeError("simulated render failure")

    output_path = tmp_path / "out.pdf"

    with pytest.raises(OutputError):
        generate_pdf(failing_pages(), output_path, page_width_pixels=400, page_height_pixels=566, total_pages=3)

    assert not output_path.exists()
    assert not (tmp_path / "out.pdf.tmp").exists()
    assert created_dirs, "expected tempfile.mkdtemp to be called"
    assert not Path(created_dirs[0]).exists()


def test_generate_output_jpg_writes_pages_directly_into_output_dir(tmp_path):
    colors = [(255, 0, 0), (0, 255, 0)]
    pages = (make_solid_page(c) for c in colors)
    output_dir = tmp_path / "out"

    output_files = generate_output(
        pages=pages,
        output_format='jpg',
        output_dir=output_dir,
        base_filename='album',
        page_width=400,
        page_height=566,
        total_pages=len(colors),
    )

    expected = [output_dir / "album_page_001.jpg", output_dir / "album_page_002.jpg"]
    assert output_files == expected
    for path in expected:
        assert path.is_file()

    # No subfolder named after the base filename/format was created - the
    # output directory contains exactly the page files, nothing else.
    assert sorted(p.name for p in output_dir.iterdir()) == [p.name for p in expected]


def test_generate_output_png_writes_pages_directly_into_output_dir(tmp_path):
    colors = [(10, 20, 30), (40, 50, 60), (70, 80, 90)]
    pages = (make_solid_page(c) for c in colors)
    output_dir = tmp_path / "out"

    output_files = generate_output(
        pages=pages,
        output_format='png',
        output_dir=output_dir,
        base_filename='book',
        page_width=400,
        page_height=566,
        total_pages=len(colors),
    )

    expected = [output_dir / f"book_page_{i:03d}.png" for i in range(1, 4)]
    assert output_files == expected
    for path in expected:
        assert path.is_file()

    assert sorted(p.name for p in output_dir.iterdir()) == [p.name for p in expected]


def test_generate_output_png_preserves_alpha_channel_for_transparent_pages(tmp_path):
    # generate_png_pages needs no special handling for RGBA pages - PIL's PNG
    # writer already preserves an image's alpha channel as-is - but this
    # confirms the round-trip actually holds: a page with a genuinely
    # transparent pixel and a genuinely opaque one both survive save+reload.
    page = Image.new('RGBA', (100, 60), (0, 0, 0, 0))
    for x in range(50, 100):
        for y in range(60):
            page.putpixel((x, y), (255, 0, 0, 255))
    pages = iter([page])
    output_dir = tmp_path / "out"

    output_files = generate_output(
        pages=pages,
        output_format='png',
        output_dir=output_dir,
        base_filename='book',
        page_width=100,
        page_height=60,
        total_pages=1,
    )

    saved = Image.open(output_files[0])
    assert saved.mode == 'RGBA'
    assert saved.getpixel((10, 10)) == (0, 0, 0, 0)
    assert saved.getpixel((75, 30)) == (255, 0, 0, 255)


def test_generate_output_pdf_builds_file_from_dir_and_base_filename(tmp_path):
    colors = [(1, 2, 3)]
    pages = (make_solid_page(c) for c in colors)
    output_dir = tmp_path / "out"

    output_files = generate_output(
        pages=pages,
        output_format='pdf',
        output_dir=output_dir,
        base_filename='album',
        page_width=400,
        page_height=566,
        total_pages=len(colors),
    )

    assert output_files == [output_dir / "album.pdf"]
    assert output_files[0].is_file()
