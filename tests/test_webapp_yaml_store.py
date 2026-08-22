"""
Tests for the round-trip-safe YAML persistence layer used by the web editor.
"""

from pathlib import Path

from photobook_as_code.config import load_config
from photobook_as_code.photos import PhotoMetadata
from photobook_as_code.text_labels import associate_text_labels_with_photos
from photobook_as_code.webapp import yaml_store


SAMPLE_CONFIG = """\
photos: ./photos/
output:
  size: A4
layout:
  photos_per_page: 2
theme: clean

text_labels:
  - timestamp: "2026-01-01T10:00:00"  # title.jpg
    title: |
      # Trip Title

      ## January 2026
  - timestamp: "2026-01-02T09:00:00"  # a.jpg
    text: ""
  - timestamp: "2026-01-03T09:00:00"  # b.jpg
    text: "existing text"
"""


def _write_config(tmp_path: Path, content: str) -> Path:
    config_path = tmp_path / "test-config.yaml"
    config_path.write_text(content)
    return config_path


def _photo(filename: str, iso_timestamp: str) -> PhotoMetadata:
    from datetime import datetime

    return PhotoMetadata(
        path=Path(f"/photos/{filename}"),
        filename=filename,
        date_taken=datetime.fromisoformat(iso_timestamp),
        width=1600,
        height=1200,
    )


class TestUpdateExistingEntry:
    """Editing an already-associated entry preserves everything else."""

    def test_update_preserves_comments_order_and_title(self, tmp_path):
        config_path = _write_config(tmp_path, SAMPLE_CONFIG)
        config = load_config(config_path)

        b_photo = _photo("b.jpg", "2026-01-03T09:00:00")
        a_photo = _photo("a.jpg", "2026-01-02T09:00:00")
        photos = [a_photo, b_photo]
        associations = associate_text_labels_with_photos(config.text_labels, photos)
        _, b_label = associations[1]
        assert b_label is not None and b_label.text == "existing text"

        yaml_store.save_photo_text(config_path, config.text_labels, b_photo, b_label, "updated text")

        # ruamel preserves the entry's original double-quoted style when its
        # value is overwritten - only the text itself changes
        expected = SAMPLE_CONFIG.replace(
            '    text: "existing text"', '    text: "updated text"'
        )
        assert config_path.read_text() == expected

    def test_update_leaves_no_changes_to_other_entries_text(self, tmp_path):
        config_path = _write_config(tmp_path, SAMPLE_CONFIG)
        config = load_config(config_path)

        a_photo = _photo("a.jpg", "2026-01-02T09:00:00")
        b_photo = _photo("b.jpg", "2026-01-03T09:00:00")
        photos = [a_photo, b_photo]
        associations = associate_text_labels_with_photos(config.text_labels, photos)
        _, a_label = associations[0]

        yaml_store.save_photo_text(config_path, config.text_labels, a_photo, a_label, "a's new caption")

        content = config_path.read_text()
        assert '# title.jpg' in content
        assert '# Trip Title' in content
        assert '    text: "existing text"' in content  # b.jpg entry untouched
        assert "a's new caption" in content


class TestInsertNewEntry:
    """Saving text for a photo with no existing association creates one."""

    def test_insert_at_end_when_latest(self, tmp_path):
        config_path = _write_config(tmp_path, SAMPLE_CONFIG)
        config = load_config(config_path)

        c_photo = _photo("c.jpg", "2026-01-04T09:00:00")

        yaml_store.save_photo_text(config_path, config.text_labels, c_photo, None, "new caption")

        content = config_path.read_text()
        assert content.startswith(SAMPLE_CONFIG)
        tail = content[len(SAMPLE_CONFIG):]
        assert '  - timestamp: "2026-01-04T09:00:00"  # c.jpg' in tail
        assert 'text: new caption' in tail

    def test_insert_in_chronological_middle(self, tmp_path):
        config_path = _write_config(tmp_path, SAMPLE_CONFIG)
        config = load_config(config_path)

        mid_photo = _photo("mid.jpg", "2026-01-02T15:00:00")

        yaml_store.save_photo_text(config_path, config.text_labels, mid_photo, None, "midday")

        content = config_path.read_text()
        a_pos = content.index("a.jpg")
        mid_pos = content.index("mid.jpg")
        b_pos = content.index("b.jpg")
        assert a_pos < mid_pos < b_pos
        # entries untouched either side of the insertion
        assert '# title.jpg' in content
        assert '    text: ""' in content  # a.jpg's entry, still empty
        assert '    text: "existing text"' in content  # b.jpg's entry, untouched

    def test_title_entry_untouched_by_insert(self, tmp_path):
        config_path = _write_config(tmp_path, SAMPLE_CONFIG)
        config = load_config(config_path)

        c_photo = _photo("c.jpg", "2026-01-04T09:00:00")
        yaml_store.save_photo_text(config_path, config.text_labels, c_photo, None, "new caption")

        content = config_path.read_text()
        assert "# Trip Title" in content
        assert "## January 2026" in content
        assert '- timestamp: "2026-01-01T10:00:00"  # title.jpg' in content

    def test_insert_creates_text_labels_section_when_absent(self, tmp_path):
        no_labels_config = """\
photos: ./photos/
output:
  size: A4
layout:
  photos_per_page: 2
theme: clean
"""
        config_path = _write_config(tmp_path, no_labels_config)
        config = load_config(config_path)
        assert config.text_labels == []

        photo = _photo("only.jpg", "2026-02-01T08:00:00")
        yaml_store.save_photo_text(config_path, config.text_labels, photo, None, "first caption")

        content = config_path.read_text()
        assert content.startswith(no_labels_config)
        assert "text_labels:" in content
        assert '# only.jpg' in content
        assert "first caption" in content

        # the new file itself must still be a valid, loadable config
        reloaded = load_config(config_path)
        assert len(reloaded.text_labels) == 1
        assert reloaded.text_labels[0]["text"] == "first caption"
