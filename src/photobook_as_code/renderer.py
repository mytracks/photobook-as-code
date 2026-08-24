"""
Page rendering with photos and styling.
"""

from pathlib import Path
from typing import Iterator, List, Optional, Tuple, Union
import logging

from PIL import Image, ImageDraw, ImageFont

from .layout import fit_photo_in_cell, match_template
from .photos import PhotoMetadata
from .themes import Theme, LayoutTemplate, TextPosition
from .text_labels import TextLabel, TitleLabel, parse_markdown_text

logger = logging.getLogger(__name__)


DPI = 300  # Standard print resolution


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def create_blank_page(width: int, height: int, background_color: str) -> Image.Image:
    """
    Create a blank page image with background color.
    
    Args:
        width: Page width in pixels
        height: Page height in pixels
        background_color: Hex color string (e.g., "#FFFFFF")
        
    Returns:
        PIL Image instance
    """
    rgb = hex_to_rgb(background_color)
    image = Image.new('RGB', (width, height), rgb)
    return image


def load_and_resize_photo(photo: PhotoMetadata, target_width: int, 
                          target_height: int) -> Image.Image:
    """
    Load photo and resize to fit target dimensions.
    
    Args:
        photo: Photo metadata
        target_width: Target width in pixels
        target_height: Target height in pixels
        
    Returns:
        Resized PIL Image
    """
    try:
        img = Image.open(photo.path)
        
        # Convert to RGB if needed (handles RGBA, grayscale, etc.)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Calculate fitted dimensions
        fitted_w, fitted_h, _, _ = fit_photo_in_cell(
            img.width, img.height, target_width, target_height
        )
        
        # Resize with high-quality resampling
        img_resized = img.resize((fitted_w, fitted_h), Image.Resampling.LANCZOS)
        
        return img_resized
        
    except Exception as e:
        logger.error(f"Failed to load photo {photo.path}: {e}")
        raise


def draw_border(draw: ImageDraw.Draw, x: int, y: int, width: int, height: int,
                border_width: int, border_color: str) -> None:
    """
    Draw a border rectangle.
    
    Args:
        draw: ImageDraw instance
        x: Left position
        y: Top position
        width: Border width (in pixels)
        height: Border height (in pixels)
        border_width: Width of border line
        border_color: Hex color string
    """
    rgb = hex_to_rgb(border_color)
    
    # Draw border by drawing multiple rectangles
    for i in range(border_width):
        draw.rectangle(
            [x + i, y + i, x + width - i - 1, y + height - i - 1],
            outline=rgb,
            width=1
        )


