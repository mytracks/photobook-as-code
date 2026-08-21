import pytest
from PIL import Image, ImageDraw, ImageFont
from photobook_as_code.renderer import render_page, render_text_label
from photobook_as_code.themes import Theme, BackgroundStyle, BorderStyle, SpacingStyle, TextStyle, TitleStyle, TextPosition, LayoutTemplate, LayoutPhoto, LayoutPosition, LayoutPhotoSize
from photobook_as_code.photos import PhotoMetadata
from photobook_as_code.text_labels import TextLabel, TitleLabel
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


def test_render_page_title_slot_skips_photo_and_border(tmp_path):
    """A title slot fills its cell with theme-styled text and no photo/border/shadow."""
    img1_path = tmp_path / "img1.jpg"
    Image.new("RGB", (1920, 1080), color="red").save(img1_path)

    photo = make_photo('landscape', str(img1_path))
    title = TitleLabel(timestamp=datetime.now(), title="Hello")

    theme = Theme(
        name="test",
        description="",
        background=BackgroundStyle("#FFFFFF"),
        borders=BorderStyle(enabled=True, width=4, color="#000000", shadow=False),
        spacing=SpacingStyle(page_margin=10),
        title=TitleStyle(
            base_font_size=20,
            align='center',
            text_background_enabled=True,
            text_background_color="#00FF00",
            text_background_opacity=100,
        ),
        layouts=[
            LayoutTemplate(
                count=2,
                photos=[
                    LayoutPhoto('landscape', LayoutPosition(0.5, 0.25), LayoutPhotoSize(width=1.0, height=0.5)),
                    LayoutPhoto('portrait', LayoutPosition(0.5, 0.75), LayoutPhotoSize(width=1.0, height=0.5))
                ]
            )
        ]
    )

    page = render_page(
        page_width=1000,
        page_height=1000,
        photos=[photo, title],
        theme=theme
    )

    assert page.width == 1000
    assert page.height == 1000

    # Photo slot (top half) still shows the pasted red photo
    r, g, b = page.getpixel((500, 250))
    assert r > 250 and g < 5 and b < 5

    # Title slot (bottom half): near its top-left corner (inside padding,
    # away from the centered "Hello" text) should show its own green
    # background, not a photo, not the border color, not the page background.
    r, g, b = page.getpixel((20, 510))
    assert r < 5 and g > 250 and b < 5


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


