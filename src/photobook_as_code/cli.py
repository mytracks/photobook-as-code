"""
Command-line interface for photobook generation.
"""

import sys
import logging
from pathlib import Path
from typing import Optional

import click

from . import __version__
from .config import load_config, validate_photos_path, ConfigurationError
from .photos import collect_photos, PhotoCollectionError
from .themes import load_theme, ThemeError
from .layout import (
    distribute_photos, calculate_page_layout, LayoutError
)
from .renderer import render_all_pages
from .output import generate_output, prepare_output_path, OutputError


# Configure logging
def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(levelname)s: %(message)s',
        stream=sys.stderr
    )


@click.command()
@click.option(
    '--config', '-c',
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
    help='Path to YAML configuration file'
)
@click.option(
    '--output', '-o',
    type=click.Path(path_type=Path),
    default=None,
    help='Override output location (file path or directory)'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Enable verbose output'
)
@click.version_option(version=__version__, prog_name='photobook')
def main(config: Path, output: Optional[Path], verbose: bool):
    """
    Generate photobook layouts from YAML configuration.
    
    Takes photos from a directory, arranges them in a grid layout,
    and outputs print-ready PDF or image files.
    
    Example:
    
        photobook --config my-album.yaml
    """
    setup_logging(verbose)
    logger = logging.getLogger(__name__)
    
    try:
        # Stage 1: Load and validate configuration
        click.echo("📖 Loading configuration...")
        pb_config = load_config(config)
        validate_photos_path(pb_config)
        
        # Stage 2: Collect photos
        click.echo("📷 Collecting photos...")
        photos_path = pb_config.resolve_photos_path()
        photos = collect_photos(
            photos_path,
            order=pb_config.layout.order,
            recursive=False
        )
        click.echo(f"   Found {len(photos)} photos")
        
        # Stage 3: Load theme
        click.echo(f"🎨 Loading theme '{pb_config.theme}'...")
        theme = load_theme(pb_config.theme)
        
        # Stage 4: Calculate layout
        click.echo("📐 Calculating layout...")
        
        # Get paper dimensions
        page_width, page_height = pb_config.get_paper_size_pixels()
        
        # Calculate photo distribution
        distribution = distribute_photos(
            total_photos=len(photos),
            photos_per_page=pb_config.layout.photos_per_page,
            total_pages=pb_config.layout.pages
        )
        
        click.echo(f"   {distribution.total_pages} pages, "
                  f"{distribution.photos_per_page} photos per page")
        
        # Calculate page layout
        page_layout = calculate_page_layout(
            page_width=page_width,
            page_height=page_height,
            photos_per_page=distribution.photos_per_page,
            page_margin=theme.spacing.page_margin,
            grid_gap=theme.spacing.grid_gap
        )
        
        # Stage 5: Render pages
        click.echo("🖼️  Rendering pages...")
        
        with click.progressbar(
            length=distribution.total_pages,
            label='Rendering',
            show_percent=True
        ) as bar:
            # We'll render all at once, but update progress
            pages = render_all_pages(page_layout, photos, distribution, theme)
            bar.update(distribution.total_pages)
        
        # Stage 6: Generate output
        click.echo("💾 Generating output...")
        
        # Determine output path
        if output:
            output_path = output
        else:
            output_dir = pb_config.get_output_directory()
            filename = pb_config.get_output_filename(config.name)
            output_path = prepare_output_path(
                output_dir,
                filename,
                pb_config.output.format,
                ensure_unique=False
            )
        
        # Generate output files
        output_files = generate_output(
            pages=pages,
            output_format=pb_config.output.format,
            output_path=output_path,
            page_width=page_width,
            page_height=page_height,
            quality=pb_config.output.quality,
            dpi=300
        )
        
        # Stage 7: Success!
        click.echo()
        click.secho("✅ Photobook generated successfully!", fg='green', bold=True)
        click.echo()
        click.echo("Output files:")
        for file_path in output_files:
            click.echo(f"  📄 {file_path}")
        click.echo()
        
    except ConfigurationError as e:
        click.secho(f"❌ Configuration error: {e}", fg='red', err=True)
        sys.exit(1)
    
    except PhotoCollectionError as e:
        click.secho(f"❌ Photo collection error: {e}", fg='red', err=True)
        sys.exit(1)
    
    except ThemeError as e:
        click.secho(f"❌ Theme error: {e}", fg='red', err=True)
        sys.exit(1)
    
    except LayoutError as e:
        click.secho(f"❌ Layout error: {e}", fg='red', err=True)
        sys.exit(1)
    
    except OutputError as e:
        click.secho(f"❌ Output error: {e}", fg='red', err=True)
        sys.exit(1)
    
    except Exception as e:
        click.secho(f"❌ Unexpected error: {e}", fg='red', err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
