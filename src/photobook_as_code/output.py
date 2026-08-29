"""
Output file generation (PDF and images).
"""

from pathlib import Path
from typing import Iterator, List
import gc
import io
import logging
import shutil
import tempfile
from datetime import datetime

import pikepdf
from PIL import Image
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab import rl_config

logger = logging.getLogger(__name__)

# ASCII85 is a transport encoding with no compression/quality benefit; disabling
# it cuts ~25% off every stream reportlab retains in memory while building a PDF.
rl_config.useA85 = 0


class OutputError(Exception):
    """Raised when output generation fails."""
    pass


def generate_pdf(pages: Iterator[Image.Image], output_path: Path,
                 page_width_pixels: int, page_height_pixels: int,
                 total_pages: int, dpi: int = 300, quality: int = 95) -> None:
    """
    Generate PDF from rendered page images using streaming approach.

    Each page is rendered onto its own single-page PDF with a fresh
    reportlab Canvas, immediately saved to a temp file, and released -
    reportlab's Canvas/PDFDocument keeps every embedded image alive in
    memory until save(), so a single long-lived Canvas would retain every
    page's image for the whole run. Finalizing one page at a time bounds
    peak memory to roughly one page, regardless of total page count. The
    interim single-page PDFs are merged into the final output with pikepdf
    once every page has been rendered.

    Args:
        pages: Iterator of page images (yields pages one at a time)
        output_path: Path for output PDF file
        page_width_pixels: Page width in pixels
        page_height_pixels: Page height in pixels
        total_pages: Expected number of pages for progress reporting
        dpi: Dots per inch for conversion
        quality: JPEG quality used to embed each page's image (1-100)

    Raises:
        OutputError: If PDF generation fails
    """
    try:
        # Convert pixels to points (PDF units)
        page_width_pts = (page_width_pixels / dpi) * 72
        page_height_pts = (page_height_pixels / dpi) * 72

        logger.info(f"Generating PDF with {total_pages} pages...")

        temp_dir = Path(tempfile.mkdtemp(prefix="photobook_pdf_"))
        try:
            interim_paths = []

            for i, page in enumerate(pages, start=1):
                logger.debug(f"Rendering page {i}/{total_pages} to interim PDF")

                # Encode as JPEG rather than PNG: reportlab can embed JPEG
                # bytes almost verbatim (DCTDecode passthrough), instead of
                # decoding back to raw pixels and re-compressing them, which
                # is both slower and far more memory-hungry per page.
                img_buffer = io.BytesIO()
                page.save(img_buffer, format='JPEG', quality=quality)
                img_buffer.seek(0)
                img_reader = ImageReader(img_buffer)

                interim_path = temp_dir / f"page_{i:05d}.pdf"
                page_canvas = canvas.Canvas(str(interim_path), pagesize=(page_width_pts, page_height_pts))
                page_canvas.drawImage(
                    img_reader,
                    0, 0,
                    width=page_width_pts,
                    height=page_height_pts,
                    preserveAspectRatio=True
                )
                page_canvas.save()

                interim_paths.append(interim_path)

                # reportlab's Canvas/PDFDocument hold internal back-references
                # to one another, so the object graph behind each finalized
                # page is a reference cycle, not just a chain CPython's
                # refcounting can free immediately. Left to the generational
                # GC's normal thresholds, these cycles - individually modest
                # in object count but each anchoring several MB of image
                # stream data - accumulate faster than automatic collection
                # keeps up with, and memory grows without bound over a large
                # book. An explicit collect per page keeps peak memory flat.
                del page_canvas
                gc.collect()

            logger.info("Merging interim pages into final PDF...")
            tmp_output_path = output_path.parent / f"{output_path.name}.tmp"
            with pikepdf.Pdf.new() as merged:
                for interim_path in interim_paths:
                    with pikepdf.open(interim_path) as interim_pdf:
                        merged.pages.extend(interim_pdf.pages)
                merged.save(tmp_output_path)

            # Only replace the final output path once the merge over every
            # interim page has fully succeeded, so a failure never leaves a
            # partial/corrupt file at output_path.
            tmp_output_path.replace(output_path)
            logger.info(f"PDF saved to {output_path}")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    except Exception as e:
        raise OutputError(f"Failed to generate PDF: {e}")


