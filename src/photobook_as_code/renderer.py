"""
Page rendering with photos and styling.
"""

from pathlib import Path
from typing import Iterator, List, Optional, Tuple
import logging

from PIL import Image, ImageDraw, ImageFont

from .layout import fit_photo_in_cell, match_template
from .photos import PhotoMetadata
from .themes import Theme, LayoutTemplate
from .text_labels import TextLabel, parse_markdown_text

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


def render_text_label(draw: ImageDraw.Draw, text_label: TextLabel, text_pos: 'TextPosition',
                      page_width: int, page_height: int, theme: Theme) -> None:
    """
    Render text label with markdown formatting.
    
    Args:
        draw: ImageDraw instance
        text_label: TextLabel with text content
        text_pos: TextPosition specifying where to draw text
        page_width: Page width in pixels
        page_height: Page height in pixels
        theme: Theme with text styling properties
    """
    # Calculate bounding box from percentages
    box_x = int(page_width * text_pos.x / 100)
    box_y = int(page_height * text_pos.y / 100)
    box_width = int(page_width * text_pos.width / 100)
    box_height = int(page_height * text_pos.height / 100)
    
    # Parse markdown
    parsed_lines = parse_markdown_text(text_label.text)
    
    # Get theme text styling
    base_font_size = theme.text.base_font_size
    font_family = theme.text.font_family
    text_color = theme.text.text_color
    
    # Try to load fonts (fall back to default if not available)
    try:
        font_regular = ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{font_family}.ttf", base_font_size)
        font_bold = ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{font_family}-Bold.ttf", base_font_size)
        font_italic = ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{font_family}-Oblique.ttf", base_font_size)
        font_bold_italic = ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{font_family}-BoldOblique.ttf", base_font_size)
    except:
        # Fall back to default font
        logger.warning(f"Font {font_family} with size {base_font_size} not found.")
        font_regular = ImageFont.load_default()
        font_bold = font_regular
        font_italic = font_regular
        font_bold_italic = font_regular
    
    rgb = hex_to_rgb(text_color)
    padding = theme.text.text_padding
    
    # Calculate text area with padding
    text_box_x = box_x + padding
    text_box_y = box_y + padding
    text_box_width = box_width - 2 * padding
    text_box_height = box_height - 2 * padding
    
    current_y = text_box_y
    line_spacing = 4
    
    # Draw semi-transparent background if enabled
    if theme.text.text_background_enabled:
        # Use template-specified dimensions for background
        # This ensures background matches the template size regardless of text width
        bg_x = box_x
        bg_y = box_y
        bg_width = box_width
        bg_height = box_height
        
        # Create semi-transparent overlay
        bg_color = hex_to_rgb(theme.text.text_background_color)
        opacity = int(255 * theme.text.text_background_opacity / 100)
        
        # Draw rectangle with transparency
        overlay = Image.new('RGBA', (int(bg_width), int(bg_height)), bg_color + (opacity,))
        # Get the page as RGBA for compositing
        page_img = draw._image
        if page_img.mode != 'RGBA':
            page_img = page_img.convert('RGBA')
        page_img.paste(overlay, (int(bg_x), int(bg_y)), overlay)
        # Update draw to use the new image
        if draw._image.mode == 'RGB':
            draw._image.paste(page_img.convert('RGB'), (0, 0))
    
    for segments, heading_level in parsed_lines:
        if current_y > text_box_y + text_box_height:
            break  # Clip at boundary
        
        # Calculate line width for alignment
        line_width = 0
        line_height = 0
        segment_infos = []
        
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
            
            # Get text bounding box
            bbox = draw.textbbox((0, 0), segment.text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            segment_infos.append((segment, font, text_width, text_height))
            line_width += text_width
            line_height = max(line_height, text_height)
        
        # Apply horizontal alignment within padded text box
        if text_pos.align == 'center':
            current_x = text_box_x + (text_box_width - line_width) // 2
        elif text_pos.align == 'right':
            current_x = text_box_x + text_box_width - line_width
        else:  # left
            current_x = text_box_x
        
        # Draw segments
        for segment, font, seg_width, seg_height in segment_infos:
            # Check if text fits in padded box
            if current_x + seg_width > text_box_x + text_box_width:
                break  # Clip horizontally
            
            # Draw text
            draw.text((current_x, current_y), segment.text, fill=rgb, font=font)
            current_x += seg_width
        
        # Move to next line
        current_y += line_height + line_spacing


def render_page(page_width: int, page_height: int, photos: List[PhotoMetadata],
                theme: Theme, page_number: int = 0, 
                text_labels: Optional[List[Optional[TextLabel]]] = None) -> Image.Image:
    """
    Render a single page with photos and styling.
    
    Args:
        page_width: Page width in pixels
        page_height: Page height in pixels
        photos: List of photos to place on this page
        theme: Theme to apply
        page_number: Page number for logging (0-indexed)
        text_labels: Optional list of text labels for each photo (same length as photos)
        
    Returns:
        Rendered page as PIL Image
    """
    logger.info(f"Rendering page {page_number + 1} with {len(photos)} photos")
    
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
    
    for i, (photo, spec) in enumerate(zip(photos, template.photos)):
        try:
            # Calculate target dimensions using dual boundaries
            target_width = max(1, int(usable_width * spec.size.width) - (2 * theme.spacing.photo_margin))
            target_height = max(1, int(usable_height * spec.size.height) - (2 * theme.spacing.photo_margin))
                
            # Load and resize photo
            photo_img = load_and_resize_photo(photo, target_width, target_height)
            
            # Calculate center position
            center_x = theme.spacing.page_margin + int(usable_width * spec.position.x)
            center_y = theme.spacing.page_margin + int(usable_height * spec.position.y)
            
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
            logger.error(f"Failed to render photo {photo.filename} on page {page_number + 1}: {e}")
            # Store empty placement to maintain index alignment
            photo_placements.append((0, 0, 0, 0))
            # Continue with other photos
    
    # PHASE 2: Draw borders and text labels on top of all photos
    # Create draw object after all photos are pasted
    draw = ImageDraw.Draw(page)
    
    for i, spec in enumerate(template.photos):
        if i >= len(photo_placements):
            break
            
        pos_x, pos_y, width, height = photo_placements[i]
        
        if width == 0 or height == 0:
            continue  # Skip if photo failed to load
        
        try:
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
                    theme
                )
            
        except Exception as e:
            logger.error(f"Failed to render border/text for photo on page {page_number + 1}: {e}")
            # Continue with other elements
    
    return page


def render_all_pages(page_width: int, page_height: int, all_photos: List[PhotoMetadata],
                     distribution, theme: Theme, 
                     text_label_associations: Optional[List[Tuple[PhotoMetadata, Optional[TextLabel]]]] = None):
    """
    Render all pages for the photobook incrementally.
    
    This is a generator function that yields pages one at a time to minimize
    memory usage. The generator can only be consumed once.
    
    Args:
        page_width: Page width in pixels
        page_height: Page height in pixels
        all_photos: All photos in order
        distribution: PhotoDistribution instance
        theme: Theme to apply
        text_label_associations: Optional list of (photo, text_label) tuples
        
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
        
        # Get corresponding text labels
        page_text_labels = None
        if text_labels_map:
            page_text_labels = [text_labels_map.get(photo.path) for photo in page_photos]
        
        # Render page
        page = render_page(page_width, page_height, page_photos, theme, page_num, page_text_labels)
        
        # Yield page for processing (memory-efficient streaming)
        yield page
    
    logger.info(f"Completed rendering {distribution.total_pages} pages")
