"""
Command-line interface for photobook generation.
"""

import dataclasses
import sys
import logging
import tracemalloc
from pathlib import Path
from typing import Optional

import click

from . import __version__
from .config import load_config, validate_photo_folders, ConfigurationError
from .photos import collect_photos, format_text_label_stubs, PhotoCollectionError
from .themes import load_theme, ThemeError
from .layout import (
    distribute_photos, LayoutError
)
from .renderer import render_all_pages
from .output import generate_output, prepare_output_path, OutputError
from .text_labels import associate_text_labels_with_photos, parse_title_labels, merge_titles_with_photos


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
@click.option(
    '--extract-labels',
    is_flag=True,
    help='Print an empty text_labels YAML stub for every photo timestamp to '
         'stdout, then exit without generating a photobook. Ignores the '
         "config's existing text_labels and any --output option; photos "
         'sharing an identical timestamp collapse into one stub entry, '
         'annotated with all their filenames.'
)
@click.version_option(version=__version__, prog_name='photobook')
def main(config: Path, output: Optional[Path], verbose: bool, extract_labels: bool):
    """
    Generate photobook layouts from YAML configuration.

    Takes photos from a directory, arranges them in a grid layout,
    and outputs print-ready PDF or image files.

    Example:

        photobook --config my-album.yaml

    Use --extract-labels to instead print an empty text_labels stub for
    every photo timestamp (one per distinct timestamp), for pasting into
    the config's text_labels section:

        photobook --config my-album.yaml --extract-labels
    """
    setup_logging(verbose)
    logger = logging.getLogger(__name__)
    
    # Start memory tracking in verbose mode
    if verbose:
        tracemalloc.start()
        logger.debug("Memory tracking enabled")
    
    try:
        # Stage 1: Load and validate configuration
        if not extract_labels:
            click.echo("📖 Loading configuration...")
        pb_config = load_config(config)
        validate_photo_folders(pb_config)

        # Stage 2: Collect photos
        if not extract_labels:
            click.echo("📷 Collecting photos...")
        photo_folders = pb_config.resolve_photo_folders()
        photos = collect_photos(
            photo_folders,
            order=pb_config.layout.order,
            recursive=False
        )
        if not extract_labels:
            click.echo(f"   Found {len(photos)} photos")

        if extract_labels:
            click.echo(format_text_label_stubs(photos), nl=False)
            return

        # Stage 3: Load theme
        click.echo(f"🎨 Loading theme '{pb_config.theme}'...")
        theme = load_theme(pb_config.theme)

        # Config's output.page_margin, when set, overrides the theme's own
        # spacing.page_margin for this run - applied once here so every
        # downstream consumer (distribute_photos, render_all_pages) sees it
        # through the theme object without any further plumbing.
        if pb_config.output.page_margin is not None:
            theme = dataclasses.replace(
                theme,
                spacing=dataclasses.replace(theme.spacing, page_margin=pb_config.output.page_margin)
            )

        # Stage 3.5: Associate text labels with photos, and parse title slots
        text_label_associations = None
        if pb_config.text_labels:
            click.echo("📝 Associating text labels with photos...")
            text_label_associations = associate_text_labels_with_photos(pb_config.text_labels, photos)
            click.echo(f"   {len([label for _, label in text_label_associations if label is not None])} text labels associated")

            # Log each association
            for photo, text_label in text_label_associations:
                if text_label:
                    logger.info(f"Association: Photo '{photo.path.name}' (date: {photo.sort_date}) -> Text label at {text_label.timestamp}: {text_label.text[:50]}...")
                else:
                    logger.info(f"Association: Photo '{photo.path.name}' (date: {photo.sort_date}) -> No text label")

        titles = parse_title_labels(pb_config.text_labels)
        page_items = merge_titles_with_photos(titles, photos) if titles else photos
        if titles:
            click.echo(f"   {len(titles)} titles merged as page slots")

        # Stage 4: Calculate layout
        click.echo("📐 Calculating layout...")

        # Get paper dimensions
        page_width, page_height = pb_config.get_paper_size_pixels()
        book_orientation = pb_config.get_book_orientation()

        # Calculate photo distribution (titles count as page slots, same as photos)
        distribution = distribute_photos(
            items=page_items,
            photos_per_page=pb_config.layout.photos_per_page,
            total_pages=pb_config.layout.pages,
            max_items_per_page=theme.max_layout_count,
            book_orientation=book_orientation,
            new_page_per_day=pb_config.layout.new_page_per_day,
        )

        click.echo(f"   {distribution.total_pages} pages, "
                  f"{distribution.photos_per_page} items per page")

        # Stage 5: Render pages
        click.echo("🖼️  Rendering pages...")

        # Create page generator (memory-efficient streaming)
        pages_generator = render_all_pages(page_width, page_height, page_items, distribution, theme,
                                            text_label_associations, pb_config.output.transparent)
        
        # Stage 6: Generate output
        click.echo("💾 Generating output...")
        
        # Determine output directory and base filename. PDF resolves to a
        # single file (output_dir/base_filename.pdf); png/jpg resolve to
        # output_dir itself, with base_filename used as each page's prefix -
        # never as a subfolder name.
        if output:
            if pb_config.output.format == 'pdf':
                output_dir = output.parent
                base_filename = output.stem
            else:
                output_dir = output
                base_filename = Path(pb_config.get_output_filename(config.name)).stem
        else:
            output_dir = pb_config.get_output_directory()
            filename = pb_config.get_output_filename(config.name)
            if pb_config.output.format == 'pdf':
                output_path = prepare_output_path(output_dir, filename, ensure_unique=False)
                output_dir = output_path.parent
                base_filename = output_path.stem
            else:
                base_filename = Path(filename).stem

        # Generate output files with streaming pages
        with click.progressbar(
            length=distribution.total_pages,
            label='Processing',
            show_percent=True
        ) as bar:
            # We'll consume the generator during output generation
            # Progress updates happen inside the output functions
            output_files = generate_output(
                pages=pages_generator,
                output_format=pb_config.output.format,
                output_dir=output_dir,
                base_filename=base_filename,
                page_width=page_width,
                page_height=page_height,
                total_pages=distribution.total_pages,
                quality=pb_config.output.quality,
                dpi=300
            )
            bar.update(distribution.total_pages)
        
        # Stage 7: Success!
        click.echo()
        click.secho("✅ Photobook generated successfully!", fg='green', bold=True)
        click.echo()
        click.echo("Output files:")
        for file_path in output_files:
            click.echo(f"  📄 {file_path}")
        click.echo()
        
        # Show memory statistics in verbose mode
        if verbose:
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            logger.info(f"Memory usage - Current: {current / 1024 / 1024:.1f} MB, "
                       f"Peak: {peak / 1024 / 1024:.1f} MB")
            click.echo(f"💾 Peak memory usage: {peak / 1024 / 1024:.1f} MB")
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
            # Stop memory tracking on error
            if tracemalloc.is_tracing():
                tracemalloc.stop()
        sys.exit(1)


if __name__ == '__main__':
    main()
