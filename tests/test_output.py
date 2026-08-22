import tempfile
from pathlib import Path

import pikepdf
import pytest
from PIL import Image

from photobook_as_code.output import OutputError, generate_pdf


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
