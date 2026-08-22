## 1. Project setup

- [x] 1.1 Add `Flask` and `ruamel.yaml` to `pyproject.toml` dependencies
- [x] 1.2 Create the `src/photobook_as_code/webapp/` package (`__init__.py`, `app.py`, `yaml_store.py`, `templates/`, `static/`)
- [x] 1.3 Add the `photobook-edit-labels` console script entry to `pyproject.toml`

## 2. Round-trip YAML store

- [x] 2.1 Implement `yaml_store.py`: load the config file with `ruamel.yaml.YAML(typ="rt")` into a `CommentedMap`
- [x] 2.2 Implement lookup of the `text_labels` entry index for a given photo, by matching a `TextLabel` (from `text_labels.associate_text_labels_with_photos`) back to its source index in the plain-dict `config.text_labels` list
- [x] 2.3 Implement updating an existing entry's `text` scalar in the ruamel document by index
- [x] 2.4 Implement inserting a new entry (timestamp, text, filename comment) at the correct chronological position, creating the `text_labels` key at the document root if absent
- [x] 2.5 Implement safe write-back: write to a temp file in the same directory, then `os.replace` onto the original path
- [x] 2.6 Unit tests: editing an existing entry preserves all other entries' comments, order, and formatting (see design.md's documented ruamel blank-line limitation for the one known exception)
- [x] 2.7 Unit tests: inserting a new entry for a photo with no prior association (including into a file with no `text_labels` section at all) lands in chronological order with a correct filename comment
- [x] 2.8 Unit tests: `title` entries are never altered, moved, or removed by either update or insert paths

## 3. Read-side wiring (photo list + associations)

- [x] 3.1 Implement a request-scoped loader that calls `load_config()`, `validate_photos_path()`, and `collect_photos()` to produce the ordered photo list for a given config path
- [x] 3.2 Implement per-photo lookup of current text via `associate_text_labels_with_photos`, returning empty string when no association exists
- [x] 3.3 Unit tests: photo order in the editor matches `collect_photos()` order for both `alphabetical` and `date` `layout.order` settings

## 4. Flask routes

- [x] 4.1 `GET /` — redirect to `/photos/0`
- [x] 4.2 `GET /photos/<int:index>` — render the photo-editing page (image, textarea pre-filled with current text, prev/next controls, disabled at the first/last photo)
- [x] 4.3 `GET /photos/<int:index>/image` — stream a downscaled (e.g. max ~1600px) JPEG rendition of the photo via Pillow
- [x] 4.4 `POST /photos/<int:index>/text` — save the submitted text via the YAML store (update-or-insert) and return a JSON save confirmation
- [x] 4.5 Return a 404/clear error for an out-of-range photo index
- [x] 4.6 Integration tests (Flask test client) covering: viewing a photo, saving new text, saving an edit to existing text, saving empty text, out-of-range index

## 5. Frontend

- [x] 5.1 Base Jinja2 template: photo image, plain `<textarea>`, prev/next buttons, photo position indicator (e.g. "12 / 277")
- [x] 5.2 Minimal CSS: modern, plain, no decorative/playful styling
- [x] 5.3 Small vanilla-JS: fire the save request on textarea `blur` and before a prev/next navigation completes; show a brief "Saved" indicator on success
- [x] 5.4 Keyboard navigation (left/right arrow or similar) between photos, without stealing focus from the textarea while typing

## 6. CLI entry point

- [x] 6.1 Implement `photobook-edit-labels` Click command: `--config` (required), `--host` (default `127.0.0.1`), `--port` (default `5000`)
- [x] 6.2 Eagerly call `load_config()` / `validate_photos_path()` at startup and exit with the existing clear error messages on failure, before starting the server
- [x] 6.3 CLI test: invalid config path and unreadable photo directory both fail fast with a clear message and non-zero exit code

## 7. Documentation

- [x] 7.1 Add a "Web Editor" section to `README.md` describing `photobook-edit-labels`, what it edits (text only, not titles), and that it writes directly to the given YAML file
