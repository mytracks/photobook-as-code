"""
Tests for the `photobook-edit-labels` CLI entry point's startup validation.
"""

from click.testing import CliRunner

from photobook_as_code.webapp.cli import main


def test_nonexistent_config_file_fails_fast(tmp_path):
    missing = tmp_path / "does-not-exist.yaml"
    runner = CliRunner()

    result = runner.invoke(main, ["--config", str(missing)])

    assert result.exit_code != 0


def test_nonexistent_photos_directory_fails_fast(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        f"photos: {tmp_path / 'no-such-photos-dir'}\n"
        "output:\n"
        "  size: A4\n"
        "layout:\n"
        "  photos_per_page: 2\n"
        "theme: clean\n"
    )
    runner = CliRunner()

    result = runner.invoke(main, ["--config", str(config_path)])

    assert result.exit_code != 0
    assert "does not exist" in result.output.lower() or "photo" in result.output.lower()


def test_invalid_config_contents_fails_fast(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text("not_a_valid_key: true\n")
    runner = CliRunner()

    result = runner.invoke(main, ["--config", str(config_path)])

    assert result.exit_code != 0
