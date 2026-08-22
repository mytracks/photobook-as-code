## Why

To write a `text_labels` entry, the user must already know a photo's timestamp - today the only way to find it is to inspect each photo's EXIF data by hand. This change adds a CLI flag that extracts every photo's timestamp from a config's photo directory and prints ready-to-paste, empty `text_labels` stubs, so timestamps can be discovered without manual EXIF lookups.

## What Changes

- Add an `--extract-labels` flag to the `photobook` command. When passed, the CLI loads the config, collects photos (same EXIF/mtime logic used for generation), and prints a `text_labels:` YAML block to stdout - one stub entry per distinct photo timestamp, each with `text: ""` - then exits without loading a theme, computing layout, or rendering/writing any output file.
- Photos sharing the exact same timestamp collapse into a single stub entry; that entry's trailing YAML comment lists all contributing filenames (comma-separated) so the timestamp can be traced back to its photo(s).
- Stub entries are sorted chronologically, independent of the config's `layout.order` setting.
- This flag does not read or merge against the config's existing `text_labels` section at all - output is always the full set of stubs for every photo, for the user to copy/merge by hand.
- **Fix:** `render_text_label` currently has no early-return for empty content - a `text: ""` entry (or one that parses to zero content lines) still computes a non-zero box height from padding alone and, under themes with `text_background_enabled: true` (the `clean` default), draws a visible background rectangle with no text in it. Add a guard so empty/blank text renders nothing at all - no text, no background. This is required for the extracted stubs to be safe to run through the full pipeline unfilled.

## Capabilities

### New Capabilities
- `label-timestamp-extraction`: CLI flag that extracts photo timestamps from a config's photo directory and prints empty `text_labels` stub entries (grouped by identical timestamp, annotated with source filenames) to stdout.

### Modified Capabilities
- `text-labels`: A `text` label whose content is empty, or parses to zero content lines, renders no visual output (no text, no background) instead of drawing an empty background box.

## Impact

- `src/photobook_as_code/cli.py`: new `--extract-labels` option on `main`; short-circuit branch that collects photos and prints stubs instead of generating a photobook.
- `src/photobook_as_code/renderer.py`: `render_text_label` gains an early-return guard for empty/blank parsed content.
- No new dependencies - the config's existing `text_labels` value is not touched, so no YAML round-trip/comment-preservation concerns apply.
- No changes to `config.py` validation, association logic, or output generation.
