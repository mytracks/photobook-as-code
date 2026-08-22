## Why

Navigating between photos in the web editor is noticeably slow (~550ms per click, measured against a real 168-photo album). The cause isn't missing prefetching — it's that every request (`view_photo`, `photo_image`, and `save_text` each independently) re-scans the *entire* photo directory, opening every single photo file with PIL to read its EXIF date and dimensions, even though only one photo is actually needed. A single "type a caption, click Next" round trip triggers that full rescan three times, wasting ~450ms rescanning 167 photos the user isn't even looking at.

## What Changes

- Cache the expensive part of loading editor data (the photo-directory scan: paths, EXIF dates, dimensions) for the lifetime of a running editor server process, computed once instead of on every request.
- Keep the YAML configuration (including `text_labels`/captions) fully re-parsed on every request, unchanged from today — that part is cheap and correctness-critical (edits must show up immediately).
- **Trade-off, accepted deliberately**: photos added, removed, or renamed in the photo directory while the editor server is running will not be picked up until the server is restarted. Today's implementation would pick these up immediately (as a side effect of rescanning on every request, not as a documented requirement). No existing spec requirement promises live directory-change detection, so this is not a spec regression — but it is a real, user-visible change from current behavior, called out here explicitly.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
(none — this is a pure performance/implementation change with no spec-level behavior change; see the accepted trade-off above, which isn't covered by any existing requirement)

## Impact

- `src/photobook_as_code/webapp/data.py`: new `PhotoDirectoryCache` class; `load_editor_data()` gains an optional `photo_cache` parameter (default `None` = today's always-fresh behavior, used by the CLI's startup validation call and existing tests).
- `src/photobook_as_code/webapp/app.py`: `create_app()` creates one `PhotoDirectoryCache` instance and passes it to every `_load_data_or_404()` call.
- No changes to the YAML round-trip writer, autosave behavior, routes' request/response contracts, or any spec-level requirement.
- No new dependencies.
