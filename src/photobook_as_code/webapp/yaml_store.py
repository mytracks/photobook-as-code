"""
Round-trip-safe reading and writing of the `text_labels` section of a
photobook YAML configuration file.

Unlike `config.load_config` (which uses `yaml.safe_load` and is read-only),
this module edits the file in place with `ruamel.yaml`'s round-trip mode so
that comments, key order, and unrelated sections survive a save unchanged.
"""

import os
import tempfile
from pathlib import Path
from typing import List, Optional

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from ruamel.yaml.scalarstring import DoubleQuotedScalarString

from ..photos import PhotoMetadata
from ..text_labels import TextLabel, TitleLabel, _parse_timestamp


def _make_yaml() -> YAML:
    """Build a YAML instance configured to match this project's file style exactly."""
    yaml = YAML(typ="rt")
    yaml.preserve_quotes = True
    yaml.width = 4096
    yaml.indent(mapping=2, sequence=4, offset=2)
    return yaml


def load_document(config_path: Path) -> CommentedMap:
    """Load the full YAML document in round-trip mode, preserving comments and formatting."""
    yaml = _make_yaml()
    with open(config_path, "r") as f:
        return yaml.load(f)


def save_document(config_path: Path, document: CommentedMap) -> None:
    """
    Write the document back to config_path, preserving formatting.

    Writes to a temp file in the same directory first, then replaces the
    original atomically, so a failure mid-write cannot truncate the file.
    """
    yaml = _make_yaml()
    directory = config_path.parent
    fd, tmp_path = tempfile.mkstemp(dir=directory, prefix=f".{config_path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            yaml.dump(document, f)
        os.replace(tmp_path, config_path)
    except BaseException:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def find_entry_index(text_labels: List[dict], label: TextLabel) -> Optional[int]:
    """
    Find the index within a plain text_labels list (as parsed by
    config.load_config) of the entry that produced the given TextLabel.

    Both the plain list and the round-trip document are parsed from the same
    unmodified file, so this index is also the correct index into the
    round-trip document's text_labels sequence.
    """
    for index, entry in enumerate(text_labels):
        if "text" not in entry:
            continue
        try:
            candidate = TextLabel.from_dict(entry)
        except (KeyError, ValueError):
            continue
        if candidate.timestamp == label.timestamp and candidate.text == label.text:
            return index
    return None


def insert_new_entry(document: CommentedMap, photo: PhotoMetadata, text: str) -> int:
    """
    Insert a new text_labels entry for a photo that has none yet, using the
    photo's own timestamp, positioned in chronological order among existing
    entries. Creates the text_labels key if the document doesn't have one.

    Returns the index the new entry was inserted at.
    """
    if document.get("text_labels") is None:
        document["text_labels"] = CommentedSeq()

    text_labels_seq = document["text_labels"]

    insert_at = len(text_labels_seq)
    for i, existing in enumerate(text_labels_seq):
        if _parse_timestamp(existing["timestamp"]) > photo.sort_date:
            insert_at = i
            break

    entry = CommentedMap()
    entry["timestamp"] = DoubleQuotedScalarString(photo.sort_date.isoformat())
    entry["text"] = text
    entry.yaml_add_eol_comment(photo.filename, "timestamp")

    text_labels_seq.insert(insert_at, entry)
    return insert_at


def save_photo_text(
    config_path: Path,
    text_labels: List[dict],
    photo: PhotoMetadata,
    label: Optional[TextLabel],
    new_text: str,
) -> None:
    """
    Save `new_text` as the text_labels entry for `photo`.

    Updates the existing entry in place if `label` identifies one (found via
    `find_entry_index` against `text_labels`), otherwise inserts a new entry.
    Loads and writes the document fresh so the save always reflects the
    file's current on-disk content.
    """
    document = load_document(config_path)

    index = find_entry_index(text_labels, label) if label is not None else None
    if index is not None:
        document["text_labels"][index]["text"] = new_text
    else:
        insert_new_entry(document, photo, new_text)

    save_document(config_path, document)


def find_title_entry_index(text_labels: List[dict], label: TitleLabel) -> Optional[int]:
    """
    Find the index within a plain text_labels list (as parsed by
    config.load_config) of the entry that produced the given TitleLabel.

    Mirrors `find_entry_index`, matching on `(timestamp, title)` instead of
    `(timestamp, text)`.
    """
    for index, entry in enumerate(text_labels):
        if "title" not in entry:
            continue
        try:
            candidate = TitleLabel.from_dict(entry)
        except (KeyError, ValueError):
            continue
        if candidate.timestamp == label.timestamp and candidate.title == label.title:
            return index
    return None


def insert_new_title_entry(document: CommentedMap, photo: PhotoMetadata, title_text: str = "") -> int:
    """
    Insert a new title entry timestamped to `photo`'s own timestamp,
    positioned in chronological order among existing entries. Creates the
    text_labels key if the document doesn't have one.

    Using the photo's own timestamp means the new title sorts immediately
    before that specific photo once merged with the photo sequence (see
    `text_labels.merge_titles_with_photos`), without any editor-side
    ordering logic of its own.

    Returns the index the new entry was inserted at.
    """
    if document.get("text_labels") is None:
        document["text_labels"] = CommentedSeq()

    text_labels_seq = document["text_labels"]

    insert_at = len(text_labels_seq)
    for i, existing in enumerate(text_labels_seq):
        if _parse_timestamp(existing["timestamp"]) > photo.sort_date:
            insert_at = i
            break

    entry = CommentedMap()
    entry["timestamp"] = DoubleQuotedScalarString(photo.sort_date.isoformat())
    entry["title"] = title_text
    entry.yaml_add_eol_comment(photo.filename, "timestamp")

    text_labels_seq.insert(insert_at, entry)
    return insert_at


def insert_new_title(config_path: Path, photo: PhotoMetadata) -> None:
    """
    Create a new, empty title entry timestamped to `photo`, saving it to
    `config_path`. Loads and writes the document fresh so the save always
    reflects the file's current on-disk content.
    """
    document = load_document(config_path)
    insert_new_title_entry(document, photo, "")
    save_document(config_path, document)


def save_title_text(
    config_path: Path,
    text_labels: List[dict],
    label: TitleLabel,
    new_text: str,
) -> None:
    """
    Save `new_text` as the title entry identified by `label`.

    Loads and writes the document fresh so the save always reflects the
    file's current on-disk content.
    """
    document = load_document(config_path)
    index = find_title_entry_index(text_labels, label)
    document["text_labels"][index]["title"] = new_text
    save_document(config_path, document)


def prepend_to_title_entry(
    config_path: Path,
    text_labels: List[dict],
    label: TitleLabel,
    date_text: str,
) -> None:
    """
    Prepend `date_text` to the title entry identified by `label`: the new
    first line of its content, separated from any existing content by a
    blank line - matching this project's own hand-written convention of a
    plain date line followed by the rest of a title's Markdown content. When
    the title has no existing content, `date_text` becomes its entire
    content.

    Loads and writes the document fresh so the save always reflects the
    file's current on-disk content.
    """
    document = load_document(config_path)
    index = find_title_entry_index(text_labels, label)
    existing = document["text_labels"][index]["title"]
    document["text_labels"][index]["title"] = (
        f"{date_text}\n\n{existing}" if existing else date_text
    )
    save_document(config_path, document)


def delete_title_entry(
    config_path: Path,
    text_labels: List[dict],
    label: TitleLabel,
) -> None:
    """
    Delete the title entry identified by `label` from the configuration
    file. Loads and writes the document fresh so the save always reflects
    the file's current on-disk content.
    """
    document = load_document(config_path)
    index = find_title_entry_index(text_labels, label)
    del document["text_labels"][index]
    save_document(config_path, document)