def _render_text_box(y, photo_pos_y, photo_height, page_height=1000, photo_pos_x=0, photo_width=200):
    """Render a text label with an opaque background and return the resulting image.

    Uses an explicit `text.height` (20% of page_height = 200px) so box_height is
    deterministic, and a fully opaque background so its rectangle is pixel-exact.
    Boundary checks use x=195 (far right of the "Hi" label) to avoid glyph pixels.
    Default photo_pos_x=0/photo_width=200 (matching the 200px-wide page) combined
    with x=0/width=100 below reproduces a box spanning the full page width, as
    these tests are only exercising vertical (y) positioning.
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
                       photo_pos_x=photo_pos_x, photo_pos_y=photo_pos_y,
                       photo_width=photo_width, photo_height=photo_height, theme=theme)
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


def _render_text_box_x(x, photo_pos_x, photo_width, page_width=1000, dock=None):
    """Render a text label with an opaque background and return the resulting image.

    Mirrors `_render_text_box` but exercises horizontal (x/dock) positioning. Uses
    an explicit `text.width` (50% of photo_width) and `text.height` (100% of the
    50px-tall page) so both box dimensions are deterministic and pixel-exact.
    Boundary checks use y=5 (a couple rows into the label) to avoid glyph pixels.
    """
    page_height = 50
    img = Image.new("RGB", (page_width, page_height), color="white")
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
    text_pos = TextPosition(x=x, y=0, width=50, height=100, dock=dock)
    render_text_label(draw, label, text_pos, page_width=page_width, page_height=page_height,
                       photo_pos_x=photo_pos_x, photo_pos_y=0,
                       photo_width=photo_width, photo_height=page_height, theme=theme)
    return img


def test_text_label_x_zero_aligns_label_left_with_photo_left():
    img = _render_text_box_x(x=0, photo_pos_x=300, photo_width=400)
    assert img.getpixel((299, 5)) == (255, 255, 255)  # left of box: background
    assert img.getpixel((305, 5)) == (0, 0, 0)  # inside box


def test_text_label_x_hundred_aligns_label_right_with_photo_right():
    # box_width=200, photo_width=400, slack=200 -> box_x=300+200=500, box right=700=photo right
    img = _render_text_box_x(x=100, photo_pos_x=300, photo_width=400)
    assert img.getpixel((699, 5)) == (0, 0, 0)  # inside box, last column
    assert img.getpixel((700, 5)) == (255, 255, 255)  # right of box: background


def test_text_label_x_fifty_centers_label_in_photo():
    # slack=200, offset=100 -> box_x=400, box spans cols 400-599, photo spans 300-700 (center 500)
    img = _render_text_box_x(x=50, photo_pos_x=300, photo_width=400)
    assert img.getpixel((399, 5)) == (255, 255, 255)
    assert img.getpixel((400, 5)) == (0, 0, 0)
    assert img.getpixel((599, 5)) == (0, 0, 0)
    assert img.getpixel((600, 5)) == (255, 255, 255)


def test_text_label_dock_left_ignores_x_and_photo_position():
    # dock=left pins box to the page's left border regardless of x or photo_pos_x
    img = _render_text_box_x(x=50, photo_pos_x=300, photo_width=400, dock='left')
    assert img.getpixel((0, 5)) == (0, 0, 0)  # flush at page's left border
    assert img.getpixel((199, 5)) == (0, 0, 0)  # box_width=200, still from photo_width
    assert img.getpixel((200, 5)) == (255, 255, 255)


def test_text_label_dock_right_ignores_x_and_photo_position():
    # dock=right pins box to the page's right border regardless of x or photo_pos_x
    img = _render_text_box_x(x=50, photo_pos_x=100, photo_width=400, page_width=1000, dock='right')
    assert img.getpixel((999, 5)) == (0, 0, 0)  # flush at page's right border
    assert img.getpixel((800, 5)) == (0, 0, 0)  # box_width=200, box starts at page_width-200
    assert img.getpixel((799, 5)) == (255, 255, 255)


# --- Word-wrap tests -------------------------------------------------------
#
# The canvas uses a distinct gray so it is never mistaken for the box
# background (black) or glyph ink (white) - checking for "white present"
# against a white canvas would trivially pass outside the box too. Word/space
# widths are measured with the same font/size the test theme uses, so line
# breaks are exact and assertions use precise pixel row/column bands.

_WRAP_FONT_SIZE = 20
_WRAP_FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
_WRAP_BOLD_FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
_WRAP_CANVAS_COLOR = (128, 128, 128)
_wrap_probe_draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
_wrap_font = ImageFont.truetype(_WRAP_FONT_PATH, _WRAP_FONT_SIZE)


def _measure(text, font=None):
    bbox = _wrap_probe_draw.textbbox((0, 0), text, font=font or _wrap_font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _render_wrap_box(text, box_width_px, photo_pos_y=300, photo_height=700,
                      page_width=2000, page_height=1200, align='left', height=None):
    """Render a text label with an opaque white-on-black background and auto
    height (unless `height` is given), into a photo of the given pixel width
    (text.width=100% maps to box_width_px exactly). y=0 top-aligns the box to
    photo_pos_y regardless of box_height, so line positions are predictable
    purely from font metrics. Canvas is gray (see module note above).
    """
    img = Image.new("RGB", (page_width, page_height), color=_WRAP_CANVAS_COLOR)
    draw = ImageDraw.Draw(img)
    theme = Theme(
        name="wrap-test",
        description="",
        background=BackgroundStyle("#FFFFFF"),
        borders=BorderStyle(enabled=False, width=0, color="#000000", shadow=False),
        spacing=SpacingStyle(page_margin=0, photo_margin=0),
        text=TextStyle(
            base_font_size=_WRAP_FONT_SIZE,
            font_family="DejaVuSansMono",
            text_color="#FFFFFF",
            text_background_enabled=True,
            text_background_color="#000000",
            text_background_opacity=100,
            text_padding=0,
        ),
    )
    label = TextLabel(datetime.now(), text)
    text_pos = TextPosition(x=0, y=0, width=100, height=height, align=align)
    render_text_label(draw, label, text_pos, page_width=page_width, page_height=page_height,
                       photo_pos_x=0, photo_pos_y=photo_pos_y, photo_width=box_width_px,
                       photo_height=photo_height, theme=theme)
    return img


def _has_ink(img, x0, x1, y0, y1):
    """Any white (glyph ink) pixel within the given region."""
    for y in range(max(y0, 0), min(y1, img.height)):
        for x in range(max(x0, 0), min(x1, img.width)):
            if img.getpixel((x, y)) == (255, 255, 255):
                return True
    return False


def _count_ink(img, x0, x1, y0, y1):
    """Count of white (glyph ink) pixels within the given region."""
    count = 0
    for y in range(max(y0, 0), min(y1, img.height)):
        for x in range(max(x0, 0), min(x1, img.width)):
            if img.getpixel((x, y)) == (255, 255, 255):
                count += 1
    return count


def _box_height_at(img, x, start_y):
    """Count contiguous black (box background) rows from start_y down at
    column x. Callers must pick x so no glyph ink ever reaches it (e.g. the
    box's rightmost column, left as slack by construction)."""
    height = 0
    y = start_y
    while y < img.height and img.getpixel((x, y)) == (0, 0, 0):
        height += 1
        y += 1
    return height


def test_text_label_wraps_long_line_onto_multiple_display_lines():
    # "AAAA" fits alone; "AAAA BBBB" together does not -> must wrap onto 2
    # display lines instead of the whole line disappearing (the original bug).
    w1, h1 = _measure("AAAA")
    box_width_px = w1 + 2
    photo_pos_y = 300
    img = _render_wrap_box("AAAA BBBB", box_width_px=box_width_px, photo_pos_y=photo_pos_y)

    line_spacing = 4
    line1_y0, line1_y1 = photo_pos_y, photo_pos_y + h1
    line2_y0 = line1_y1 + line_spacing
    line2_y1 = line2_y0 + h1

    assert _has_ink(img, 0, box_width_px, line1_y0, line1_y1)  # "AAAA" drawn on line 1
    assert _has_ink(img, 0, box_width_px, line2_y0, line2_y1)  # "BBBB" drawn on line 2


def test_text_label_wrap_grows_auto_height():
    # Same text, auto height (text.height=None): a box too narrow to fit the
    # text on one line ends up taller than a box wide enough for one line.
    text = "AAAA BBBB CCCC"
    words_width = sum(_measure(w)[0] for w in text.split())
    space_w, _ = _measure(" ")
    wide_width = words_width + 2 * space_w + 10  # fits all three words on one line
    narrow_width = _measure("AAAA")[0] + 2  # forces one word per line (3 lines)

    photo_pos_y = 300
    wide_img = _render_wrap_box(text, box_width_px=wide_width, photo_pos_y=photo_pos_y, photo_height=900)
    narrow_img = _render_wrap_box(text, box_width_px=narrow_width, photo_pos_y=photo_pos_y, photo_height=900)

    # Measure at each box's own rightmost column, which is always background
    # (kept as slack: +10 for the wide box, +2 for the narrow one).
    wide_height = _box_height_at(wide_img, x=wide_width - 1, start_y=photo_pos_y)
    narrow_height = _box_height_at(narrow_img, x=narrow_width - 1, start_y=photo_pos_y)
    assert narrow_height > wide_height


def test_text_label_single_word_wider_than_box_still_drawn():
    # A single word wider than the box on its own must still be drawn (allowed
    # to overflow), not silently dropped.
    word = "SUPERCALIFRAGILISTIC"
    word_w, word_h = _measure(word)
    box_width_px = word_w // 3  # much narrower than the word itself
    photo_pos_y = 300
    img = _render_wrap_box(word, box_width_px=box_width_px, photo_pos_y=photo_pos_y,
                            page_width=box_width_px + word_w + 100)
    assert _has_ink(img, 0, box_width_px + word_w, photo_pos_y, photo_pos_y + word_h)


def test_text_label_wrapped_word_keeps_bold_style():
    # DejaVuSansMono keeps identical advance width across weights (it's
    # monospace), so verify boldness via ink density (bold strokes are
    # thicker) rather than measured width.
    plain_w, h = _measure("plain")
    word_w, _ = _measure("BOLDWORD")
    box_width_px = plain_w + 2  # forces "**BOLDWORD**" onto its own wrapped line
    photo_pos_y = 300
    img = _render_wrap_box("plain **BOLDWORD**", box_width_px=box_width_px,
                            photo_pos_y=photo_pos_y, page_width=box_width_px + word_w + 100)

    line_spacing = 4
    line2_y0 = photo_pos_y + h + line_spacing
    line2_y1 = line2_y0 + h
    wrapped_ink = _count_ink(img, 0, box_width_px + word_w, line2_y0, line2_y1)

    # Control: the same word, alone, rendered at the regular weight
    regular_img = _render_wrap_box("BOLDWORD", box_width_px=word_w + 20, photo_pos_y=photo_pos_y,
                                    page_width=word_w + 100)
    regular_ink = _count_ink(regular_img, 0, word_w + 20, photo_pos_y, photo_pos_y + h)

    assert wrapped_ink > regular_ink  # bold strokes cover more pixels than regular


def test_text_label_wrapped_content_clips_at_fixed_height():
    # With an explicit height fixed to roughly one line, later wrapped lines
    # must clip at the boundary - same as today's per-line clipping behavior.
    text = "AAAA BBBB CCCC"
    w1, h1 = _measure("AAAA")
    narrow_width = w1 + 2  # forces one word per line (3 display lines)
    photo_pos_y = 300
    page_height = 1200
    line_spacing = 4

    fixed_height_px = h1 + 2  # fits line 1 only
    fixed_height_pct = fixed_height_px / page_height * 100

    img = _render_wrap_box(text, box_width_px=narrow_width, photo_pos_y=photo_pos_y,
                            photo_height=900, page_height=page_height, height=fixed_height_pct)

    line1_y0, line1_y1 = photo_pos_y, photo_pos_y + h1
    line3_y0 = photo_pos_y + 2 * (h1 + line_spacing)
    line3_y1 = line3_y0 + h1

    assert _has_ink(img, 0, narrow_width, line1_y0, line1_y1)  # "AAAA" still drawn
    assert not _has_ink(img, 0, narrow_width, line3_y0, line3_y1)  # "CCCC" clipped away


def test_text_label_wrap_bug_reproduction_with_clean_theme():
    """Direct reproduction of the reported bug: a heading too wide for its
    photo's box must render visibly (wrapped), not vanish entirely."""
    import dataclasses
    import yaml
    from photobook_as_code.layout import fit_photo_in_cell

    theme_path = Path(__file__).parent.parent / 'src' / 'photobook_as_code' / 'themes' / 'clean.yaml'
    clean_theme = Theme.from_dict(yaml.safe_load(theme_path.read_text()))

    # The 4-photo mixed layout's first slot (landscape, size {width:1.0,
    # height:0.33}) with a centered text position - the block that silently
    # dropped "# Auf nach Hamburg" before word-wrap was added.
    template = next(
        t for t in clean_theme.layouts
        if t.count == 4 and [p.orientation for p in t.photos] == ['landscape', 'landscape', 'portrait', 'landscape']
    )
    spec = template.photos[0]
    assert spec.text is not None

    page_width, page_height = 2480, 3508
    usable_width = page_width - 2 * clean_theme.spacing.page_margin
    usable_height = page_height - 2 * clean_theme.spacing.page_margin
    target_width = max(1, int(usable_width * spec.size.width) - 2 * clean_theme.spacing.photo_margin)
    target_height = max(1, int(usable_height * spec.size.height) - 2 * clean_theme.spacing.photo_margin)
    fitted_w, fitted_h, _, _ = fit_photo_in_cell(1600, 1200, target_width, target_height)
    center_x = clean_theme.spacing.page_margin + int(usable_width * spec.position.x)
    center_y = clean_theme.spacing.page_margin + int(usable_height * spec.position.y)
    pos_x = center_x - fitted_w // 2
    pos_y = center_y - fitted_h // 2

    # Use the theme's real text position (x/y/width/align) and font settings,
    # but force pure black/white ink-vs-background so glyph ink is
    # unambiguous - the real theme blends a semi-transparent white overlay
    # over the underlying photo's own color, which isn't reliably
    # distinguishable from ink without knowing that photo's exact pixels.
    probe_theme = dataclasses.replace(
        clean_theme,
        text=dataclasses.replace(
            clean_theme.text,
            text_color="#FFFFFF",
            text_background_color="#000000",
            text_background_opacity=100,
        ),
    )

    img = Image.new("RGB", (page_width, page_height), color=_WRAP_CANVAS_COLOR)
    draw = ImageDraw.Draw(img)
    label = TextLabel(datetime.now(), "# Auf nach Hamburg")
    render_text_label(draw, label, spec.text, page_width, page_height,
                       photo_pos_x=pos_x, photo_pos_y=pos_y,
                       photo_width=fitted_w, photo_height=fitted_h, theme=probe_theme)

    # Before the fix, this exact case (real theme position/font, real
    # heading text) rendered an empty background box with no glyph ink at
    # all. Confirm ink (white) now exists within the photo's own region.
    assert _has_ink(img, pos_x, pos_x + fitted_w, pos_y, pos_y + fitted_h)
