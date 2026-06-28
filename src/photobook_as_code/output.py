"""
Output file generation (PDF and images).
"""

from pathlib import Path
from typing import List
import logging
from datetime import datetime

from PIL import Image
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

logger = logging.getLogger(__name__)


class OutputError(Exception):
    """Raised when output generation fails."""
    pass


def generate_pdf(pages: List[Image.Image], output_path: Path,
                 page_width_pixels: int, page_height_pixels: int,
                 dpi: int = 300) -> None:
    """
    Generate PDF from rendered page images.
    
    Args:
        pages: List of page images
        output_path: Path for output PDF file
        page_width_pixels: Page width in pixels
        page_height_pixels: Page height in pixels
        dpi: Dots per inch for conversion
        
    Raises:
        OutputError: If PDF generation fails
    """
    try:
        # Convert pixels to points (PDF units)
        page_width_pts = (page_width_pixels / dpi) * 72
        page_height_pts = (page_height_pixels / dpi) * 72
        
        # Create PDF canvas
        c = canvas.Canvas(str(output_path), pagesize=(page_width_pts, page_height_pts))
        
        logger.info(f"Generating PDF with {len(pages)} pages...")
        
        for i, page in enumerate(pages):
            logger.debug(f"Adding page {i + 1}/{len(pages)} to PDF")
            
            # Save page image to temporary bytes
            import io
            img_buffer = io.BytesIO()
            page.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            # Create ImageReader for ReportLab
            img_reader = ImageReader(img_buffer)
            
            # Draw image on PDF page
            c.drawImage(
                img_reader,
                0, 0,
                width=page_width_pts,
                height=page_height_pts,
                preserveAspectRatio=True
            )
            
            # Add new page for next image (except on last page)
            if i < len(pages) - 1:
                c.showPage()
        
        # Save PDF
        c.save()
        logger.info(f"PDF saved to {output_path}")
        
    except Exception as e:
        raise OutputError(f"Failed to generate PDF: {e}")


def generate_png_pages(pages: List[Image.Image], output_dir: Path,
                       base_filename: str) -> List[Path]:
    """
    Generate PNG images for each page.
    
    Args:
        pages: List of page images
        output_dir: Directory for output files
        base_filename: Base name for files (without extension)
        
    Returns:
        List of generated file paths
        
    Raises:
        OutputError: If image generation fails
    """
    try:
        output_paths = []
        
        logger.info(f"Generating {len(pages)} PNG pages...")
        
        for i, page in enumerate(pages):
            # Generate sequential filename
            page_filename = f"{base_filename}_page_{i+1:03d}.png"
            output_path = output_dir / page_filename
            
            logger.debug(f"Saving page {i + 1}/{len(pages)} as PNG")
            
            # Save as PNG
            page.save(output_path, format='PNG', optimize=False)
            output_paths.append(output_path)
        
        logger.info(f"PNG pages saved to {output_dir}")
        return output_paths
        
    except Exception as e:
        raise OutputError(f"Failed to generate PNG pages: {e}")


def generate_jpg_pages(pages: List[Image.Image], output_dir: Path,
                       base_filename: str, quality: int = 95) -> List[Path]:
    """
    Generate JPG images for each page.
    
    Args:
        pages: List of page images
        output_dir: Directory for output files
        base_filename: Base name for files (without extension)
        quality: JPEG quality (1-100)
        
    Returns:
        List of generated file paths
        
    Raises:
        OutputError: If image generation fails
    """
    try:
        output_paths = []
        
        logger.info(f"Generating {len(pages)} JPG pages with quality {quality}...")
        
        for i, page in enumerate(pages):
            # Generate sequential filename
            page_filename = f"{base_filename}_page_{i+1:03d}.jpg"
            output_path = output_dir / page_filename
            
            logger.debug(f"Saving page {i + 1}/{len(pages)} as JPG")
            
            # Save as JPEG
            page.save(output_path, format='JPEG', quality=quality, optimize=True)
            output_paths.append(output_path)
        
        logger.info(f"JPG pages saved to {output_dir}")
        return output_paths
        
    except Exception as e:
        raise OutputError(f"Failed to generate JPG pages: {e}")


def generate_output(pages: List[Image.Image], output_format: str,
                    output_path: Path, page_width: int, page_height: int,
                    quality: int = 95, dpi: int = 300) -> List[Path]:
    """
    Generate output files in specified format.
    
    Args:
        pages: List of rendered page images
        output_format: Output format ('pdf', 'png', or 'jpg')
        output_path: Output file path (for PDF) or directory (for images)
        page_width: Page width in pixels
        page_height: Page height in pixels
        quality: JPEG quality for JPG output
        dpi: DPI for PDF conversion
        
    Returns:
        List of generated file paths
        
    Raises:
        OutputError: If output generation fails
    """
    if not pages:
        raise OutputError("No pages to output")
    
    # Ensure output directory exists
    output_dir = output_path.parent if output_format == 'pdf' else output_path
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if output_format == 'pdf':
        generate_pdf(pages, output_path, page_width, page_height, dpi)
        return [output_path]
    
    elif output_format == 'png':
        base_name = output_path.stem if output_path.suffix else output_path.name
        return generate_png_pages(pages, output_dir, base_name)
    
    elif output_format == 'jpg':
        base_name = output_path.stem if output_path.suffix else output_path.name
        return generate_jpg_pages(pages, output_dir, base_name, quality)
    
    else:
        raise OutputError(f"Unsupported output format: {output_format}")


def ensure_unique_filename(path: Path) -> Path:
    """
    Ensure filename is unique by adding timestamp if file exists.
    
    Args:
        path: Desired output path
        
    Returns:
        Unique path (may be modified with timestamp)
    """
    if not path.exists():
        return path
    
    # Add timestamp to make unique
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = path.stem
    suffix = path.suffix
    
    new_name = f"{stem}_{timestamp}{suffix}"
    return path.parent / new_name


def prepare_output_path(output_dir: Path, filename: str,
                        format: str, ensure_unique: bool = False) -> Path:
    """
    Prepare output path with proper extension.
    
    Args:
        output_dir: Output directory
        filename: Desired filename (may or may not have extension)
        format: Output format ('pdf', 'png', or 'jpg')
        ensure_unique: Whether to ensure filename is unique
        
    Returns:
        Prepared output path
    """
    # Ensure directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Add extension if missing
    path = Path(filename)
    expected_ext = f".{format}"
    
    if path.suffix.lower() != expected_ext:
        filename = f"{path.stem}{expected_ext}"
    
    output_path = output_dir / filename
    
    if ensure_unique:
        output_path = ensure_unique_filename(output_path)
    
    return output_path
