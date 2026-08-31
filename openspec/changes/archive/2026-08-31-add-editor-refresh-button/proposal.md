## Why

The per-item web editor's photo listing is scanned once and cached for the life of the running server process. When a user adds, removes, or renames photos in the configured folder while the editor is still open, those changes never appear until the process is restarted, even though hand-edited YAML content (captions, titles) already reloads fresh on every navigation. Users need an explicit way to tell the editor "re-check the disk," and that same action is the moment most likely to expose a related gap: if a hand-edit leaves the YAML briefly invalid, the editor currently crashes with a raw, unhandled error instead of a clear message.

## What Changes

- Add a "Refresh" control to the per-item editor's header, available for both photo and title items, that saves any pending text edit and then re-scans the photo folder from disk, bypassing the process-lifetime photo listing cache.
- After refreshing, always navigate to the first item in the (freshly computed) sequence, so the navigation itself confirms the refresh happened.
- The refresh is manual only (no polling, no automatic staleness detection) and has no keyboard shortcut.
- The thumbnail cache is left untouched by refresh; it is already keyed by each photo's path and modification time, so a replaced file already gets a fresh thumbnail on next access without needing invalidation.
- When loading the configuration or photo folder fails (invalid YAML, unreadable or misconfigured photo path) during a running session - most likely to happen right after the user hand-edits the file and clicks Refresh, but possible on any navigation - the editor SHALL show a clear, friendly error page instead of an unhandled server error. This closes an existing gap: today only the CLI startup path reports these errors cleanly; the running Flask app does not.
- Out of scope: the batch settings and batch progress pages are not affected by this change.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `text-label-web-editor`: adds a requirement for a manual refresh control that re-scans the photo folder and lands on the first item, and adds a requirement that configuration/photo-folder load failures during a running session are reported clearly instead of crashing.

## Impact

- `src/photobook_as_code/webapp/app.py`: new `POST /refresh` route; error handling around configuration/photo loading shared by that route and the existing per-item routes.
- `src/photobook_as_code/webapp/data.py`: a way to drop `PhotoDirectoryCache`'s cached scan so the next load re-scans from disk.
- `src/photobook_as_code/webapp/templates/editor.html`: new header control.
- `src/photobook_as_code/webapp/static/editor.js`: click handler that saves, calls the new endpoint, and navigates to item 0.
- A new template (or reused error rendering) for the friendly configuration-error page.
- Tests: `tests/test_webapp_app.py`, `tests/test_webapp_data.py`.
