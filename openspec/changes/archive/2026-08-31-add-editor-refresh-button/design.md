## Context

See `proposal.md` - Why for motivation. Two existing pieces of the webapp shape this design:

- `PhotoDirectoryCache` (`data.py`) caches the result of scanning the photo folder (EXIF reads etc.) for the lifetime of the running Flask process, keyed by `(photo_folders, order)`. `load_editor_data()` reloads the YAML config fresh on every request already; only this photo-scan cache goes stale when files are added/removed/renamed under an unchanged folder path.
- Nothing in `app.py` currently catches `ConfigurationError` or `PhotoCollectionError` (both raised from inside `load_editor_data()`); only `cli.py`'s startup path handles them. Any route that calls `load_editor_data()` - which is all of them - currently lets a bad config crash the request with an unhandled 500.

## Goals / Non-Goals

**Goals:**
- Let the user force a re-scan of the photo folder without restarting the server.
- Make a config/photo-path failure encountered after startup (via refresh or otherwise) fail as cleanly as a failure at startup does today.

**Non-Goals:**
- No automatic staleness detection or polling (confirmed manual-only).
- No change to `ThumbnailCache` (already self-corrects via its `(path, mtime)` key).
- No change to the batch settings/progress pages.
- No attempt to preserve the user's position across a refresh - always lands on item 0 by design (confirmed: this is what signals to the user that the refresh happened).

## Decisions

**Cache invalidation: add `PhotoDirectoryCache.clear()`.**
A single `self._cache.clear()` method on the existing class. Simplest option; considered re-keying by a folder mtime/listing hash instead (so any request would naturally self-invalidate), but that adds a stat() call to every request to solve a problem an explicit user action already solves more predictably.

**New endpoint: `POST /refresh`.**
Clears the cache and returns `{"status": "ok"}`. It does not itself call `load_editor_data()` or return a target index - unlike `add-title`/`delete-title`, the target is fixed (item 0), so the client redirects there directly after the call succeeds. Client flow mirrors the existing add-title/delete-title pattern: `save()` (per the modified requirement, pending text is saved first) `.then(fetch POST /refresh).then(() => window.location.href = "/items/0")`.

**Error handling: Flask-level `errorhandler`s, not per-route try/except.**
Register `@app.errorhandler(ConfigurationError)` and `@app.errorhandler(PhotoCollectionError)` once, rendering a new `error.html` template with the exception's message and a "Try again" link back to the same path (`request.path`), returning HTTP 500. Because every route already funnels through `load_editor_data()`, this single registration covers `view_item`, `item_image`, `photo_thumbnail`, `save_text`, `save_title`, `add_title`, `reverse_geocode_item`, and `delete_title` without touching each route body - the alternative (wrapping every call site in try/except) would duplicate the same handling eight times for no behavioral difference. This also naturally covers the `/refresh`-triggered follow-up navigation to `/items/0`, since that's just an ordinary `view_item` request once the client redirects.
`error.html` keeps the same dark theme as the rest of the editor (per the existing "present the editor in a dark theme" requirement, which this page is still part of).

**Refresh control: icon + visible "Refresh" label, placed next to "Batch…".**
Consistent with the existing `header-actions` icon+label style used for less-frequent, more-discoverable actions (`Add title before this photo`). Grouped with "Batch…" because both are item-independent, whole-book actions, distinct from the photo/title-specific controls (geo, maps, add/delete title) that the spec already pins to a specific relative order. A new `icon-refresh` sprite symbol is added alongside the existing ones in `editor.html`; the exact glyph is a visual detail with no spec-level requirement.

## Risks / Trade-offs

- [Risk] Registering the error handlers is a behavior change for every existing route, not just the new one → Mitigation: this is intentional and matches the modified spec requirement's broadened scope (approved during exploration); the failure mode it replaces (unhandled 500) was strictly worse.
- [Risk] `PhotoDirectoryCache` has no locking; clearing it while another request is mid-scan is theoretically racy → Mitigation: this is an existing characteristic of the cache (a single-operator local dev tool, per its own docstring's "one running editor session" assumption), not something this change introduces or worsens.
- [Risk] Always landing on item 0 loses the user's place in a large book → Mitigation: explicitly the desired behavior - confirmed that reaching item 0 is itself meant to be the visible confirmation that refresh did something.
- [Risk] The friendly error message is only as good as `str(ConfigurationError)`/`str(PhotoCollectionError)` → Mitigation: these are the same exceptions and messages already relied on at CLI startup, so message quality is unchanged, just displayed in HTML instead of on stderr.

## Migration Plan

No data or config schema changes; purely additive to the webapp. Deploy is a normal code update; rollback is a normal revert with no cleanup required.