def generate_png_pages(pages: Iterator[Image.Image], output_dir: Path,
                       base_filename: str, total_pages: int) -> List[Path]:
    """
    Generate PNG images for each page using streaming approach.
    
    Processes pages one at a time to minimize memory usage. The pages iterator
    can only be consumed once.
    
    Args:
        pages: Iterator of page images (yields pages one at a time)
        output_dir: Directory for output files
        base_filename: Base name for files (without extension)
        total_pages: Expected number of pages for progress reporting
        
    Returns:
        List of generated file paths
        
    Raises:
        OutputError: If image generation fails
    """
    try:
        output_paths = []
        
        logger.info(f"Generating {total_pages} PNG pages...")
        
        for i, page in enumerate(pages, start=1):
            # Generate sequential filename
            page_filename = f"{base_filename}_page_{i:03d}.png"
            output_path = output_dir / page_filename
            
            logger.debug(f"Saving page {i}/{total_pages} as PNG")
            
            # Save as PNG
            page.save(output_path, format='PNG', optimize=False)
            output_paths.append(output_path)
        
        logger.info(f"PNG pages saved to {output_dir}")
        return output_paths
        
    except Exception as e:
        raise OutputError(f"Failed to generate PNG pages: {e}")


def generate_jpg_pages(pages: Iterator[Image.Image], output_dir: Path,
                       base_filename: str, total_pages: int, quality: int = 95) -> List[Path]:
    """
    Generate JPG images for each page using streaming approach.
    
    Processes pages one at a time to minimize memory usage. The pages iterator
    can only be consumed once.
    
    Args:
        pages: Iterator of page images (yields pages one at a time)
        output_dir: Directory for output files
        base_filename: Base name for files (without extension)
        total_pages: Expected number of pages for progress reporting
        quality: JPEG quality (1-100)
        
    Returns:
        List of generated file paths
        
    Raises:
        OutputError: If image generation fails
    """
    try:
        output_paths = []
        
        logger.info(f"Generating {total_pages} JPG pages with quality {quality}...")
        
        for i, page in enumerate(pages, start=1):
            # Generate sequential filename
            page_filename = f"{base_filename}_page_{i:03d}.jpg"
            output_path = output_dir / page_filename
            
            logger.debug(f"Saving page {i}/{total_pages} as JPG")
            
            # Save as JPEG
            page.save(output_path, format='JPEG', quality=quality, optimize=True)
            output_paths.append(output_path)
        
        logger.info(f"JPG pages saved to {output_dir}")
        return output_paths
        
    except Exception as e:
        raise OutputError(f"Failed to generate JPG pages: {e}")


def generate_output(pages: Iterator[Image.Image], output_format: str,
                    output_dir: Path, base_filename: str, page_width: int, page_height: int,
                    total_pages: int, quality: int = 95, dpi: int = 300) -> List[Path]:
    """
    Generate output files in specified format using streaming approach.

    Processes pages one at a time to minimize memory usage. The pages iterator
    can only be consumed once.

    Args:
        pages: Iterator of rendered page images (yields pages one at a time)
        output_format: Output format ('pdf', 'png', or 'jpg')
        output_dir: Directory to write output into (created if missing)
        base_filename: Base name for output (without extension) - used as the
            whole PDF filename's stem, or as the prefix for each page image
        page_width: Page width in pixels
        page_height: Page height in pixels
        total_pages: Expected number of pages for progress reporting
        quality: JPEG quality for JPG output
        dpi: DPI for PDF conversion

    Returns:
        List of generated file paths

    Raises:
        OutputError: If output generation fails
    """
    if total_pages <= 0:
        raise OutputError("No pages to output")

    output_dir.mkdir(parents=True, exist_ok=True)

    if output_format == 'pdf':
        output_path = output_dir / f"{base_filename}.pdf"
        generate_pdf(pages, output_path, page_width, page_height, total_pages, dpi, quality)
        return [output_path]

    elif output_format == 'png':
        return generate_png_pages(pages, output_dir, base_filename, total_pages)

    elif output_format == 'jpg':
        return generate_jpg_pages(pages, output_dir, base_filename, total_pages, quality)

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
                        ensure_unique: bool = False) -> Path:
    """
    Prepare the single output file path for PDF output, with a .pdf extension.

    PDF is the only format that resolves to one file path; png/jpg resolve to
    an output directory plus a base filename instead (see generate_output),
    so this helper is PDF-specific.

    Args:
        output_dir: Output directory
        filename: Desired filename (may or may not have a .pdf extension)
        ensure_unique: Whether to ensure filename is unique

    Returns:
        Prepared output path
    """
    # Ensure directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Add extension if missing
    path = Path(filename)

    if path.suffix.lower() != '.pdf':
        filename = f"{path.stem}.pdf"

    output_path = output_dir / filename

    if ensure_unique:
        output_path = ensure_unique_filename(output_path)

    return output_path
