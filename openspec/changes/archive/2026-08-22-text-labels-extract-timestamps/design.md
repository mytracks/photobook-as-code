## Context

See proposal.md - Why/What Changes for motivation and scope. Relevant existing code:
- `cli.py`'s `main` is a single `@click.command()` (not a group) that always runs the full load→collect→theme→layout→render→output pipeline.
- `photos.py`'s `collect_photos` returns `PhotoMetadata` ordered per `layout.order` (`alphabetical` or `date`); `PhotoMetadata.sort_date` gives the best-available timestamp (EXIF `date_taken`, falling back to `file_modified`).
- `config.py` loads `text_labels` via plain `yaml.safe_load` with no comment/formatting preservation - which is exactly why this change avoids touching the config file at all (per prior discussion: writing to stdout only, no round-trip).
- `renderer.py`'s `render_text_label` (line 321) parses the label via `parse_markdown_text`, then unconditionally computes a box height (`2 * padding` minimum) and, if the theme enables it, draws a background rectangle - even when there are zero content lines.

## Goals / Non-Goals

**Goals:**
- Let a user get every photo's timestamp (paired with its filename) without opening EXIF viewers, in a form directly pasteable into `text_labels`.
- Make an empty `text: ""` stub visually inert when run through the real rendering pipeline, so pasting unfilled stubs into a config and generating is harmless.

**Non-Goals:**
- No modification of the config file itself (confirmed in prior discussion - stdout only, no ruamel.yaml, no comment-preserving round-trip).
- No merging/deduplication against the config's existing `text_labels` (confirmed - always print the full stub set; user merges by hand).
- No stub generation for `title` entries - titles are deliberate section markers the user adds, not a per-photo concept.
- No change to association (`find_closest_photo`), validation, or output-generation behavior beyond the one rendering guard.

## Decisions

**CLI surface: a flag on the existing command, not a group.** `--extract-labels` on `main`, short-circuiting after photo collection and before theme load. Rejected converting `cli.py` to a `click.group()` (would break `photobook --config file.yaml` as an invocation for existing users/scripts) and a second console-script entry point (two binaries to install/document for one small feature). Confirmed with user.

**Stub timestamps always sorted chronologically, independent of `layout.order`.** The whole point of the flag is timestamp discovery, so output order should reflect time even when the config's `layout.order` is `alphabetical`. Implementation sorts the collected photos by `sort_date` for this operation specifically, regardless of what `collect_photos` was asked to produce for normal generation.

**Grouping identical timestamps: group by exact `sort_date` equality, one stub per group.** After sorting by `sort_date`, photos with an identical timestamp are adjacent; group consecutively and join filenames with `, ` in a trailing YAML comment. Confirmed with user (one entry is fine; filenames included for traceability).

**Output is hand-formatted YAML text, not `yaml.safe_dump`.** PyYAML's dumper has no way to emit a trailing inline comment per entry, and offers no benefit here since the structure is a flat, fixed shape (`timestamp`, `text`, one comment). The extraction code builds the block directly as formatted strings: 2-space list indentation, ISO-8601 timestamp quoted (`photo.sort_date.isoformat()`, no timezone - matches the naive datetimes already used throughout, and the existing example configs' string style), `text: ""`, comment appended after the timestamp line. This keeps output byte-for-byte predictable and avoids a dependency for a one-shot flat print.

**Renderer guard lives inside `render_text_label`, before any drawing.** After `parsed_lines = parse_markdown_text(text_label.text)`, return immediately if `parsed_lines` is empty - skipping both the background-box draw and the text draw. This is the single call site for photo-caption text rendering, so a guard here covers the empty-stub case without touching the call site's existing `spec.text` / truthiness check at renderer.py:590 (that check gates on the layout template having a text slot at all, a different and unrelated concern).

**`--extract-labels` combined with `--output` ignores `--output` silently.** Since `--extract-labels` short-circuits before the output stage entirely, `--output` simply has no effect when both are passed. Not worth a warning for this niche combination; documented in `--help` text instead.

## Risks / Trade-offs

- **Photos sharing an identical timestamp collapse to one stub, so they can't get distinct captions without manual timestamp adjustment.** This mirrors an existing limitation in `associate_text_labels_with_photos` (it can already only bind one label per unique timestamp value to one photo) - not a new problem, but the filename comment on the collapsed stub is the only mitigation offered: the user can see multiple filenames share a slot and knows to offset one manually if distinct captions are needed.
- **Photos without EXIF fall back to file modification time**, which can reflect a copy/import date rather than capture date, producing a misleading stub timestamp. This is inherited from `collect_photos`'s existing fallback/warning behavior; no new mitigation added here.

## Migration Plan

Purely additive: one new CLI flag and one rendering guard, no data or config migration. Rollback is a plain revert.
