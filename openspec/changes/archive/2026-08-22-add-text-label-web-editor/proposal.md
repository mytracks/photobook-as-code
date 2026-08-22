## Why

Writing `text` captions into a `text_labels` YAML block today means cross-referencing timestamps and filename comments against a separate photo viewer by hand. Real configs make this painful at scale: `sevilla.yaml` already has 277 `text_labels` entries (mostly `text: ""` stubs produced by `--extract-labels`), and there is no way to see the photo a given entry refers to while typing its caption. A minimal browser-based editor that shows one photo at a time next to an editable text field removes that manual bookkeeping.

## What Changes

- New web application (Flask) that:
  - Displays photos one at a time, in the same order the CLI uses for layout (`layout.order`), with prev/next navigation.
  - Shows a plain `<textarea>` for the photo's associated `text_labels` entry — raw Markdown, no WYSIWYG editing, no rendered preview.
  - Autosaves the edited text to the YAML config file when the user navigates away from a photo (blur/prev/next), with a small saved-state indicator.
  - Serves photos read-only from the configured photo directory (resized for browser display; never writes to the photo directory).
- New round-trip-preserving YAML read/write layer (`ruamel.yaml`) that updates only the specific `text:` scalar belonging to the edited photo, leaving every other line — comments (e.g. `# IMG_0001.jpg`), key order, formatting, and any `title:` entries — byte-for-byte unchanged.
- Auto-creation of a missing `text_labels` entry the first time text is saved for a photo that has none yet, using the same timestamp/comment convention as `--extract-labels` (photo's own timestamp, `# filename.jpg` comment), inserted in chronological order. This means the editor can be used directly on a config with no `text_labels` at all — `--extract-labels` remains available for scripted/headless use but is no longer a required first step.
- New CLI entry point `photobook-edit-labels --config <file> [--host] [--port]` that starts a long-running local web server, kept separate from the existing one-shot `photobook` render command.
- New dependencies: `Flask`, `ruamel.yaml`.

**Out of scope for this change** (explicitly deferred):
- Editing `title:` entries (title entries are shown as read-only/skipped if encountered; editing them is a future change).
- Docker packaging/deployment of the editor.
- Markdown preview of the edited text.
- A "jump to next empty text" navigation aid or progress indicator.
- Authentication/multi-user support (single local user, matches how the CLI is used today).

## Capabilities

### New Capabilities
- `text-label-web-editor`: Browser-based editor for viewing photos and editing their `text_labels` `text` content directly against the YAML config file, including photo navigation, autosave, read-only photo serving, round-trip-safe persistence, and auto-creation of missing entries.

### Modified Capabilities
(none — `text-labels` and `yaml-configuration` requirements are unchanged; the editor is a new consumer/producer of the existing file format, not a change to parsing, association, or rendering behavior)

## Impact

- **New code**: a new web app module (routes, templates, YAML read/write helper), a new CLI entry point, new templates/static assets.
- **Reused, unchanged code**: `config.load_config`, `photos.collect_photos`, `text_labels.associate_text_labels_with_photos` (read-side logic is assembled from existing pure functions).
- **Dependencies**: adds `Flask` and `ruamel.yaml` to `pyproject.toml`.
- **Packaging**: adds a second console script (`photobook-edit-labels`) alongside the existing `photobook` script.
- **No impact** on the existing `photobook` render pipeline, output formats, or theme system.
