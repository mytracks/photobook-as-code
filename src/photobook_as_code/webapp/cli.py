"""
Command-line entry point for the text_labels web editor.
"""

import sys
from pathlib import Path

import click

from ..config import ConfigurationError
from ..photos import PhotoCollectionError
from .app import create_app
from .data import PhotoDirectoryCache, load_editor_data


@click.command()
@click.option(
    "--config", "-c",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
    help="Path to the YAML configuration file whose text_labels will be edited.",
)
@click.option(
    "--host", default="127.0.0.1", show_default=True,
    help="Host/interface to bind the web server to.",
)
@click.option(
    "--port", default=5000, show_default=True, type=int,
    help="Port to bind the web server to.",
)
def main(config: Path, host: str, port: int):
    """
    Start a local web editor for a photobook configuration's text_labels.

    Shows one photo at a time and lets you write its text_labels caption
    directly, saving edits back into the same YAML file as you navigate.
    Photos are read-only; only the given configuration file is ever written.

    Example:

        photobook-edit-labels --config my-album.yaml
    """
    photo_cache = PhotoDirectoryCache()
    try:
        data = load_editor_data(config, photo_cache=photo_cache)
    except ConfigurationError as e:
        click.secho(f"❌ Configuration error: {e}", fg="red", err=True)
        sys.exit(1)
    except PhotoCollectionError as e:
        click.secho(f"❌ Photo collection error: {e}", fg="red", err=True)
        sys.exit(1)

    click.echo(f"📖 Editing text_labels in {config}")
    click.echo(f"📷 {data.count} photos found")
    click.echo(f"🌐 Open http://{host}:{port}/ in your browser")

    app = create_app(config, photo_cache=photo_cache)
    app.run(host=host, port=port)


if __name__ == "__main__":
    main()
