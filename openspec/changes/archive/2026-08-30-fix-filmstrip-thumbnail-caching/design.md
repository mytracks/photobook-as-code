## Context

See `proposal.md` for the bug and its root cause. Relevant current state (`webapp/`):

- `GET /items/<index>/thumbnail` (`app.py`) resolves `index` to a `PhotoMetadata` via `EditorData.photo_at(index)` - a position in the *merged* item+title sequence - then serves it with `Cache-Control: public, immutable, max-age=31536000`.
- `ThumbnailCache.get(photo)` (`data.py`) already keys its *internal* dict by `str(photo.path)`, not by index - that part was already position-independent. The bug is entirely in the externally-visible URL the browser caches against, which is index-based.
- `PhotoMetadata` (`photos.py`) already carries `file_modified` (a `datetime`, read from `stat().st_mtime` during the directory scan) alongside `path` and `filename` - no new data collection is needed for this fix.
- The photo-directory scan itself (`collect_photos`, via `PhotoDirectoryCache`) only runs once per server process and is already documented elsewhere as not detecting mid-session directory changes - restart is the only way new/changed photos are picked up. This fix is about what happens *after* such a restart, from a browser that was already open before it.

## Goals / Non-Goals

**Goals:**
- Make the thumbnail URL's identity depend only on the photo's own file (path + modification time), never on its position in any ordering - so the existing long-lived cache policy's promise becomes true instead of false.
- Keep the fix minimal and targeted: same cache policy, same `ThumbnailCache`, just a different, stable identifier feeding both the cache's internal key and the externally-visible URL.

**Non-Goals:**
- Not touching `/items/<index>/image` (the main per-item display route) - it has no caching today, so it isn't exposed to this bug. The same trap would apply if it were ever cached the same way; left as a noted risk, not fixed here, per the proposal's scope.
- Not adding live detection of photo-directory changes mid-session - out of scope, unrelated to this bug (which is specifically about what a *browser* does with a *stale cache entry* across a restart it doesn't know happened).
- Not preserving the old `/items/<index>/thumbnail` URL shape for backward compatibility - this is a local, single-session editing tool with no persisted/bookmarked deep links to individual endpoints, so there's nothing external to preserve compatibility for.

## Decisions

### 1. Identity key = short hash of `(resolved path, file_modified)`, not the raw filename
A raw filename isn't safe to use directly: the config supports multiple `photo_folders`, and two different folders could contain same-named files (already handled elsewhere in this codebase by resolving and deduplicating on the *full* path, not the filename, in `discover_photos`). Hashing `f"{photo.path}:{photo.file_modified.isoformat()}"` (SHA-256, truncated to 16 hex chars) gives a short, URL-safe, deterministic token that:
- differs between two different files (via `path`), closing the title-shift and folder-reorder-after-restart cases;
- differs if the same filename's *content* is replaced in place (via `file_modified`), closing that narrower edge case too.

16 hex chars (64 bits) is far more than enough collision resistance for a book with any realistic number of photos - not a meaningful risk at this scale.

**Alternative considered**: query-string cache-busting (`?v=<generation>`, bumped on every title add/delete). Rejected as the primary fix - it invalidates *every* thumbnail on *any* title edit, even ones nowhere near the edit point, and does nothing for the photo-folder-plus-restart case the user specifically asked about. The identity-based key handles both cases naturally, with no invalidation at all for photos that didn't actually change.

### 2. New route, keyed by identity: `GET /photos/<key>/thumbnail`
Replaces `GET /items/<index>/thumbnail` outright (not added alongside it - see Non-Goals on backward compatibility). The handler resolves `key` back to a `PhotoMetadata` by computing the same key for every photo in `EditorData.photos` and matching - an O(n) lookup, same cost class as the filmstrip's own per-request item-list construction, which prior measurement already showed is sub-millisecond even at 600 photos with no `text_labels`.

### 3. `ThumbnailCache` reuses the same key function internally
`ThumbnailCache.get()` currently keys its dict by `str(photo.path)` alone (already position-independent, but not content-freshness-aware - a file replaced in place under the same name would keep returning the old cached bytes for the life of the server process, a much smaller-blast-radius version of the same class of bug, self-correcting on the next restart). Switching it to the same `(path, file_modified)` key used for the URL gives one source of truth for "what identifies a specific version of a specific photo," rather than two slightly different identity notions living in two places.

### 4. Filmstrip markup: `FilmstripItem` carries the key, not the index, for its thumbnail URL
`FilmstripItem.filename` (used today for the `alt` text) is unaffected. A new field carries the identity key so the template builds `url_for('photo_thumbnail', key=item.thumbnail_key)` instead of `url_for('item_thumbnail', index=item.index)`. The cell's own `data-index`/navigation `href` (used for click-to-navigate and highlighting) are untouched - only the *thumbnail image source* moves off index-based addressing; navigating the filmstrip is still, correctly, about merged-sequence position.

## Risks / Trade-offs

- **[Risk]** This is a breaking change to the thumbnail route's URL shape. → **Mitigation**: no external consumers of this URL exist (single-user local tool, no bookmarked deep links); flagged **BREAKING (internal only)** in the proposal for visibility, not because anything needs a migration path.
- **[Trade-off]** Hash-based URLs are not human-readable the way `/items/5/thumbnail` was. → Accepted: the position information a developer might want from the URL is already available elsewhere in the same markup (`data-index`, the cell's own navigation `href`), so nothing is lost, just moved.
- **[Risk]** O(n) key→photo resolution per thumbnail request instead of O(1) index lookup. → **Mitigation**: negligible at realistic book sizes, per prior measurement of comparable per-request work in this same route family.

## Migration Plan

Route-shape and internal-keying change to `webapp/app.py`, `webapp/data.py`, and `webapp/templates/editor.html`. Existing tests referencing `/items/<index>/thumbnail` need updating to the new shape (tracked in `tasks.md`). No YAML schema, CLI, or persisted-data changes. Rollback is reverting those files.
