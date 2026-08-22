import os
from datetime import datetime, timedelta

from click.testing import CliRunner
from PIL import Image

from photobook_as_code.cli import main


def _make_photos_dir(tmp_path):
    """
    Create a photos directory with 3 photos whose deterministic mtimes are
    NOT in filename-alphabetical order, so a test can distinguish
    chronological stub ordering from alphabetical layout order.
    """
    photos_dir = tmp_path / "photos"
    photos_dir.mkdir()

    base = datetime(2026, 7, 1, 10, 0, 0)
    # filename -> hours offset from base; alphabetical filename order
    # (photo_a, photo_m, photo_z) differs from chronological order
    # (photo_z, photo_m, photo_a).
    offsets = {"photo_a.jpg": 2, "photo_m.jpg": 1, "photo_z.jpg": 0}
    for filename, hours in offsets.items():
        path = photos_dir / filename
        Image.new("RGB", (800, 600), color="blue").save(path)
        mtime = (base + timedelta(hours=hours)).timestamp()
        os.utime(path, (mtime, mtime))

    return photos_dir, base


def test_extract_labels_prints_stubs_and_writes_no_output(tmp_path):
    photos_dir, base = _make_photos_dir(tmp_path)
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    config_content = f"""photos: {photos_dir}
output:
  size: A4
  format: pdf
  directory: {output_dir}
layout:
  photos_per_page: 4
theme: clean
text_labels:
  - timestamp: "2020-01-01T00:00:00"
    text: "Pre-existing entry, must be ignored"
"""
    config_path = tmp_path / "test-config.yaml"
    config_path.write_text(config_content)

    runner = CliRunner()
    result = runner.invoke(main, ["--config", str(config_path), "--extract-labels"])

    assert result.exit_code == 0, result.output

    expected = (
        "text_labels:\n"
        f'  - timestamp: "{base.isoformat()}"  # photo_z.jpg\n'
        '    text: ""\n'
        f'  - timestamp: "{(base + timedelta(hours=1)).isoformat()}"  # photo_m.jpg\n'
        '    text: ""\n'
        f'  - timestamp: "{(base + timedelta(hours=2)).isoformat()}"  # photo_a.jpg\n'
        '    text: ""\n'
    )
    assert result.output == expected

    # Chronological order beats the config's (default) alphabetical layout order
    assert result.output.index("photo_z.jpg") < result.output.index("photo_m.jpg") < result.output.index("photo_a.jpg")

    # No photobook output was generated
    assert list(output_dir.iterdir()) == []


def test_extract_labels_collapses_shared_timestamp(tmp_path):
    photos_dir = tmp_path / "photos"
    photos_dir.mkdir()

    shared = datetime(2026, 7, 1, 10, 0, 0)
    for filename in ("photo_b.jpg", "photo_c.jpg"):
        path = photos_dir / filename
        Image.new("RGB", (800, 600), color="blue").save(path)
        mtime = shared.timestamp()
        os.utime(path, (mtime, mtime))

    config_content = f"""photos: {photos_dir}
output:
  size: A4
  format: pdf
layout:
  photos_per_page: 4
theme: clean
"""
    config_path = tmp_path / "test-config.yaml"
    config_path.write_text(config_content)

    runner = CliRunner()
    result = runner.invoke(main, ["--config", str(config_path), "--extract-labels"])

    assert result.exit_code == 0, result.output
    assert result.output == (
        "text_labels:\n"
        f'  - timestamp: "{shared.isoformat()}"  # photo_b.jpg, photo_c.jpg\n'
        '    text: ""\n'
    )
