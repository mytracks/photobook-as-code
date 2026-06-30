"""
Page rendering with photos and styling.
"""

from pathlib import Path
from typing import Iterator, List, Optional
import logging

from PIL import Image, ImageDraw

from .layout import LayoutTemplate, PhotoOrientation, TemplateMatcher
from .photos import PhotoMetadata
from .themes import Theme

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
    Load photo and resize to target dimensions, maintaining aspect ratio.
    
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
        
        # Calculate aspect ratio of the photo
        photo_aspect_ratio = img.width / img.height
        
        # Calculate dimensions to fit within target_width x target_height while maintaining aspect ratio
        if (target_width / target_height) > photo_aspect_ratio:
            # Target is wider than photo, fit by height
            new_height = target_height
            new_width = int(new_height * photo_aspect_ratio)
        else:
            # Target is taller than photo, fit by width
            new_width = target_width
            new_height = int(new_width / photo_aspect_ratio)
            
        # Resize with high-quality resampling
        img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
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


def render_page(layout_template: LayoutTemplate, photos: List[PhotoMetadata],
                page_width: int, page_height: int, theme: Theme, page_number: int = 0) -> Image.Image:
    """
    Render a single page with photos and styling.
    
    Args:
        page_layout: Page layout specification
        photos: List of photos to place on this page
        theme: Theme to apply
        page_number: Page number for logging (0-indexed)
        
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

    # Place each photo according to layout template
    for i, photo_metadata in enumerate(photos):
        if i >= len(layout_template.photos):
            logger.warning(f"More photos than photo specs in template on page {page_number + 1}")
            break

        photo_spec = layout_template.photos[i]

        try:
            # Calculate target dimensions based on orientation and size
            if photo_spec.orientation == PhotoOrientation.LANDSCAPE:
                target_width = int(page_width * photo_spec.size)
                # Calculate height to maintain aspect ratio after loading
                # Temporarily open image to get aspect ratio
                with Image.open(photo_metadata.path) as temp_img:
                    photo_aspect_ratio = temp_img.width / temp_img.height
                target_height = int(target_width / photo_aspect_ratio)
            else:  # PhotoOrientation.PORTRAIT
                target_height = int(page_height * photo_spec.size)
                # Calculate width to maintain aspect ratio after loading
                # Temporarily open image to get aspect ratio
                with Image.open(photo_metadata.path) as temp_img:
                    photo_aspect_ratio = temp_img.width / temp_img.height
                target_width = int(target_height * photo_aspect_ratio)

            # Load and resize photo
            photo_img = load_and_resize_photo(photo_metadata, target_width, target_height)

            # Calculate absolute position (center-point based)
            abs_x = int(page_width * photo_spec.position.x - photo_img.width / 2)
            abs_y = int(page_height * photo_spec.position.y - photo_img.height / 2)

            # Apply shadow if enabled
            if theme.borders.shadow:
                page = draw_shadow(
                    page,
                    abs_x,
                    abs_y,
                    photo_img.width,
                    photo_img.height
                )

            # Paste photo onto page
            page.paste(
                photo_img,
                (abs_x, abs_y)
            )

            # Draw border if enabled
            if theme.borders.enabled and theme.borders.width > 0:
                draw = ImageDraw.Draw(page)
                draw_border(
                    draw,
                    abs_x,
                    abs_y,
                    photo_img.width,
                    photo_img.height,
                    theme.borders.width,
                    theme.borders.color
                )

        except Exception as e:
            logger.error(f"Failed to render photo {photo_metadata.filename} on page {page_number + 1}: {e}")
            # Continue with other photos

    return page


def render_all_pages(all_photos: List[PhotoMetadata], distribution, theme: Theme,
                     template_matcher: TemplateMatcher, page_width: int, page_height: int):
    """
    Render all pages for the photobook incrementally.
    
    This is a generator function that yields pages one at a time to minimize
    memory usage. The generator can only be consumed once.
    
    Args:
        page_layout: Page layout specification
        all_photos: All photos in order
        distribution: PhotoDistribution instance
        theme: Theme to apply
        
    Yields:
        Rendered page images (Iterator[Image.Image])
    """
    photo_index = 0

    for page_num in range(distribution.total_pages):
        # Get photos for this page
        photos_on_page = distribution.get_photos_for_page(page_num)
        page_photos = all_photos[photo_index:photo_index + photos_on_page]

        # Detect photo orientations for the current page
        photo_orientations = [photo.orientation for photo in page_photos]

        # Match page photos to template from theme layouts
        layout_template = template_matcher.find_best_template(photo_orientations)
        # find_best_template will raise LayoutError if no template matches

        # Render page
        page = render_page(layout_template, page_photos, page_width, page_height, theme, page_num)

        # Yield page for processing (memory-efficient streaming)
        yield page

        photo_index += photos_on_page

    logger.info(f"Completed rendering {distribution.total_pages} pages")
