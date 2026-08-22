## Context

See `proposal.md` for motivation. Relevant current state:

- `config.load_config()` parses the YAML with plain `yaml.safe_load` — read-only, no round-trip/write path exists anywhere in the codebase today.
- `photos.collect_photos()` discovers and orders photos per `layout.order`.
- `text_labels.associate_text_labels_with_photos(text_labels, photos)` is a pure function that returns `(photo, TextLabel | None)` pairs by nearest-timestamp matching; it already silently skips `title`-only entries (KeyError on `data['text']`, caught).
- Real configs (`sevilla.yaml`) are large (277 `text_labels` entries) and carry per-entry `# filename.jpg` comments that are load-bearing for the user's workflow.
- The project has no web framework, no YAML-writing dependency, and no long-running server process today — `photobook` is a single one-shot Click command.

## Goals / Non-Goals

**Goals:**
- Reuse the existing pure read-side logic (`load_config`, `collect_photos`, `associate_text_labels_with_photos`) unchanged.
- Persist edits with a round-trip-safe YAML writer so comments, ordering, and `title:` entries survive untouched.
- Keep the server stateless across requests (always reflects the file's current on-disk content).

**Non-Goals** (see proposal.md for the full list): title editing, Docker packaging, markdown preview, "next empty" navigation, authentication/multi-user support.

## Decisions

### 1. New module: `src/photobook_as_code/webapp/`
- `yaml_store.py` — round-trip load/save built on `ruamel.yaml.YAML(typ="rt")`.
- `app.py` — Flask app factory `create_app(config_path: Path) -> Flask`.
- `templates/`, `static/` — server-rendered Jinja2 page + minimal CSS, no JS build step.
- New console script `photobook-edit-labels` (own `main()`/Click command), separate from `photobook`.

**Alternative considered**: add a `--serve`/`--edit` flag to the existing `photobook` Click command. Rejected — that command's lifecycle (load → render → exit, with a progress bar) doesn't mix well with a long-running server process, and a separate entry point maps directly to a distinct process/entrypoint when this gets containerized later.

### 2. Keeping two parses of the same file in sync
Each request re-parses the config file twice, fresh:
1. `load_config()` (existing, plain `yaml.safe_load`) → used for `photos`, `output`, `layout`, `theme`, and as the plain-dict source for matching.
2. `ruamel.yaml.YAML(typ="rt").load(...)` → a mutable, comment-preserving `CommentedMap` used only for writing.

Since both parses read the identical, unmodified file, the index of a given entry in `config.text_labels` (plain list, from parse #1) is the same index as the corresponding node in the ruamel `text_labels` `CommentedSeq` (parse #2). `associate_text_labels_with_photos` is called against parse #1 exactly as today (no changes to `text_labels.py`); the resulting `TextLabel` is matched back to its source index by scanning `config.text_labels` for the dict it came from. That index is what the write path uses to locate the node to mutate in parse #2.

Re-parsing per request (rather than caching server-side state) means the editor always reflects the file's actual current content — including if the user hand-edits the file in another window between requests — and stays correct with zero cache-invalidation logic. At realistic file sizes (hundreds of entries) this costs milliseconds; not a concern.

**Alternative considered**: parse once with ruamel only, and derive photo/order/text_labels from the `CommentedMap` directly, dropping `yaml.safe_load` entirely. Rejected for this change — it would mean either duplicating `load_config`'s validation logic against ruamel's data structures, or loosening `text_labels.py`'s pure-dict interface; re-parsing twice is a few extra milliseconds and keeps all existing modules completely untouched.

### 3. Saving an edit
`POST /photos/<index>/text`:
1. Re-parse (both ways), recompute the association for `photos[index]`.
2. **Existing entry found** → set that ruamel mapping node's `text` value to the new string. Ruamel preserves the node's own comment and the rest of the document automatically since only the scalar changes.
3. **No entry found** → build a new mapping (`timestamp: <photo's ISO timestamp>`, `text: <new text>`) with an end-of-line filename comment, matching the convention already used by `--extract-labels`. Insert it into the `text_labels` sequence in chronological position (scan by timestamp; append if latest). Create the `text_labels` key at the document root first if the file has none yet.
4. Write back via a temp-file-then-`os.replace` in the same directory, so a crash mid-write can't truncate the user's file.
5. Respond with a small JSON status the frontend uses to show a "Saved" indicator.

### 4. Frontend
Server-rendered Jinja2, one page per photo at `GET /photos/<index>`. A small vanilla-JS snippet fires the save `fetch()` on textarea `blur` and before a prev/next click completes; no SPA framework, no Node build step — keeps the eventual Docker image simple and matches "modern but simple". The photo index lives in the URL path, so reloading or bookmarking a specific photo works without any client-side state.

### 5. Photo image serving
`GET /photos/<index>/image` opens the source file with the already-present Pillow dependency, downscales it (e.g. longest edge ~1600px) and streams it as JPEG. Print-resolution originals (300 DPI) can be tens of MB; sending them to the browser unmodified would be slow. No on-disk thumbnail cache in v1 — recomputed per request, acceptable for a single local user.

### 6. Framework choice: Flask
Per decision: lightweight, synchronous, minimal additional dependency surface (no ASGI server, no pydantic/starlette) for what is a handful of routes with no database.

### 7. `photobook-edit-labels` CLI
Click command: `--config` (required), `--host` (default `127.0.0.1`), `--port` (default `5000`). Calls `load_config()` and `validate_photos_path()` eagerly at startup — reusing the existing `ConfigurationError`/`PhotoCollectionError` messages — so a broken config or unreadable photo directory fails fast with a clear message before the server starts listening, satisfying the spec's startup-error requirement with no new error-handling code.

## Risks / Trade-offs

- **[Risk]** Re-parsing the whole file twice per request → negligible at real-world scale (277 entries parses in milliseconds); revisit only if a config ever grows to an unrealistic size.
- **[Risk]** Two new dependencies (`Flask`, `ruamel.yaml`) → both are small, pure-Python-friendly, widely used, no native build requirements beyond what Pillow/reportlab already need.
- **[Risk]** Writing the file while it's open in another editor can trigger that editor's "changed on disk" warning → inherent to any external tool editing a shared file; not solved here.
- **[Known limitation, not fixed here]** `ruamel.yaml`'s round-trip dump collapses one blank line when a mapping (e.g. `output:`, `layout:`) has multiple separate blank-line-separated comment-only groups trailing its last real key (verified against `sevilla.yaml`, `hamburg.yaml` — both round-trip perfectly; only `example-config.yaml`'s heavily-commented placeholder sections hit this). No key, value, or comment text is lost — only a spacing blank line in a comment-only region. Accepted as an inherent limitation of writing the whole document back through ruamel on every save, rather than patching the touched byte range directly (which was considered and rejected as disproportionate engineering for a cosmetic edge case that doesn't occur in real target files).
- **[Known limitation, not fixed here]** `associate_text_labels_with_photos` binds a text label to only the *first* photo among an identical-timestamp group (mirrors `--extract-labels`'s collapsing behavior). Browsing to a later photo in such a group shows an empty field, and saving text there creates a second entry at the same timestamp rather than editing the sibling. Pre-existing ambiguity in the underlying association logic, not introduced by this change.
- **[Trade-off]** No server-side session/cache state keeps the implementation simple and always-correct relative to the file on disk, at the cost of re-parsing per request — accepted given realistic file sizes.

## Migration Plan

Purely additive: new module, new console script, two new dependencies in `pyproject.toml`. No changes to `photobook`'s behavior, the config schema, or the render pipeline. Rollback is simply removing the new module/entry point/dependencies — there is no persisted state specific to the editor; the YAML files it produces remain ordinary valid `text_labels` configs.