def draw_shadow(page: Image.Image, x: int, y: int, width: int, height: int) -> Image.Image:
    """
    Draw a simple drop shadow effect.
    
    Args:
        page: Page image
        x: Photo x position
        y: Photo y position
        width: Photo width
        height: Photo height
        
    Returns:
        Page image with shadow applied
    """
    # Create shadow layer
    shadow_offset = 5
    shadow_color = (128, 128, 128, 128)  # Semi-transparent gray
    
    shadow = Image.new('RGBA', page.size, (255, 255, 255, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    
    shadow_draw.rectangle(
        [x + shadow_offset, y + shadow_offset, 
         x + width + shadow_offset, y + height + shadow_offset],
        fill=shadow_color
    )
    
    # Convert page to RGBA for compositing
    page_rgba = page.convert('RGBA')
    page_rgba = Image.alpha_composite(page_rgba, shadow)
    
    return page_rgba.convert('RGB')


def _load_font_variants(font_family: str, base_font_size: int):
    """
    Load regular/bold/italic/bold-italic variants of a font, falling back to
    PIL's built-in default font (for all four) if any variant can't be loaded.

    Returns:
        Tuple of (font_regular, font_bold, font_italic, font_bold_italic)
    """
    try:
        font_regular = ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{font_family}.ttf", base_font_size)
        font_bold = ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{font_family}-Bold.ttf", base_font_size)
        font_italic = ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{font_family}-Oblique.ttf", base_font_size)
        font_bold_italic = ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{font_family}-BoldOblique.ttf", base_font_size)
        return font_regular, font_bold, font_italic, font_bold_italic
    except:
        logger.warning(f"Font {font_family} with size {base_font_size} not found.")
        font_regular = ImageFont.load_default()
        return font_regular, font_regular, font_regular, font_regular


def _wrap_markdown_lines(draw: ImageDraw.Draw, parsed_lines, base_font_size: int, font_family: str,
                         font_regular, font_bold, font_italic, font_bold_italic,
                         text_box_width: int, line_spacing: int = 4):
    """
    Word-wrap parsed Markdown lines to fit text_box_width, measuring each
    resulting display line.

    Returns:
        Tuple of (all_lines_info, total_text_height) where all_lines_info is
        a list of (word_infos, line_height, line_width, line_top) per display
        line. All words in a line are drawn from the same y with the same
        PIL anchor ("la"), so they already share one baseline - line_height
        and line_top are the union of the words' ink spans relative to that
        shared anchor (max bottom-offset minus min top-offset, and min
        top-offset respectively), not the max of each word's own tight ink
        height. The two differ whenever a line's tallest-looking word and its
        highest-starting word aren't the same word (see design.md for the
        worked example and why this matters for box padding/line spacing).
    """
    space_width_cache = {}

    def space_width_for(font) -> int:
        if font not in space_width_cache:
            bbox = draw.textbbox((0, 0), ' ', font=font)
            space_width_cache[font] = bbox[2] - bbox[0]
        return space_width_cache[font]

    all_lines_info = []  # list of (word_infos, line_height, line_width, line_top)
    total_text_height = 0
    blank_line_height = None  # lazily computed: regular font's nominal line height

    for segments, heading_level in parsed_lines:
        current_words = []
        current_width = 0
        current_top = None
        current_bottom = None

        for segment in segments:
            # Select font based on style
            if segment.bold and segment.italic:
                font = font_bold_italic
            elif segment.bold:
                font = font_bold
            elif segment.italic:
                font = font_italic
            else:
                font = font_regular

            # Apply size multiplier for headings
            if segment.font_size_multiplier != 1.0:
                try:
                    font_size = int(base_font_size * segment.font_size_multiplier)
                    if segment.bold and segment.italic:
                        font = ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{font_family}-BoldOblique.ttf", font_size)
                    elif segment.bold:
                        font = ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{font_family}-Bold.ttf", font_size)
                    elif segment.italic:
                        font = ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{font_family}-Oblique.ttf", font_size)
                    else:
                        font = ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{font_family}.ttf", font_size)
                except:
                    pass  # Keep default if loading fails

            # Tokenize this segment into words, each keeping the segment's style
            for word in segment.text.split():
                bbox = draw.textbbox((0, 0), word, font=font)
                word_width = bbox[2] - bbox[0]
                word_height = bbox[3] - bbox[1]
                word_top = bbox[1]
                word_bottom = bbox[3]

                added_width = word_width
                if current_words:
                    added_width += space_width_for(font)

                if current_words and current_width + added_width > text_box_width:
                    # Wrap: finish the current display line, start a new one.
                    # A lone word wider than text_box_width is never split or
                    # dropped - it simply becomes the only word on its line.
                    current_height = current_bottom - current_top
                    all_lines_info.append((current_words, current_height, current_width, current_top))
                    total_text_height += current_height + line_spacing
                    current_words = []
                    current_width = 0
                    current_top = None
                    current_bottom = None
                    added_width = word_width

                current_words.append((word, font, word_width, word_height))
                current_width += added_width
                current_top = word_top if current_top is None else min(current_top, word_top)
                current_bottom = word_bottom if current_bottom is None else max(current_bottom, word_bottom)

        # A source line with no words (blank, or whitespace-only) still needs
        # real height - otherwise it renders as a near-invisible line_spacing
        # sliver next to actual text. Use the regular font's nominal line
        # height (ascent + descent), independent of any particular glyphs.
        # It has no ink to shift, so line_top is unused for it - 0 is fine.
        if not current_words:
            if blank_line_height is None:
                ascent, descent = font_regular.getmetrics()
                blank_line_height = ascent + descent
            current_height = blank_line_height
            current_top = 0
        else:
            current_height = current_bottom - current_top

        # Flush this source line's final (or only) display line.
        all_lines_info.append((current_words, current_height, current_width, current_top))
        total_text_height += current_height + line_spacing

    # Remove the last line spacing since it was added after the last line
    if all_lines_info:
        total_text_height -= line_spacing

    return all_lines_info, total_text_height


def _draw_text_background(draw: ImageDraw.Draw, box_x: int, box_y: int,
                          box_width: int, box_height: int,
                          background_color: str, opacity_pct: int) -> None:
    """Draw a semi-transparent background rectangle behind a text box."""
    bg_color = hex_to_rgb(background_color)
    opacity = int(255 * opacity_pct / 100)

    overlay = Image.new('RGBA', (int(box_width), int(box_height)), bg_color + (opacity,))
    page_img = draw._image
    if page_img.mode != 'RGBA':
        page_img = page_img.convert('RGBA')
    page_img.paste(overlay, (int(box_x), int(box_y)), overlay)
    if draw._image.mode == 'RGB':
        draw._image.paste(page_img.convert('RGB'), (0, 0))


def _draw_wrapped_lines(draw: ImageDraw.Draw, all_lines_info, text_box_x: int, start_y: int,
                        text_box_width: int, align: str, rgb: tuple,
                        height_limit: Optional[int] = None, line_spacing: int = 4) -> None:
    """
    Draw pre-wrapped, pre-measured display lines with horizontal alignment,
    optionally clipping once height_limit (measured from start_y) is exceeded.
    """
    space_width_cache = {}

    def space_width_for(font) -> int:
        if font not in space_width_cache:
            bbox = draw.textbbox((0, 0), ' ', font=font)
            space_width_cache[font] = bbox[2] - bbox[0]
        return space_width_cache[font]

    current_y = start_y

    for (word_infos, line_height, line_width, line_top) in all_lines_info:
        if height_limit is not None and current_y > start_y + height_limit:
            break  # Clip at boundary

        # Apply horizontal alignment within padded text box. line_width already
        # accounts for inter-word spacing (computed during packing), so this
        # works whether or not the line was actually wrapped.
        if align == 'center':
            current_x = text_box_x + (text_box_width - line_width) // 2
        elif align == 'right':
            current_x = text_box_x + text_box_width - line_width
        else:  # left
            current_x = text_box_x

        # Shift up by this line's own top offset so its actual topmost ink
        # lands at current_y (its intended position) instead of current_y +
        # line_top, which is where PIL's default anchor="la" would otherwise
        # place it. Every word in the line gets the same shift, so they keep
        # the common baseline they already share (see design.md).
        draw_y = current_y - line_top

        # Draw each word. No width clip here: the packing pass already
        # guaranteed the line fits text_box_width, except for a lone word
        # wider than the box on its own, which is drawn anyway rather than
        # dropped (see design.md).
        first_word = True
        for word, font, word_width, word_height in word_infos:
            if not first_word:
                current_x += space_width_for(font)
            draw.text((current_x, draw_y), word, fill=rgb, font=font)
            current_x += word_width
            first_word = False

        current_y += line_height + line_spacing


def render_text_label(draw: ImageDraw.Draw, text_label: TextLabel, text_pos: TextPosition,
                      page_width: int, page_height: int,
                      photo_pos_x: int, photo_pos_y: int, photo_width: int, photo_height: int,
                      theme: Theme) -> None:
    """
    Render text label with markdown formatting.

    Args:
        draw: ImageDraw instance
        text_label: TextLabel with text content
        text_pos: TextPosition specifying where to draw text (height is optional)
        page_width: Page width in pixels
        page_height: Page height in pixels
        photo_pos_x: Associated photo's left edge in pixels (x is relative to this photo, unless docked)
        photo_pos_y: Associated photo's top edge in pixels (y is relative to this photo)
        photo_width: Associated photo's width in pixels
        photo_height: Associated photo's height in pixels
        theme: Theme with text styling properties
    """
    # Calculate box width from the associated photo's pixel width
    box_width = int(photo_width * text_pos.width / 100)

    # Calculate horizontal position: dock pins to the page's literal border,
    # otherwise x interpolates within the photo's width (slack floored at 0).
    if text_pos.dock == 'left':
        box_x = 0
    elif text_pos.dock == 'right':
        box_x = page_width - box_width
    else:
        slack_x = max(0, photo_width - box_width)
        box_x = photo_pos_x + int(text_pos.x / 100 * slack_x)

    # Parse markdown
    parsed_lines = parse_markdown_text(text_label.text)

    # Empty/blank content (e.g. an unfilled stub) renders nothing at all -
    # no text, no background box.
    if not parsed_lines:
        return

    # Get theme text styling
    base_font_size = theme.text.base_font_size
    font_family = theme.text.font_family
    text_color = theme.text.text_color

    font_regular, font_bold, font_italic, font_bold_italic = _load_font_variants(font_family, base_font_size)

    rgb = hex_to_rgb(text_color)
    padding = theme.text.text_padding
    line_spacing = theme.text.line_spacing

    # Text box width is needed up front so word-wrapping can use it during the
    # first (measurement) pass, not just for drawing in the second pass.
    text_box_width = box_width - 2 * padding

    # FIRST PASS: word-wrap and measure
    all_lines_info, total_text_height = _wrap_markdown_lines(
        draw, parsed_lines, base_font_size, font_family,
        font_regular, font_bold, font_italic, font_bold_italic,
        text_box_width, line_spacing
    )

    # Calculate box height: use calculated height if not specified, otherwise use specified height
    if text_pos.height is None:
        # Auto-calculate height based on actual text + padding
        box_height = int(total_text_height + 2 * padding)
    else:
        # Use specified height from template
        box_height = int(page_height * text_pos.height / 100)

    # Calculate vertical position relative to the associated photo: y=0 aligns the
    # label's top edge with the photo's top edge, y=100 aligns the label's bottom
    # edge with the photo's bottom edge. Slack is floored at 0 so a label taller
    # than the photo top-aligns regardless of y.
    slack = max(0, photo_height - box_height)
    box_y = photo_pos_y + int(text_pos.y / 100 * slack)

    # Calculate text area with padding (text_box_width was already computed
    # above, before the first pass, since word-wrapping needs it early)
    text_box_x = box_x + padding
    text_box_y = box_y + padding
    text_box_height = box_height - 2 * padding

    # Draw semi-transparent background if enabled
    if theme.text.text_background_enabled:
        _draw_text_background(draw, box_x, box_y, box_width, box_height,
                              theme.text.text_background_color, theme.text.text_background_opacity)

    # SECOND PASS: render each wrapped display line using pre-calculated dimensions
    height_limit = text_box_height if text_pos.height is not None else None
    _draw_wrapped_lines(draw, all_lines_info, text_box_x, text_box_y,
                        text_box_width, text_pos.align, rgb, height_limit, line_spacing)


def render_title_slot(draw: ImageDraw.Draw, title_label: TitleLabel,
                      box_x: int, box_y: int, box_width: int, box_height: int,
                      theme: Theme) -> None:
    """
    Render a title slot's Markdown-formatted text, filling its matched layout
    slot's box. Unlike a caption (positioned relative to a photo it overlays),
    a title slot has no photo underneath - its box is the full layout slot
    cell, and the text is vertically centered within it.

    Args:
        draw: ImageDraw instance
        title_label: TitleLabel with title content
        box_x: Slot box left edge in pixels
        box_y: Slot box top edge in pixels
        box_width: Slot box width in pixels
        box_height: Slot box height in pixels
        theme: Theme with title styling properties
    """
    parsed_lines = parse_markdown_text(title_label.title)

    base_font_size = theme.title.base_font_size
    font_family = theme.title.font_family
    align = theme.title.align

    font_regular, font_bold, font_italic, font_bold_italic = _load_font_variants(font_family, base_font_size)

    rgb = hex_to_rgb(theme.title.text_color)
    padding = theme.title.text_padding
    line_spacing = theme.title.line_spacing

    text_box_width = box_width - 2 * padding
    text_box_height = box_height - 2 * padding

    all_lines_info, total_text_height = _wrap_markdown_lines(
        draw, parsed_lines, base_font_size, font_family,
        font_regular, font_bold, font_italic, font_bold_italic,
        text_box_width, line_spacing
    )

    if theme.title.text_background_enabled:
        _draw_text_background(draw, box_x, box_y, box_width, box_height,
                              theme.title.text_background_color, theme.title.text_background_opacity)

    # Vertically center the rendered text within the slot's box; a title
    # taller than its box top-aligns instead (slack floored at 0), then clips.
    vertical_slack = max(0, text_box_height - total_text_height)
    text_box_x = box_x + padding
    text_box_y = box_y + padding + vertical_slack // 2

    _draw_wrapped_lines(draw, all_lines_info, text_box_x, text_box_y,
                        text_box_width, align, rgb, text_box_height, line_spacing)


def render_page(page_width: int, page_height: int, photos: List[Union[PhotoMetadata, TitleLabel]],
                theme: Theme, page_number: int = 0,
                text_labels: Optional[List[Optional[TextLabel]]] = None) -> Image.Image:
    """
    Render a single page with photos, title slots, and styling.

    Args:
        page_width: Page width in pixels
        page_height: Page height in pixels
        photos: List of page items to place on this page - photos and/or title slots
        theme: Theme to apply
        page_number: Page number for logging (0-indexed)
        text_labels: Optional list of text labels for each photo (same length as photos;
            entries corresponding to a title slot are ignored)

    Returns:
        Rendered page as PIL Image
    """
    logger.info(f"Rendering page {page_number + 1} with {len(photos)} items")
    
    # Create blank page
    page = create_blank_page(
        page_width,
        page_height,
        theme.background.color
    )
    
    if not photos:
        return page
        
    # Match template
    template = match_template(theme.layouts, photos)
    
    # Calculate usable area
    usable_width = page_width - (2 * theme.spacing.page_margin)
    usable_height = page_height - (2 * theme.spacing.page_margin)
    
    # PHASE 1: Draw all photos first
    # Store photo positions and dimensions for later border/text rendering
    photo_placements = []  # List of (pos_x, pos_y, width, height)
    
    for i, (item, spec) in enumerate(zip(photos, template.photos)):
        try:
            # Calculate target dimensions using dual boundaries
            target_width = max(1, int(usable_width * spec.size.width) - (2 * theme.spacing.photo_margin))
            target_height = max(1, int(usable_height * spec.size.height) - (2 * theme.spacing.photo_margin))

            # Calculate center position
            center_x = theme.spacing.page_margin + int(usable_width * spec.position.x)
            center_y = theme.spacing.page_margin + int(usable_height * spec.position.y)

            if isinstance(item, TitleLabel):
                # A title slot has no photo to load/fit - it fills the full
                # cell box directly, and its text is drawn in Phase 2.
                pos_x = center_x - (target_width // 2)
                pos_y = center_y - (target_height // 2)
                photo_placements.append((pos_x, pos_y, target_width, target_height))
                continue

            # Load and resize photo
            photo_img = load_and_resize_photo(item, target_width, target_height)

            # Calculate top-left corner
            pos_x = center_x - (photo_img.width // 2)
            pos_y = center_y - (photo_img.height // 2)

            # Store placement for later use
            photo_placements.append((pos_x, pos_y, photo_img.width, photo_img.height))

            # Apply shadow if enabled
            if theme.borders.shadow:
                page = draw_shadow(
                    page,
                    pos_x,
                    pos_y,
                    photo_img.width,
                    photo_img.height
                )

            # Paste photo onto page
            page.paste(
                photo_img,
                (pos_x, pos_y)
            )

        except Exception as e:
            item_label = item.filename if isinstance(item, PhotoMetadata) else "title slot"
            logger.error(f"Failed to render {item_label} on page {page_number + 1}: {e}")
            # Store empty placement to maintain index alignment
            photo_placements.append((0, 0, 0, 0))
            # Continue with other items
    
    # PHASE 2: Draw borders and text labels on top of all photos
    # Create draw object after all photos are pasted
    draw = ImageDraw.Draw(page)
    
    for i, spec in enumerate(template.photos):
        if i >= len(photo_placements):
            break

        pos_x, pos_y, width, height = photo_placements[i]

        if width == 0 or height == 0:
            continue  # Skip if photo/title slot failed to render

        item = photos[i] if i < len(photos) else None

        try:
            if isinstance(item, TitleLabel):
                # Title slots get their own formatted-text rendering - no
                # photo border/shadow and no caption overlay apply to them.
                render_title_slot(draw, item, pos_x, pos_y, width, height, theme)
                continue

            # Draw border if enabled
            if theme.borders.enabled and theme.borders.width > 0:
                draw_border(
                    draw,
                    pos_x,
                    pos_y,
                    width,
                    height,
                    theme.borders.width,
                    theme.borders.color
                )

            # Render text label if present
            if text_labels and i < len(text_labels) and text_labels[i] and spec.text:
                render_text_label(
                    draw,
                    text_labels[i],
                    spec.text,
                    page_width,
                    page_height,
                    pos_x,
                    pos_y,
                    width,
                    height,
                    theme
                )

        except Exception as e:
            logger.error(f"Failed to render border/text for item on page {page_number + 1}: {e}")
            # Continue with other elements
    
    return page


def render_all_pages(page_width: int, page_height: int, all_photos: List[Union[PhotoMetadata, TitleLabel]],
                     distribution, theme: Theme,
                     text_label_associations: Optional[List[Tuple[PhotoMetadata, Optional[TextLabel]]]] = None):
    """
    Render all pages for the photobook incrementally.

    This is a generator function that yields pages one at a time to minimize
    memory usage. The generator can only be consumed once.

    Args:
        page_width: Page width in pixels
        page_height: Page height in pixels
        all_photos: All page items in order - photos and/or title slots (e.g. the
            output of text_labels.merge_titles_with_photos)
        distribution: PhotoDistribution instance
        theme: Theme to apply
        text_label_associations: Optional list of (photo, text_label) tuples for captions

    Yields:
        Rendered page images (Iterator[Image.Image])
    """
    # Create a lookup dictionary for text labels
    text_labels_map = {}
    if text_label_associations:
        for photo, label in text_label_associations:
            text_labels_map[photo.path] = label

    for page_num in range(distribution.total_pages):
        # Get photo indices for this page (handles both sparse and normal distribution)
        photo_indices = distribution.get_photo_indices_for_page(page_num)
        page_photos = [all_photos[i] for i in photo_indices]

        # Get corresponding text labels (title slots have no caption association)
        page_text_labels = None
        if text_labels_map:
            page_text_labels = [
                text_labels_map.get(item.path) if isinstance(item, PhotoMetadata) else None
                for item in page_photos
            ]

        # Render page
        page = render_page(page_width, page_height, page_photos, theme, page_num, page_text_labels)

        # Yield page for processing (memory-efficient streaming)
        yield page

    logger.info(f"Completed rendering {distribution.total_pages} pages")
