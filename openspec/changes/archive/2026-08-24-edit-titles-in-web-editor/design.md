## Context

See `proposal.md` - Why/What Changes for motivation and scope.

Two pieces already exist and are reused as-is:
- `text_labels.parse_title_labels(text_labels)` - extracts `TitleLabel` entries from the raw config list.
- `text_labels.merge_titles_with_photos(titles, photos)` - the renderer's own ordering function: inserts each title immediately before the first photo whose `sort_date >= title.timestamp` (ties go to the title), appending any remaining titles at the end.

Today `webapp/data.py`'s `EditorData` only ever builds a `photos` list plus a parallel `associations: List[Tuple[PhotoMetadata, Optional[TextLabel]]]` list for captions; titles are never parsed. `webapp/yaml_store.py` only knows how to insert/update a `text` caption entry (`insert_new_entry`, `save_photo_text`, `find_entry_index`) - there is no title-entry insert, lookup, or delete.

## Goals / Non-Goals

**Goals:**
- Make the editor's browsable sequence match the renderer's actual merged photo+title order, so what the user pages through is what will end up in the book.
- Add title create/edit/delete without introducing a second, parallel ordering mechanism - reuse `merge_titles_with_photos` rather than re-deriving placement logic in the web layer.

**Non-Goals:**
- Reordering titles independently of timestamp (e.g. drag-and-drop) - placement is still purely timestamp-driven, as it is for the renderer.
- Editing a title's timestamp directly, or moving an existing title to a different photo - only create-before-current-photo and delete are in scope.
- Any change to `text_labels` validation, schema, or the render pipeline itself.

## Decisions

### Merged sequence replaces the photo-only sequence
`EditorData` builds its item list as `merge_titles_with_photos(parse_title_labels(config.text_labels), photos)`, giving a single ordered list of `PhotoMetadata | TitleLabel`. `index` now addresses this merged list. Caption `associations` are still computed only against the underlying `photos` list (captions only ever attach to photos), and looked up via the photo's own position when the current item is a photo.

**Alternative considered**: keep two separate index spaces (a photo index and a title index) with a mapping table. Rejected - it would require re-deriving the same interleaving `merge_titles_with_photos` already computes, in two places, and the merged-index approach mirrors the renderer's own model directly.

### Routing: `/photos/<index>` becomes `/items/<index>`
A single GET route renders either a photo view (image + caption field + "Add title" action) or a title view (no image + title text field + "Delete title" action), branching on the item's type at that index. This is a breaking rename (per proposal), acceptable for a local single-user tool with no persisted links; the README describes only the CLI entry point, not routes, so needs no route-specific update.

Mutation endpoints, scoped to what's valid for the item type at that index:
- `POST /items/<index>/text` - save caption text (photo items only; same behavior as today's `/photos/<index>/text`, renamed).
- `POST /items/<index>/title` - save title text (title items only).
- `POST /items/<index>/add-title` - create a new, empty title positioned immediately before the photo at `<index>` (photo items only).
- `POST /items/<index>/delete-title` - delete the title at `<index>` (title items only).

Each mutation endpoint 400s (not 404s - the index itself is valid) if called against an item of the wrong type, mirroring the existing `abort(400)` pattern for malformed payloads in `app.py`.

### New title placement uses the photo's own timestamp
`add-title` calls a new `yaml_store.insert_new_title_entry(document, photo, title_text="")`, structurally parallel to the existing `insert_new_entry` for captions: same chronological-insert-into-`text_labels` logic, writing `title` instead of `text`, timestamped with `photo.sort_date`. No new ordering logic is needed - `merge_titles_with_photos`'s `<=` tie-break already guarantees this timestamp sorts the title immediately before that specific photo on the next load.

### Title entry identity for edit/delete
A title's YAML entry is located the same way a caption's is - by matching `(timestamp, content)` against the freshly-loaded document, mirroring `find_entry_index`. This is a new `find_title_entry_index` (or an extension of the existing lookup) matching on `title` instead of `text`. This carries the same pre-existing, non-new ambiguity as caption lookup: two entries with identical timestamp and identical text are indistinguishable. Acceptable - it's the same risk the caption editor already accepts today.

### Redirect targets after add/delete reuse index arithmetic, not lookup
Because the new title is inserted immediately before the photo at `<index>` in the merged sequence, that photo's own position shifts to `<index> + 1` and the new title takes `<index>`. The client redirects to the same numeric `<index>` after `add-title` - which now shows the newly created title, ready for editing (reusing the existing session-storage auto-focus flag pattern from caption editing).

Symmetrically, deleting the title at `<index>` shifts everything after it back by one, so the item that was previously at `<index> + 1` (the following photo, per the proposal) now occupies `<index>`. The client redirects to that same numeric `<index>`. If the deleted title was the last item in the sequence (no following item), the client redirects to `<index> - 1` instead; if that is also out of range (the sequence is now empty), it falls back to the editor's root redirect.

## Risks / Trade-offs

- **Breaking route change** (`/photos/` → `/items/`) → Mitigated by scope: no external consumers, no bookmarks worth preserving for a locally-run single-user editor.
- **`merge_titles_with_photos` assumes a roughly chronological `photos` order** to produce sensible placement; with `layout.order: alphabetical` the "before this photo" placement can look surprising relative to wall-clock time → Not a new risk: the renderer already has this exact behavior for existing titles today: this change doesn't introduce a new failure mode, it just makes the existing one visible/interactive in the editor.
- **Ambiguous entry identity on exact timestamp+text duplicates** (edit/delete could resolve to the wrong entry) → Pre-existing risk, already accepted for captions; not worsened by titles.
