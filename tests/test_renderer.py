import pytest
from PIL import Image, ImageDraw
from photobook_as_code.renderer import render_page, render_text_label
from photobook_as_code.themes import Theme, BackgroundStyle, BorderStyle, SpacingStyle, TextStyle, TextPosition, LayoutTemplate, LayoutPhoto, LayoutPosition, LayoutPhotoSize
from photobook_as_code.photos import PhotoMetadata
from photobook_as_code.text_labels import TextLabel
from pathlib import Path
from datetime import datetime

def make_photo(orientation: str, path: str) -> PhotoMetadata:
    width = 1920 if orientation == 'landscape' else 1080
    height = 1080 if orientation == 'landscape' else 1920
    return PhotoMetadata(
        path=Path(path),
        filename=Path(path).name,
        date_taken=datetime.now(),
        width=width,
        height=height
    )

def test_renderer_applies_layout_templates(tmp_path):
    # Create dummy images
    img1_path = tmp_path / "img1.jpg"
    img2_path = tmp_path / "img2.jpg"
    Image.new("RGB", (1920, 1080), color="red").save(img1_path)
    Image.new("RGB", (1080, 1920), color="blue").save(img2_path)
    
    photos = [
        make_photo('landscape', str(img1_path)),
        make_photo('portrait', str(img2_path))
    ]
    
    theme = Theme(
        name="test",
        description="",
        background=BackgroundStyle("#FFFFFF"),
        borders=BorderStyle(enabled=False, width=0, color="#000000", shadow=False),
        spacing=SpacingStyle(page_margin=10),
        layouts=[
            LayoutTemplate(
                count=2,
                photos=[
                    LayoutPhoto('landscape', LayoutPosition(0.5, 0.25), LayoutPhotoSize(width=0.5, height=1.0)),
                    LayoutPhoto('portrait', LayoutPosition(0.5, 0.75), LayoutPhotoSize(width=1.0, height=0.5))
                ]
            )
        ]
    )
    
    page = render_page(
        page_width=1020,
        page_height=1020,
        photos=photos,
        theme=theme
    )
    
    assert page.width == 1020
    assert page.height == 1020
    
    # Check pixels at center of placed photos
    # Top photo (landscape) is at y = 0.25 of usable height + margin
    # Usable height = 1000. 0.25 = 250. + margin 10 = 260
    # Center = 500 + margin 10 = 510
    r, g, b = page.getpixel((510, 260))
    assert r > 250 and g < 5 and b < 5
    
    r, g, b = page.getpixel((510, 760))
    assert r < 5 and g < 5 and b > 250


def test_renderer_with_photo_margin(tmp_path):
    # Create dummy image
    img1_path = tmp_path / "img1_margin.jpg"
    Image.new("RGB", (1000, 1000), color="red").save(img1_path)
    
    photos = [make_photo('landscape', str(img1_path))]
    
    # Theme with photo_margin
    theme = Theme(
        name="test_margin",
        description="",
        background=BackgroundStyle("#FFFFFF"),
        borders=BorderStyle(enabled=False, width=0, color="#000000", shadow=False),
        spacing=SpacingStyle(page_margin=0, photo_margin=100),
        layouts=[
            LayoutTemplate(
                count=1,
                photos=[
                    LayoutPhoto('landscape', LayoutPosition(0.5, 0.5), LayoutPhotoSize(width=1.0, height=1.0))
                ]
            )
        ]
    )
    
    page = render_page(
        page_width=1000,
        page_height=1000,
        photos=photos,
        theme=theme
    )
    
    # With photo_margin = 100 on a 1000x1000 page and size=1.0,
    # the target width/height would be 1000 - 200 = 800.
    # Center is at 500,500. So photo starts at 100,100 and ends at 900,900.
    
    # Pixel at (50, 50) should be white (background)
    r, g, b = page.getpixel((50, 50))
    assert r == 255 and g == 255 and b == 255, f"Expected white at (50, 50), got {r},{g},{b}"
    
    # Pixel at (500, 500) should be red (photo)
    r, g, b = page.getpixel((500, 500))
    assert r > 250 and g < 5 and b < 5, f"Expected red at (500, 500), got {r},{g},{b}"
    
    # Pixel at (105, 105) should be red (photo)
    r, g, b = page.getpixel((105, 105))
    assert r > 250 and g < 5 and b < 5, f"Expected red at (105, 105), got {r},{g},{b}"


def _render_text_box(y, photo_pos_y, photo_height, page_height=1000):
    """Render a text label with an opaque background and return the resulting image.

    Uses an explicit `text.height` (20% of page_height = 200px) so box_height is
    deterministic, and a fully opaque background so its rectangle is pixel-exact.
    Boundary checks use x=195 (far right of the "Hi" label) to avoid glyph pixels.
    """
    img = Image.new("RGB", (200, page_height), color="white")
    draw = ImageDraw.Draw(img)
    theme = Theme(
        name="text-test",
        description="",
        background=BackgroundStyle("#FFFFFF"),
        borders=BorderStyle(enabled=False, width=0, color="#000000", shadow=False),
        spacing=SpacingStyle(page_margin=0, photo_margin=0),
        text=TextStyle(
            base_font_size=10,
            font_family="DejaVuSans",
            text_color="#FFFFFF",
            text_background_enabled=True,
            text_background_color="#000000",
            text_background_opacity=100,
            text_padding=0,
        ),
    )
    label = TextLabel(datetime.now(), "Hi")
    text_pos = TextPosition(x=0, y=y, width=100, height=20)
    render_text_label(draw, label, text_pos, page_width=200, page_height=page_height,
                       photo_pos_y=photo_pos_y, photo_height=photo_height, theme=theme)
    return img


def test_text_label_y_zero_aligns_label_top_with_photo_top():
    img = _render_text_box(y=0, photo_pos_y=300, photo_height=400)
    assert img.getpixel((195, 299)) == (255, 255, 255)  # above box: background
    assert img.getpixel((195, 305)) == (0, 0, 0)  # inside box


def test_text_label_y_hundred_aligns_label_bottom_with_photo_bottom():
    # box_height=200, photo_height=400, slack=200 -> box_y=300+200=500, box bottom=700=photo bottom
    img = _render_text_box(y=100, photo_pos_y=300, photo_height=400)
    assert img.getpixel((195, 699)) == (0, 0, 0)  # inside box, last row
    assert img.getpixel((195, 700)) == (255, 255, 255)  # below box: background


def test_text_label_y_fifty_centers_label_in_photo():
    # slack=200, offset=100 -> box_y=400, box spans rows 400-599, photo spans 300-700 (center 500)
    img = _render_text_box(y=50, photo_pos_y=300, photo_height=400)
    assert img.getpixel((195, 399)) == (255, 255, 255)
    assert img.getpixel((195, 400)) == (0, 0, 0)
    assert img.getpixel((195, 599)) == (0, 0, 0)
    assert img.getpixel((195, 600)) == (255, 255, 255)


def test_text_label_taller_than_photo_clamps_to_top_aligned():
    # box_height=200 > photo_height=100 -> slack=0, so y is ignored and label top-aligns
    img = _render_text_box(y=100, photo_pos_y=300, photo_height=100)
    assert img.getpixel((195, 299)) == (255, 255, 255)  # above box: background
    assert img.getpixel((195, 305)) == (0, 0, 0)  # inside box, top-aligned to photo_pos_y

